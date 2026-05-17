"""Activity logging — the growth/insight backbone."""
from activity import log_event
from models import ActivityEvent


def _count(db_, etype):
    return db_.session.query(ActivityEvent).filter_by(event_type=etype).count()


def test_register_logs_register_and_login(client, db_):
    client.post("/auth/register", data={
        "first_name": "Ada", "last_name": "L", "email": "ada@x.com",
        "password": "password123"})
    assert _count(db_, ActivityEvent.REGISTER) == 1
    # Flask-Login signal auto-captures the login that follows registration
    assert _count(db_, ActivityEvent.LOGIN) == 1
    ev = db_.session.query(ActivityEvent).filter_by(
        event_type=ActivityEvent.REGISTER).first()
    assert ev.user_id is not None


def test_login_logout_captured_via_signals(client, db_, user):
    client.post("/auth/login", data={"email": user.email, "password": "password123"})
    client.get("/auth/logout")
    assert _count(db_, ActivityEvent.LOGIN) == 1
    assert _count(db_, ActivityEvent.LOGOUT) == 1


def test_product_view_logged_with_product(client, db_, products):
    client.get("/handbags/classic-tote")
    ev = db_.session.query(ActivityEvent).filter_by(
        event_type=ActivityEvent.PRODUCT_VIEW).first()
    assert ev is not None
    assert ev.product_id == products["classic"].id


def test_add_to_cart_logged(client, db_, products):
    vid = products["classic"].primary_variant.id
    client.post("/cart/add", data={"variant_id": vid, "qty": 2})
    ev = db_.session.query(ActivityEvent).filter_by(
        event_type=ActivityEvent.ADD_TO_CART).first()
    assert ev is not None and ev.meta["qty"] == 2


def test_anon_events_keyed_by_session_then_user(client, db_, products):
    # Anonymous add-to-cart → anon_id set, user_id null
    vid = products["classic"].primary_variant.id
    client.post("/cart/add", data={"variant_id": vid, "qty": 1})
    ev = db_.session.query(ActivityEvent).filter_by(
        event_type=ActivityEvent.ADD_TO_CART).first()
    assert ev.user_id is None
    assert ev.anon_id  # cart session token captured pre-signup


def test_log_event_sets_revenue_on_paid(app, db_, products):
    """ORDER_PAID auto-captures order value for revenue analytics."""
    from models import Address, Order
    with app.test_request_context():
        addr = Address(recipient_name="G", line1="L1", postcode="123456",
                       country="SG", phone="9")
        db_.session.add(addr); db_.session.flush()
        o = Order(order_number="MC-2026-PAID01", guest_email="g@g.com",
                  status="paid", subtotal_cents=35000, shipping_cents=0,
                  total_cents=35000, shipping_address_id=addr.id)
        db_.session.add(o); db_.session.flush()
        ev = log_event(ActivityEvent.ORDER_PAID, order=o)
        assert ev.value_cents == 35000
        assert ev.order_id == o.id


def test_log_event_never_raises(app):
    """Analytics must not break the request path even on bad input."""
    with app.test_request_context():
        # event_type is NOT NULL — passing None must be swallowed, not raised
        assert log_event(None) is None
