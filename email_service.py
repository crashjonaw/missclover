"""Transactional email — order confirmation + password reset.

Uses Flask-Mail. If MAIL_USERNAME / MAIL_PASSWORD aren't set the message is
logged instead of sent (safe default in dev when Mailtrap creds aren't filled in).
"""
import logging

from flask import current_app, render_template_string, url_for
from flask_mail import Message

from extensions import mail

log = logging.getLogger(__name__)


def _can_send() -> bool:
    cfg = current_app.config
    if cfg.get("MAIL_SUPPRESS_SEND"):
        return False
    return bool(cfg.get("MAIL_USERNAME")) and bool(cfg.get("MAIL_PASSWORD"))


def _send(subject: str, recipients: list[str], body: str, html: str | None = None) -> None:
    if not _can_send():
        log.warning("MAIL not configured — would have sent to %s: %s\n%s", recipients, subject, body)
        return
    msg = Message(subject=subject, recipients=recipients, body=body, html=html)
    mail.send(msg)


_ORDER_TXT = """\
Hi {{ name or "" }},

Thank you for your order from MISS CLOVER.

Order:    {{ order.order_number }}
Total:    S${{ "%.2f"|format(order.total_cents / 100) }}
Items:
{% for it in order.items %}- {{ it.name_snapshot }} ({{ it.design_snapshot }}) × {{ it.qty }}  S${{ "%.2f"|format(it.line_cents / 100) }}{% if it.is_preorder %}  [PRE-ORDER]{% endif %}
{% endfor %}
{% if order.items | selectattr("is_preorder") | list %}
Some colours are made to order — we guarantee dispatch within {{ preorder_months }} month(s)
of your order date, or a full refund.
{% endif %}
Shipping to:
  {{ order.shipping_address.recipient_name }}
  {{ order.shipping_address.line1 }}{% if order.shipping_address.line2 %}, {{ order.shipping_address.line2 }}{% endif %}
  Singapore {{ order.shipping_address.postcode }}

{% if tracker_url %}Track your guest order anytime:
{{ tracker_url }}
{% endif %}

— MISS CLOVER
hello@missclover.sg
"""


def send_order_confirmation(order) -> None:
    site = current_app.config["SITE_URL"].rstrip("/")
    tracker_url = None
    if order.is_guest and order.guest_lookup_token:
        tracker_url = site + url_for(
            "orders_guest.lookup_with_token",
            email=order.guest_email,
            token=order.guest_lookup_token,
        )
    days = current_app.config.get("PREORDER_FULFILMENT_DAYS", 60)
    body = render_template_string(
        _ORDER_TXT,
        order=order,
        name=(order.user.first_name if order.user else ""),
        tracker_url=tracker_url,
        preorder_months=round(days / 30),
    )
    _send(
        subject=f"Order confirmation — {order.order_number}",
        recipients=[order.buyer_email],
        body=body,
    )


_RESET_TXT = """\
Someone (hopefully you) requested a password reset for your MISS CLOVER account.

Reset your password using the link below — it's valid for 2 hours:
{{ reset_url }}

If you didn't request this, you can ignore this email.

— MISS CLOVER
"""


def send_password_reset(email: str, reset_url: str) -> None:
    body = render_template_string(_RESET_TXT, reset_url=reset_url)
    _send(subject="Reset your MISS CLOVER password", recipients=[email], body=body)
