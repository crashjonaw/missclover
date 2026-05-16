"""Seed catalog from data/products/ — Collection → Series → Product hierarchy.

Layout (folders ARE the hierarchy):

  data/products/
    <collection>/
      _collection.yaml          ← Collection metadata (slug must == folder name)
      <series>/
        _series.yaml            ← Series metadata (slug must == folder name)
        <colour>.yaml           ← one Product per file

Idempotent — re-run safely:

  - Collections matched by `slug` (upserted)
  - Series    matched by (collection, `slug`) (upserted)
  - Products  matched by `slug` (upserted)
  - Variants  matched by `sku` (upserted; existing stock_qty preserved)
  - Images    replaced wholesale (YAML is the source of truth)

To add a colour: drop `<colour>.yaml` into a series folder + the matching
image(s) into static/img/products/<collection>/<series>/<colour>/, then run
`python seed.py`. No template / CSS / blueprint edits.
"""
from pathlib import Path

import yaml

from app import app
from extensions import db
from models import Collection, Product, ProductImage, ProductVariant, Series


DATA_DIR = Path(__file__).parent / "data" / "products"


# ─── Loaders ──────────────────────────────────────────────────────────────────


def _read_yaml(path: Path) -> dict:
    spec = yaml.safe_load(path.read_text())
    if not isinstance(spec, dict):
        raise SystemExit(f"Expected a mapping at top of {path.relative_to(DATA_DIR.parent)}, "
                         f"got {type(spec).__name__}")
    return spec


def _load_metadata(kind: str, folder: Path, expected_slug: str) -> dict:
    """Load `_collection.yaml` / `_series.yaml`; validate slug == folder name."""
    fname = f"_{kind}.yaml"
    path = folder / fname
    if not path.is_file():
        raise SystemExit(f"Missing {fname} in {folder.relative_to(DATA_DIR.parent)}/")
    spec = _read_yaml(path)
    if spec.get("slug") != expected_slug:
        raise SystemExit(
            f"{path.relative_to(DATA_DIR.parent)}: slug '{spec.get('slug')}' "
            f"must match folder name '{expected_slug}'")
    if not spec.get("name"):
        raise SystemExit(f"{path.relative_to(DATA_DIR.parent)}: 'name' is required")
    return spec


def _load_product_files() -> list[tuple[Path, str, str, dict]]:
    """Glob every product YAML (skipping `_`-prefixed metadata files).

    Each product must live exactly at data/products/<collection>/<series>/<file>.yaml.
    Returns (path, collection_slug, series_slug, spec) tuples."""
    if not DATA_DIR.is_dir():
        raise SystemExit(f"Catalog directory not found: {DATA_DIR}")
    files = sorted(
        p for p in DATA_DIR.rglob("*")
        if p.is_file() and p.suffix in {".yaml", ".yml"} and not p.name.startswith("_")
    )
    if not files:
        raise SystemExit(f"No product YAML files in {DATA_DIR}")

    out: list[tuple[Path, str, str, dict]] = []
    for f in files:
        parts = f.relative_to(DATA_DIR).parts
        if len(parts) != 3:
            raise SystemExit(
                f"{f.relative_to(DATA_DIR)}: products must be nested exactly as "
                f"<collection>/<series>/<colour>.yaml")
        collection_slug, series_slug, _ = parts
        spec = _read_yaml(f)
        if not spec.get("slug") or not spec.get("design_code"):
            raise SystemExit(f"{f.relative_to(DATA_DIR)}: 'slug' and 'design_code' are required")
        out.append((f, collection_slug, series_slug, spec))
    return out


# ─── Upserts ──────────────────────────────────────────────────────────────────


def _meta_fields(spec: dict) -> dict:
    """Shared Collection/Series field set drawn from a metadata spec."""
    return dict(
        name=spec["name"],
        description=spec.get("description"),
        color_hex=spec.get("color_hex"),
        tile_eyebrow=spec.get("tile_eyebrow"),
        tile_headline=spec.get("tile_headline"),
        tile_body=spec.get("tile_body"),
        hero_image_path=spec.get("hero_image_path"),
        is_active=bool(spec.get("is_active", True)),
        is_featured=bool(spec.get("is_featured", False)),
        display_order=int(spec.get("display_order", 100)),
    )


def _upsert_collection(spec: dict) -> Collection:
    c = Collection.query.filter_by(slug=spec["slug"]).first()
    fields = _meta_fields(spec)
    if not c:
        c = Collection(slug=spec["slug"], **fields)
        db.session.add(c)
        db.session.flush()
        print(f"  + Collection: {c.slug}")
    else:
        for k, v in fields.items():
            setattr(c, k, v)
        print(f"  ~ Collection: {c.slug}")
    return c


def _upsert_series(spec: dict, collection: Collection) -> Series:
    s = Series.query.filter_by(collection_id=collection.id, slug=spec["slug"]).first()
    fields = _meta_fields(spec)
    if not s:
        s = Series(collection_id=collection.id, slug=spec["slug"], **fields)
        db.session.add(s)
        db.session.flush()
        print(f"    + Series: {collection.slug}/{s.slug}")
    else:
        for k, v in fields.items():
            setattr(s, k, v)
        print(f"    ~ Series: {collection.slug}/{s.slug}")
    return s


def _upsert_product(spec: dict, series: Series) -> Product:
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
        series_id=series.id,
    )
    if not p:
        p = Product(slug=spec["slug"], **fields)
        db.session.add(p)
        db.session.flush()
        print(f"      + Product: {p.slug}")
    else:
        for k, v in fields.items():
            setattr(p, k, v)
        print(f"      ~ Product: {p.slug}")
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
            print(f"        + Variant: {v.sku}")
        else:
            v.product_id = p.id
            v.name = vs["name"]
            v.price_cents = int(vs["price_cents"])
            # stock_qty preserved on re-seed
            print(f"        ~ Variant: {v.sku} (stock unchanged: {v.stock_qty})")


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
        print(f"        images: {len(images_spec)}")


# ─── Orchestration ────────────────────────────────────────────────────────────


def seed_from_yaml():
    files = _load_product_files()

    # Pre-scan: catch duplicate slugs / design_codes before touching the DB.
    seen_slugs: set[str] = set()
    seen_codes: set[str] = set()
    for f, _c, _s, spec in files:
        if spec["slug"] in seen_slugs:
            raise SystemExit(f"Duplicate slug '{spec['slug']}' in {f.relative_to(DATA_DIR)}")
        if spec["design_code"] in seen_codes:
            raise SystemExit(
                f"Duplicate design_code '{spec['design_code']}' in {f.relative_to(DATA_DIR)}")
        seen_slugs.add(spec["slug"])
        seen_codes.add(spec["design_code"])

    with app.app_context():
        print(f"Loading {len(files)} product file(s) from {DATA_DIR}/")
        # Cache upserted collections/series so each is processed once, in FK order.
        collections: dict[str, Collection] = {}
        series_cache: dict[tuple[str, str], Series] = {}

        for f, cslug, sslug, spec in files:
            if cslug not in collections:
                cmeta = _load_metadata("collection", DATA_DIR / cslug, cslug)
                collections[cslug] = _upsert_collection(cmeta)
            collection = collections[cslug]

            key = (cslug, sslug)
            if key not in series_cache:
                smeta = _load_metadata("series", DATA_DIR / cslug / sslug, sslug)
                series_cache[key] = _upsert_series(smeta, collection)
            series = series_cache[key]

            print(f"\n[{f.relative_to(DATA_DIR)}]")
            p = _upsert_product(spec, series)
            _upsert_variants(p, spec.get("variants", []))
            db.session.flush()
            _replace_images(p, spec.get("images", []))

        db.session.commit()
        print(
            f"\nSeed complete. "
            f"Collections: {Collection.query.count()} · "
            f"Series: {Series.query.count()} · "
            f"Products: {Product.query.count()} "
            f"({Product.query.filter_by(is_active=True).count()} active, "
            f"{Product.query.filter_by(is_featured=True).count()} featured)")


if __name__ == "__main__":
    seed_from_yaml()
