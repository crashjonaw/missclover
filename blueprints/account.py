"""Account blueprint — dashboard, orders, profile, addresses."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from models import Order

bp = Blueprint("account", __name__)


@bp.route("/", endpoint="dashboard")
@login_required
def dashboard():
    orders = (Order.query
              .filter_by(user_id=current_user.id)
              .order_by(Order.created_at.desc())
              .limit(5)
              .all())
    return render_template("account/dashboard.html", orders=orders)


@bp.route("/orders", endpoint="orders")
@login_required
def orders():
    orders = (Order.query
              .filter_by(user_id=current_user.id)
              .order_by(Order.created_at.desc())
              .all())
    return render_template("account/orders.html", orders=orders)


@bp.route("/orders/<order_no>", endpoint="order_detail")
@login_required
def order_detail(order_no: str):
    order = Order.query.filter_by(order_number=order_no, user_id=current_user.id).first_or_404()
    return render_template("account/order_detail.html", order=order)


@bp.route("/profile", methods=["GET", "POST"], endpoint="profile")
@login_required
def profile():
    if request.method == "POST":
        current_user.first_name = (request.form.get("first_name") or "").strip()
        current_user.last_name = (request.form.get("last_name") or "").strip()
        current_user.phone = (request.form.get("phone") or "").strip()
        current_user.newsletter_opt_in = bool(request.form.get("newsletter"))

        new_password = request.form.get("new_password")
        if new_password:
            if len(new_password) < 8:
                flash("Password must be at least 8 characters.", "error")
            else:
                current_user.set_password(new_password)
                flash("Password updated.", "success")

        db.session.commit()
        flash("Profile saved.", "success")
        return redirect(url_for("account.profile"))
    return render_template("account/profile.html")


@bp.route("/addresses", endpoint="addresses")
@login_required
def addresses():
    return render_template("account/addresses.html", addresses=current_user.addresses)
