"""Auth: register / login / logout / forgot / reset."""
from models import PasswordResetToken, User


def test_register_creates_user_and_signs_in(client):
    r = client.post("/auth/register", data={
        "email": "new@user.com",
        "password": "supersecret",
        "first_name": "New",
        "last_name": "User",
        "newsletter": "on",
    }, follow_redirects=False)
    assert r.status_code == 302
    u = User.query.filter_by(email="new@user.com").first()
    assert u is not None
    assert u.first_name == "New"
    assert u.newsletter_opt_in is True
    # Session: hitting /account/ should now succeed
    r2 = client.get("/account/")
    assert r2.status_code == 200


def test_register_rejects_short_password(client):
    r = client.post("/auth/register", data={
        "email": "a@b.com", "password": "short", "first_name": "A", "last_name": "B"
    })
    assert r.status_code == 200  # re-renders with error
    assert b"at least 8 characters" in r.data
    assert User.query.filter_by(email="a@b.com").first() is None


def test_register_rejects_duplicate_email(client, user):
    r = client.post("/auth/register", data={
        "email": "alice@example.com", "password": "anotherpass",
        "first_name": "X", "last_name": "Y"
    })
    assert b"already exists" in r.data


def test_login_with_correct_credentials(client, user):
    r = client.post("/auth/login", data={"email": "alice@example.com", "password": "password123"})
    assert r.status_code == 302
    assert client.get("/account/").status_code == 200


def test_login_wrong_password_rerenders_with_error(client, user):
    r = client.post("/auth/login", data={"email": "alice@example.com", "password": "wrong"})
    assert r.status_code == 200
    assert b"incorrect" in r.data
    # not logged in
    assert client.get("/account/").status_code == 302


def test_login_unknown_email_rerenders_with_error(client):
    r = client.post("/auth/login", data={"email": "ghost@nowhere.com", "password": "whatever"})
    assert b"incorrect" in r.data


def test_logout(signed_in):
    r = signed_in.get("/auth/logout")
    assert r.status_code == 302
    # No longer logged in
    r2 = signed_in.get("/account/")
    assert r2.status_code == 302
    assert "/auth/login" in r2.headers["Location"]


def test_forgot_password_creates_reset_token_for_existing_user(client, user, db_):
    r = client.post("/auth/forgot", data={"email": "alice@example.com"})
    assert r.status_code == 200
    assert PasswordResetToken.query.filter_by(user_id=user.id).count() == 1


def test_forgot_password_silent_for_unknown_email(client, db_):
    """For privacy, unknown emails get the same response and no token is created."""
    r = client.post("/auth/forgot", data={"email": "nobody@example.com"})
    assert r.status_code == 200
    assert b"sent a reset link" in r.data
    assert PasswordResetToken.query.count() == 0


def test_reset_with_invalid_token_shows_error(client):
    r = client.get("/auth/reset/garbage-token")
    assert b"invalid or has expired" in r.data
