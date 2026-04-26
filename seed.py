"""Seed catalog from data/products.yaml. Idempotent — re-run safely:

  - Products are matched by `slug` (upserted)
  - Variants matched by `sku` (upserted; existing stock_qty preserved)
  - Images are replaced wholesale (delete then insert) so YAML is the source of truth

To add a new design, append to data/products.yaml, drop image(s) into
static/img/, and run `python seed.py`. No template / CSS / blueprint edits.
"""
from pathlib import Path

import yaml

from app import app
from extensions import db
from models import Product, ProductImage, ProductVariant


DATA_FILE = Path(__file__).parent / "data" / "products.yaml"


def _upsert_product(spec: dict) -> Product:
    p = Product.query.filter_by(slug=spec["slug"]).first()
    fields = dict(
        name=spec["name"],
        description=spec.get("description"),
        design_code=spec["design_code"],
        base_price_cents=spec["base_price_cents"],
        color_hex=spec.get("color_hex"),
        tile_eyebrow=spec.get("tile_eyebrow"),
        tile_headline=spec.get("tile_headline"),
        tile_body=spec.get("tile_body"),
        is_featured=bool(spec.get("is_featured", False)),
        display_order=int(spec.get("display_order", 100)),
        is_active=bool(spec.get("is_active", True)),
    )
    if not p:
        p = Product(slug=spec["slug"], **fields)
        db.session.add(p)
        db.session.flush()
        print(f"  + Product: {p.slug}")
    else:
        for k, v in fields.items():
            setattr(p, k, v)
        print(f"  ~ Product: {p.slug}")
    return p


def _upsert_variants(p: Product, variants_spec: list[dict]) -> None:
    for vs in variants_spec:
        v = ProductVariant.query.filter_by(sku=vs["sku"]).first()
        if not v:
            v = ProductVariant(
                product_id=p.id,
                name=vs["name"],
                sku=vs["sku"],
                stock_qty=int(vs.get("stock_qty", 0)),
                price_cents=int(vs["price_cents"]),
            )
            db.session.add(v)
            print(f"    + Variant: {v.sku}")
        else:
            v.name = vs["name"]
            v.price_cents = int(vs["price_cents"])
            # stock_qty preserved on re-seed
            print(f"    ~ Variant: {v.sku} (stock unchanged: {v.stock_qty})")


def _replace_images(p: Product, images_spec: list[dict]) -> None:
    # Replace wholesale — YAML is the source of truth
    for img in list(p.images):
        db.session.delete(img)
    for ix, im in enumerate(images_spec or []):
        db.session.add(ProductImage(
            product_id=p.id,
            path=im["path"],
            alt=im.get("alt"),
            sort_order=int(im.get("sort_order", ix + 1)),
        ))
    if images_spec:
        print(f"    images: {len(images_spec)}")


def seed_from_yaml():
    if not DATA_FILE.exists():
        raise SystemExit(f"Data file not found: {DATA_FILE}")
    spec = yaml.safe_load(DATA_FILE.read_text())
    products = spec.get("products") or []
    if not products:
        raise SystemExit(f"No products defined in {DATA_FILE}")

    with app.app_context():
        for ps in products:
            p = _upsert_product(ps)
            _upsert_variants(p, ps.get("variants", []))
            db.session.flush()
            _replace_images(p, ps.get("images", []))
        db.session.commit()
        total = Product.query.count()
        active = Product.query.filter_by(is_active=True).count()
        featured = Product.query.filter_by(is_featured=True).count()
        print(f"\nSeed complete. Products: {total} ({active} active, {featured} featured)")


if __name__ == "__main__":
    seed_from_yaml()
