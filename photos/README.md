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
| `Round clover baby blue .png` | Pastel Blue Bubble Bag — **and the shared exterior for all four Bubble Bags** |
| `round clover pastel lavender.png` | Pastel Lavender Bubble Bag (interior only) |
| `round clover pastel pink.png` | Dusty Blush Pink Bubble Bag (interior only) |
| `round clover sage green.png` | Sage Green Bubble Bag (interior only) |
| `Clover Bubble Series.jpg` | The homepage Clover Bubble Series banner |
| `Website reference.jpg` | Design reference for layout/presentation. Not built into the site. |

## ⚠️ The Bubble Bag exteriors on product cards are synthetic

The real bag has a **cream shell** in every colourway — the colour is the
interior lining. All four `round clover *.png` sheets show the same cream
exterior, and `Clover Bubble Series.jpg` confirms it: four cream bags,
distinguished only by their labels.

Product cards do **not** show it that way. Four identical cream thumbnails were
indistinguishable in the grid, so `build_images.py` recolours each colourway's
front/back views to its lining colour (hue and saturation swapped in, original
per-pixel brightness kept, so the real shading and highlights survive).

**This means the shop currently shows exterior colours the product doesn't
have**, while the series banner on the same page shows the true cream. Worth
resolving before launch — either reshoot the bags in real colours, or drop the
recolour step so the cards show cream and let the swatch/lining photos carry
the colourway. To do the latter, replace the `_recolour(...)` call in
`build_bubble_bags()` with a straight save of the cut-out.

The interior shots are genuine per-colourway photographs and are cropped
straight through.

## Not built from here

`static/img/home/hero-lifestyle.jpg` — the homepage hero — is a separate
lifestyle photograph used unmodified.
