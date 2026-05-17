"""Checkout blueprint — start (sign-in / register / continue-as-guest), shipping, payment, return, success, webhook."""
from datetime import datetime

from flask import (Blueprint, abort, current_app, flash, redirect, render_template,
                   request, session, url_for)
from flask_login import current_user, login_user

from activity import log_event
from extensions import db
from models import ActivityEvent, Address, Order, OrderItem, ProductVariant, User
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


# ─── Step 3: payment ─────────────────────────────────────────────────────────


@bp.route("/payment", methods=["GET", "POST"])
def payment():
    if not _is_authorised_for_checkout():
        return redirect(url_for("checkout.start"))

    cart = get_cart(create=False)
    addr_id = session.get(SHIPPING_ADDR_KEY)
    if not cart or not cart.items or not addr_id:
        return redirect(url_for("checkout.shipping"))

    address = Address.query.get_or_404(addr_id)
    shipping_cents, total_cents = _shipping_total(cart)

    if request.method == "POST":
        # Build the order, then call HitPay
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

        db.session.commit()
        session[PENDING_ORDER_KEY] = order.id
        log_event(ActivityEvent.ORDER_PLACED, order=order)

        # Call HitPay
        from hitpay import create_payment_request, HitPayError
        site = current_app.config["SITE_URL"].rstrip("/")
        try:
            resp = create_payment_request(
                amount_cents=order.total_cents,
                email=order.buyer_email,
                reference=order.order_number,
                redirect_url=site + url_for("checkout.return_from_hitpay"),
                webhook_url=site + url_for("checkout.webhook"),
                name=address.recipient_name,
            )
        except HitPayError as e:
            current_app.logger.error("HitPay error: %s", e)
            flash("Payment couldn't be initialised. Please check that HitPay is configured.", "error")
            return redirect(url_for("checkout.payment"))

        order.hitpay_payment_request_id = resp.get("id")
        db.session.commit()
        return redirect(resp.get("url"))

    return render_template("checkout/payment.html",
                           cart=cart,
                           address=address,
                           shipping_cents=shipping_cents,
                           total_cents=total_cents)


# ─── HitPay redirect_url ─────────────────────────────────────────────────────


@bp.route("/return")
def return_from_hitpay():
    """User comes back here after the HitPay hosted page."""
    order_id = session.get(PENDING_ORDER_KEY)
    if not order_id:
        return redirect(url_for("shop.home"))
    order = Order.query.get_or_404(order_id)
    return redirect(url_for("checkout.success", order_no=order.order_number))


# ─── HitPay webhook ──────────────────────────────────────────────────────────


@bp.post("/webhook")
def webhook():
    """Server-to-server callback from HitPay. Verify signature; mutate state."""
    from hitpay import verify_webhook
    form = request.form.to_dict()
    sent_hmac = form.get("hmac", "")

    if not verify_webhook(form, sent_hmac):
        current_app.logger.warning("HitPay webhook signature mismatch")
        return ("invalid signature", 400)

    reference = form.get("reference_number")
    status = form.get("status")
    payment_id = form.get("payment_id") or form.get("payment_request_id")

    order = Order.query.filter_by(order_number=reference).first()
    if not order:
        return ("order not found", 404)

    order.hitpay_status = status
    order.hitpay_reference = payment_id
    if status == "completed" and order.status == "pending":
        order.status = "paid"
        order.paid_at = datetime.utcnow()
        # decrement stock
        for item in order.items:
            if item.variant:
                item.variant.stock_qty = max(0, item.variant.stock_qty - item.qty)
        # clear the cart
        cart = get_cart(create=False)
        if cart:
            for it in list(cart.items):
                db.session.delete(it)
        # send confirmation
        try:
            from email_service import send_order_confirmation
            send_order_confirmation(order)
        except Exception as e:
            current_app.logger.exception("Failed to send confirmation email: %s", e)
        log_event(ActivityEvent.ORDER_PAID, user=order.user, order=order, commit=False)
    elif status in {"failed", "expired"} and order.status == "pending":
        order.status = "cancelled"
        log_event(ActivityEvent.ORDER_CANCELLED, user=order.user, order=order, commit=False)

    db.session.commit()
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
