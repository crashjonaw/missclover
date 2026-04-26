"""MISS CLOVER — Flask application factory."""
from flask import Flask, render_template

from config import Config
from extensions import db, login_manager, mail, migrate


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # ensure instance folder exists for sqlite
    import os
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

    # late imports to avoid circulars
    from models import User
    from blueprints.shop import bp as shop_bp
    from blueprints.cart import bp as cart_bp
    from blueprints.auth import bp as auth_bp
    from blueprints.checkout import bp as checkout_bp
    from blueprints.account import bp as account_bp
    from blueprints.orders_guest import bp as guest_bp

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    app.register_blueprint(shop_bp)
    app.register_blueprint(cart_bp, url_prefix="/cart")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(checkout_bp, url_prefix="/checkout")
    app.register_blueprint(account_bp, url_prefix="/account")
    app.register_blueprint(guest_bp)

    # Make cart count, currency, and featured products available everywhere
    @app.context_processor
    def inject_globals():
        from datetime import datetime
        from blueprints.cart import get_cart
        from models import Product
        cart = get_cart(create=False)
        featured = (Product.query
                    .filter_by(is_active=True, is_featured=True)
                    .order_by(Product.display_order)
                    .all())
        return dict(
            cart_qty=cart.total_qty if cart else 0,
            cart_subtotal_cents=cart.subtotal_cents if cart else 0,
            currency="SGD",
            now_year=datetime.utcnow().year,
            featured_products=featured,
        )

    @app.template_filter("sgd")
    def sgd_filter(cents):
        if cents is None:
            return "—"
        return f"S${int(cents) / 100:,.2f}"

    @app.template_filter("text_on")
    def text_on_filter(bg_hex: str) -> str:
        """Pick legible foreground colour for a background hex.

        Uses standard relative luminance — light backgrounds get ink, dark
        backgrounds get cream. Lets templates render coloured tiles without
        per-design CSS classes."""
        if not bg_hex:
            return "#111111"
        h = bg_hex.lstrip("#")
        if len(h) != 6:
            return "#111111"
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return "#111111" if luminance > 0.55 else "#FBFAF7"

    @app.errorhandler(404)
    def not_found(_):
        return render_template("404.html"), 404

    return app


# Module-level `app` for `flask --app app.py` and `gunicorn app:app`
app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002, debug=True)
