# singapore.katespade.com — HTML Reference

A structured reference of the public HTML and front-end components served by **https://singapore.katespade.com**, the Kate Spade Singapore storefront.

## What this is

Captured by crawling the live site (homepage, category, product, search, store-locator, CMS) and parsing each response. The site is a **Magento 2** Open Source storefront built with the **Wow / katespade theme**, the **Magezon** page-builder ecosystem, and the **Amasty** shop-by-filter / Xsearch suite.

## Files in this folder

| File | What's in it |
|---|---|
| [00-overview.md](00-overview.md) | Stack, page templates, body-class taxonomy, request map |
| [01-head-meta.md](01-head-meta.md) | `<head>`: title, meta, viewport, favicons, SEO/social verification |
| [02-header-and-navigation.md](02-header-and-navigation.md) | Header shell, logo, mega-nav (NinjaMenus), Amasty Xsearch bar, mini-cart |
| [03-footer-and-newsletter.md](03-footer-and-newsletter.md) | Footer columns, links, social, newsletter form fields |
| [04-homepage.md](04-homepage.md) | `cms-home` rows, hero, featured products, lookbook iframe |
| [05-category-listing.md](05-category-listing.md) | `catalog-category-view` layout, Amasty filters, toolbar, product card anatomy |
| [06-product-detail.md](06-product-detail.md) | `catalog-product-view` layout, gallery (Fotorama), swatches, add-to-cart, related |
| [07-search-results.md](07-search-results.md) | `catalogsearch-result-index` layout (Amasty Xsearch) |
| [08-cms-pages.md](08-cms-pages.md) | `cms-page-view` (About) and the custom `storelocator` page |
| [09-assets-css-js.md](09-assets-css-js.md) | All CSS/JS bundles by module, third-party scripts and pixels |
| [10-sitemap-links.md](10-sitemap-links.md) | Map of all internal URLs surfaced from the global header & footer |
| [reference.md](reference.md) | Original reference URL pointer |

## Sources

- **Live crawl** — 11 pages fetched from the public site:
  `/`, `/handbags.html`, `/wallets.html`, `/clothing.html`, `/shoes.html`, `/jewelry.html`, `/sales.html`, `/new/loop-small-shoulder-bag-ko768-x3x.html`, `/catalogsearch/result/?q=tote`, `/storeinfo/storelocator/storelocator`, `/about-us`.
- **Local file** — `kate spade new york® … New ….html` (the saved `/new.html` listing page).
- Robots: `/checkout/`, `/customer/`, `/catalog/` (admin paths) and any `?` query URLs are disallowed for crawlers and were **not** scanned.

## Conventions used in this reference

- **Selectors** are shown verbatim from the rendered HTML. CSS classes prefixed `mgz-` come from Magezon page builder; `am-` / `amshopby-` / `amsearch-` come from Amasty extensions; `hfb-` is Magezon Header/Footer Builder.
- **Magento body classes** (e.g. `cms-home`, `catalog-category-view`, `page-layout-2columns-left`) are the canonical handles used in layout XML; they are reproduced here as routing keys.
