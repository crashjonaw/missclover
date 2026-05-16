# Catalog — Collection › Series › Colour

The folder structure **is** the hierarchy. Three levels:

```
data/products/
├── README.md                          ← this file
├── <collection>/                      ← a Collection (e.g. signature)
│   ├── _collection.yaml               ← Collection metadata (slug == folder name)
│   └── <series>/                      ← a Series (e.g. clover)
│       ├── _series.yaml               ← Series metadata (slug == folder name)
│       └── <colour>.yaml              ← one Product per file
└── …
```

Current catalog:

```
signature/                  Signature collection
  _collection.yaml
  clover/                   Clover series   (bag_type: tote)
    _series.yaml
    classic.yaml            → Classic Clover Tote
    maroon.yaml             → Maroon Clover Tote
cosy/                       Cosy collection
  _collection.yaml
  pillow/                   Pillow series   (bag_type: shoulderbag)
    _series.yaml
    sand.yaml               → Sand Pillow
    thyme.yaml              → Thyme Pillow
```

`seed.py` recursively globs `data/products/<collection>/<series>/*.yaml`,
**skipping** any file whose name starts with `_` (those are Collection/Series
metadata). Every product must sit exactly two folders deep.

## Three concepts, do not conflate them

| Concept | Where it lives | Drives |
|---|---|---|
| **Collection** | folder + `_collection.yaml` | `/collections`, `/collections/<c>`, header mega-nav top level, home tiles, footer |
| **Series** | folder + `_series.yaml` | `/collections/<c>/<s>`, mega-nav second level, breadcrumbs |
| **`design_code`** | product YAML | bare colour key (e.g. `classic`). Unique **globally**. Drives `OrderItem` snapshots, image-path fallback, legacy `/collections/<design_code>` 301-redirects |
| **`bag_type`** | product YAML | the physical silhouette taxonomy (`tote`, `shoulderbag`, `crossbody`, `satchel`, `backpack`). Visible badge on card + PDP, plus the "Sort by bag type" + sidebar "Bag type" filter |

`bag_type` is **independent** of Series. The Clover series is `bag_type: tote`;
the Pillow series is `bag_type: shoulderbag` — but a series could mix bag types.

## Images

`static/img/products/<collection>/<series>/<colour>/hero.jpg` (any number of
views per colour). Each product YAML's `images[].path` is relative to
`static/img/` — e.g. `products/signature/clover/classic/hero.jpg`.

## Add a new colour (to an existing series)

1. `cp data/products/signature/clover/classic.yaml data/products/signature/clover/sage.yaml`
2. Edit `slug`, `name`, `design_code` (globally unique), `color_hex`, copy, SKU.
3. Drop image(s) into `static/img/products/signature/clover/sage/` and update `images[].path`.
4. `python seed.py`

## Add a new series (to an existing collection)

1. `mkdir data/products/signature/<series>` and add a `_series.yaml` (slug == folder name).
2. Add one `<colour>.yaml` per colour inside it + matching image folders.
3. `python seed.py`

## Add a new collection

1. `mkdir -p data/products/<collection>/<series>`; add `_collection.yaml` and `_series.yaml`.
2. Add the colour YAMLs + image folders.
3. `python seed.py`

After any of these the new bag(s)/series/collection appear automatically in the
header mega-nav, homepage tiles, `/collections`, `/handbags`, the listing
sidebar filters, and their own landing pages — **zero template / CSS / blueprint
edits**.

## Metadata fields (`_collection.yaml` / `_series.yaml`)

| Field | Required | Notes |
|---|---|---|
| `slug` | ✓ | Must equal the folder name. URL key |
| `name` | ✓ | Display name, e.g. *Signature*, *Clover* |
| `description` | optional | Long copy |
| `color_hex` | optional | Hero background; text colour auto-picked by the `text_on` filter |
| `tile_eyebrow` / `tile_headline` / `tile_body` | optional | Hero / tile copy |
| `hero_image_path` | optional | Under `static/img/`. Falls back to the first product's hero |
| `is_featured` | optional (default false) | If true: shows in header nav, home tiles, footer |
| `is_active` | optional (default true) | false hides it everywhere (landing 404s) |
| `display_order` | optional (default 100) | Lower comes first |

## Product fields (`<colour>.yaml`)

| Field | Required | Notes |
|---|---|---|
| `slug` | ✓ | URL-safe, globally unique. Used in `/handbags/<slug>` |
| `name` | ✓ | Full display name, e.g. *Classic Clover Tote* |
| `design_code` | ✓ | Bare colour key, globally unique. NOT folder-prefixed |
| `bag_type` | optional (default `tote`) | `tote` \| `shoulderbag` \| `crossbody` \| `satchel` \| `backpack` |
| `color_hex` | ✓ | Swatch + tile background |
| `base_price_cents` | ✓ | SGD cents. `35000` = S$350.00 |
| `variants[]` | ✓ | Each: `name`, `sku` (unique), `stock_qty`, `price_cents` |
| `images[]` | recommended | Each: `path`, `alt`, `sort_order`. First is the hero |
| `description` | optional | PDP copy |
| `tile_eyebrow` / `tile_headline` / `tile_body` | optional | Card/landing copy |
| `is_featured` | optional (default false) | |
| `display_order` | optional (default 100) | Colour order within its series |
| `is_active` | optional (default true) | false hides without deleting |

Collection/Series are derived from the **folder path** — there are no
`collection`/`series` keys in the product YAML.

## Re-seed semantics

`python seed.py` is idempotent:

- Collections matched by `slug`; Series by `(collection, slug)`; Products by
  `slug`. New ones inserted; existing ones overwritten from YAML.
- Variants matched by `sku`. New inserted; existing updated, but `stock_qty`
  is **preserved** (re-seeding never resets stock). To rename a SKU, update the
  variant's stock-bearing row via a migration first, or accept a fresh row.
- Images replaced wholesale — YAML is the source of truth.
