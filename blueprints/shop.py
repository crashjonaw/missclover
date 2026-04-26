"""Shop blueprint — home, listing, product detail, collection landings, about."""
from flask import Blueprint, abort, render_template, request
from sqlalchemy import case, func

from extensions import db
from models import Order, OrderItem, Product, ProductVariant

bp = Blueprint("shop", __name__)


# ─── Sort options for /handbags ───────────────────────────────────────────────

SORT_OPTIONS = [
    ("featured",   "Featured"),           # default — display_order
    ("type",       "Bag type"),           # group by bag_type, then name
    ("price_asc",  "Price — low to high"),
    ("price_desc", "Price — high to low"),
    ("popularity", "Most popular"),       # qty sold across paid+fulfilled orders
]
_SORT_KEYS = {k for k, _ in SORT_OPTIONS}


def _sorted_products(sort: str) -> list[Product]:
    """Return active products in the requested order. Falls back to `featured`
    for any unknown key (so a tampered query string never errors)."""
    q = Product.query.filter_by(is_active=True)

    if sort == "price_asc":
        return q.order_by(Product.base_price_cents.asc(), Product.name).all()
    if sort == "price_desc":
        return q.order_by(Product.base_price_cents.desc(), Product.name).all()
    if sort == "type":
        return q.order_by(Product.bag_type.asc(), Product.name.asc()).all()
    if sort == "popularity":
        # Sum qty per product, but ONLY counting OrderItems whose Order is paid
        # or fulfilled. Pending / cancelled orders don't bump popularity. Products
        # with zero sales tie at 0 and fall through to display_order.
        paid_qty = case(
            (Order.status.in_(["paid", "fulfilled"]), OrderItem.qty),
            else_=0,
        )
        sold_subq = (
            db.session.query(
                ProductVariant.product_id.label("pid"),
                func.coalesce(func.sum(paid_qty), 0).label("sold"),
            )
            .outerjoin(OrderItem, OrderItem.variant_id == ProductVariant.id)
            .outerjoin(Order, Order.id == OrderItem.order_id)
            .group_by(ProductVariant.product_id)
            .subquery()
        )
        return (q.outerjoin(sold_subq, sold_subq.c.pid == Product.id)
                 .order_by(func.coalesce(sold_subq.c.sold, 0).desc(),
                           Product.display_order.asc(),
                           Product.name.asc())
                 .all())

    # featured / default
    return q.order_by(Product.display_order.asc(), Product.name.asc()).all()


@bp.route("/")
def home():
    products = Product.query.filter_by(is_active=True).order_by(Product.display_order).all()
    return render_template("home.html", products=products)


@bp.route("/handbags")
def handbags():
    sort = (request.args.get("sort") or "featured").lower()
    if sort not in _SORT_KEYS:
        sort = "featured"
    products = _sorted_products(sort)
    return render_template(
        "shop/listing.html",
        products=products,
        total=len(products),
        sort_key=sort,
        sort_options=SORT_OPTIONS,
    )


@bp.route("/handbags/<slug>")
def product(slug: str):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    related = Product.query.filter(Product.id != product.id, Product.is_active.is_(True)).all()
    return render_template("shop/product.html", product=product, related=related)


@bp.route("/collections/<key>")
def collection(key: str):
    """Editorial single-design landing — one collection page per active product
    (looked up by design_code). Drop a new design into data/products.yaml and
    its collection landing appears automatically."""
    product = Product.query.filter_by(design_code=key, is_active=True).first_or_404()
    return render_template("shop/collection.html", key=key, product=product)


@bp.route("/about")
def about():
    return render_template("about.html")
