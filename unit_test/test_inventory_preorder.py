"""Inventory admin + pre-order behaviour."""
from models import ActivityEvent, Order, OrderItem, ProductVariant


# ─── Variant stock model ──────────────────────────────────────────────────────

def test_variant_stock_properties(db_, products):
    v = products["classic"].primary_variant
    v.stock_qty = 5
    assert v.in_stock and not v.is_preorder and v.is_purchasable
    v.stock_qty = 0
    v.allow_preorder = True
    assert not v.in_stock and v.is_preorder and v.is_purchasable
    v.allow_preorder = False
    assert not v.is_preorder and not v.is_purchasable  # sold out


# ─── Inventory admin ──────────────────────────────────────────────────────────

def test_inventory_add_and_set_stock(admin_client, db_, products):
    v = products["classic"].primary_variant
    vid, start = v.id, v.stock_qty
    admin_client.post(f"/admin/inventory/{vid}",
                      data={"add_stock": "10", "allow_preorder": "on"})
    assert db_.session.get(ProductVariant, vid).stock_qty == start + 10
    admin_client.post(f"/admin/inventory/{vid}", data={"set_stock": "3"})
    fresh = db_.session.get(ProductVariant, vid)
    assert fresh.stock_qty == 3
    assert fresh.allow_preorder is False  # checkbox absent → off


def test_inventory_requires_admin(client, products):
    vid = products["classic"].primary_variant.id
    assert client.post(f"/admin/inventory/{vid}", data={"set_stock": "1"}).status_code == 404


def test_mark_fulfilled(admin_client, db_, products):
    from models import Address
    addr = Address(recipient_name="X", line1="L", postcode="123456",
                   country="SG", phone="9")
    db_.session.add(addr); db_.session.flush()
    o = Order(order_number="MC-2026-FUL01", guest_email="g@g.com",
              status="paid", subtotal_cents=100, shipping_cents=0,
              total_cents=100, shipping_address_id=addr.id)
    db_.session.add(o); db_.session.commit()
    admin_client.post(f"/admin/orders/{o.id}/fulfil")
    assert db_.session.get(Order, o.id).status == "fulfilled"


# ─── Pre-order storefront ─────────────────────────────────────────────────────

def _out_of_stock(db_, products, code="classic", preorder=True):
    v = products[code].primary_variant
    v.stock_qty = 0
    v.allow_preorder = preorder
    db_.session.commit()
    return v


def test_pdp_preorder_cta_and_guarantee(client, db_, products):
    _out_of_stock(db_, products, preorder=True)
    body = client.get("/handbags/classic-tote").get_data(as_text=True)
    assert "Pre-order" in body
    assert "preorder-note" in body
    assert "money back" in body


def test_pdp_sold_out_when_preorder_off(client, db_, products):
    _out_of_stock(db_, products, preorder=False)
    body = client.get("/handbags/classic-tote").get_data(as_text=True)
    assert "Sold out" in body


def test_cart_blocks_sold_out_but_allows_preorder(client, db_, products):
    v = _out_of_stock(db_, products, code="maroon", preorder=False)
    r = client.post("/cart/add", data={"variant_id": v.id, "qty": 1},
                    follow_redirects=True)
    assert "sold out" in r.get_data(as_text=True).lower()

    v2 = _out_of_stock(db_, products, code="classic", preorder=True)
    client.post("/cart/add", data={"variant_id": v2.id, "qty": 1})
    cart_body = client.get("/cart/").get_data(as_text=True)
    assert "Pre-order" in cart_body


def test_orderitem_preorder_snapshot(app, db_, products):
    """An out-of-stock line is snapshotted is_preorder=True at order time."""
    from models import Address
    v = _out_of_stock(db_, products, code="classic", preorder=True)
    addr = Address(recipient_name="X", line1="L", postcode="123456",
                   country="SG", phone="9")
    db_.session.add(addr); db_.session.flush()
    o = Order(order_number="MC-2026-PRE01", guest_email="g@g.com",
              status="pending", subtotal_cents=v.price_cents, shipping_cents=0,
              total_cents=v.price_cents, shipping_address_id=addr.id)
    db_.session.add(o); db_.session.flush()
    oi = OrderItem(order_id=o.id, variant_id=v.id, qty=1,
                   unit_price_cents=v.price_cents, is_preorder=v.stock_qty <= 0,
                   name_snapshot=v.product.name, design_snapshot=v.product.design_code)
    db_.session.add(oi); db_.session.commit()
    assert db_.session.get(OrderItem, oi.id).is_preorder is True
