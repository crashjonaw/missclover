"""Google OAuth: graceful-disable, CSRF state, find-or-create."""
from urllib.parse import parse_qs, urlparse

import pytest

import google_oauth
from models import User


@pytest.fixture()
def google_on(monkeypatch):
    """Enable Google OAuth with fake creds (no secret file needed)."""
    monkeypatch.setattr(google_oauth, "_creds",
                        lambda: {"client_id": "cid", "client_secret": "sec"})
    return monkeypatch


# ─── Disabled (no google_api_secret.json) ─────────────────────────────────────

def test_disabled_hides_button_everywhere(client, products):
    for path in ("/auth/login", "/auth/register"):
        assert "Continue with Google" not in client.get(path).get_data(as_text=True)


def test_disabled_google_route_redirects(client):
    r = client.get("/auth/google")
    assert r.status_code == 302
    assert r.headers["Location"].endswith("/auth/login")


# ─── Enabled ──────────────────────────────────────────────────────────────────

def test_enabled_shows_button(client, google_on):
    body = client.get("/auth/login").get_data(as_text=True)
    assert "Continue with Google" in body


def test_google_login_redirects_to_consent_with_state(client, google_on):
    r = client.get("/auth/google")
    assert r.status_code == 302
    loc = r.headers["Location"]
    assert loc.startswith("https://accounts.google.com/o/oauth2/v2/auth")
    qs = parse_qs(urlparse(loc).query)
    assert qs["client_id"] == ["cid"]
    assert qs["state"][0]
    with client.session_transaction() as s:
        assert s["oauth_state"] == qs["state"][0]


def _begin(client):
    """Start the flow; return the CSRF state the server stored."""
    loc = client.get("/auth/google").headers["Location"]
    return parse_qs(urlparse(loc).query)["state"][0]


def test_callback_rejects_bad_state(client, google_on):
    _begin(client)
    r = client.get("/auth/google/callback?state=tampered&code=x")
    assert r.status_code == 302 and r.headers["Location"].endswith("/auth/login")
    assert User.query.filter_by(email="x@gmail.com").first() is None


def test_callback_creates_and_logs_in_new_user(client, google_on, monkeypatch, db_):
    monkeypatch.setattr(google_oauth, "exchange_code",
                        lambda code: {"access_token": "tok"})
    monkeypatch.setattr(google_oauth, "fetch_userinfo", lambda t: {
        "email": "New.Person@Gmail.com", "given_name": "New", "family_name": "Person"})
    state = _begin(client)
    r = client.get(f"/auth/google/callback?state={state}&code=abc")
    assert r.status_code == 302
    assert r.headers["Location"].endswith("/account/")

    u = User.query.filter_by(email="new.person@gmail.com").first()
    assert u is not None
    assert u.oauth_provider == "google"
    assert u.password_hash is None
    assert u.first_name == "New" and u.last_name == "Person"
    # Session is authenticated → a login-required page works
    assert client.get("/account/").status_code == 200


def test_callback_links_existing_account(client, google_on, monkeypatch, user):
    monkeypatch.setattr(google_oauth, "exchange_code",
                        lambda code: {"access_token": "tok"})
    monkeypatch.setattr(google_oauth, "fetch_userinfo", lambda t: {
        "email": user.email, "given_name": "Alice", "family_name": "A"})
    state = _begin(client)
    r = client.get(f"/auth/google/callback?state={state}&code=abc")
    assert r.status_code == 302
    from extensions import db
    refreshed = db.session.get(User, user.id)
    assert refreshed.oauth_provider == "google"
    assert refreshed.password_hash is not None  # original password kept
    assert client.get("/account/").status_code == 200


def test_callback_token_failure_is_handled(client, google_on, monkeypatch):
    monkeypatch.setattr(google_oauth, "exchange_code",
                        lambda code: {"error": "invalid_grant"})
    state = _begin(client)
    r = client.get(f"/auth/google/callback?state={state}&code=abc")
    assert r.status_code == 302 and r.headers["Location"].endswith("/auth/login")


def test_open_redirect_next_is_ignored(client, google_on, monkeypatch):
    monkeypatch.setattr(google_oauth, "exchange_code",
                        lambda code: {"access_token": "tok"})
    monkeypatch.setattr(google_oauth, "fetch_userinfo", lambda t: {
        "email": "redir@gmail.com", "given_name": "R", "family_name": "X"})
    # Unsafe absolute next must not be honoured
    client.get("/auth/google?next=https://evil.example.com")
    with client.session_transaction() as s:
        state = s["oauth_state"]
        assert "oauth_next" not in s
    r = client.get(f"/auth/google/callback?state={state}&code=abc")
    assert r.headers["Location"].endswith("/account/")


def test_safe_next_is_honoured(client, google_on, monkeypatch):
    monkeypatch.setattr(google_oauth, "exchange_code",
                        lambda code: {"access_token": "tok"})
    monkeypatch.setattr(google_oauth, "fetch_userinfo", lambda t: {
        "email": "safe@gmail.com", "given_name": "S", "family_name": "N"})
    client.get("/auth/google?next=/checkout/shipping")
    with client.session_transaction() as s:
        state = s["oauth_state"]
        assert s["oauth_next"] == "/checkout/shipping"
    r = client.get(f"/auth/google/callback?state={state}&code=abc")
    assert r.headers["Location"].endswith("/checkout/shipping")
