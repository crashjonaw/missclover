"""Centralised activity logging — the growth & customer-insight backbone.

One import, one call:

    from activity import log_event
    from models import ActivityEvent
    log_event(ActivityEvent.PRODUCT_VIEW, product=p)

Design goals:
  * Zero-risk: analytics must never break a checkout. Every failure is
    swallowed (logged, session rolled back) — the caller continues.
  * Low coupling: login/logout are captured automatically via Flask-Login
    signals (see app.create_app); call sites only add the commerce events.
  * Pre-signup visibility: anonymous visitors are keyed by the cart session
    token, so the funnel is measurable before an account exists and can be
    stitched to the user on sign-up.
"""
import logging

from flask import has_request_context, request, session
from flask_login import current_user

from extensions import db
from models import ActivityEvent

log = logging.getLogger(__name__)

# Mirror blueprints.cart.CART_TOKEN_KEY without importing it (avoid a cycle).
_CART_TOKEN_KEY = "mc_cart_token"


def _anon_id() -> str | None:
    if has_request_context():
        return session.get(_CART_TOKEN_KEY)
    return None


def log_event(event_type: str, *, user=None, product=None, order=None,
              value_cents: int | None = None, meta: dict | None = None,
              commit: bool = True):
    """Record one activity event. Returns the row, or None on failure."""
    try:
        uid = None
        if user is not None:
            uid = user.id
        elif has_request_context() and current_user.is_authenticated:
            uid = current_user.id

        if value_cents is None and order is not None and \
                event_type in (ActivityEvent.ORDER_PLACED, ActivityEvent.ORDER_PAID):
            value_cents = order.total_cents

        ev = ActivityEvent(
            user_id=uid,
            anon_id=None if uid else _anon_id(),
            event_type=event_type,
            product_id=product.id if product is not None else None,
            order_id=order.id if order is not None else None,
            value_cents=value_cents,
            meta=meta or None,
            ip=request.remote_addr if has_request_context() else None,
            user_agent=(request.user_agent.string[:255]
                        if has_request_context() and request.user_agent else None),
        )
        db.session.add(ev)
        if commit:
            db.session.commit()
        return ev
    except Exception as e:  # analytics must never break the request
        log.warning("activity log failed (%s): %s", event_type, e)
        try:
            db.session.rollback()
        except Exception:
            pass
        return None
