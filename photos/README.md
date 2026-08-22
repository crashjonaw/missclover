# Master product photography

Source of truth for the site's product imagery. Everything under
`static/img/products/` is **generated from these files** by `build_images.py`
— edit here, then rebuild; don't hand-edit the output.

```
pip install -r requirements-dev.txt
python build_images.py
```

## What's here

| File | Feeds |
|---|---|
| `Baby Blue Clover Handbag.jpg` | Baby Blue Pillow |
| `Black Clover Handbag.jpg` | Black Pillow |
| `Dusty pink Clover Handbag.jpg` | Dusty Pink Pillow |
| `Mint Green Clover Handbag.jpg` | Mint Green Pillow |
| `Round clover baby blue .png` | Pastel Blue Moon Bag — **and the shared exterior for all four Moon Bags** |
| `round clover pastel lavender.png` | Pastel Lavender Moon Bag (interior only) |
| `round clover pastel pink.png` | Dusty Blush Pink Moon Bag (interior only) |
| `round clover sage green.png` | Sage Green Moon Bag (interior only) |
| `Website reference.jpg` | Design reference for layout/presentation. Not built into the site. |

## The Moon Bag exterior is synthetic

Worth knowing before you reshoot: only one Moon Bag exterior was ever
photographed. All four `round clover *.png` sheets show the **same cream
shell** — they differ only in the interior lining panels. Four listings all
showing an identical cream bag were indistinguishable in the product grid, so
`build_images.py` recolours the front/back views per colourway (hue and
saturation from the lining colour, original per-pixel brightness kept, so the
real shading and highlights survive).

If you shoot the Moon Bag in actual colours later, drop the new files in and
replace the recolour step in `build_images.py` with a straight crop — the
synthetic colouring exists only to cover the gap in the photography.

The interior shots are genuine per-colourway photographs and are cropped
straight through.

## Not built from here

`static/img/home/hero-lifestyle.jpg` — the homepage hero — is a separate
lifestyle photograph used unmodified.
