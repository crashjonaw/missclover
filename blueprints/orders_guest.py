"""Guest order lookup — `/order/lookup` with email + token."""
from flask import Blueprint, render_template, request

from models import Order

bp = Blueprint("orders_guest", __name__, url_prefix="/order")


@bp.route("/lookup", methods=["GET", "POST"], endpoint="lookup")
def lookup():
    """Form for entering email + order number to view a guest order."""
    error = None
    order = None
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        order_no = (request.form.get("order_number") or "").strip()
        order = Order.query.filter_by(order_number=order_no, guest_email=email).first()
        if not order:
            error = "We couldn't find a guest order with those details."
            order = None
    return render_template("account/order_lookup.html", error=error, order=order)


@bp.route("/track", endpoint="lookup_with_token")
def lookup_with_token():
    """Magic-link variant: ?email=...&token=... shows the order if both match."""
    email = (request.args.get("email") or "").strip().lower()
    token = (request.args.get("token") or "").strip()
    order = (Order.query
             .filter_by(guest_email=email, guest_lookup_token=token)
             .first())
    if not order:
        return render_template("account/order_lookup.html",
                               error="This tracker link is invalid or has expired.",
                               order=None), 404
    return render_template("account/order_lookup.html", error=None, order=order)
