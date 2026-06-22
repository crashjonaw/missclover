"""Fixtures for the Playwright mobile end-to-end tests.

These are heavier than the unit suite (real browser + a live server thread), so
they are OPT-IN: they only run when RUN_PLAYWRIGHT=1 is set. Otherwise they're
skipped during collection, keeping `pytest` fast and dependency-free.

    playwright install chromium            # one-time: download the browser
    RUN_PLAYWRIGHT=1 pytest unit_test/playwright

The live server runs the real app against a throwaway SQLite file with a minimal
seeded catalog, and Stripe is stubbed in-process so the payment page renders
without any network/live API calls.
"""
from __future__ import annotations

import os
import socket
import sys
import tempfile
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# iPhone-12-class viewport used for every test.
MOBILE_VIEWPORT = {"width": 390, "height": 844}
SCREENSHOT_DIR = Path(os.getenv("SCREENSHOT_DIR", str(Path(__file__).parent / "screenshots")))


# ── opt-in gate + marker ──────────────────────────────────────────────────────


def pytest_configure(config):
    config.addinivalue_line("markers", "playwright: browser end-to-end test (opt-in via RUN_PLAYWRIGHT=1)")


def pytest_collection_modifyitems(config, items):
    if os.getenv("RUN_PLAYWRIGHT") == "1":
        return
    skip = pytest.mark.skip(reason="Playwright E2E — set RUN_PLAYWRIGHT=1 to run")
    for item in items:
        if "playwright" in str(item.fspath).replace("\\", "/"):
            item.add_marker(skip)


# ── test config + seed ─────────────────────────────────────────────────────────


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _make_test_app(db_path: str):
    from config import Config

    class PWConfig(Config):
        TESTING = True
        SECRET_KEY = "playwright-secret"
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
        # The server runs in its own thread; allow the connection to cross it.
        SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"check_same_thread": False}}
        WTF_CSRF_ENABLED = False
        MAIL_SUPPRESS_SEND = True
        SITE_URL = "http://127.0.0.1"
        STRIPE_SECRET_KEY = "sk_test_dummy"
        STRIPE_PUBLISHABLE_KEY = "pk_test_dummy"
        STRIPE_WEBHOOK_SECRET = "whsec_test_dummy"
        SHIPPING_FLAT_RATE_CENTS = 800
        FREE_SHIPPING_THRESHOLD_CENTS = 20000

    from app import create_app

    return create_app(PWConfig)


def _seed(app):
    """A tiny catalog: one collection/series with two in-stock products."""
    from extensions import db
    from models import Collection, Product, ProductImage, ProductVariant, Series

    with app.app_context():
        db.create_all()
        col = Collection(slug="cosy", name="Cosy", is_active=True, is_featured=True,
                         display_order=10, color_hex="#D8C3A5", tile_eyebrow="Cosy")
        db.session.add(col); db.session.flush()
        series = Series(collection_id=col.id, slug="pillow", name="Pillow", is_active=True,
                        is_featured=True, display_order=10, color_hex="#D8C3A5")
        db.session.add(series); db.session.flush()
        ids = {}
        for code, name, sku, color in [
            ("sand", "Sand Pillow", "PW-SD", "#D8C3A5"),
            ("thyme", "Thyme Pillow", "PW-TH", "#7C8A5A"),
        ]:
            p = Product(slug=f"{code}-pillow", name=name, description=f"Test {name}",
                        design_code=code, bag_type="shoulderbag", series_id=series.id,
                        base_price_cents=24000, color_hex=color, is_active=True,
                        is_featured=True)
            db.session.add(p); db.session.flush()
            v = ProductVariant(product_id=p.id, name=name, sku=sku, stock_qty=5,
                               price_cents=24000)
            db.session.add(v)
            db.session.add(ProductImage(product_id=p.id, path=f"products/{code}.jpg",
                                        alt=name, sort_order=1))
            db.session.flush()
            ids[code] = v.id
        db.session.commit()
        return ids


def _stub_stripe():
    """Replace the Stripe gateway with in-process fakes so the payment page
    renders without hitting the network or the live API."""
    import stripe_gateway

    class FakePI:
        def __init__(self, amount=0, status="requires_payment_method", id="pi_pw_test"):
            self.id = id
            self.status = status
            self.amount = amount
            self.client_secret = f"{id}_secret_pw"

        def get(self, k, default=None):
            return getattr(self, k, default)

    last = {}

    def create_payment_intent(*, amount_cents, currency, reference, email, metadata=None):
        last["pi"] = FakePI(amount=amount_cents)
        return last["pi"]

    def retrieve_payment_intent(pid):
        return last.get("pi") or FakePI(id=pid)

    def update_payment_intent_amount(pid, amount_cents):
        pi = last.get("pi") or FakePI(id=pid)
        pi.amount = amount_cents
        return pi

    stripe_gateway.create_payment_intent = create_payment_intent
    stripe_gateway.retrieve_payment_intent = retrieve_payment_intent
    stripe_gateway.update_payment_intent_amount = update_payment_intent_amount


# ── live server ────────────────────────────────────────────────────────────────


class _ServerThread(threading.Thread):
    def __init__(self, app, port):
        super().__init__(daemon=True)
        from werkzeug.serving import make_server
        self._srv = make_server("127.0.0.1", port, app, threaded=True)

    def run(self):
        self._srv.serve_forever()

    def stop(self):
        self._srv.shutdown()


@pytest.fixture(scope="session")
def live_server():
    """Run the real app (seeded, Stripe-stubbed) on a free port for the session.

    Yields a dict: {"url": base_url, "variants": {design_code: variant_id}}.
    """
    fd, db_path = tempfile.mkstemp(suffix=".db", prefix="mc_pw_")
    os.close(fd)
    app = _make_test_app(db_path)
    variants = _seed(app)
    _stub_stripe()

    port = _free_port()
    server = _ServerThread(app, port)
    server.start()

    # Wait for the port to accept connections.
    base = f"http://127.0.0.1:{port}"
    for _ in range(100):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                break
        except OSError:
            threading.Event().wait(0.05)

    yield {"url": base, "variants": variants}

    server.stop()
    try:
        os.remove(db_path)
    except OSError:
        pass


# ── browser / page ──────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def _playwright():
    sync_api = pytest.importorskip("playwright.sync_api")
    with sync_api.sync_playwright() as pw:
        yield pw


@pytest.fixture(scope="session")
def browser(_playwright):
    try:
        b = _playwright.chromium.launch()
    except Exception as e:  # browser binary not installed
        pytest.skip(f"Chromium not available — run `playwright install chromium` ({e})")
    yield b
    b.close()


@pytest.fixture()
def page(browser):
    ctx = browser.new_context(viewport=MOBILE_VIEWPORT, device_scale_factor=2)
    pg = ctx.new_page()
    yield pg
    ctx.close()


# ── helpers exposed to tests ────────────────────────────────────────────────────


@pytest.fixture()
def shot_dir():
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    return SCREENSHOT_DIR
