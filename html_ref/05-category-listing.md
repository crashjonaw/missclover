# Category listing pages

Used by every storefront category: `/new.html`, `/handbags.html`, `/wallets.html`, `/clothing.html`, `/shoes.html`, `/jewelry.html`, `/accessories.html`, `/sales.html`, plus subcategories like `/handbags/totes.html`. The same template renders the search-results page (see [07-search-results.md](07-search-results.md)).

## Body classes (handbags.html as canonical example)

```
page-with-filter
page-products
categorypath-handbags
category-handbags
catalog-category-view
page-layout-2columns-left
page-layout-category-full-width
```

## Layout

Two-column layout: left = filter sidebar, right = product grid. Inside `<main id="maincontent">`:

```
<div class="page-title-wrapper">
  <h1 class="page-title" id="page-title-heading"
      aria-labelledby="page-title-heading toolbar-amount">
    <span class="base">Handbags</span>
  </h1>
</div>

<div class="breadcrumbs">
  <ul class="items">
    <li class="item home"><a href="/">Home</a></li>
    <li class="item category">Handbags</li>
  </ul>
</div>

<div class="columns">
  <div class="sidebar sidebar-main">          ← left
    <div class="left_category"> … category tree (custom) … </div>
    <div class="filter">                       ← Amasty Shop By
      <div class="filter-options"> … filter blocks … </div>
    </div>
  </div>

  <div class="column main">                    ← right
    <div class="toolbar toolbar-products"> … sort/limit, view-mode, count … </div>
    <div class="products wrapper grid products-grid">
      <ol class="products list items product-items">
        <li class="item product product-item"> … card … </li>
        …
      </ol>
    </div>
    <div class="toolbar toolbar-products"> … bottom toolbar with pagination … </div>
    <div id="amshopby-filters-bottom-cms"> … SEO copy / linked sub-categories … </div>
  </div>
</div>
```

## Toolbar

```html
<div class="toolbar toolbar-products" data-mage-init='{"productListToolbarForm": {"…"}}'>
  <p class="toolbar-amount" id="toolbar-amount"><span>218 RESULTS</span></p>
  <div class="toolbar-sorter sorter">
    <label class="sorter-label">Sort By</label>
    <select id="sorter">
      <option value="position">Position</option>
      <option value="price_asc">Price - Low To High</option>
      <option value="price_desc">Price - High To Low</option>
      <option value="just_added">Just Added</option>
    </select>
    <a class="action sorter-action sort-desc" title="Set Descending Direction">…</a>
  </div>
  <div class="limiter">
    <select id="limiter">
      <option value="12">12</option>
      <option value="24">24</option>
      <option value="36">36</option>
    </select>
    <span class="limiter-text">per page</span>
  </div>
</div>
```

The toolbar's pagination block (bottom toolbar) yields URLs of the form `?p=2`, `?p=3`, …. These are blocked by `robots.txt` (the global `Disallow: /*?` rule).

## Amasty filter sidebar

Filters are independent forms (one `<form>` per filter), each with `data-amshopby-filter` and `data-amshopby-filter-request-var` attributes that match the URL parameter Magento accepts.

| Filter title | `data-amshopby-filter` | Request var | Form id |
|---|---|---|---|
| Color | `colorgroup` | `colorgroup` | (no `id`) |
| Item Type | `item_type` | `item_type` | `am-ranges-item_type` |
| Price | `price` | `price` | `am-ranges-price` |
| Material | `material` | `material` | `am-ranges-material` |
| Handbag Size | `handbag_size` | `handbag_size` | `am-ranges-handbag_size` |
| Collection | `collections` | `collections` | `am-ranges-collections` |

Other category templates may show fewer filters (e.g. `clothing.html` removes "Handbag Size"; `jewelry.html` removes both size filters). The price filter is rendered as a slider via `data-amshopby-js="price-ranges"`.

Each filter's form looks like:

```html
<form class="am-ranges" id="am-ranges-item_type"
      data-am-js="ranges"
      data-amshopby-filter="item_type"
      data-amshopby-filter-request-var="item_type"
      autocomplete="off">
  <ol class="items am-filter-items-attr_item_type" data-amshopby-list="ranges">
    <li class="item"> <a href="?item_type=…"> … <span class="count">23</span> </a> </li>
    …
  </ol>
</form>
```

Color is rendered as **swatches** (CSS-coloured circles) via `data-am-color` hex attributes.

## Product card anatomy (`<li class="product-item">`)

```html
<li class="item product product-item">
  <div class="product-item-info" id="product-item-info_29987" data-product-id="29987">

    <a class="product photo product-item-photo" href="/new/loop-suede-small-shoulder-bag-ko780-y24.html">
      <span class="product-image-container product-image-container-29987">
        <span class="product-image-wrapper">
          <img class="product-image-photo"
               src="https://singapore.katespade.com/media/catalog/product/f/7/…jpg"
               alt="Loop Suede Small Shoulder Bag"
               loading="lazy"/>
          <img class="product-image-photo hover_image"
               src="…second image…" loading="lazy"/>
        </span>
      </span>
      <div class="product-label-container"> … sale/new/exclusive badges … </div>
    </a>

    <div class="product details product-item-details">
      <strong class="product name product-item-name">
        <a class="product-item-link" href="…">Loop Suede Small Shoulder Bag</a>
      </strong>

      <div class="price-box price-final_price">
        <span class="normal-price">
          <span class="price-container price-final_price tax weee">
            <span class="price-wrapper" data-price-amount="350">
              <span class="price">S$350.00</span>
            </span>
          </span>
        </span>
        <!-- when on sale, also includes <span class="old-price"> … </span> -->
      </div>

      <div class="swatch-opt-29987"> … color swatches via data-option-id … </div>
    </div>

  </div>
</li>
```

Each `<li>` carries the Magento product entity ID twice (`data-product-id`, `id="product-item-info_<id>"`). The swatch container id matches the product id and is wired by `Magento_Swatches/js/swatch-renderer`. There is no Add-to-Cart or Wishlist button on the card itself — those actions live on the product detail page.

## Bottom CMS block (SEO)

Below the bottom toolbar, every category page renders an Amasty CMS block:

```html
<div id="amshopby-filters-bottom-cms"> … category description / inter-link copy … </div>
```

This is editable in the Magento admin and is used for SEO copy — for example, a category-introduction paragraph and inter-linked sub-category lists.
