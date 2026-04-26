"""Smoke tests: every public route returns the expected status code."""
import pytest


PUBLIC_OK = [
    "/",
    "/handbags",
    "/about",
    "/cart/",
    "/auth/login",
    "/auth/register",
    "/auth/forgot",
    "/order/lookup",
]


@pytest.mark.parametrize("path", PUBLIC_OK)
def test_public_routes_return_200(client, products, path):
    r = client.get(path)
    assert r.status_code == 200, f"{path} returned {r.status_code}"


def test_handbags_lists_seeded_products(client, products):
    r = client.get("/handbags")
    body = r.get_data(as_text=True)
    assert "The Classic Tote" in body
    assert "The Maroon Tote" in body
    assert "S$350.00" in body


def test_pdp_renders(client, products):
    r = client.get("/handbags/classic-tote")
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert "The Classic Tote" in body
    assert "S$350.00" in body
    assert "Add to bag" in body


def test_pdp_404_for_unknown_slug(client, products):
    assert client.get("/handbags/nope").status_code == 404


def test_collections_classic_and_maroon(client, products):
    assert client.get("/collections/classic").status_code == 200
    assert client.get("/collections/maroon").status_code == 200
    assert client.get("/collections/foo").status_code == 404


def test_account_routes_require_login(client):
    """Account pages should redirect to /auth/login when anonymous."""
    for path in ["/account/", "/account/orders", "/account/profile", "/account/addresses"]:
        r = client.get(path)
        assert r.status_code == 302
        assert "/auth/login" in r.headers["Location"]


def test_account_dashboard_when_signed_in(signed_in):
    r = signed_in.get("/account/")
    assert r.status_code == 200
    assert b"Recent orders" in r.data


def test_logout_requires_login(client):
    r = client.get("/auth/logout")
    assert r.status_code == 302  # redirect to login
    assert "/auth/login" in r.headers["Location"]


def test_404_renders_template(client):
    r = client.get("/this-does-not-exist")
    assert r.status_code == 404
    assert b"404" in r.data


def test_static_assets_served(client):
    # Site-critical static files
    for path in ["/static/css/tokens.css", "/static/css/components.css", "/static/css/base.css"]:
        r = client.get(path)
        assert r.status_code == 200, path

    # tokens.css should mention sage
    css = client.get("/static/css/tokens.css").get_data(as_text=True)
    assert "accent-sage" in css
