"""Checkout flow: trifecta start (sign-in / register / continue-as-guest), shipping, payment.

The Stripe gateway is stubbed via the `stripe_stub` fixture so tests never hit
the network.
"""
import pytest

from models import Address, Order, User


def _vid(products, code):
    return products[code].primary_variant.id


# ─── /checkout/start guards ──────────────────────────────────────────────────


def test_checkout_start_redirects_if_cart_empty(client):
    r = client.get("/checkout/start")
    assert r.status_code == 302
    assert "/cart/" in r.headers["Location"]


def test_checkout_start_renders_trifecta_with_cart(client, products):
    client.post("/cart/add", data={"variant_id": _vid(products, "classic"), "qty": 1})
    r = client.get("/checkout/start")
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    # All three options visible
    assert "Sign in" in body
    assert "Create account" in body
    assert "Continue as guest" in body


def test_checkout_start_logged_in_skips_to_shipping(signed_in, products):
    signed_in.post("/cart/add", data={"variant_id": _vid(products, "classic"), "qty": 1})
    r = signed_in.get("/checkout/start")
    assert r.status_code == 302
    assert "/checkout/shipping" in r.headers["Location"]


# ─── Guest path ──────────────────────────────────────────────────────────────


def test_guest_action_sets_email_and_redirects_to_shipping(client, products):
    client.post("/cart/add", data={"variant_id": _vid(products, "classic"), "qty": 1})
    r = client.post("/checkout/start", data={"action": "guest", "email": "guest@example.com"})
    assert r.status_code == 302
    assert "/checkout/shipping" in r.headers["Location"]


def test_guest_email_validation(client, products):
    client.post("/cart/add", data={"variant_id": _vid(products, "classic"), "qty": 1})
    r = client.post("/checkout/start", data={"action": "guest", "email": "not-an-email"})
    # re-renders with error
    assert r.status_code == 200
    assert b"valid email" in r.data


def test_guest_shipping_form_requires_authorisation(client, products):
    """Without going through /checkout/start (no guest email in session), shipping should bounce."""
    client.post("/cart/add", data={"variant_id": _vid(products, "classic"), "qty": 1})
    r = client.get("/checkout/shipping")
    assert r.status_code == 302
    assert "/checkout/start" in r.headers["Location"]


def test_guest_full_to_shipping_to_payment(client, products):
    client.post("/cart/add", data={"variant_id": _vid(products, "classic"), "qty": 1})
    client.post("/checkout/start", data={"action": "guest", "email": "g@g.com"})

    r = client.post("/checkout/shipping", data={
        "recipient_name": "G Guest",
        "line1": "12 Test St",
        "line2": "",
        "postcode": "123456",
        "phone": "91234567",
    })
    assert r.status_code == 302
    assert "/checkout/payment" in r.headers["Location"]
    assert Address.query.count() == 1


def test_shipping_form_validates_required_fields(client, products):
    client.post("/cart/add", data={"variant_id": _vid(products, "classic"), "qty": 1})
    client.post("/checkout/start", data={"action": "guest", "email": "g@g.com"})
    r = client.post("/checkout/shipping", data={"recipient_name": "Only Name"})
    assert r.status_code == 200
    assert b"fill in all required fields" in r.data
    assert Address.query.count() == 0


# ─── Sign-in path ─────────────────────────────────────────────────────────────


def test_signin_action_correct_credentials(client, products, user):
    client.post("/cart/add", data={"variant_id": _vid(products, "classic"), "qty": 1})
    r = client.post("/checkout/start", data={
        "action": "signin", "email": "alice@example.com", "password": "password123"
    })
    assert r.status_code == 302
    assert "/checkout/shipping" in r.headers["Location"]


def test_signin_action_wrong_password(client, products, user):
    client.post("/cart/add", data={"variant_id": _vid(products, "classic"), "qty": 1})
    r = client.post("/checkout/start", data={
        "action": "signin", "email": "alice@example.com", "password": "wrong"
    })
    assert r.status_code == 200
    assert b"incorrect" in r.data


# ─── Register path ────────────────────────────────────────────────────────────


def test_register_action_creates_user_and_proceeds(client, products):
    client.post("/cart/add", data={"variant_id": _vid(products, "classic"), "qty": 1})
    r = client.post("/checkout/start", data={
        "action": "register",
        "email": "fresh@example.com", "password": "password123",
        "first_name": "F", "last_name": "L",
    })
    assert r.status_code == 302
    assert "/checkout/shipping" in r.headers["Location"]
    assert User.query.filter_by(email="fresh@example.com").first() is not None


def test_register_action_rejects_existing_email(client, products, user):
    client.post("/cart/add", data={"variant_id": _vid(products, "classic"), "qty": 1})
    r = client.post("/checkout/start", data={
        "action": "register",
        "email": "alice@example.com", "password": "password123",
        "first_name": "F", "last_name": "L",
    })
    assert b"already exists" in r.data


# ─── Payment (Stripe stubbed) ─────────────────────────────────────────────────


def test_payment_creates_order_and_renders_element(client, products, stripe_stub):
    """GET /checkout/payment should: create Order + items, create a Stripe
    PaymentIntent, store its id, and render the Payment Element with the
    client secret + publishable key."""
    # Walk: add → guest → shipping → payment GET
    client.post("/cart/add", data={"variant_id": _vid(products, "classic"), "qty": 2})
    client.post("/checkout/start", data={"action": "guest", "email": "g@g.com"})
    client.post("/checkout/shipping", data={
        "recipient_name": "G G", "line1": "L1", "line2": "", "postcode": "123456", "phone": "91234567"
    })

    r = client.get("/checkout/payment")
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert "payment-element" in body
    assert "pk_test_dummy" in body          # publishable key rendered
    assert "js.stripe.com/v3" in body       # Stripe.js loaded

    # Order persisted
    order = Order.query.first()
    assert order is not None
    assert order.status == "pending"
    assert order.subtotal_cents == 70000  # 2 × S$350
    assert order.shipping_cents == 0       # over free-shipping threshold
    assert order.total_cents == 70000
    assert order.guest_email == "g@g.com"
    assert order.guest_lookup_token  # not None / empty
    assert order.stripe_payment_intent_id == "pi_test_123"
    assert order.stripe_status == "requires_payment_method"

    # The client_secret reaches the page
    assert "pi_test_123_secret_test" in body
    # PaymentIntent created with the right amount
    assert stripe_stub["last"].amount == 70000


def test_payment_reuses_pending_order_on_reload(client, products, stripe_stub):
    """A second GET /checkout/payment must NOT create a duplicate order."""
    client.post("/cart/add", data={"variant_id": _vid(products, "classic"), "qty": 1})
    client.post("/checkout/start", data={"action": "guest", "email": "g@g.com"})
    client.post("/checkout/shipping", data={
        "recipient_name": "G", "line1": "L", "postcode": "123456", "phone": "91234567"})

    client.get("/checkout/payment")
    client.get("/checkout/payment")
    assert Order.query.count() == 1


def _drive_to_payment_guest(client, products):
    client.post("/cart/add", data={"variant_id": _vid(products, "classic"), "qty": 1})
    client.post("/checkout/start", data={"action": "guest", "email": "g@g.com"})
    client.post("/checkout/shipping", data={
        "recipient_name": "G", "line1": "L", "postcode": "123456", "phone": "91234567"})
    client.get("/checkout/payment")


def test_success_page_shows_guest_tracker_for_guest_orders(client, products, stripe_stub):
    _drive_to_payment_guest(client, products)

    order = Order.query.first()
    r = client.get(f"/checkout/success/{order.order_number}")
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert order.order_number in body
    # Guest tracker block visible
    assert "Track this guest order" in body
    assert order.guest_lookup_token in body


def test_success_page_for_signed_in_order_no_guest_tracker(client, products, stripe_stub, user):
    # sign in
    client.post("/auth/login", data={"email": user.email, "password": "password123"})
    client.post("/cart/add", data={"variant_id": _vid(products, "classic"), "qty": 1})
    client.post("/checkout/shipping", data={
        "recipient_name": "U", "line1": "L", "postcode": "123456", "phone": "91234567"})
    client.get("/checkout/payment")

    order = Order.query.first()
    r = client.get(f"/checkout/success/{order.order_number}")
    body = r.get_data(as_text=True)
    assert "Track this guest order" not in body
    assert "View my orders" in body
