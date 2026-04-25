"""HitPay client. Singapore payment gateway — cards, PayNow, GrabPay."""
import hashlib
import hmac
import logging

import requests
from flask import current_app

log = logging.getLogger(__name__)


class HitPayError(RuntimeError):
    pass


def _headers() -> dict:
    api_key = current_app.config.get("HITPAY_API_KEY", "")
    if not api_key:
        raise HitPayError("HITPAY_API_KEY is not configured.")
    return {
        "X-BUSINESS-API-KEY": api_key,
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded",
    }


def create_payment_request(*, amount_cents: int, email: str, reference: str,
                           redirect_url: str, webhook_url: str,
                           name: str | None = None) -> dict:
    """Create a HitPay hosted payment request. Returns the JSON response, which
    contains an `id` and a `url` to redirect the buyer to."""
    base = current_app.config["HITPAY_API_BASE"].rstrip("/")
    methods = current_app.config.get("HITPAY_PAYMENT_METHODS", ["paynow_online", "card", "grabpay"])

    data = {
        "amount": f"{amount_cents / 100:.2f}",
        "currency": "SGD",
        "email": email,
        "reference_number": reference,
        "redirect_url": redirect_url,
        "webhook": webhook_url,
    }
    if name:
        data["name"] = name
    # HitPay expects payment_methods[]= for arrays; requests serialises lists by repeating the key
    data_list = list(data.items()) + [("payment_methods[]", m) for m in methods]

    resp = requests.post(f"{base}/payment-requests", headers=_headers(), data=data_list, timeout=15)
    if not resp.ok:
        log.error("HitPay create_payment_request failed: %s %s", resp.status_code, resp.text)
        raise HitPayError(f"HitPay returned {resp.status_code}: {resp.text}")
    return resp.json()


def verify_webhook(form: dict, sent_hmac: str) -> bool:
    """Verify HMAC-SHA256 signature on a HitPay webhook callback.

    HitPay's algorithm: concatenate keys (sorted) with their values like
    `key0val0key1val1...`, then HMAC-SHA256 with the salt; compare hex digests.
    """
    salt = current_app.config.get("HITPAY_SALT", "")
    if not salt:
        return False

    # Skip the hmac key itself when computing
    fields = {k: v for k, v in form.items() if k != "hmac"}
    payload = "".join(f"{k}{fields[k]}" for k in sorted(fields))
    digest = hmac.new(salt.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, (sent_hmac or "").lower())
