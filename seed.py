"""Seed catalog from data/products/*.yaml — one file per product.

Idempotent — re-run safely:

  - Products are matched by `slug` (upserted)
  - Variants matched by `sku` (upserted; existing stock_qty preserved)
  - Images are replaced wholesale (delete then insert) so YAML is the source of truth

To add a new design, drop a new `data/products/<design_code>.yaml` and the
matching image(s) into static/img/products/<design_code>/, then run
`python seed.py`. No template / CSS / blueprint edits.
"""
from pathlib import Path

import yaml

from app import app
from extensions import db
from models import Product, ProductImage, ProductVariant


DATA_DIR = Path(__file__).parent / "data" / "products"


def _upsert_product(spec: dict) -> Product:
    p = Product.query.filter_by(slug=spec["slug"]).first()
    fields = dict(
        name=spec["name"],
        description=spec.get("description"),
        design_code=spec["design_code"],
        bag_type=(spec.get("bag_type") or "tote").lower(),
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


def _load_product_files() -> list[tuple[Path, dict]]:
    """Load every `*.yaml` (and `*.yml`) under data/products/ recursively.
    Subdirectories group products by silhouette family (e.g. tote_design_1/,
    tote_design_2/), but the seed treats them all as a flat list of products.
    Returns (path, parsed_spec) tuples so error messages can name the file."""
    if not DATA_DIR.is_dir():
        raise SystemExit(f"Catalog directory not found: {DATA_DIR}")
    files = sorted(
        p for p in DATA_DIR.rglob("*")
        if p.is_file() and p.suffix in {".yaml", ".yml"}
    )
    if not files:
        raise SystemExit(f"No product YAML files in {DATA_DIR}")
    out: list[tuple[Path, dict]] = []
    for f in files:
        spec = yaml.safe_load(f.read_text())
        if not spec:
            print(f"  ! Skipping empty file: {f.relative_to(DATA_DIR)}")
            continue
        if not isinstance(spec, dict):
            raise SystemExit(f"Expected mapping at top of {f}, got {type(spec).__name__}")
        if not spec.get("slug") or not spec.get("design_code"):
            raise SystemExit(f"{f.relative_to(DATA_DIR)}: 'slug' and 'design_code' are required")
        out.append((f, spec))
    return out


def seed_from_yaml():
    files = _load_product_files()
    seen_slugs: set[str] = set()
    seen_codes: set[str] = set()
    for f, spec in files:
        if spec["slug"] in seen_slugs:
            raise SystemExit(f"Duplicate slug '{spec['slug']}' in {f.name}")
        if spec["design_code"] in seen_codes:
            raise SystemExit(f"Duplicate design_code '{spec['design_code']}' in {f.name}")
        seen_slugs.add(spec["slug"])
        seen_codes.add(spec["design_code"])

    with app.app_context():
        print(f"Loading {len(files)} product file(s) from {DATA_DIR}/")
        for f, spec in files:
            print(f"\n[{f.relative_to(DATA_DIR)}]")
            p = _upsert_product(spec)
            _upsert_variants(p, spec.get("variants", []))
            db.session.flush()
            _replace_images(p, spec.get("images", []))
        db.session.commit()
        total = Product.query.count()
        active = Product.query.filter_by(is_active=True).count()
        featured = Product.query.filter_by(is_featured=True).count()
        print(f"\nSeed complete. Products: {total} ({active} active, {featured} featured)")


if __name__ == "__main__":
    seed_from_yaml()
