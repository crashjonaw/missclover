# `<head>` & meta

The `<head>` is identical across every page except for `<title>`, `<meta name="title">`, `<meta name="description">`, and the JS-config payload Magento injects late in the head.

## Document opening

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <script>(window.NREUM||(NREUM={})).init=…  // New Relic browser-RUM, accountID 3361666
  </script>
  <meta charset="utf-8"/>
  <meta name="title" content="kate spade new york® Singapore Official Site  I  Handbags, Clothing & Accessories  …"/>
  <meta name="description" content="Discover kate spade new york® Handbags, Clothing, Accessories & More."/>
  <meta name="keywords" content="Discover kate spade new york® Handbags, Clothing, Accessories & More."/>
  <meta name="robots" content="INDEX,FOLLOW"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"/>
  <meta name="format-detection" content="telephone=no"/>

  <!-- Domain ownership / SEO verification -->
  <meta name="p:domain_verify"        content="BeCi1TU9WC4KteI8yFODhWdIPndM3e8s"/>
  <meta name="p:domain_verify"        content="6IRGyqHSjKSkFo6QosyUPlr3sZKtNoxo"/>  <!-- two Pinterest verifications -->
  <meta name="google-site-verification" content="fo_btJ1zCSy4dvp3W2nbfoSldLJF1en8nBGFB84t9I4"/>

  <title>kate spade new york® Singapore Official Site  I  Handbags, Clothing & Accessories</title>
  …
</head>
```

### Notes on the meta block

- `<meta name="viewport">` uses `maximum-scale=1.0, user-scalable=no` — pinch-zoom is disabled (an accessibility regression, but consistent with the brand's mobile UX choice).
- `<meta name="title">` content is double-printed on every page: the global brand string is concatenated with the page title (e.g. `"… Accessories Handbags kate spade new york® Singapore Official Site  I  Handbags, Clothing & Accessories"`). This appears to be a theme bug rather than a deliberate pattern.
- There is **no Open Graph / Twitter Card** meta — pages share without rich previews unless the platform falls back to title/description.
- There are **no `<link rel="preload">` / `rel="preconnect"`** hints, no canonical link, no hreflang. SEO is left to the title and the `robots: INDEX,FOLLOW` directive.

## Stylesheets (link rel="stylesheet")

All bundled CSS is theme-versioned at `/static/version1773900781/frontend/Wow/katespade/en_US/`. Loaded in this order on every page:

```
mage/calendar.css
Wow_Catalog/fonts/font-awesome-4.5.0/css/font-awesome.min.css
css/styles-m.css                          # mobile-first base
Amasty_ShopbyBase/css/swiper.min.css
Amasty_Base/vendor/slick/amslick.min.css
Magezon_Core/css/styles.css
Magezon_Core/css/owlcarousel/owl.carousel.min.css
Magezon_Core/css/animate.css
Magezon_Core/css/fontawesome5.css
Magezon_Core/css/mgz_font.css
Magezon_Core/css/mgz_bootstrap.css
Magezon_Builder/css/openiconic.min.css
Magezon_Builder/css/styles.css
Magezon_Builder/css/common.css
Magezon_Core/css/magnific.css
Magezon_PageBuilder/css/styles.css
Magezon_PageBuilder/vendor/photoswipe/photoswipe.css
Magezon_PageBuilder/vendor/photoswipe/default-skin/default-skin.css
Magezon_PageBuilder/vendor/blueimp/css/blueimp-gallery.min.css
Magezon_Newsletter/css/styles.css
Magezon_Newsletter/css/intlTelInput.min.css
Magezon_NinjaMenus/css/styles.css
Magezon_HeaderFooterBuilder/css/styles.css
Magezon_PageBuilderIconBox/css/styles.css
Magezon_ScrollToTop/css/animate.css
Amasty_ShopbyBase/css/chosen/chosen.css
Amasty_ShopbyBrand/css/source/mkcss/ambrands.css
Amasty_Xsearch/css/source/mkcss/am-xsearch.css
css/styles-l.css                          # screen and (min-width: 768px)
css/print.css                             # media="print"
Wow_ProductLabel/css/label_list.css
```

## Favicons

```html
<link rel="icon"          type="image/x-icon" href="https://singapore.katespade.com/media/favicon/stores/1/150by150.png"/>
<link rel="shortcut icon" type="image/x-icon" href="https://singapore.katespade.com/media/favicon/stores/1/150by150.png"/>
```

There are no apple-touch / Android / Windows tiles.
