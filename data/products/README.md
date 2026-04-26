# Catalog — one YAML per product

Each `*.yaml` file in this directory defines one product. Filename convention:
`<design_code>.yaml` (mirrors the image folder name in `static/img/products/<design_code>/`).

## To add a new bag

1. Copy `classic.yaml` to `data/products/<your-design>.yaml`.
2. Edit `slug`, `name`, `design_code`, `color_hex`, all the marketing copy, and the SKU.
3. Drop one or more images into `static/img/products/<your-design>/` and list them under `images:`.
4. Run `python seed.py` from the project root.
5. Restart the dev server (or `./run.sh`).

The new bag now appears in the header nav, on the homepage tile-split, on `/handbags`,
on `/collections/<your-design>`, and as its own PDP. Zero template, CSS, or blueprint edits.

## Fields

| Field | Required | Notes |
|---|---|---|
| `slug` | ✓ | URL-safe identifier, used in `/handbags/<slug>` |
| `name` | ✓ | Full display name, e.g. *"The Forest Tote"* |
| `design_code` | ✓ | Short key, e.g. `forest`. Drives `/collections/<key>` and the image-folder name |
| `color_hex` | ✓ | The bag's actual colour. Used for swatch chips and the tile background |
| `base_price_cents` | ✓ | SGD cents. `35000` = S$350.00 |
| `variants[]` | ✓ | At least one. Each: `name`, `sku` (unique), `stock_qty`, `price_cents` |
| `images[]` | recommended | Each: `path` (under `static/img/`), `alt`, `sort_order`. The first is the hero |
| `description` | optional | Short marketing line shown on PDP |
| `tile_eyebrow` | optional | Short label, e.g. *"The Classic"* — used in nav and on tile heading |
| `tile_headline` | optional | The big headline on `/collections/<key>` |
| `tile_body` | optional | Marketing paragraph on `/collections/<key>` and homepage tile |
| `is_featured` | optional (default false) | If true: shows in nav, on homepage tile-split, in listing colour filter |
| `display_order` | optional (default 100) | Lower numbers come first in nav and tile-split |
| `is_active` | optional (default true) | Set false to hide everywhere without deleting |

## Re-seed semantics

`python seed.py` is idempotent:

- Products are matched by `slug`. New ones are inserted; existing ones have all
  fields overwritten from YAML.
- Variants are matched by `sku`. New ones inserted; existing ones updated
  (but `stock_qty` is preserved so re-running won't reset stock counts).
- Images are replaced wholesale — YAML is the source of truth.
