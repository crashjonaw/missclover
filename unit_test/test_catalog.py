"""Refactor proof: adding a third design via the catalog API alone makes it
appear everywhere — header nav, homepage tiles, listing, collection landing,
PDP — with NO template, CSS, or blueprint edits.

Mirrors what `python seed.py` does after a YAML edit. If a future change
hardcodes "classic"/"maroon" anywhere, one of these tests will fail."""
from models import Product, ProductImage, ProductVariant


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


def test_new_design_has_collection_landing_no_whitelist(client, products, db_):
    """Whitelist removal: any design_code becomes a valid collections URL."""
    _add_design(db_, code="forest", name="The Forest Tote", color="#2C4031")
    r = client.get("/collections/forest")
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert "Forest Tote headline" in body or "Forest" in body
    # Background colour rendered inline from color_hex
    assert "#2C4031" in body


def test_new_design_appears_in_header_nav(client, products, db_):
    _add_design(db_, code="forest", name="The Forest Tote", color="#2C4031")
    body = client.get("/").get_data(as_text=True)
    assert "/collections/forest" in body
    assert "The Forest" in body  # tile_eyebrow


def test_new_design_appears_in_home_tile_split(client, products, db_):
    _add_design(db_, code="forest", name="The Forest Tote", color="#2C4031")
    body = client.get("/").get_data(as_text=True)
    # The new tile is rendered with the design's color_hex inline
    assert "background: #2C4031" in body
    assert "The Forest Tote" in body or "The Forest" in body


def test_unfeatured_design_excluded_from_nav_and_home(client, products, db_):
    """A new design with is_featured=False shouldn't appear in nav or home tiles."""
    _add_design(db_, code="hidden", name="The Hidden Tote", color="#000000", featured=False)
    body = client.get("/").get_data(as_text=True)
    assert "/collections/hidden" not in body
    # But the listing and PDP still work
    assert client.get("/handbags/hidden-tote").status_code == 200
    assert client.get("/collections/hidden").status_code == 200


def test_unknown_collection_404s(client, products):
    """Without a matching design_code, the collection page is a real 404."""
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
