"""Sort options on /handbags. Each `?sort=...` query orders the grid the right way.

Uses a small mixed catalog (3 products at different prices + bag_types) plus
a paid order to exercise the popularity ranking.
"""
import pytest

from extensions import db
from models import (Order, OrderItem, Product, ProductImage,
                    ProductVariant, User)


@pytest.fixture()
def mixed_products(db_):
    """Three active products at different prices + bag_types so sorts produce
    a deterministic order."""
    products = [
        # (slug, name, code, bag_type, price_cents, display_order, sku)
        ("alpha-tote",        "Alpha Tote",      "alpha",  "tote",      30000, 30, "MC-A-1"),
        ("bravo-cross",       "Bravo Crossbody", "bravo",  "crossbody", 25000, 10, "MC-B-1"),
        ("charlie-shoulder",  "Charlie Shoulder","charlie","shoulder",  40000, 20, "MC-C-1"),
    ]
    out = {}
    for slug, name, code, bt, price, order, sku in products:
        p = Product(slug=slug, name=name, design_code=code, bag_type=bt,
                    base_price_cents=price, color_hex="#888888",
                    tile_eyebrow=name, is_featured=True, display_order=order)
        db_.session.add(p); db_.session.flush()
        db_.session.add(ProductVariant(product_id=p.id, name=name, sku=sku,
                                       stock_qty=10, price_cents=price))
        db_.session.add(ProductImage(product_id=p.id, path=f"products/{code}.jpg",
                                     alt=name, sort_order=1))
        out[code] = p
    db_.session.commit()
    return out


def _slugs_in_order(html: str, products: dict) -> list[str]:
    """Read product slugs in the order they appear in the rendered listing."""
    out = []
    for slug in [p.slug for p in products.values()]:
        idx = html.find(f"/handbags/{slug}")
        if idx >= 0:
            out.append((idx, slug))
    return [s for _, s in sorted(out)]


# ─── Sort-key validation ──────────────────────────────────────────────────────


def test_sort_dropdown_renders_all_five_options(client, mixed_products):
    body = client.get("/handbags").get_data(as_text=True)
    for label in ["Featured", "Bag type", "Price &mdash; low to high",
                  "Price &mdash; high to low", "Most popular"]:
        # Allow either em-dash or HTML entity rendering
        plain = label.replace("&mdash;", "—")
        assert plain in body or label in body, f"missing sort label: {label}"
    # The form actually submits to itself
    assert 'action="/handbags"' in body
    assert 'name="sort"' in body


def test_unknown_sort_falls_back_to_featured(client, mixed_products):
    """A tampered ?sort=... value mustn't error — default to featured."""
    body = client.get("/handbags?sort=DROP_TABLE").get_data(as_text=True)
    # Featured option is selected
    assert '<option value="featured" selected' in body \
        or 'value="featured" selected' in body


def test_active_sort_is_preselected_in_dropdown(client, mixed_products):
    body = client.get("/handbags?sort=price_asc").get_data(as_text=True)
    assert 'value="price_asc" selected' in body


# ─── Featured (default) ──────────────────────────────────────────────────────


def test_default_sort_is_by_display_order(client, mixed_products):
    """Default = display_order ascending → bravo (10), charlie (20), alpha (30)."""
    body = client.get("/handbags").get_data(as_text=True)
    assert _slugs_in_order(body, mixed_products) == \
        ["bravo-cross", "charlie-shoulder", "alpha-tote"]


# ─── Price ────────────────────────────────────────────────────────────────────


def test_sort_price_asc(client, mixed_products):
    """Bravo S$250 → Alpha S$300 → Charlie S$400."""
    body = client.get("/handbags?sort=price_asc").get_data(as_text=True)
    assert _slugs_in_order(body, mixed_products) == \
        ["bravo-cross", "alpha-tote", "charlie-shoulder"]


def test_sort_price_desc(client, mixed_products):
    """Charlie S$400 → Alpha S$300 → Bravo S$250."""
    body = client.get("/handbags?sort=price_desc").get_data(as_text=True)
    assert _slugs_in_order(body, mixed_products) == \
        ["charlie-shoulder", "alpha-tote", "bravo-cross"]


# ─── Bag type ─────────────────────────────────────────────────────────────────


def test_sort_by_bag_type_groups_alphabetically(client, mixed_products):
    """Crossbody → Shoulder → Tote (alphabetical bag_type, then name)."""
    body = client.get("/handbags?sort=type").get_data(as_text=True)
    assert _slugs_in_order(body, mixed_products) == \
        ["bravo-cross", "charlie-shoulder", "alpha-tote"]


# ─── Popularity ───────────────────────────────────────────────────────────────


def _record_paid_order(db_, user, products_to_qty: list[tuple[Product, int]]):
    """Create a paid order with the given product/qty pairs."""
    o = Order(
        order_number=f"MC-2026-{len(products_to_qty):06X}",
        user_id=user.id,
        status="paid",
        subtotal_cents=sum(p.base_price_cents * q for p, q in products_to_qty),
        shipping_cents=0,
        total_cents=sum(p.base_price_cents * q for p, q in products_to_qty),
    )
    db_.session.add(o); db_.session.flush()
    for p, q in products_to_qty:
        db_.session.add(OrderItem(
            order_id=o.id, variant_id=p.primary_variant.id, qty=q,
            unit_price_cents=p.base_price_cents,
            name_snapshot=p.name, design_snapshot=p.design_code,
        ))
    db_.session.commit()


def test_popularity_with_no_orders_falls_back_to_display_order(client, mixed_products):
    """With zero sales, popularity ties → display_order asc."""
    body = client.get("/handbags?sort=popularity").get_data(as_text=True)
    assert _slugs_in_order(body, mixed_products) == \
        ["bravo-cross", "charlie-shoulder", "alpha-tote"]


def test_popularity_ranks_by_qty_sold(client, mixed_products, user, db_):
    """Sell some bags and the popularity sort should put the bestseller first."""
    # Charlie: 5 sold; Alpha: 2 sold; Bravo: 0 sold.
    _record_paid_order(db_, user, [
        (mixed_products["charlie"], 3),
        (mixed_products["alpha"],   2),
    ])
    _record_paid_order(db_, user, [
        (mixed_products["charlie"], 2),
    ])
    body = client.get("/handbags?sort=popularity").get_data(as_text=True)
    assert _slugs_in_order(body, mixed_products) == \
        ["charlie-shoulder", "alpha-tote", "bravo-cross"]


def test_popularity_ignores_pending_or_cancelled_orders(client, mixed_products, user, db_):
    """Orders that aren't paid/fulfilled shouldn't bump popularity.

    Setup: Alpha sells 1 (paid), Bravo has 99 pending and 50 cancelled units.
    Expectation: Alpha ranks first (1 paid > 0 paid for the others), Bravo's
    149 non-paid units don't count at all.
    """
    # Paid: alpha × 1
    _record_paid_order(db_, user, [(mixed_products["alpha"], 1)])

    # Pending: bravo × 99 (must NOT count)
    bravo = mixed_products["bravo"]
    pending = Order(order_number="MC-2026-PEND01", user_id=user.id, status="pending",
                    subtotal_cents=100, shipping_cents=0, total_cents=100)
    db_.session.add(pending); db_.session.flush()
    db_.session.add(OrderItem(order_id=pending.id, variant_id=bravo.primary_variant.id,
                              qty=99, unit_price_cents=bravo.base_price_cents,
                              name_snapshot=bravo.name, design_snapshot=bravo.design_code))

    # Cancelled: bravo × 50 (must NOT count either)
    cancelled = Order(order_number="MC-2026-CANC01", user_id=user.id, status="cancelled",
                      subtotal_cents=100, shipping_cents=0, total_cents=100)
    db_.session.add(cancelled); db_.session.flush()
    db_.session.add(OrderItem(order_id=cancelled.id, variant_id=bravo.primary_variant.id,
                              qty=50, unit_price_cents=bravo.base_price_cents,
                              name_snapshot=bravo.name, design_snapshot=bravo.design_code))
    db_.session.commit()

    body = client.get("/handbags?sort=popularity").get_data(as_text=True)
    # Alpha (1 paid) ranks ahead of Bravo's 149 non-paid units
    order = _slugs_in_order(body, mixed_products)
    assert order[0] == "alpha-tote", \
        f"Alpha should rank first via 1 paid sale; got order {order}"
    assert order.index("alpha-tote") < order.index("bravo-cross"), \
        "Pending/cancelled units must not bump bravo above alpha"
