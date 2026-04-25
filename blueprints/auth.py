"""Auth blueprint — login, register, logout, forgot password, reset."""
import hashlib
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from extensions import db
from models import PasswordResetToken, User

bp = Blueprint("auth", __name__)


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("account.dashboard"))
    error = None
    next_url = request.args.get("next") or url_for("account.dashboard")
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=bool(request.form.get("remember")))
            flash("Welcome back.", "success")
            return redirect(next_url)
        error = "Email or password is incorrect."
    return render_template("auth/login.html", error=error, next_url=next_url)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("account.dashboard"))
    error = None
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        first = (request.form.get("first_name") or "").strip()
        last = (request.form.get("last_name") or "").strip()
        newsletter = bool(request.form.get("newsletter"))

        if not email or not password or len(password) < 8:
            error = "Password must be at least 8 characters."
        elif User.query.filter_by(email=email).first():
            error = "An account with that email already exists."
        else:
            u = User(email=email, first_name=first, last_name=last, newsletter_opt_in=newsletter)
            u.set_password(password)
            db.session.add(u)
            db.session.commit()
            login_user(u)
            flash("Welcome to MISS CLOVER.", "success")
            return redirect(url_for("account.dashboard"))
    return render_template("auth/register.html", error=error)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Signed out.", "info")
    return redirect(url_for("shop.home"))


@bp.route("/forgot", methods=["GET", "POST"])
def forgot():
    sent = False
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            raw = secrets.token_urlsafe(32)
            tok = PasswordResetToken(
                user_id=user.id,
                token_hash=_hash_token(raw),
                expires_at=datetime.utcnow() + timedelta(hours=2),
            )
            db.session.add(tok)
            db.session.commit()

            from email_service import send_password_reset
            reset_url = current_app.config["SITE_URL"].rstrip("/") + url_for("auth.reset", token=raw)
            send_password_reset(user.email, reset_url)
        # Always show "sent" — don't leak whether the email exists.
        sent = True
    return render_template("auth/forgot.html", sent=sent)


@bp.route("/reset/<token>", methods=["GET", "POST"])
def reset(token: str):
    tok = PasswordResetToken.query.filter_by(token_hash=_hash_token(token)).first()
    if not tok or tok.used_at or tok.expires_at < datetime.utcnow():
        return render_template("auth/reset.html", error="This link is invalid or has expired.", token=None)

    error = None
    if request.method == "POST":
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""
        if len(password) < 8:
            error = "Password must be at least 8 characters."
        elif password != confirm:
            error = "Passwords don't match."
        else:
            tok.user.set_password(password)
            tok.used_at = datetime.utcnow()
            db.session.commit()
            flash("Password updated. Please sign in.", "success")
            return redirect(url_for("auth.login"))
    return render_template("auth/reset.html", error=error, token=token)
