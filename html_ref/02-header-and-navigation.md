# Header & global navigation

The header is rendered by **Magezon Header/Footer Builder** (HFB). On every page it is the first child of `.page-wrapper`:

```html
<header class="magezon-builder magezon-builder-preload hfb hfb-header hfb-header4">
```

## Three-row layout

The header is composed of three Magezon rows stacked top-to-bottom:

| Row | `mgz-element-row` token | Contents |
|---|---|---|
| 1 | `header-top`   | Promo strip / utility links (e.g. *"Reach out to us on Whatsapp"*) |
| 2 | `logo-row`     | Three columns: left utility links, centered logo, right (intentionally empty placeholder) |
| 3 | `navbar-row` (followed by `row-submenu`) | Search bar + main NinjaMenu navigation, mega-menu submenu rows |
| (4) | `header-bottom` | Hidden by class `display-none` on most templates — reserved for breadcrumbs row |

Each row uses Bootstrap-12 columns through Magezon's `mgz-col-md-*` utility classes.

## Logo

```html
<div class="… mgz-element-site_logo ks-logo hfb-logo-hamburger">
  <a class="logo" href="https://singapore.katespade.com/" title="kate spade new york®">
    <img src="…/media/logo/stores/1/Kate-Spade-Logo.png" alt="kate spade new york®"/>
  </a>
</div>
```

## Top-level navigation

The mega-nav is rendered by **Magezon NinjaMenus**. The `<nav class="navigation">` is a `<div>`-based menu — there are **no `<li>` elements**. Top-level items use `class="… nav-item level0 …"` and the category title sits in `<span class="title">`.

Top-level items (in order of appearance, with their hrefs):

| Title | Href |
|---|---|
| Home | `/` |
| New | `/new.html` |
| Handbags | `/handbags.html` |
| Wallets | `/wallets.html` |
| Clothing | `/clothing.html` |
| Shoes | `/shoes.html` |
| Jewelry | `/jewelry.html` |
| Accessories | `/accessories.html` |
| Sale | `/sales.html` |
| SEARCH | `javascript:void(0);` (opens overlay) |

(There is also a "Reach out to us on Whatsapp" link in the top promo strip, pointing at the store-locator page.)

### Mega-menu submenu

Each top-level category opens a 3- or 4-column flyout (`mgz-element-row row-submenu`). For example, `Handbags > Crossbody Bags / Tote Bags / Shoulder Bags / Satchels & Top Handles / Backpacks & Beltbags`, plus a "Collections" column linking to: `Duo`, `Halo`, `Loop`, `Deco`, `Liv`, `Grace`, `Spade Flower Jacquard`, `Suite`, `Tilly`, `454`. The complete sitemap of nav links is in [10-sitemap-links.md](10-sitemap-links.md).

## Search

The search input is **Amasty Xsearch** (Magento ajax autocomplete), rendered twice on every page (once in the desktop nav row, once in the mobile overlay). Each instance is its own form posting to `/catalogsearch/result/`:

```html
<form class="form minisearch">
  <div class="field search">
    <label class="label" for="search"><span>Search</span></label>
    <div class="control">
      <section class="amsearch-wrapper-block"
               data-amsearch-wrapper="block"
               data-bind="scope: 'amsearch_wrapper_<id>',
                          mageInit: { 'Magento_Ui/js/core/app': { components: { … } } }">
        <input type="text" name="q" placeholder="what are you looking for?"
               aria-label="Search" autocomplete="off"
               data-amsearch-js="input"/>
        <button class="amsearch-button -loupe -clear -icon"  type="submit">…</button>
        <button class="amsearch-button -close -clear -icon"  type="reset">…</button>
        <section class="amsearch-result-section" data-amsearch-js="results" style="display:none;">…</section>
      </section>
    </div>
  </div>
</form>
```

Knockout config (passed via `data-bind`) declares the autocomplete endpoints:

```json
{
  "url":              "https://singapore.katespade.com/amasty_xsearch/autocomplete/index/",
  "url_result":       "https://singapore.katespade.com/catalogsearch/result/",
  "url_popular":      "https://singapore.katespade.com/search/term/popular/",
  "isDynamicWidth":   true,
  "isProductBlockEnabled": true,
  "minChars":         3,
  "delay":            500
}
```

## Mini-cart

The cart icon is a Magento `Magento_Customer/js/section-config` block plus `Magento_Checkout/js/view/minicart`. It does **not** render on the public crawl because the cart UI is hydrated by Knockout from `customerData.get('cart')` after page load. The container is:

```html
<div data-block="minicart" class="minicart-wrapper"> … </div>
```

This was not surfaced in the crawled HTML because the icon row collapses if the JS hasn't run. On the live site the icon is the standard Magento bag icon at the right end of the navbar.

## Mobile

- The header has `hfb-logo-hamburger` next to the logo: a hamburger toggle that swaps the desktop NinjaMenu for an accordion drawer (`<h2 id="mobile_accordion">Shop By Category</h2>` triggers it).
- The `<meta name="viewport">` disables zoom (see [01-head-meta.md](01-head-meta.md)).
- The Amasty search renders a separate full-screen overlay on mobile (`amsearch-overlay-block`).

## Skip-link / accessibility

```html
<a id="contentarea" tabindex="-1" href="#contentarea"></a>
```

A skip-to-content anchor is present at the top of `<main>`, but there is no visible "Skip to content" link in the header (the anchor exists but no preceding `<a class="skip-link">`).
