"""Shop blueprint — home, listing, product detail, collection landings, about."""
from flask import Blueprint, abort, render_template

from models import Product

bp = Blueprint("shop", __name__)


@bp.route("/")
def home():
    products = Product.query.filter_by(is_active=True).all()
    return render_template("home.html", products=products)


@bp.route("/handbags")
def handbags():
    products = Product.query.filter_by(is_active=True).all()
    return render_template("shop/listing.html", products=products, total=len(products))


@bp.route("/handbags/<slug>")
def product(slug: str):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    related = Product.query.filter(Product.id != product.id, Product.is_active.is_(True)).all()
    return render_template("shop/product.html", product=product, related=related)


@bp.route("/collections/<key>")
def collection(key: str):
    """Editorial single-design landing — `classic` or `maroon`."""
    if key not in {"classic", "maroon"}:
        abort(404)
    product = Product.query.filter_by(design_code=key, is_active=True).first()
    return render_template("shop/collection.html", key=key, product=product)


@bp.route("/about")
def about():
    return render_template("about.html")
