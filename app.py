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

    # Make cart count + currency available everywhere
    @app.context_processor
    def inject_globals():
        from datetime import datetime
        from blueprints.cart import get_cart
        cart = get_cart(create=False)
        return dict(
            cart_qty=cart.total_qty if cart else 0,
            cart_subtotal_cents=cart.subtotal_cents if cart else 0,
            currency="SGD",
            now_year=datetime.utcnow().year,
        )

    @app.template_filter("sgd")
    def sgd_filter(cents):
        if cents is None:
            return "—"
        return f"S${int(cents) / 100:,.2f}"

    @app.errorhandler(404)
    def not_found(_):
        return render_template("404.html"), 404

    return app


# Module-level `app` for `flask --app app.py` and `gunicorn app:app`
app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002, debug=True)
