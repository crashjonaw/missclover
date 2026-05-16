"""Shop blueprint — home, listing, product detail, collection/series landings, about."""
from flask import (Blueprint, abort, redirect, render_template, request,
                   url_for)
from sqlalchemy import case, func

from extensions import db
from models import Collection, Order, OrderItem, Product, ProductVariant, Series

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


def _sorted_products(sort: str, *, collection_slug: str | None = None,
                     series_slug: str | None = None,
                     bag_type: str | None = None) -> list[Product]:
    """Active products in the requested order, optionally filtered by
    collection / series / bag_type. Unknown sort keys fall back to `featured`."""
    q = Product.query.filter_by(is_active=True)

    if collection_slug or series_slug:
        q = q.join(Series, Product.series_id == Series.id)
        if series_slug:
            q = q.filter(Series.slug == series_slug)
        if collection_slug:
            q = (q.join(Collection, Series.collection_id == Collection.id)
                  .filter(Collection.slug == collection_slug))
    if bag_type:
        q = q.filter(Product.bag_type == bag_type)

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
    collection_slug = request.args.get("collection") or None
    series_slug = request.args.get("series") or None
    bag_type = request.args.get("bag_type") or None

    products = _sorted_products(sort, collection_slug=collection_slug,
                                series_slug=series_slug, bag_type=bag_type)

    collections = (Collection.query.filter_by(is_active=True)
                   .order_by(Collection.display_order, Collection.name).all())
    bag_types = [r[0] for r in (db.session.query(Product.bag_type)
                                .filter_by(is_active=True)
                                .distinct().order_by(Product.bag_type).all())]

    return render_template(
        "shop/listing.html",
        products=products,
        total=len(products),
        sort_key=sort,
        sort_options=SORT_OPTIONS,
        collections=collections,
        bag_types=bag_types,
        active_collection=collection_slug,
        active_series=series_slug,
        active_bag_type=bag_type,
    )


@bp.route("/handbags/<slug>")
def product(slug: str):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    related = []
    if product.series:
        related = [p for p in product.series.active_products if p.id != product.id]
    if not related:
        related = Product.query.filter(Product.id != product.id,
                                       Product.is_active.is_(True)).all()
    return render_template("shop/product.html", product=product, related=related)


# ─── Collection / Series landings ─────────────────────────────────────────────


@bp.route("/collections")
def collections_index():
    collections = (Collection.query.filter_by(is_active=True)
                   .order_by(Collection.display_order, Collection.name).all())
    return render_template("shop/collections_index.html", collections=collections)


@bp.route("/collections/<collection_slug>")
def collection(collection_slug: str):
    c = Collection.query.filter_by(slug=collection_slug, is_active=True).first()
    if c is None:
        # Legacy /collections/<design_code> (e.g. old `classic`) → 301 to the PDP.
        p = Product.query.filter_by(design_code=collection_slug, is_active=True).first()
        if p:
            return redirect(url_for("shop.product", slug=p.slug), code=301)
        abort(404)
    return render_template("shop/collection.html", collection=c)


@bp.route("/collections/<collection_slug>/<series_slug>")
def series(collection_slug: str, series_slug: str):
    c = Collection.query.filter_by(slug=collection_slug, is_active=True).first()
    s = None
    if c is not None:
        s = Series.query.filter_by(collection_id=c.id, slug=series_slug,
                                   is_active=True).first()
    if s is None:
        # Legacy /collections/<old_silhouette>/<design_code> → 301 to the PDP
        # using the last path segment as the bare design_code.
        p = Product.query.filter_by(design_code=series_slug, is_active=True).first()
        if p:
            return redirect(url_for("shop.product", slug=p.slug), code=301)
        abort(404)
    return render_template("shop/series.html", collection=c, series=s,
                           products=s.active_products)


@bp.route("/about")
def about():
    return render_template("about.html")
