"""Auth blueprint — login, register, logout, forgot password, reset."""
import hashlib
import secrets
from datetime import datetime, timedelta

from flask import (Blueprint, current_app, flash, redirect, render_template,
                   request, session, url_for)
from flask_login import current_user, login_required, login_user, logout_user

import google_oauth
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


# ─── Google OAuth ─────────────────────────────────────────────────────────────


def _safe_next(target: str | None) -> str | None:
    """Only allow same-site relative redirects (guards against open redirect)."""
    if target and target.startswith("/") and not target.startswith(("//", "/\\")):
        return target
    return None


@bp.route("/google")
def google_login():
    if not google_oauth.is_enabled():
        flash("Google sign-in isn't configured yet.", "info")
        return redirect(url_for("auth.login"))
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state
    nxt = _safe_next(request.args.get("next"))
    if nxt:
        session["oauth_next"] = nxt
    else:
        session.pop("oauth_next", None)
    return redirect(google_oauth.authorization_url(state))


@bp.route("/google/callback")
def google_callback():
    if request.args.get("error"):
        flash("Google sign-in was cancelled.", "info")
        return redirect(url_for("auth.login"))

    state = request.args.get("state")
    if not state or state != session.pop("oauth_state", None):
        flash("Google sign-in failed (invalid state). Please try again.", "error")
        return redirect(url_for("auth.login"))

    code = request.args.get("code")
    if not code:
        flash("Google sign-in failed (no authorization code).", "error")
        return redirect(url_for("auth.login"))

    try:
        token = google_oauth.exchange_code(code)
        access_token = token.get("access_token")
        if not access_token:
            raise RuntimeError(token.get("error_description")
                               or token.get("error") or "no access token")
        info = google_oauth.fetch_userinfo(access_token)
    except Exception as e:  # network / Google error — never 500 the user
        current_app.logger.warning("Google OAuth failed: %s", e)
        flash("We couldn't complete Google sign-in. Please try again.", "error")
        return redirect(url_for("auth.login"))

    email = (info.get("email") or "").strip().lower()
    if not email:
        flash("Google didn't return an email address.", "error")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()
    if user is None:
        user = User(
            email=email,
            first_name=(info.get("given_name") or "").strip(),
            last_name=(info.get("family_name") or "").strip(),
            oauth_provider="google",
        )
        db.session.add(user)
        db.session.commit()
        flash("Welcome to MISS CLOVER.", "success")
    else:
        if not user.oauth_provider:
            user.oauth_provider = "google"  # link Google to the existing account
            db.session.commit()
        flash("Welcome back.", "success")

    login_user(user, remember=True)
    nxt = _safe_next(session.pop("oauth_next", None))
    return redirect(nxt or url_for("account.dashboard"))
