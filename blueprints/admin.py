"""Admin blueprint — staff-only console: customers, sales, activity.

Auth model (mirrors ref/bloomburrow): admins are `User` rows with
`is_admin=True`; a dedicated `/admin/login` accepts a username *or* email so
staff don't share the customer email-only form. Every view is gated by
`@admin_required`, which 404s rather than redirecting for non-admins so the
console isn't even discoverable.
"""
from datetime import timedelta
from functools import wraps

from flask import (Blueprint, abort, current_app, flash, redirect,
                    render_template, request, url_for)
from flask_login import current_user, login_required, login_user, logout_user

import admin_stats
from extensions import db
from models import Order, Product, ProductVariant, User

bp = Blueprint("admin", __name__)


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(404)  # don't reveal the console exists
        return fn(*args, **kwargs)
    return wrapper


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for("admin.dashboard"))
    error = None
    if request.method == "POST":
        ident = (request.form.get("username") or "").strip().lower()
        password = request.form.get("password") or ""
        user = (User.query
                .filter((func_lower(User.username) == ident)
                        | (func_lower(User.email) == ident))
                .first())
        if user and user.is_admin and user.check_password(password):
            login_user(user)
            return redirect(url_for("admin.dashboard"))
        error = "Invalid admin credentials."
    return render_template("admin/login.html", error=error)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Signed out of admin.", "info")
    return redirect(url_for("admin.login"))


@bp.route("/")
@admin_required
def dashboard():
    return render_template(
        "admin/dashboard.html",
        kpi=admin_stats.overview(),
        funnel=admin_stats.funnel(),
        top_products=admin_stats.top_products(8),
        recent_orders=admin_stats.recent_orders(10),
        recent_signups=admin_stats.recent_signups(8),
        recent_activity=admin_stats.recent_activity(20),
    )


@bp.route("/users")
@admin_required
def users():
    sort = request.args.get("sort", "spend")
    return render_template("admin/users.html",
                           rows=admin_stats.customers(sort=sort), sort=sort)


@bp.route("/users/<int:uid>")
@admin_required
def user_detail(uid):
    data = admin_stats.customer_detail(uid)
    if data is None:
        abort(404)
    return render_template("admin/user_detail.html", **data)


@bp.route("/orders")
@admin_required
def orders():
    status = request.args.get("status")
    q = Order.query
    if status:
        q = q.filter(Order.status == status)
    return render_template(
        "admin/orders.html",
        orders=q.order_by(Order.created_at.desc()).all(),
        status=status,
    )


@bp.route("/inventory")
@admin_required
def inventory():
    rows = (db.session.query(ProductVariant, Product)
            .join(Product, Product.id == ProductVariant.product_id)
            .order_by(Product.display_order, Product.name,
                      ProductVariant.name).all())
    return render_template("admin/inventory.html", rows=rows,
                           low=current_app.config["LOW_STOCK_THRESHOLD"])


@bp.route("/inventory/<int:vid>", methods=["POST"])
@admin_required
def inventory_update(vid):
    v = db.session.get(ProductVariant, vid)
    if v is None:
        abort(404)
    add = request.form.get("add_stock", type=int)
    setto = request.form.get("set_stock", type=int)
    if setto is not None:
        v.stock_qty = max(0, setto)
    elif add:
        v.stock_qty = max(0, v.stock_qty + add)
    v.allow_preorder = bool(request.form.get("allow_preorder"))
    db.session.commit()
    flash(f"Updated {v.sku}: stock {v.stock_qty}, "
          f"pre-order {'on' if v.allow_preorder else 'off'}.", "success")
    return redirect(url_for("admin.inventory"))


@bp.route("/fulfilment")
@admin_required
def fulfilment():
    """The fulfil queue: paid orders awaiting dispatch, oldest first."""
    paid = (Order.query.filter_by(status="paid")
            .order_by(Order.created_at.asc()).all())
    eta_days = current_app.config["PREORDER_FULFILMENT_DAYS"]
    queue = [{
        "order": o,
        "preorder": any(it.is_preorder for it in o.items),
        "eta": o.created_at + timedelta(days=eta_days),
    } for o in paid]
    return render_template("admin/fulfilment.html", queue=queue,
                           eta_days=eta_days)


@bp.route("/orders/<int:order_id>/fulfil", methods=["POST"], endpoint="mark_fulfilled")
@admin_required
def mark_fulfilled(order_id):
    o = db.session.get(Order, order_id)
    if o is None:
        abort(404)
    if o.status == "paid":
        o.status = "fulfilled"
        db.session.commit()
        flash(f"{o.order_number} marked fulfilled.", "success")
    return redirect(request.referrer or url_for("admin.fulfilment"))


def func_lower(col):
    """Case-insensitive match helper (username/email may be mixed-case input)."""
    from sqlalchemy import func
    return func.lower(col)
