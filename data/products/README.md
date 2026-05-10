# Catalog — one YAML per product, grouped by silhouette family

```
data/products/
├── README.md                          ← this file
├── tote_design_1/                     ← the 8″×11″ structured tote silhouette
│   ├── classic.yaml                   ← cream colourway
│   └── maroon.yaml                    ← burgundy colourway
└── tote_design_2/                     ← (your next silhouette here)
    └── …yaml files for each colourway
```

Each `*.yaml` file defines **one product** (one silhouette × one colourway). The
subfolder is the silhouette family — group all colourways of the same bag under
the same folder.

`seed.py` recursively globs `data/products/**/*.yaml`, so subfolders are
purely organisational; no template / blueprint changes needed when adding one.

## To add a new colourway to an existing silhouette

1. Copy an existing yaml into the same silhouette folder, e.g.
   `cp data/products/tote_design_1/classic.yaml data/products/tote_design_1/sage.yaml`.
2. Edit `slug`, `name`, `design_code`, `color_hex`, marketing copy, and SKU.
3. Drop image(s) into `static/img/products/tote_design_1/<design_code>/` and list
   them under `images:` with paths like `products/tote_design_1/<design_code>/hero.jpg`.
4. Run `python seed.py`.

## To add an entirely new silhouette

1. Create `data/products/tote_design_2/` (or another descriptive name).
2. Add one yaml per colourway inside it.
3. Create the matching `static/img/products/tote_design_2/<design_code>/` folders
   and drop image files in.
4. Make sure each yaml's `images.path` field starts with
   `products/tote_design_2/<design_code>/…`.
5. Run `python seed.py`.

After either, the new bag(s) appear in the header nav, on the homepage tile-split,
on `/handbags`, on `/collections/<design_code>`, and as their own PDPs.
Zero template, CSS, or blueprint edits.

## Fields

| Field | Required | Notes |
|---|---|---|
| `slug` | ✓ | URL-safe identifier, used in `/handbags/<slug>` |
| `name` | ✓ | Full display name, e.g. *"The Forest Tote"* |
| `design_code` | ✓ | Short key, e.g. `forest`. Drives `/collections/<key>` and the image-folder name |
| `bag_type` | optional (default `tote`) | One of `tote`, `crossbody`, `shoulder`, `satchel`, `backpack`. Used by the "Sort by bag type" option |
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
