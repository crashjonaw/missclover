# Assets — CSS, JS, third-party

Audit covers 11 representative pages (homepage, 6 categories, product detail, search, store-locator, About).

## Theme asset versioning

Every static asset is served from:

```
/static/version1773900781/frontend/Wow/katespade/en_US/<Module>/<path>
```

Where `version1773900781` is the Magento static-content cache buster (theme deploy timestamp). All pages share **the same asset hashes** — there is no per-page bundling.

## Stylesheets (29 unique paths bundled on every page)

Grouped by module (counts = number of distinct CSS files contributed by the module):

| Module | Files | Purpose |
|---|---|---|
| `Magezon_Core` | 7 | Page builder core: bootstrap grid, fonts, animate, owl carousel, magnific lightbox |
| `Magezon_PageBuilder` | 4 | PageBuilder element styles + photoswipe vendor + blueimp gallery |
| `Magezon_Builder` | 3 | Magezon Builder element styles + open-iconic |
| `Magezon_Newsletter` | 2 | Newsletter form + intl-tel-input |
| `Magezon_NinjaMenus` | 1 | Mega-menu styles |
| `Magezon_HeaderFooterBuilder` | 1 | HFB layout (`.hfb-*`) |
| `Magezon_PageBuilderIconBox` | 1 | Icon-box element |
| `Magezon_ScrollToTop` | 1 | Scroll-to-top animation |
| `Amasty_Base` | 1 | Slick carousel |
| `Amasty_ShopbyBase` | 2 | Swiper + Chosen |
| `Amasty_ShopbyBrand` | 1 | Brand listing |
| `Amasty_Xsearch` | 1 | Search overlay/results |
| `Amasty_BannersLite` | 1 | Promo banner element (loaded once via inline `<style>`) |
| `Wow_Catalog` | 1 | Theme: font-awesome 4.5.0 |
| `Wow_ProductLabel` | 2 | Custom product badge styles |
| `Wow_ROPIS` | 1 | Reserve Online / Pickup In Store widget |
| `mage` | 2 | calendar, validation |
| `css` (theme root) | 3 | `styles-m.css` (mobile-base), `styles-l.css` (≥768px), `print.css` |

The site does not appear to bundle CSS into a single `merged.css` — the 29 link tags mean Magento's "merge CSS files" production option is **off**.

## Scripts

External (third-party) scripts loaded as `<script src=…>`:

| Source | Pages | Purpose |
|---|---|---|
| `https://js.adsrvr.org/up_loader.1.1.0.js` | 11/11 | The Trade Desk Universal Pixel (UID2 / programmatic ads) |
| `https://www.google.com/recaptcha/api.js` | 1/11 | Google reCAPTCHA (loaded only on the page that needs it — likely newsletter / contact) |
| `https://static.addtoany.com/menu/page.js` | 1/11 | AddToAny social-share kit (product detail) |
| `https://maps.googleapis.com/maps/api/js` | 1/11 | Google Maps (store locator only) |

All Magento JavaScript is loaded via **RequireJS** (`requirejs/require.js`) and Magento's `mage-init` / `text/x-magento-init` declarative initialisation (every page emits both). Notable bundles referenced via `mage-init`:

- `Magento_Ui/js/core/app` (bootstrapping Knockout components)
- `Magento_Catalog/js/product/list/toolbar`
- `Magento_Swatches/js/swatch-renderer` (configurable product swatches)
- `Magento_ProductVideo/js/fotorama-add-video`
- `Amasty_Xsearch/js/wrapper` (search box / autocomplete)
- `Amasty_ShopbyBase/js/...` (filter sliders, slick range)
- `Magezon_Newsletter/js/form` (newsletter validation + AJAX)
- `Magezon_Core/js/jquery-scrolltofixed-min` (sticky header)

## Inline / pixel-style trackers (present on every page)

| Tracker | Identifier | Notes |
|---|---|---|
| **Google Tag Manager** | `GTM-NT3THGF` | Inline bootstrap + `<noscript>` iframe |
| **Facebook Pixel** | `fbq('init', …)` | Multiple `fbq('track', …)` calls per page |
| **TikTok Pixel** | `ttq.load(…)` / `ttq.track(…)` | |
| **Pinterest tag** | meta `p:domain_verify` (×2) | Plus a `pinit.js` reference deep in inline code |
| **New Relic Browser RUM** | `NREUM` (`accountID 3361666`, `applicationID 1110657878`) | Always loaded as the very first thing in `<head>` |
| **The Trade Desk** | `js.adsrvr.org` | External script (above) + inline trigger |
| **FlippingBook** | iframe to `online.flippingbook.com/view/613305494/` | Used for the seasonal lookbook on the homepage |

There is no Google Analytics 4 `gtag()` reference in the HTML — analytics is presumably injected through GTM rather than hardcoded.

## Images / media

- Product imagery: `https://singapore.katespade.com/media/catalog/product/<x>/<y>/<hash>.jpg` — sized-on-demand via Magento's image cache (e.g. `/cache/<hash>/<…>`) when needed.
- CMS / WYSIWYG imagery: `https://singapore.katespade.com/media/wysiwyg/<YYYYMM>/<filename>.png` (e.g. `/media/wysiwyg/202604/...` for April-2026 banners).
- Logos / favicons: `https://singapore.katespade.com/media/logo/stores/1/` and `…/favicon/stores/1/`.
- The only off-domain image host observed: `www.facebook.com/tr` (Pixel beacon, not a real image).
