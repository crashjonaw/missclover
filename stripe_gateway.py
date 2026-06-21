"""Stripe client. Cards / PayNow / GrabPay via the embedded Payment Element.

Wraps the Stripe SDK so the rest of the app never touches it directly. Named
`stripe_gateway` (not `stripe`) so it doesn't shadow the installed `stripe`
package.
"""
import logging

import stripe
from flask import current_app

log = logging.getLogger(__name__)


class StripeError(RuntimeError):
    pass


def _client() -> None:
    """Point the SDK at our secret key for this request. Raises if unset so we
    fail loudly instead of silently calling Stripe unauthenticated."""
    key = current_app.config.get("STRIPE_SECRET_KEY", "")
    if not key:
        raise StripeError("STRIPE_SECRET_KEY is not configured.")
    stripe.api_key = key


def create_payment_intent(*, amount_cents: int, currency: str, reference: str,
                          email: str, metadata: dict | None = None) -> "stripe.PaymentIntent":
    """Create a PaymentIntent for an order. Returns the PaymentIntent, whose
    `client_secret` the front-end uses to confirm payment with the Payment
    Element. `automatic_payment_methods` lets the methods enabled in the Stripe
    Dashboard (cards, PayNow, GrabPay) surface without per-method code here."""
    _client()
    meta = {"reference": reference, **(metadata or {})}
    try:
        return stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=currency.lower(),
            receipt_email=email or None,
            description=f"MISS CLOVER order {reference}",
            metadata=meta,
            automatic_payment_methods={"enabled": True},
        )
    except stripe.StripeError as e:  # network / auth / card errors
        log.error("Stripe create_payment_intent failed: %s", e)
        raise StripeError(str(e)) from e


def retrieve_payment_intent(payment_intent_id: str) -> "stripe.PaymentIntent":
    """Fetch a PaymentIntent from Stripe (used by the return page to read the
    latest status without trusting client-supplied data)."""
    _client()
    try:
        return stripe.PaymentIntent.retrieve(payment_intent_id)
    except stripe.StripeError as e:
        log.error("Stripe retrieve_payment_intent failed: %s", e)
        raise StripeError(str(e)) from e


def update_payment_intent_amount(payment_intent_id: str, amount_cents: int) -> "stripe.PaymentIntent":
    """Update a PaymentIntent's amount (e.g. the cart changed before payment).
    Only valid while the intent still awaits a payment method."""
    _client()
    try:
        return stripe.PaymentIntent.modify(payment_intent_id, amount=amount_cents)
    except stripe.StripeError as e:
        log.error("Stripe update_payment_intent_amount failed: %s", e)
        raise StripeError(str(e)) from e


def verify_webhook(payload: bytes, sig_header: str) -> "stripe.Event":
    """Verify and parse a Stripe webhook callback. Raises StripeError on a bad
    or missing signature, or if the signing secret isn't configured. Stripe's
    construct_event also guards against replay via the timestamp tolerance.
    """
    secret = current_app.config.get("STRIPE_WEBHOOK_SECRET", "")
    if not secret:
        raise StripeError("STRIPE_WEBHOOK_SECRET is not configured.")
    try:
        return stripe.Webhook.construct_event(payload, sig_header, secret)
    except (stripe.SignatureVerificationError, ValueError) as e:
        log.warning("Stripe webhook signature verification failed: %s", e)
        raise StripeError("invalid signature") from e
