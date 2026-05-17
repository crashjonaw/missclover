"""Google OAuth 2.0 (authorization-code flow).

Mirrors the pattern in ref/quantiesunite but uses `requests` (already a
dependency, used by hitpay.py) instead of shelling out to curl.

Credentials live in `google_api_secret.json` at the repo root — the standard
"Web application" OAuth client file downloaded from Google Cloud Console:

    {"web": {"client_id": "...", "client_secret": "...", ...}}

That filename is covered by .gitignore (`*secret*.json`) so it is never
committed. If the file is absent the whole feature degrades gracefully:
`is_enabled()` returns False, the UI hides the button, and the routes flash
"not configured" instead of erroring.
"""
import json
import os
from pathlib import Path
from urllib.parse import urlencode

import requests
from flask import current_app, url_for

GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URI = "https://www.googleapis.com/oauth2/v2/userinfo"

_ROOT = Path(__file__).resolve().parent


def _secret_path() -> Path:
    """Resolve the Google OAuth client JSON. In priority order:

    1. $GOOGLE_OAUTH_SECRET_FILE (explicit override; used verbatim, no fallback
       — also how the test suite forces a deterministic 'disabled' state).
    2. ./google_api_secret.json (the documented default location).
    3. The Google-default download name dropped into ./bizfile/
       (client_secret_*.json) or ./bizfile/google_api_secret.json.
    """
    env = os.getenv("GOOGLE_OAUTH_SECRET_FILE")
    if env:
        p = Path(env)
        return p if p.is_absolute() else _ROOT / p

    root = _ROOT / "google_api_secret.json"
    if root.exists():
        return root

    for cand in sorted((_ROOT / "bizfile").glob("client_secret_*.json")):
        return cand
    return _ROOT / "bizfile" / "google_api_secret.json"


def _creds() -> dict:
    """The `web` block of the OAuth client JSON, or {} if absent/invalid.

    Read on each call (not import) so dropping the file in needs no restart
    and tests can monkeypatch it.
    """
    path = _secret_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text()).get("web", {}) or {}
    except (ValueError, OSError):
        return {}


def is_enabled() -> bool:
    c = _creds()
    return bool(c.get("client_id") and c.get("client_secret"))


def redirect_uri() -> str:
    """Built off SITE_URL so it matches whatever the app advertises (the same
    base used for email links). Register every value in Google Console:
      http://127.0.0.1:5002/auth/google/callback   (local dev)
      https://missclover.co/auth/google/callback    (production)
    """
    base = current_app.config["SITE_URL"].rstrip("/")
    return base + url_for("auth.google_callback")


def authorization_url(state: str) -> str:
    params = {
        "client_id": _creds().get("client_id", ""),
        "redirect_uri": redirect_uri(),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_URI}?{urlencode(params)}"


def exchange_code(code: str) -> dict:
    """Authorization code → token response (contains `access_token`)."""
    c = _creds()
    resp = requests.post(GOOGLE_TOKEN_URI, data={
        "code": code,
        "client_id": c.get("client_id", ""),
        "client_secret": c.get("client_secret", ""),
        "redirect_uri": redirect_uri(),
        "grant_type": "authorization_code",
    }, timeout=15)
    return resp.json()


def fetch_userinfo(access_token: str) -> dict:
    """Access token → Google profile (email, given_name, family_name, ...)."""
    resp = requests.get(
        GOOGLE_USERINFO_URI,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    return resp.json()
