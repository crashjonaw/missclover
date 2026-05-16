"""Pytest fixtures for the MISS CLOVER test suite.

Each test gets:
  - `app`     — a Flask app bound to a fresh in-memory SQLite DB
  - `client`  — Flask test client (cookies persist within a single test)
  - `db_`     — the SQLAlchemy session, with `db.create_all()` already run
  - `products`— Classic + Maroon products seeded into the DB
  - `user`    — a registered user (alice@example.com / password123)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Make project root importable so `import app`, `import models`, etc. resolve
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import Config  # noqa: E402


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-only"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True
    SITE_URL = "http://testserver"
    HITPAY_API_KEY = "test-api-key"
    HITPAY_SALT = "test-salt-for-hmac"
    HITPAY_API_BASE = "https://api.sandbox.hit-pay.com/v1"
    HITPAY_PAYMENT_METHODS = ["paynow_online", "card", "grabpay"]
    SHIPPING_FLAT_RATE_CENTS = 800
    FREE_SHIPPING_THRESHOLD_CENTS = 20000


@pytest.fixture()
def app():
    # Import inside the fixture so the module-level prod app
    # (in app.py) is created against real env, but each test creates its own
    # isolated app + in-memory DB.
    from app import create_app
    from extensions import db

    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db_(app):
    from extensions import db
    return db


@pytest.fixture()
def hierarchy(db_):
    """Signature→Clover and Cosy→Pillow, featured + active. Returned by slug."""
    from models import Collection, Series

    sig = Collection(slug="signature", name="Signature", is_active=True,
                      is_featured=True, display_order=10, color_hex="#F0E6D2",
                      tile_eyebrow="Signature", tile_body="Signature body")
    cosy = Collection(slug="cosy", name="Cosy", is_active=True,
                      is_featured=True, display_order=20, color_hex="#D8C3A5",
                      tile_eyebrow="Cosy", tile_body="Cosy body")
    db_.session.add_all([sig, cosy]); db_.session.flush()
    clover = Series(collection_id=sig.id, slug="clover", name="Clover",
                    is_active=True, is_featured=True, display_order=10,
                    color_hex="#F0E6D2")
    pillow = Series(collection_id=cosy.id, slug="pillow", name="Pillow",
                    is_active=True, is_featured=True, display_order=10,
                    color_hex="#D8C3A5")
    db_.session.add_all([clover, pillow]); db_.session.flush()
    db_.session.commit()
    return {"signature": sig, "cosy": cosy, "clover": clover, "pillow": pillow}


@pytest.fixture()
def products(db_, hierarchy):
    """Classic + Maroon (featured, with images) under Signature→Clover.
    Returned as a dict keyed by design_code."""
    from models import Product, ProductImage, ProductVariant

    out = {}
    for code, name, sku, color, order in [
        ("classic", "The Classic Tote", "MC-CLS-CR", "#F0E6D2", 10),
        ("maroon",  "The Maroon Tote",  "MC-MRN-BG", "#6E1A2D", 20),
    ]:
        p = Product(
            slug=f"{code}-tote",
            name=name,
            description=f"Test {code}",
            design_code=code,
            bag_type="tote",
            series_id=hierarchy["clover"].id,
            base_price_cents=35000,
            color_hex=color,
            tile_eyebrow=f"The {code.capitalize()}",
            tile_headline=f"{code.capitalize()} headline",
            tile_body=f"Test body for {code}",
            is_featured=True,
            display_order=order,
            is_active=True,
        )
        db_.session.add(p); db_.session.flush()
        db_.session.add(ProductVariant(
            product_id=p.id, name=code.capitalize(), sku=sku, stock_qty=20, price_cents=35000,
        ))
        db_.session.add(ProductImage(
            product_id=p.id, path=f"products/{code}.jpg", alt=f"{name} — front", sort_order=1,
        ))
        out[code] = p
    db_.session.commit()
    return out


@pytest.fixture()
def user(db_):
    """A logged-out registered user."""
    from models import User
    u = User(email="alice@example.com", first_name="Alice", last_name="A")
    u.set_password("password123")
    db_.session.add(u)
    db_.session.commit()
    return u


@pytest.fixture()
def signed_in(client, user):
    """A test client already authenticated as `user`."""
    client.post("/auth/login", data={"email": user.email, "password": "password123"})
    return client
