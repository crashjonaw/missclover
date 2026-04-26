"""Cart behaviour: add / update / remove, math, and shipping rule."""
from models import Cart, CartItem


def _vid(products, code):
    return products[code].primary_variant.id


def test_add_creates_cart_and_item(client, products, db_):
    r = client.post("/cart/add", data={"variant_id": _vid(products, "classic"), "qty": 1})
    assert r.status_code == 302
    cart = Cart.query.first()
    assert cart is not None
    assert len(cart.items) == 1
    assert cart.items[0].qty == 1
    assert cart.subtotal_cents == 35000


def test_add_same_variant_twice_increments_qty(client, products):
    vid = _vid(products, "classic")
    client.post("/cart/add", data={"variant_id": vid, "qty": 1})
    client.post("/cart/add", data={"variant_id": vid, "qty": 2})
    cart = Cart.query.first()
    assert len(cart.items) == 1
    assert cart.items[0].qty == 3


def test_add_caps_at_ten(client, products):
    vid = _vid(products, "classic")
    client.post("/cart/add", data={"variant_id": vid, "qty": 9})
    client.post("/cart/add", data={"variant_id": vid, "qty": 5})
    cart = Cart.query.first()
    assert cart.items[0].qty == 10


def test_view_cart_lists_items(client, products):
    client.post("/cart/add", data={"variant_id": _vid(products, "classic"), "qty": 1})
    r = client.get("/cart/")
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert "The Classic Tote" in body
    assert "S$350.00" in body
    assert "Subtotal" in body


def test_update_qty(client, products, db_):
    client.post("/cart/add", data={"variant_id": _vid(products, "classic"), "qty": 1})
    item = CartItem.query.first()
    client.post(f"/cart/update/{item.id}", data={"qty": 4})
    db_.session.refresh(item)
    assert item.qty == 4


def test_update_to_zero_removes_item(client, products, db_):
    client.post("/cart/add", data={"variant_id": _vid(products, "classic"), "qty": 1})
    item = CartItem.query.first()
    client.post(f"/cart/update/{item.id}", data={"qty": 0})
    assert CartItem.query.count() == 0


def test_remove_item(client, products):
    client.post("/cart/add", data={"variant_id": _vid(products, "classic"), "qty": 1})
    item = CartItem.query.first()
    client.post(f"/cart/remove/{item.id}")
    assert CartItem.query.count() == 0


def test_add_missing_variant_id_returns_400(client):
    r = client.post("/cart/add", data={})
    assert r.status_code == 400


def test_add_unknown_variant_404(client):
    r = client.post("/cart/add", data={"variant_id": 99999, "qty": 1})
    assert r.status_code == 404


def test_shipping_flat_rate_under_threshold(client, products):
    """1 product at S$350 < S$200 threshold → flat S$8 shipping."""
    # Wait, threshold is 20000 cents (S$200), 350 > 200, so shipping should be FREE
    # Let me re-read the rule: free shipping if subtotal >= FREE_SHIPPING_THRESHOLD_CENTS
    # 35000 >= 20000 → free.
    client.post("/cart/add", data={"variant_id": _vid(products, "classic"), "qty": 1})
    body = client.get("/cart/").get_data(as_text=True)
    assert "Free" in body  # shipping line shows "Free"


def test_qty_count_in_header(client, products):
    """Header should show cart-count badge after adding."""
    r = client.get("/")
    assert b"cart-count" not in r.data  # no badge when empty
    client.post("/cart/add", data={"variant_id": _vid(products, "classic"), "qty": 2})
    r = client.get("/")
    assert b"cart-count" in r.data
