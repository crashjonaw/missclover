"""Stripe webhook signature verification + the paid/failed webhook flow.

Signature verification is security-critical: an unsigned or tampered webhook
must never flip an order to "paid".
"""
import hashlib
import hmac
import json
import time

import pytest

from models import Order, ProductVariant
from stripe_gateway import StripeError, verify_webhook


def _vid(products, code):
    return products[code].primary_variant.id


def _sig_header(payload: bytes, secret: str, timestamp: int | None = None) -> str:
    """Build a Stripe-Signature header the way Stripe signs webhooks:
    HMAC-SHA256 of "<timestamp>.<payload>" with the signing secret."""
    ts = timestamp if timestamp is not None else int(time.time())
    signed_payload = f"{ts}.".encode() + payload
    v1 = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={v1}"


_EVENT = {
    "id": "evt_test_1",
    "type": "payment_intent.succeeded",
    "data": {"object": {"id": "pi_test_123", "status": "succeeded",
                        "metadata": {"reference": "MC-2026-AAAAAA"}}},
}


# ─── verify_webhook (unit) ────────────────────────────────────────────────────


def test_valid_signature_constructs_event(app):
    secret = app.config["STRIPE_WEBHOOK_SECRET"]
    payload = json.dumps(_EVENT).encode()
    header = _sig_header(payload, secret)
    with app.app_context():
        event = verify_webhook(payload, header)
        assert event["type"] == "payment_intent.succeeded"
        assert event["data"]["object"]["id"] == "pi_test_123"


def test_wrong_secret_rejected(app):
    payload = json.dumps(_EVENT).encode()
    header = _sig_header(payload, "whsec_not_the_real_secret")
    with app.app_context():
        with pytest.raises(StripeError):
            verify_webhook(payload, header)


def test_tampered_payload_rejected(app):
    secret = app.config["STRIPE_WEBHOOK_SECRET"]
    payload = json.dumps(_EVENT).encode()
    header = _sig_header(payload, secret)
    tampered = payload.replace(b"pi_test_123", b"pi_evil_999")
    with app.app_context():
        with pytest.raises(StripeError):
            verify_webhook(tampered, header)


def test_empty_signature_rejected(app):
    payload = json.dumps(_EVENT).encode()
    with app.app_context():
        with pytest.raises(StripeError):
            verify_webhook(payload, "")


def test_missing_secret_raises(app):
    payload = json.dumps(_EVENT).encode()
    header = _sig_header(payload, "whsec_anything")
    app.config["STRIPE_WEBHOOK_SECRET"] = ""
    with app.app_context():
        with pytest.raises(StripeError):
            verify_webhook(payload, header)


def test_stale_timestamp_rejected(app):
    """Stripe's construct_event enforces a timestamp tolerance (replay guard)."""
    secret = app.config["STRIPE_WEBHOOK_SECRET"]
    payload = json.dumps(_EVENT).encode()
    header = _sig_header(payload, secret, timestamp=1)  # 1970 — way outside tolerance
    with app.app_context():
        with pytest.raises(StripeError):
            verify_webhook(payload, header)


# ─── Webhook endpoint (integration) ───────────────────────────────────────────


def _post_webhook(client, app, event: dict):
    payload = json.dumps(event).encode()
    header = _sig_header(payload, app.config["STRIPE_WEBHOOK_SECRET"])
    return client.post("/checkout/stripe-webhook", data=payload,
                       content_type="application/json",
                       headers={"Stripe-Signature": header})


def _pending_order(client, products, stripe_stub):
    """Drive a guest order to the pending state and return it."""
    client.post("/cart/add", data={"variant_id": _vid(products, "classic"), "qty": 1})
    client.post("/checkout/start", data={"action": "guest", "email": "g@g.com"})
    client.post("/checkout/shipping", data={
        "recipient_name": "G", "line1": "L", "postcode": "123456", "phone": "91234567"})
    client.get("/checkout/payment")
    return Order.query.first()


def test_webhook_marks_order_paid_and_decrements_stock(app, client, products, stripe_stub):
    order = _pending_order(client, products, stripe_stub)
    pi_id = order.stripe_payment_intent_id
    variant_id = order.items[0].variant_id
    before = ProductVariant.query.get(variant_id).stock_qty

    event = {
        "id": "evt_1", "type": "payment_intent.succeeded",
        "data": {"object": {"id": pi_id, "status": "succeeded",
                            "metadata": {"reference": order.order_number}}},
    }
    r = _post_webhook(client, app, event)
    assert r.status_code == 200

    refreshed = Order.query.get(order.id)
    assert refreshed.status == "paid"
    assert refreshed.paid_at is not None
    assert ProductVariant.query.get(variant_id).stock_qty == before - 1


def test_webhook_is_idempotent(app, client, products, stripe_stub):
    order = _pending_order(client, products, stripe_stub)
    variant_id = order.items[0].variant_id
    before = ProductVariant.query.get(variant_id).stock_qty
    event = {
        "id": "evt_1", "type": "payment_intent.succeeded",
        "data": {"object": {"id": order.stripe_payment_intent_id, "status": "succeeded",
                            "metadata": {"reference": order.order_number}}},
    }
    _post_webhook(client, app, event)
    _post_webhook(client, app, event)  # duplicate delivery
    # Stock decremented exactly once
    assert ProductVariant.query.get(variant_id).stock_qty == before - 1


def test_webhook_payment_failed_cancels_order(app, client, products, stripe_stub):
    order = _pending_order(client, products, stripe_stub)
    event = {
        "id": "evt_2", "type": "payment_intent.payment_failed",
        "data": {"object": {"id": order.stripe_payment_intent_id, "status": "requires_payment_method",
                            "metadata": {"reference": order.order_number}}},
    }
    r = _post_webhook(client, app, event)
    assert r.status_code == 200
    assert Order.query.get(order.id).status == "cancelled"


def test_webhook_bad_signature_returns_400(client):
    r = client.post("/checkout/stripe-webhook", data=b"{}",
                    content_type="application/json",
                    headers={"Stripe-Signature": "t=1,v1=deadbeef"})
    assert r.status_code == 400
