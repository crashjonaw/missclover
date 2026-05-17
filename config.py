"""Configuration for MISS CLOVER. Reads from environment via python-dotenv."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")

    # Database — relative paths land under instance/ via Flask-SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///missclover.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Public site URL for absolute links in emails
    SITE_URL = os.getenv("SITE_URL", "http://127.0.0.1:5002")

    # HitPay
    HITPAY_API_KEY = os.getenv("HITPAY_API_KEY", "")
    HITPAY_SALT = os.getenv("HITPAY_SALT", "")
    HITPAY_API_BASE = os.getenv("HITPAY_API_BASE", "https://api.sandbox.hit-pay.com/v1")
    HITPAY_PAYMENT_METHODS = [
        m.strip() for m in os.getenv("HITPAY_PAYMENT_METHODS", "paynow_online,card,grabpay").split(",") if m.strip()
    ]

    # Mail
    MAIL_SERVER = os.getenv("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "2525"))
    MAIL_USE_TLS = _bool("MAIL_USE_TLS", True)
    MAIL_USE_SSL = _bool("MAIL_USE_SSL", False)
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "hello@missclover.sg")
    MAIL_SUPPRESS_SEND = _bool("MAIL_SUPPRESS_SEND", False)

    # Admin bootstrap (override in .env for production)
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "JYVS2026")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@missclover.co")

    # Pre-orders: out-of-stock colours ship within this window (guaranteed)
    PREORDER_FULFILMENT_DAYS = int(os.getenv("PREORDER_FULFILMENT_DAYS", "60"))
    LOW_STOCK_THRESHOLD = int(os.getenv("LOW_STOCK_THRESHOLD", "3"))

    # Shipping (cents, SGD)
    SHIPPING_FLAT_RATE_CENTS = int(os.getenv("SHIPPING_FLAT_RATE_CENTS", "800"))
    FREE_SHIPPING_THRESHOLD_CENTS = int(os.getenv("FREE_SHIPPING_THRESHOLD_CENTS", "20000"))

    CURRENCY = "SGD"
