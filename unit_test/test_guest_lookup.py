"""Guest order tracker — token + email pair must match exactly."""
from models import Address, Order, OrderItem


def _make_guest_order(db_, products, *, email="g@g.com", token="tok-abc-123"):
    """Create a paid guest order directly so we can test lookup in isolation."""
    addr = Address(recipient_name="G", line1="L1", postcode="123456", country="SG", phone="91234567")
    db_.session.add(addr); db_.session.flush()
    o = Order(
        order_number="MC-2026-TEST01",
        user_id=None,
        guest_email=email,
        guest_lookup_token=token,
        status="paid",
        subtotal_cents=35000,
        shipping_cents=0,
        total_cents=35000,
        shipping_address_id=addr.id,
    )
    db_.session.add(o); db_.session.flush()
    v = products["classic"].primary_variant
    db_.session.add(OrderItem(order_id=o.id, variant_id=v.id, qty=1, unit_price_cents=35000,
                              name_snapshot="The Classic Tote", design_snapshot="classic"))
    db_.session.commit()
    return o


def test_lookup_form_finds_guest_order(client, products, db_):
    o = _make_guest_order(db_, products)
    r = client.post("/order/lookup", data={"email": "g@g.com", "order_number": o.order_number})
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert o.order_number in body
    assert "The Classic Tote" in body


def test_lookup_form_wrong_email_rejected(client, products, db_):
    o = _make_guest_order(db_, products)
    r = client.post("/order/lookup", data={"email": "nope@x.com", "order_number": o.order_number})
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert "find a guest order" in body
    assert "Classic Tote" not in body


def test_lookup_form_wrong_order_number_rejected(client, products, db_):
    _make_guest_order(db_, products)
    r = client.post("/order/lookup", data={"email": "g@g.com", "order_number": "MC-9999-DEADBE"})
    assert "find a guest order" in r.get_data(as_text=True)


def test_token_link_works_with_correct_email_and_token(client, products, db_):
    o = _make_guest_order(db_, products)
    r = client.get(f"/order/track?email={o.guest_email}&token={o.guest_lookup_token}")
    assert r.status_code == 200
    assert o.order_number in r.get_data(as_text=True)


def test_token_link_rejects_wrong_token(client, products, db_):
    o = _make_guest_order(db_, products)
    r = client.get(f"/order/track?email={o.guest_email}&token=wrong-token")
    assert r.status_code == 404
    assert b"invalid or has expired" in r.data


def test_token_link_rejects_wrong_email(client, products, db_):
    o = _make_guest_order(db_, products)
    r = client.get(f"/order/track?email=other@example.com&token={o.guest_lookup_token}")
    assert r.status_code == 404


def test_token_link_email_case_normalised(client, products, db_):
    """Lookup matches lowercased emails (we lowercase on storage)."""
    o = _make_guest_order(db_, products, email="lower@x.com")
    r = client.get(f"/order/track?email=LOWER@X.com&token={o.guest_lookup_token}")
    # Our route lowercases the query param email, so this should match
    assert r.status_code == 200
