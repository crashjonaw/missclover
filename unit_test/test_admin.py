"""Admin console — auth gating, analytics correctness, nav, actions."""
from datetime import datetime

import admin_stats
from models import Address, Order, OrderItem


def _paid_order(db_, products, user=None, total=35000, when=None):
    addr = Address(recipient_name="X", line1="L1", postcode="123456",
                   country="SG", phone="9")
    db_.session.add(addr); db_.session.flush()
    o = Order(order_number=f"MC-T-{datetime.utcnow().timestamp()}",
              user_id=user.id if user else None,
              guest_email=None if user else "g@g.com",
              status="paid", subtotal_cents=total, shipping_cents=0,
              total_cents=total, shipping_address_id=addr.id)
    if when:
        o.created_at = when
    db_.session.add(o); db_.session.flush()
    v = products["classic"].primary_variant
    db_.session.add(OrderItem(order_id=o.id, variant_id=v.id, qty=1,
                              unit_price_cents=total, name_snapshot="X",
                              design_snapshot="classic"))
    db_.session.commit()
    return o


# ─── Auth gating ──────────────────────────────────────────────────────────────

def test_console_hidden_from_anonymous(client):
    assert client.get("/admin/").status_code == 404
    assert client.get("/admin/users").status_code == 404
    assert client.get("/admin/login").status_code == 200


def test_console_hidden_from_regular_customer(signed_in):
    assert signed_in.get("/admin/").status_code == 404


def test_admin_login_bad_then_good(client, admin):
    bad = client.post("/admin/login", data={"username": "admin", "password": "nope"})
    assert b"Invalid admin credentials" in bad.data
    good = client.post("/admin/login",
                       data={"username": "ADMIN", "password": "JYVS2026"})
    assert good.status_code == 302 and good.headers["Location"].endswith("/admin/")


def test_storefront_login_accepts_admin_username(client, admin):
    """Typing 'admin' on the main Sign-in (no @) works and lands in console."""
    r = client.post("/auth/login", data={"email": "admin", "password": "JYVS2026"})
    assert r.status_code == 302
    assert r.headers["Location"].endswith("/admin/")


def test_admin_can_login_with_email_too(client, admin):
    r = client.post("/admin/login",
                    data={"username": "admin@missclover.co", "password": "JYVS2026"})
    assert r.status_code == 302


def test_all_admin_pages_render(admin_client, products):
    for path in ("/admin/", "/admin/users", "/admin/orders",
                 "/admin/inventory", "/admin/fulfilment"):
        assert admin_client.get(path).status_code == 200


def test_admin_nav_link_shows_for_admin(admin_client, products):
    assert ">Admin<" in admin_client.get("/").get_data(as_text=True)


def test_admin_nav_link_hidden_for_customer(signed_in, products):
    assert ">Admin<" not in signed_in.get("/").get_data(as_text=True)


def test_admin_nav_link_hidden_for_anonymous(client, products):
    assert ">Admin<" not in client.get("/").get_data(as_text=True)


# ─── Analytics correctness ────────────────────────────────────────────────────

def test_overview_revenue_and_customers(app, db_, products, user):
    with app.app_context():
        _paid_order(db_, products, user=user, total=35000)
        _paid_order(db_, products, user=user, total=24000)
        ov = admin_stats.overview()
        assert ov["revenue_cents"] == 59000
        assert ov["paid_orders"] == 2
        assert ov["paying_customers"] == 1
        assert ov["repeat_customers"] == 1          # same user, 2 paid orders
        assert ov["customers"] >= 1
        assert ov["aov_cents"] == 29500


def test_customers_aggregation_lifetime_spend(app, db_, products, user):
    with app.app_context():
        _paid_order(db_, products, user=user, total=35000)
        rows = admin_stats.customers()
        me = next(r for r in rows if r["user"].id == user.id)
        assert me["spend_cents"] == 35000
        assert me["paid_orders"] == 1


def test_admin_excluded_from_customer_counts(app, db_, admin):
    with app.app_context():
        ov = admin_stats.overview()
        emails = [r["user"].email for r in admin_stats.customers()]
        assert "admin@missclover.co" not in emails


def test_user_detail_page(admin_client, db_, products, user):
    from extensions import db
    with admin_client.application.app_context():
        _paid_order(db, products, user=user)
    r = admin_client.get(f"/admin/users/{user.id}")
    assert r.status_code == 200
    assert user.email.encode() in r.data


def test_user_detail_404_for_unknown(admin_client):
    assert admin_client.get("/admin/users/99999").status_code == 404
