"""HitPay HMAC-SHA256 webhook signature verification — security critical."""
import hashlib
import hmac

from hitpay import verify_webhook


def _sign(form: dict, salt: str) -> str:
    fields = {k: v for k, v in form.items() if k != "hmac"}
    payload = "".join(f"{k}{fields[k]}" for k in sorted(fields))
    return hmac.new(salt.encode(), payload.encode(), hashlib.sha256).hexdigest()


def test_correct_signature_verifies(app):
    salt = app.config["HITPAY_SALT"]
    form = {
        "payment_id": "pay_abc123",
        "amount": "350.00",
        "currency": "SGD",
        "status": "completed",
        "reference_number": "MC-2026-AAAAAA",
    }
    sig = _sign(form, salt)
    with app.app_context():
        assert verify_webhook({**form, "hmac": sig}, sig) is True


def test_wrong_signature_rejected(app):
    salt = app.config["HITPAY_SALT"]
    form = {"payment_id": "x", "status": "completed", "reference_number": "MC-2026-XXXXXX"}
    bad = "0" * 64
    with app.app_context():
        assert verify_webhook({**form, "hmac": bad}, bad) is False


def test_tampered_field_invalidates_signature(app):
    salt = app.config["HITPAY_SALT"]
    form = {"payment_id": "p", "status": "completed", "amount": "350.00",
            "reference_number": "MC-2026-AAAAAA"}
    sig = _sign(form, salt)
    # Attacker changes the amount but keeps the original signature
    tampered = {**form, "amount": "0.01", "hmac": sig}
    with app.app_context():
        assert verify_webhook(tampered, sig) is False


def test_empty_signature_rejected(app):
    form = {"payment_id": "x", "status": "completed", "reference_number": "MC-2026-XXXXXX"}
    with app.app_context():
        assert verify_webhook({**form, "hmac": ""}, "") is False


def test_missing_salt_returns_false(app):
    form = {"payment_id": "x", "status": "completed"}
    sig = _sign(form, "not-the-real-salt")
    # Override salt to empty
    app.config["HITPAY_SALT"] = ""
    with app.app_context():
        assert verify_webhook({**form, "hmac": sig}, sig) is False


def test_signature_is_case_insensitive_hex(app):
    """HitPay sends lowercase hex; verify we compare in a stable way."""
    salt = app.config["HITPAY_SALT"]
    form = {"payment_id": "p", "status": "completed", "reference_number": "MC-2026-AAAAAA"}
    sig = _sign(form, salt)
    with app.app_context():
        # Same digest, uppercase — our verify lowercases the sent hmac before comparing
        assert verify_webhook({**form, "hmac": sig.upper()}, sig.upper()) is True
