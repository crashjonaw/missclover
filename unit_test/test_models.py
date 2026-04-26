"""Model behaviour: password hashing, order numbering, computed properties."""
from datetime import datetime

from models import (Address, Cart, CartItem, Order, OrderItem, Product,
                    ProductVariant, User)


def test_user_password_hashing(db_):
    u = User(email="x@y.com")
    u.set_password("hunter2")
    db_.session.add(u); db_.session.commit()
    assert u.password_hash != "hunter2"
    assert u.check_password("hunter2") is True
    assert u.check_password("wrong") is False


def test_user_full_name_falls_back_to_email():
    u = User(email="bob@example.com", first_name=None, last_name=None)
    assert u.full_name == "bob@example.com"
    u.first_name, u.last_name = "Bob", "Builder"
    assert u.full_name == "Bob Builder"


def test_product_price_display(products):
    p = products["classic"]
    assert p.price_display == "S$350.00"


def test_product_primary_variant(products):
    p = products["classic"]
    assert p.primary_variant is not None
    assert p.primary_variant.sku == "MC-CLS-CR"


def test_cart_subtotal_and_qty(db_, products):
    cart = Cart(session_token="tok-test", user_id=None)
    db_.session.add(cart); db_.session.flush()
    v = products["classic"].primary_variant
    db_.session.add(CartItem(cart_id=cart.id, variant_id=v.id, qty=2,
                             unit_price_cents_snapshot=v.price_cents))
    db_.session.add(CartItem(cart_id=cart.id, variant_id=products["maroon"].primary_variant.id,
                             qty=1, unit_price_cents_snapshot=35000))
    db_.session.commit()
    assert cart.total_qty == 3
    assert cart.subtotal_cents == 35000 * 3


def test_order_number_format():
    n = Order.generate_number()
    parts = n.split("-")
    assert len(parts) == 3
    assert parts[0] == "MC"
    assert parts[1] == str(datetime.utcnow().year)
    assert len(parts[2]) == 6  # 3 hex bytes -> 6 chars
    # Two calls produce different numbers (collision is astronomically unlikely)
    assert Order.generate_number() != n


def test_order_guest_token_is_random_and_long():
    t1 = Order.generate_guest_token()
    t2 = Order.generate_guest_token()
    assert t1 != t2
    assert len(t1) >= 24


def test_order_is_guest_when_user_id_is_none():
    o = Order(order_number="MC-2026-AAAAAA", user_id=None, guest_email="g@g.com",
              status="pending", subtotal_cents=100, shipping_cents=0, total_cents=100)
    assert o.is_guest is True
    assert o.buyer_email == "g@g.com"


def test_order_buyer_email_uses_user_when_logged_in(db_):
    u = User(email="logged@in.com"); u.set_password("x"*8)
    db_.session.add(u); db_.session.commit()
    o = Order(order_number="MC-2026-BBBBBB", user_id=u.id, status="pending",
              subtotal_cents=100, shipping_cents=0, total_cents=100)
    db_.session.add(o); db_.session.commit()
    assert o.is_guest is False
    assert o.buyer_email == "logged@in.com"


def test_order_item_line_cents():
    it = OrderItem(order_id=1, variant_id=1, qty=3,
                   unit_price_cents=12345, name_snapshot="x", design_snapshot="x")
    assert it.line_cents == 12345 * 3
