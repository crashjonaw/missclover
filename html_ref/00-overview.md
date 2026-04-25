# Overview

## Tech stack

| Layer | Identification | Evidence |
|---|---|---|
| Platform | **Magento 2** (Open Source / Adobe Commerce) | `/static/version{number}/frontend/...` asset URLs, `Magento_Ui/js/core/app`, `mage-init` data attributes, `requirejs` loader, `Knockout` bindings (`data-bind=...`) |
| Theme | **`Wow/katespade`** (en_US) | every static URL: `/static/version1773900781/frontend/Wow/katespade/en_US/...` |
| Page builder | **Magezon** (PageBuilder, Builder, NinjaMenus, HeaderFooterBuilder, Newsletter, ScrollToTop, IconBox) | hundreds of `class="… mgz-element …"` nodes; `hfb-header`, `hfb-footer` shells |
| Filters / search | **Amasty** ShopBy Base, ShopBy Brand, Xsearch, Banners Lite | `am-shopby-form`, `data-amshopby-filter`, `amsearch-wrapper-block` |
| Custom modules | **Wow_ProductLabel**, **Wow_ROPIS** (reserve online, pickup in store) | `Wow_ProductLabel/css/label_list.css`, `Wow_ROPIS/...` script |
| Tag manager | **Google Tag Manager** `GTM-NT3THGF` | inline + `<noscript>` iframe to `googletagmanager.com/ns.html?id=GTM-NT3THGF` |
| Pixels | Facebook Pixel (`fbq`), TikTok Pixel (`ttq`), Pinterest tag | inline scripts on every page |
| RUM | **New Relic Browser** (account 3361666, app 1110657878) | inline `NREUM` loader |
| Ad / DSP | **The Trade Desk** (`js.adsrvr.org`) | external `<script src>` |
| Lookbook | **FlippingBook** | `<iframe src="https://online.flippingbook.com/view/613305494/">` on homepage |
| Maps | Google Maps JS | `maps.googleapis.com` script (store locator) |

## Page templates discovered

Magento exposes the page template via the `<body>` `class` attribute. Pages crawled and the body classes they emit:

| URL | Body classes (key handles) | Layout |
|---|---|---|
| `/` | `cms-home cms-index-index` | `page-layout-1column` |
| `/handbags.html` (and other category roots) | `page-products page-with-filter categorypath-handbags category-handbags catalog-category-view` | `page-layout-2columns-left page-layout-category-full-width` |
| `/wallets.html`, `/clothing.html`, `/shoes.html`, `/jewelry.html`, `/sales.html`, saved `/new.html` | same as above with the matching `categorypath-*` / `category-*` handle | same |
| `/new/loop-small-shoulder-bag-ko768-x3x.html` | `page-product-configurable catalog-product-view product-loop-small-shoulder-bag-ko768-x3x` | `page-layout-1column` |
| `/catalogsearch/result/?q=tote` | `page-products page-with-filter amsearch-search-page catalogsearch-result-index` | `page-layout-2columns-left` |
| `/storeinfo/storelocator/storelocator` | `storeinfo-storelocator-storelocator` (custom module) | `page-layout-1column` |
| `/about-us` | `cms-about-us cms-page-view` | `page-layout-1column page-layout-cms-full-width` |

`page-with-filter` and `page-products` are the standard Magento handles that pull in the Amasty filter sidebar and the products grid renderer; they are present on every category page **and** on the search results page.

## DOM topology common to all pages

```
<html>
  <head> … (see 01-head-meta.md)
  <body data-container="body" id="html-body" class="…page-handle…">
    <div class="page-wrapper">
      <header class="magezon-builder hfb hfb-header hfb-header4"> … </header>
      <main id="maincontent" class="page-main">
        <a id="contentarea"></a>
        <div class="page-title-wrapper"><h1 class="page-title">…</h1></div>   <!-- on category/product pages -->
        <div class="columns">
          <div class="column main"> … page-specific content … </div>
          <div class="sidebar sidebar-main"> … filter blocks … </div>          <!-- only when page-with-filter -->
          <div class="sidebar sidebar-additional"> … </div>
        </div>
      </main>
      <div class="hfb hfb-footer hfb-footer4"> … (see 03-footer-and-newsletter.md) </div>
    </div>
    <script>(window.NREUM…)</script>
    <noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-NT3THGF"/></noscript>
  </body>
</html>
```

The site does **not** use `<header>` / `<footer>` semantic tags around the footer — Magezon emits the footer as a `<div class="hfb hfb-footer hfb-footer4">`. The header **does** use `<header>`.

## Robots and what was not crawled

`https://singapore.katespade.com/robots.txt`:

```
User-agent: *
Disallow: /index.php/
Disallow: /*?
Disallow: /checkout/
Disallow: /app/
Disallow: /lib/
Disallow: /*.php$
Disallow: /pkginfo/
Disallow: /report/
Disallow: /var/
Disallow: /catalog/
Disallow: /customer/
Disallow: /sendfriend/
Disallow: /review/
Disallow: /*SID=
```

So account/login (`/customer/account/login`), cart and checkout (`/checkout/cart`), product reviews submission, and any URL with a query string (`/*?`) are off-limits to crawlers. Search-results URLs work because Magento's `catalogsearch/result/` is on the path — but they are still gated by the `*?` query disallow rule, so they should not be indexed. Categories serve clean URLs.
