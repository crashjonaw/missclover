"""Collection → Series → Colour hierarchy: routes, redirects, filters, nav, badge."""


def test_collections_index_lists_active_featured(client, products):
    body = client.get("/collections").get_data(as_text=True)
    assert "Signature" in body
    assert "Cosy" in body
    assert "/collections/signature" in body
    assert "/collections/cosy" in body


def test_collection_page_lists_its_series(client, products):
    body = client.get("/collections/signature").get_data(as_text=True)
    assert "Clover" in body
    assert "/collections/signature/clover" in body


def test_series_page_lists_its_products(client, products):
    body = client.get("/collections/signature/clover").get_data(as_text=True)
    assert "The Classic Tote" in body
    assert "The Maroon Tote" in body


def test_inactive_collection_404(client, products, db_, hierarchy):
    hierarchy["cosy"].is_active = False
    db_.session.commit()
    assert client.get("/collections/cosy").status_code == 404


def test_inactive_series_404(client, products, db_, hierarchy):
    hierarchy["clover"].is_active = False
    db_.session.commit()
    assert client.get("/collections/signature/clover").status_code == 404


def test_legacy_single_segment_redirect(client, products):
    r = client.get("/collections/maroon")
    assert r.status_code == 301
    assert r.headers["Location"].endswith("/handbags/maroon-tote")


def test_legacy_two_segment_redirect(client, products):
    """Old silhouette-prefixed URL → 301 to PDP via the last path segment."""
    r = client.get("/collections/tote_design_1/classic")
    assert r.status_code == 301
    assert r.headers["Location"].endswith("/handbags/classic-tote")


def test_pdp_breadcrumb_shows_hierarchy(client, products):
    body = client.get("/handbags/classic-tote").get_data(as_text=True)
    assert "/collections/signature" in body
    assert "/collections/signature/clover" in body
    assert "Signature" in body and "Clover" in body


def test_handbags_filter_by_collection(client, products, db_, hierarchy):
    from models import Product, ProductVariant
    # Add a Cosy product so the collection filter is meaningful
    p = Product(slug="sand-pillow", name="Sand Pillow", design_code="sand",
                bag_type="shoulderbag", series_id=hierarchy["pillow"].id,
                base_price_cents=24000, color_hex="#D8C3A5", is_featured=True,
                display_order=10, is_active=True)
    db_.session.add(p); db_.session.flush()
    db_.session.add(ProductVariant(product_id=p.id, name="Sand",
                                   sku="MC-PLW-SD", stock_qty=5, price_cents=24000))
    db_.session.commit()

    body = client.get("/handbags?collection=cosy").get_data(as_text=True)
    # Product names also appear in the site-wide nav, so assert on the
    # filtered result count instead (only the one Cosy product matches).
    assert "<strong>1</strong> result" in body
    assert "Sand Pillow" in body


def test_handbags_filter_by_bag_type(client, products, db_, hierarchy):
    from models import Product, ProductVariant
    p = Product(slug="sand-pillow", name="Sand Pillow", design_code="sand",
                bag_type="shoulderbag", series_id=hierarchy["pillow"].id,
                base_price_cents=24000, color_hex="#D8C3A5", is_featured=True,
                display_order=10, is_active=True)
    db_.session.add(p); db_.session.flush()
    db_.session.add(ProductVariant(product_id=p.id, name="Sand",
                                   sku="MC-PLW-SD", stock_qty=5, price_cents=24000))
    db_.session.commit()

    body = client.get("/handbags?bag_type=shoulderbag").get_data(as_text=True)
    assert "<strong>1</strong> result" in body
    assert "Sand Pillow" in body


def test_bag_type_badge_renders(client, products):
    """The bag-type tag shows a human label on card + PDP."""
    listing = client.get("/handbags").get_data(as_text=True)
    assert "bag-type-tag" in listing
    assert "Tote" in listing
    pdp = client.get("/handbags/classic-tote").get_data(as_text=True)
    assert "bag-type-tag" in pdp
    assert "Tote" in pdp


def test_footer_collections_not_hardcoded(client, products):
    body = client.get("/").get_data(as_text=True)
    # De-hardcoded: links come from nav_collections, plus an index link
    assert "/collections/signature" in body
    assert "/collections/cosy" in body
    assert ">All collections<" in body


def test_collection_model_cascade(db_, hierarchy, products):
    """Deleting a Collection removes its Series but NOT its Products."""
    from models import Collection, Product, Series
    sig = hierarchy["signature"]
    pids = [p.id for p in Product.query.filter(Product.design_code.in_(["classic", "maroon"]))]
    assert pids
    db_.session.delete(sig)
    db_.session.commit()
    assert Collection.query.filter_by(slug="signature").first() is None
    assert Series.query.filter_by(slug="clover").first() is None
    # Products survive (orders may reference them); series_id is cleared.
    for pid in pids:
        p = Product.query.get(pid)
        assert p is not None
        assert p.series_id is None


def test_series_collection_slug_uniqueness(db_, hierarchy):
    """(collection_id, slug) is unique; same series slug in another collection is OK."""
    from models import Series
    import sqlalchemy.exc
    dup = Series(collection_id=hierarchy["signature"].id, slug="clover", name="Dup")
    db_.session.add(dup)
    try:
        db_.session.commit()
        assert False, "expected IntegrityError on duplicate (collection_id, slug)"
    except sqlalchemy.exc.IntegrityError:
        db_.session.rollback()
    # Same slug under a different collection is allowed
    ok = Series(collection_id=hierarchy["cosy"].id, slug="clover", name="OK")
    db_.session.add(ok)
    db_.session.commit()
    assert ok.id is not None
