# Homepage (`/`)

- **URL**: `https://singapore.katespade.com/`
- **Body classes**: `cms-home cms-index-index page-layout-1column`
- **Layout**: single-column (no filter sidebar). All content lives in `<div class="column main">` inside `<main id="maincontent">`.
- **Source**: a Magento CMS page rendered by Magezon page builder. There are *no* `mgz-element-row` blocks between `<header>` and `<footer>` because the homepage CMS content is composed of plain HTML/IMG/A blocks (not the page-builder grid). The header/footer are still page-builder blocks.

## Structural layout

```html
<header class="hfb hfb-header hfb-header4"> … </header>

<script>
  // Inline header behaviors:
  //  - clones .hfb-header .header.links into the .store.links zone
  //  - tags the search form with `mgz-element-search_form-wrapper`
  //  - applies Magezon_Core/jquery-scrolltofixed-min to make .hfb-header sticky (minTop: 5),
  //    and detaches it under 768px width
</script>

<main id="maincontent" class="page-main">
  <a id="contentarea" tabindex="-1"></a>
  <div class="page messages">
    <div data-placeholder="messages"></div>
    <div data-bind="scope: 'messages'"> … KO templates for cookie/session messages … </div>
  </div>

  <div class="columns">
    <div class="column main">
      <input name="form_key" type="hidden" value="…"/>
      <div id="authenticationPopup" data-bind="scope: 'authenticationPopup'"> … </div>

      <!-- CMS hero / promo blocks: a stack of <div> sections containing
           <a><picture><img></picture></a> banners and section headings.
           No mgz-element-row wrappers — the CMS page uses
           direct HTML inserted via Magento WYSIWYG / Magezon rendered HTML. -->
    </div>
  </div>
</main>

<div class="hfb hfb-footer hfb-footer4"> … </div>
```

## Promotional sections (in order)

The homepage stack consists of full-bleed banners and category tiles:

1. **Sale strip** — banner image linking to `/sale.html`.
2. **Mini Duo feature** — banner + CTA *"SHOP THE MINI DUO"* → `/duo-suede-mini-shoulder-bag-ko776.html`.
3. **New arrivals strip** — *"SHOP NEW ARRIVALS"* → `/new/handbags.html`.
4. **Trending product carousel** (`<h3>` per product card):
   - Duo Suede Mini Shoulder Bag → `/duo-suede-mini-shoulder-bag-ko776.html`
   - Dog Dangle Bag Charm → `/accessories/charms-shop/dog-dangle-bag-charm-km777.html`
   - Loop Suede Small Shoulder Bag → `/handbags/collections/loop/loop-suede-small-shoulder-bag-ko777.html`
   - Charmed Magazine Bag Charm → `/accessories/charms-shop/charmed-magazine-bag-charm-ko567.html`
   - Charmed Sunscreen Bag Charm → `/accessories/charms-shop/charmed-sunscreen-bag-charm-kp068.html`
   - Duo Crossbody Bag → `/duo-crossbody-bag-ko692.html`
5. **Sneakers feature** — *"SHOP SNEAKERS"* → `/shoes/sneakers.html`.
6. **Handbags feature** — *"SHOP HANDBAGS"* → `/handbags.htmL` *(note the capitalised `htmL` — this is a typo in the live HTML)*.
7. **Category quad-tile**: SHOP WALLETS, SHOP HANDBAGS, SHOP JEWELRY, SHOP BAG CHARMS — pointing to `/wallets.html`, `/handbags.html`, `/jewelry.html`, `/accessories/charms-shop.html`.
8. **Lookbook** — embedded as an iframe to FlippingBook:
   ```html
   <iframe src="https://online.flippingbook.com/view/613305494/" …></iframe>
   ```

All banner artwork is served from `https://singapore.katespade.com/media/wysiwyg/202604/` (April-2026 campaign folder, e.g. `1504_trend_01.png` … `1504_trend_06.png`, `1304_exc_img01.png`, `1304_exc_img02.png`).

## Headings

The CMS content uses `<h3>` for product card names (one per product in the trending carousel) and the global `<h2>` newsletter heading. The page does not use `<h1>` — the homepage has no page title heading.

## Pre-footer GTM/dataLayer

The homepage emits the standard GTM bootstrap inline:

```html
<script>
  (function(w,d,s,l,i){ … })(window,document,'script','dataLayer','GTM-NT3THGF');
</script>
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-NT3THGF" …></iframe></noscript>
```

…plus inline TikTok (`ttq`), Facebook (`fbq`), Pinterest tag, and a New Relic Browser bootstrap. See [09-assets-css-js.md](09-assets-css-js.md).
