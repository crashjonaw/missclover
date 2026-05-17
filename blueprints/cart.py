"""Cart blueprint. Session-based for anonymous users; user-attached when signed in."""
import secrets

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user

from activity import log_event
from extensions import db
from models import ActivityEvent, Cart, CartItem, ProductVariant

bp = Blueprint("cart", __name__)

CART_TOKEN_KEY = "mc_cart_token"


def _ensure_token() -> str:
    tok = session.get(CART_TOKEN_KEY)
    if not tok:
        tok = secrets.token_urlsafe(24)
        session[CART_TOKEN_KEY] = tok
    return tok


def get_cart(create: bool = True) -> Cart | None:
    """Resolve the current cart. If signed in, ensures the cart belongs to the user."""
    tok = session.get(CART_TOKEN_KEY)
    cart = None
    if current_user.is_authenticated:
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        if not cart and tok:
            # Adopt any anonymous cart this session has into the user's account
            cart = Cart.query.filter_by(session_token=tok).first()
            if cart:
                cart.user_id = current_user.id
                db.session.commit()
    elif tok:
        cart = Cart.query.filter_by(session_token=tok).first()

    if cart or not create:
        return cart

    tok = _ensure_token()
    cart = Cart(session_token=tok, user_id=current_user.id if current_user.is_authenticated else None)
    db.session.add(cart)
    db.session.commit()
    return cart


@bp.route("/", endpoint="view")
def view():
    cart = get_cart(create=False)
    items = cart.items if cart else []
    shipping_cents, total_cents = _shipping_total(cart)
    return render_template(
        "cart/cart.html",
        cart=cart,
        items=items,
        shipping_cents=shipping_cents,
        total_cents=total_cents,
    )


@bp.post("/add")
def add():
    variant_id = request.form.get("variant_id", type=int)
    qty = max(1, request.form.get("qty", 1, type=int))
    if not variant_id:
        abort(400)
    variant = ProductVariant.query.get_or_404(variant_id)
    if not variant.is_purchasable:
        flash(f"{variant.product.name} is sold out.", "error")
        return redirect(url_for("shop.product", slug=variant.product.slug))

    cart = get_cart(create=True)

    item = CartItem.query.filter_by(cart_id=cart.id, variant_id=variant.id).first()
    if item:
        item.qty = min(item.qty + qty, 10)
    else:
        item = CartItem(cart_id=cart.id, variant_id=variant.id, qty=qty,
                        unit_price_cents_snapshot=variant.price_cents)
        db.session.add(item)
    db.session.commit()
    log_event(ActivityEvent.ADD_TO_CART, product=variant.product,
              meta={"variant_sku": variant.sku, "qty": qty})
    flash(f"Added to bag: {variant.product.name}", "success")
    return redirect(url_for("cart.view"))


@bp.post("/update/<int:item_id>")
def update(item_id: int):
    item = CartItem.query.get_or_404(item_id)
    qty = request.form.get("qty", 1, type=int)
    if qty <= 0:
        db.session.delete(item)
    else:
        item.qty = min(qty, 10)
    db.session.commit()
    return redirect(url_for("cart.view"))


@bp.post("/remove/<int:item_id>")
def remove(item_id: int):
    item = CartItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash("Removed from bag.", "info")
    return redirect(url_for("cart.view"))


def _shipping_total(cart: Cart | None) -> tuple[int, int]:
    cfg = current_app.config
    flat = int(cfg.get("SHIPPING_FLAT_RATE_CENTS", 800))
    free_above = int(cfg.get("FREE_SHIPPING_THRESHOLD_CENTS", 20000))
    if not cart or not cart.items:
        return 0, 0
    sub = cart.subtotal_cents
    shipping = 0 if sub >= free_above else flat
    return shipping, sub + shipping
