"""Idempotent admin bootstrap.

    python create_admin.py

Creates (or repairs) the staff admin account from config:
ADMIN_USERNAME / ADMIN_PASSWORD / ADMIN_EMAIL (env-overridable; defaults
admin / JYVS2026 / admin@missclover.co). Safe to re-run — it upserts by
username, re-asserts is_admin, and resets the password to the configured
value (so rotating ADMIN_PASSWORD in .env + re-running rotates the login).
"""
from app import app
from extensions import db
from models import User


def ensure_admin() -> User:
    cfg = app.config
    username = cfg["ADMIN_USERNAME"]
    u = User.query.filter_by(username=username).first()
    if u is None:
        # Reuse a row that may already exist on the email, else create one.
        u = User.query.filter_by(email=cfg["ADMIN_EMAIL"]).first() or User(
            email=cfg["ADMIN_EMAIL"])
        u.username = username
        u.first_name = u.first_name or "MISS CLOVER"
        u.last_name = u.last_name or "Admin"
        db.session.add(u)
        action = "created"
    else:
        action = "updated"
    u.is_admin = True
    u.set_password(cfg["ADMIN_PASSWORD"])
    db.session.commit()
    print(f"Admin {action}: username={u.username!r} email={u.email!r} (id={u.id})")
    return u


if __name__ == "__main__":
    with app.app_context():
        ensure_admin()
