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
def products(db_):
    """Seed Classic + Maroon and return them as a dict by design_code."""
    from models import Product, ProductVariant

    out = {}
    for code, name, sku in [
        ("classic", "The Classic Tote", "MC-CLS-CR"),
        ("maroon", "The Maroon Tote", "MC-MRN-BG"),
    ]:
        p = Product(
            slug=f"{code}-tote",
            name=name,
            description=f"Test {code}",
            design_code=code,
            base_price_cents=35000,
        )
        db_.session.add(p)
        db_.session.flush()
        v = ProductVariant(
            product_id=p.id,
            name=code.capitalize(),
            sku=sku,
            stock_qty=20,
            price_cents=35000,
        )
        db_.session.add(v)
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
