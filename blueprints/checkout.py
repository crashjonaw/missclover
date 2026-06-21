"""Checkout blueprint — start (sign-in / register / continue-as-guest), shipping, payment, return, success, webhook."""
from datetime import datetime

from flask import (Blueprint, abort, current_app, flash, redirect, render_template,
                   request, session, url_for)
from flask_login import current_user, login_user

from activity import log_event
from extensions import db
from models import ActivityEvent, Address, Order, OrderItem, User
from blueprints.cart import get_cart, _shipping_total

bp = Blueprint("checkout", __name__)

GUEST_EMAIL_KEY = "mc_guest_email"
SHIPPING_ADDR_KEY = "mc_shipping_addr_id"
PENDING_ORDER_KEY = "mc_pending_order_id"


# ─── Step 1: trifecta start ──────────────────────────────────────────────────


@bp.route("/start", methods=["GET", "POST"])
def start():
    cart = get_cart(create=False)
    if not cart or not cart.items:
        flash("Your bag is empty.", "info")
        return redirect(url_for("cart.view"))

    if current_user.is_authenticated:
        return redirect(url_for("checkout.shipping"))

    if request.method == "GET":
        log_event(ActivityEvent.CHECKOUT_STARTED)

    error = None
    if request.method == "POST":
        action = request.form.get("action")

        if action == "signin":
            email = (request.form.get("email") or "").strip().lower()
            password = request.form.get("password") or ""
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for("checkout.shipping"))
            error = ("signin", "Email or password is incorrect.")

        elif action == "register":
            email = (request.form.get("email") or "").strip().lower()
            password = request.form.get("password") or ""
            first = (request.form.get("first_name") or "").strip()
            last = (request.form.get("last_name") or "").strip()
            if not email or not password or len(password) < 8:
                error = ("register", "Password must be at least 8 characters.")
            elif User.query.filter_by(email=email).first():
                error = ("register", "An account with that email already exists. Try signing in.")
            else:
                u = User(email=email, first_name=first, last_name=last)
                u.set_password(password)
                db.session.add(u)
                db.session.commit()
                log_event(ActivityEvent.REGISTER, user=u, meta={"via": "checkout"})
                login_user(u)
                return redirect(url_for("checkout.shipping"))

        elif action == "guest":
            email = (request.form.get("email") or "").strip().lower()
            if not email or "@" not in email:
                error = ("guest", "Please enter a valid email.")
            else:
                session[GUEST_EMAIL_KEY] = email
                return redirect(url_for("checkout.shipping"))
        else:
            abort(400)

    return render_template("checkout/start.html", error=error)


# ─── Step 2: shipping ────────────────────────────────────────────────────────


def _is_authorised_for_checkout() -> bool:
    return current_user.is_authenticated or bool(session.get(GUEST_EMAIL_KEY))


@bp.route("/shipping", methods=["GET", "POST"])
def shipping():
    if not _is_authorised_for_checkout():
        return redirect(url_for("checkout.start"))

    cart = get_cart(create=False)
    if not cart or not cart.items:
        flash("Your bag is empty.", "info")
        return redirect(url_for("cart.view"))

    error = None
    if request.method == "POST":
        recipient = (request.form.get("recipient_name") or "").strip()
        line1 = (request.form.get("line1") or "").strip()
        line2 = (request.form.get("line2") or "").strip()
        postcode = (request.form.get("postcode") or "").strip()
        phone = (request.form.get("phone") or "").strip()

        if not recipient or not line1 or not postcode or not phone:
            error = "Please fill in all required fields."
        else:
            addr = Address(
                user_id=current_user.id if current_user.is_authenticated else None,
                recipient_name=recipient,
                line1=line1,
                line2=line2 or None,
                postcode=postcode,
                country="SG",
                phone=phone,
            )
            db.session.add(addr)
            db.session.commit()
            session[SHIPPING_ADDR_KEY] = addr.id
            return redirect(url_for("checkout.payment"))

    return render_template("checkout/shipping.html",
                           error=error,
                           guest_email=session.get(GUEST_EMAIL_KEY))


# ─── Step 3: payment (Stripe Payment Element) ────────────────────────────────


def _rebuild_order_items(order, cart) -> None:
    """Replace an order's line items from the current cart. Lets us keep a
    reused pending order in sync if the buyer edits the cart and comes back."""
    for it in list(order.items):
        db.session.delete(it)
    db.session.flush()
    for it in cart.items:
        v = it.variant
        db.session.add(OrderItem(
            order_id=order.id,
            variant_id=v.id,
            qty=it.qty,
            unit_price_cents=it.unit_price_cents_snapshot,
            is_preorder=v.stock_qty <= 0,
            name_snapshot=v.product.name,
            design_snapshot=v.product.design_code,
        ))


def _ensure_pending_order(cart, address, shipping_cents, total_cents):
    """Get-or-create the pending Order for this session and its Stripe
    PaymentIntent. Returns (order, client_secret). Reuses the session's pending
    order on reload/back-navigation, resyncing totals and the intent amount so
    a buyer can't pay a stale price."""
    from stripe_gateway import (create_payment_intent, retrieve_payment_intent,
                                update_payment_intent_amount)

    oid = session.get(PENDING_ORDER_KEY)
    order = Order.query.get(oid) if oid else None
    if order and order.status != "pending":
        order = None  # already paid/cancelled — start a fresh order

    is_new = order is None
    if is_new:
        order = Order(
            order_number=Order.generate_number(),
            user_id=current_user.id if current_user.is_authenticated else None,
            guest_email=None if current_user.is_authenticated else session.get(GUEST_EMAIL_KEY),
            guest_lookup_token=None if current_user.is_authenticated else Order.generate_guest_token(),
            status="pending",
            subtotal_cents=cart.subtotal_cents,
            shipping_cents=shipping_cents,
            total_cents=total_cents,
            shipping_address_id=address.id,
        )
        db.session.add(order)
        db.session.flush()

    # Keep the order in sync with the cart + chosen address.
    order.shipping_address_id = address.id
    order.subtotal_cents = cart.subtotal_cents
    order.shipping_cents = shipping_cents
    order.total_cents = total_cents
    _rebuild_order_items(order, cart)

    if is_new or not order.stripe_payment_intent_id:
        intent = create_payment_intent(
            amount_cents=total_cents,
            currency=order.currency,
            reference=order.order_number,
            email=order.buyer_email,
            metadata={"order_id": str(order.id)},
        )
        order.stripe_payment_intent_id = intent.id
    else:
        intent = retrieve_payment_intent(order.stripe_payment_intent_id)
        # Resync the amount if the cart changed, but never touch an intent that's
        # already being paid (PayNow/GrabPay are async).
        if intent.status not in {"succeeded", "processing"} and intent.amount != total_cents:
            intent = update_payment_intent_amount(order.stripe_payment_intent_id, total_cents)

    order.stripe_status = intent.status
    db.session.commit()

    session[PENDING_ORDER_KEY] = order.id
    if is_new:
        log_event(ActivityEvent.ORDER_PLACED, order=order)
    return order, intent.client_secret


@bp.route("/payment", methods=["GET"])
def payment():
    if not _is_authorised_for_checkout():
        return redirect(url_for("checkout.start"))

    cart = get_cart(create=False)
    addr_id = session.get(SHIPPING_ADDR_KEY)
    if not cart or not cart.items or not addr_id:
        return redirect(url_for("checkout.shipping"))

    address = Address.query.get_or_404(addr_id)
    shipping_cents, total_cents = _shipping_total(cart)

    from stripe_gateway import StripeError
    try:
        order, client_secret = _ensure_pending_order(cart, address, shipping_cents, total_cents)
    except StripeError as e:
        current_app.logger.error("Stripe error initialising payment: %s", e)
        flash("Payment couldn't be initialised. Please try again, or contact us if it persists.", "error")
        return redirect(url_for("checkout.shipping"))

    site = current_app.config["SITE_URL"].rstrip("/")
    return render_template(
        "checkout/payment.html",
        cart=cart,
        address=address,
        shipping_cents=shipping_cents,
        total_cents=total_cents,
        client_secret=client_secret,
        stripe_publishable_key=current_app.config["STRIPE_PUBLISHABLE_KEY"],
        return_url=site + url_for("checkout.return_from_stripe"),
    )


# ─── Stripe return_url ───────────────────────────────────────────────────────


@bp.route("/return")
def return_from_stripe():
    """Stripe redirects the buyer here after confirmPayment. The webhook is the
    source of truth for marking an order paid; this page only routes the buyer
    to the right view (and clears the cart, since here we still have a session)."""
    order_id = session.get(PENDING_ORDER_KEY)
    if not order_id:
        return redirect(url_for("shop.home"))
    order = Order.query.get_or_404(order_id)

    pi = request.args.get("payment_intent")
    settled = order.status == "paid"
    if pi and pi == order.stripe_payment_intent_id and not settled:
        # Best-effort read so the buyer sees the right page even if the webhook
        # hasn't landed yet. No money-affecting state changes here.
        try:
            from stripe_gateway import retrieve_payment_intent
            intent = retrieve_payment_intent(pi)
            order.stripe_status = intent.status
            db.session.commit()
            settled = intent.status in {"succeeded", "processing"}
        except Exception as e:
            current_app.logger.warning("return: could not read PaymentIntent: %s", e)

    if settled:
        # Empty this buyer's cart now that payment is underway/complete.
        cart = get_cart(create=False)
        if cart:
            for it in list(cart.items):
                db.session.delete(it)
            db.session.commit()
        return redirect(url_for("checkout.success", order_no=order.order_number))

    flash("Your payment wasn't completed. You can try again below.", "error")
    return redirect(url_for("checkout.payment"))


# ─── Stripe webhook ──────────────────────────────────────────────────────────


def _order_for_intent(intent) -> "Order | None":
    order = Order.query.filter_by(stripe_payment_intent_id=intent.get("id")).first()
    if not order:
        ref = (intent.get("metadata") or {}).get("reference")
        if ref:
            order = Order.query.filter_by(order_number=ref).first()
    return order


def _mark_paid(intent) -> None:
    order = _order_for_intent(intent)
    if not order:
        current_app.logger.warning("Stripe webhook: no order for intent %s", intent.get("id"))
        return
    order.stripe_status = intent.get("status")
    if order.status == "pending":  # idempotent — ignore duplicate deliveries
        order.status = "paid"
        order.paid_at = datetime.utcnow()
        for item in order.items:
            if item.variant:
                item.variant.stock_qty = max(0, item.variant.stock_qty - item.qty)
        try:
            from email_service import send_order_confirmation
            send_order_confirmation(order)
        except Exception as e:
            current_app.logger.exception("Failed to send confirmation email: %s", e)
        log_event(ActivityEvent.ORDER_PAID, user=order.user, order=order, commit=False)
    db.session.commit()


def _mark_failed(intent) -> None:
    order = _order_for_intent(intent)
    if not order:
        return
    order.stripe_status = intent.get("status")
    if order.status == "pending":
        order.status = "cancelled"
        log_event(ActivityEvent.ORDER_CANCELLED, user=order.user, order=order, commit=False)
    db.session.commit()


@bp.post("/stripe-webhook")
def stripe_webhook():
    """Server-to-server callback from Stripe. Verify the signature, then mutate
    order state. Cart clearing happens on the return page (which has a session)."""
    from stripe_gateway import verify_webhook, StripeError
    payload = request.get_data()
    sig = request.headers.get("Stripe-Signature", "")

    try:
        event = verify_webhook(payload, sig)
    except StripeError:
        return ("invalid signature", 400)

    etype = event["type"]
    obj = event["data"]["object"]
    if etype == "payment_intent.succeeded":
        _mark_paid(obj)
    elif etype == "payment_intent.payment_failed":
        _mark_failed(obj)
    # Other event types are acknowledged but ignored.
    return ("ok", 200)


# ─── Success page ────────────────────────────────────────────────────────────


@bp.route("/success/<order_no>")
def success(order_no: str):
    order = Order.query.filter_by(order_number=order_no).first_or_404()
    # Build the guest-tracker link if relevant
    tracker_url = None
    if order.is_guest and order.guest_lookup_token:
        tracker_url = current_app.config["SITE_URL"].rstrip("/") + url_for(
            "orders_guest.lookup_with_token",
            email=order.guest_email,
            token=order.guest_lookup_token,
        )
    # Clear pending markers
    session.pop(PENDING_ORDER_KEY, None)
    session.pop(GUEST_EMAIL_KEY, None)
    session.pop(SHIPPING_ADDR_KEY, None)
    return render_template("checkout/success.html", order=order, tracker_url=tracker_url)
