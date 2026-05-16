"""Refactor proof: adding a third design via the catalog API alone makes it
appear everywhere — header nav, homepage tiles, listing, collection landing,
PDP — with NO template, CSS, or blueprint edits.

Mirrors what `python seed.py` does after a YAML edit. If a future change
hardcodes "classic"/"maroon" anywhere, one of these tests will fail."""
from models import Collection, Product, ProductImage, ProductVariant, Series


def _add_collection(db_, *, cslug, cname, color, featured=True, order=30):
    """Drop in a whole Collection→Series→Product branch, as `seed.py` would."""
    c = Collection(slug=cslug, name=cname, color_hex=color, is_active=True,
                    is_featured=featured, display_order=order,
                    tile_eyebrow=cname, tile_body=f"{cname} marketing body.")
    db_.session.add(c); db_.session.flush()
    s = Series(collection_id=c.id, slug=f"{cslug}-series", name=f"{cname} Series",
               color_hex=color, is_active=True, is_featured=featured,
               display_order=10)
    db_.session.add(s); db_.session.flush()
    p = Product(
        slug=f"{cslug}-bag", name=f"The {cname} Bag", description=f"A {cname} bag.",
        design_code=cslug, bag_type="tote", series_id=s.id,
        base_price_cents=35000, color_hex=color, tile_eyebrow=cname,
        is_featured=featured, display_order=10, is_active=True,
    )
    db_.session.add(p); db_.session.flush()
    db_.session.add(ProductVariant(
        product_id=p.id, name=cname, sku=f"MC-{cslug[:3].upper()}-XX",
        stock_qty=10, price_cents=35000))
    db_.session.add(ProductImage(
        product_id=p.id, path=f"products/{cslug}.jpg", alt=cname, sort_order=1))
    db_.session.commit()
    return c, s, p


def _add_design(db_, *, code, name, color, order=30, featured=True,
                images=None):
    """Helper: drop in a brand-new design as if seeded from YAML."""
    p = Product(
        slug=f"{code}-tote",
        name=name,
        description=f"Hand-finished {code} tote.",
        design_code=code,
        base_price_cents=35000,
        color_hex=color,
        tile_eyebrow=f"The {code.capitalize()}",
        tile_headline=f"{name} headline",
        tile_body=f"{name} marketing body.",
        is_featured=featured,
        display_order=order,
        is_active=True,
    )
    db_.session.add(p); db_.session.flush()
    db_.session.add(ProductVariant(
        product_id=p.id, name=code.capitalize(),
        sku=f"MC-{code[:3].upper()}-XX", stock_qty=10, price_cents=35000,
    ))
    for ix, img in enumerate(images or [f"products/{code}.jpg"]):
        db_.session.add(ProductImage(
            product_id=p.id, path=img, alt=f"{name} view {ix+1}", sort_order=ix + 1,
        ))
    db_.session.commit()
    return p


# ─── Drop-in third design ────────────────────────────────────────────────────


def test_new_design_appears_on_handbags_listing(client, products, db_):
    _add_design(db_, code="forest", name="The Forest Tote", color="#2C4031")
    body = client.get("/handbags").get_data(as_text=True)
    assert "Forest Tote" in body


def test_new_design_has_pdp(client, products, db_):
    _add_design(db_, code="forest", name="The Forest Tote", color="#2C4031")
    r = client.get("/handbags/forest-tote")
    assert r.status_code == 200
    assert b"Forest Tote" in r.data


def test_new_collection_has_landing_and_series(client, products, db_):
    """A dropped-in collection gets its landing + series pages with no code edits."""
    _add_collection(db_, cslug="forest", cname="Forest", color="#2C4031")
    r = client.get("/collections/forest")
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert "Forest" in body
    assert "#2C4031" in body                       # color_hex rendered inline
    r2 = client.get("/collections/forest/forest-series")
    assert r2.status_code == 200
    assert "The Forest Bag" in r2.get_data(as_text=True)


def test_new_collection_appears_in_header_nav(client, products, db_):
    _add_collection(db_, cslug="forest", cname="Forest", color="#2C4031")
    body = client.get("/").get_data(as_text=True)
    assert "/collections/forest" in body
    assert "Forest" in body


def test_new_collection_appears_in_home_tile_split(client, products, db_):
    _add_collection(db_, cslug="forest", cname="Forest", color="#2C4031")
    body = client.get("/").get_data(as_text=True)
    # The collection tile is rendered with the collection's color_hex inline
    assert "background: #2C4031" in body
    assert "Forest" in body


def test_unfeatured_collection_excluded_from_nav_and_home(client, products, db_):
    """is_featured=False → not in nav/home, but landing + PDP still reachable."""
    _add_collection(db_, cslug="hidden", cname="Hidden", color="#000000",
                    featured=False)
    body = client.get("/").get_data(as_text=True)
    assert "/collections/hidden" not in body
    assert client.get("/collections/hidden").status_code == 200
    assert client.get("/collections/hidden/hidden-series").status_code == 200
    assert client.get("/handbags/hidden-bag").status_code == 200


def test_unknown_collection_404s(client, products):
    """No matching collection AND no matching design_code → a real 404."""
    assert client.get("/collections/nonexistent").status_code == 404


# ─── Multi-image gallery ─────────────────────────────────────────────────────


def test_pdp_renders_multi_image_thumbnails(client, products, db_):
    """When a product has multiple images, the PDP renders thumbnails."""
    p = _add_design(db_, code="forest", name="The Forest Tote", color="#2C4031",
                    images=["products/forest/hero.jpg",
                            "products/forest/interior.jpg",
                            "products/forest/side.jpg"])
    r = client.get(f"/handbags/{p.slug}")
    body = r.get_data(as_text=True)
    assert r.status_code == 200
    assert body.count("pdp-thumb") >= 3
    assert "products/forest/hero.jpg" in body
    assert "products/forest/interior.jpg" in body
    assert "products/forest/side.jpg" in body


def test_pdp_no_thumbs_when_only_one_image(client, products):
    """Existing single-image products should NOT render the thumbnail strip."""
    body = client.get("/handbags/classic-tote").get_data(as_text=True)
    assert 'class="pdp-thumb' not in body


# ─── Inline-styled swatches (no per-design CSS) ──────────────────────────────


def test_swatches_use_inline_color_hex_not_css_classes(client, products):
    body = client.get("/").get_data(as_text=True)
    # No legacy per-design CSS classes — they were dropped in the refactor
    assert "swatch--classic" not in body
    assert "swatch--maroon" not in body
    assert "swatch--cream" not in body
    # And colours are present as inline hex from the Product model
    assert "#F0E6D2" in body  # classic cream
    assert "#6E1A2D" in body  # maroon


# ─── text_on filter (light vs dark text choice) ─────────────────────────────


def test_text_on_filter_light_bg_picks_dark_text(app):
    """Cream (#F0E6D2) is light → text should be ink (#111111)."""
    with app.app_context():
        result = app.jinja_env.filters["text_on"]("#F0E6D2")
    assert result == "#111111"


def test_text_on_filter_dark_bg_picks_light_text(app):
    """Maroon (#6E1A2D) is dark → text should be cream (#FBFAF7)."""
    with app.app_context():
        result = app.jinja_env.filters["text_on"]("#6E1A2D")
    assert result == "#FBFAF7"


def test_text_on_filter_handles_empty_or_invalid(app):
    with app.app_context():
        f = app.jinja_env.filters["text_on"]
        assert f("") == "#111111"
        assert f(None) == "#111111"
        assert f("not-a-hex") == "#111111"


# ─── ProductImage cascade ─────────────────────────────────────────────────────


def test_deleting_product_cascades_to_images_and_variants(db_, products):
    p = products["classic"]
    pid = p.id
    assert ProductImage.query.filter_by(product_id=pid).count() >= 1
    assert ProductVariant.query.filter_by(product_id=pid).count() >= 1
    db_.session.delete(p)
    db_.session.commit()
    assert ProductImage.query.filter_by(product_id=pid).count() == 0
    assert ProductVariant.query.filter_by(product_id=pid).count() == 0
