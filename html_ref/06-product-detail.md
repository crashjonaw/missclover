# Product detail page

URL pattern: `https://singapore.katespade.com/<category-path>/<product-url-key>.html`
Sample inspected: `/new/loop-small-shoulder-bag-ko768-x3x.html` (configurable product, ID 29990, SKU `KO768_X3X`).

## Body classes

```
page-product-configurable
catalog-product-view
product-loop-small-shoulder-bag-ko768-x3x   ← per-product handle
categorypath-new category-new                ← inherits parent category context
page-layout-1column
```

`page-layout-1column` means the sidebar is removed; gallery and product info sit side by side on desktop, stacked on mobile.

## Layout

```html
<main id="maincontent" class="page-main">
  <div class="page-title-wrapper page-title-wrapper-product"> </div>   <!-- empty: title moved into product-info-main -->
  <div class="breadcrumbs"> Home / New / Loop Small Shoulder Bag </div>

  <div class="columns">
    <div class="column main">

      <div class="product-info-main">
        <h1 class="custom-productname product-name">Loop Small Shoulder Bag</h1>
        <div class="product-label-container">…</div>

        <div class="product-info-price">
          <div class="product-info-stock-sku">
            <div class="availability only configurable-variation-qty"> Only %1 left </div>
          </div>
          <div class="price-box price-final_price"
               data-role="priceBox"
               data-product-id="29990">
            <span class="price-container price-final_price tax weee"
                  itemprop="offers" itemscope itemtype="http://schema.org/Offer">
              <span id="product-price-29990"
                    data-price-amount="350" data-price-type="finalPrice">
                <span class="price">$350.00</span>
              </span>
              <meta itemprop="price"        content="350"/>
              <meta itemprop="priceCurrency" content="SGD"/>
            </span>
          </div>
        </div>

        <div class="product-add-form">
          <form id="product_addtocart_form"
                method="post"
                action="https://singapore.katespade.com/checkout/cart/add/uenc/<base64-back-url>/product/29990/"
                data-product-sku="KO768_X3X">
            <input type="hidden" name="product"  value="29990"/>
            <input type="hidden" name="selected_configurable_option"/>
            <input type="hidden" name="related_product" id="related-products-field"/>
            <input type="hidden" name="item"     value="29990"/>
            <input type="hidden" name="form_key" value="…"/>

            <div class="swatch-opt"> … color/size swatches (Magento_Swatches) … </div>

            <div class="box-tocart">
              <div class="field qty"><input id="qty" name="qty" type="number" value="1"/></div>
              <button id="product-addtocart-button" type="submit" class="action primary tocart"> Add to Cart </button>
            </div>
          </form>
        </div>

        <a class="social-share-toggle">…</a>
        <div class="a2a_kit a2a_kit_size_32 a2a_default_style">…</div>   <!-- AddToAny share kit -->
        <div class="product-social-links"> … wishlist + share … </div>
      </div>

      <div class="product media">
        <!-- Magento Fotorama gallery; init payload uses mage/gallery/gallery -->
      </div>

      <h3>if you like this, you'll love</h3>
      <ol class="products list items product-items related-products"> … </ol>

      <h2>Need Help On Your Purchase?</h2>
      <!-- Static contact panel -->

    </div>
  </div>
</main>
```

## Gallery

Powered by **Fotorama** through Magento's `mage/gallery/gallery` widget. Configuration block excerpt:

```json
{
  "mage/gallery/gallery": {
    "options": { "nav": "thumbs", "navdir": "vertical", "transition": "dissolve" },
    "fullscreen": { "nav": "thumbs", "loop": true, "navdir": "horizontal" },
    "breakpoints": { "mobile": { "conditions": { "max-width": "767px" },
                                  "options": { "options": { "nav": "dots" } } } }
  }
}
```

Image media is at `https://singapore.katespade.com/media/catalog/product/<x>/<y>/<hash>.jpg` and is served in three Magento "image types" (`image`, `small_image`, `thumbnail`) configured in the theme's `view.xml`.

## Configurable options (swatches)

The product is **configurable**: the Add-to-Cart form contains `<input name="selected_configurable_option">`, and the `<div class="swatch-opt">` is populated client-side by `Magento_Swatches/js/swatch-renderer` from the JSON config script tag emitted alongside it. The swatches typically render Color and (for clothing/shoes) Size attributes.

## Schema.org markup

- `itemscope itemtype="http://schema.org/Offer"` on the price wrapper, with `<meta itemprop="price">` and `<meta itemprop="priceCurrency">`.
- The page does **not** include a JSON-LD product graph (`<script type="application/ld+json">` is absent).
- There is no `itemprop="aggregateRating"` — product reviews are not surfaced on the listing.

## Cross-sells / related

- "**if you like this, you'll love**" — Magento `related-products` block (`<ol class="products list items product-items related-products">`). Renders the same `product-item` markup as category pages.
- No upsell or "you may also like" carousel beyond this one block.
- A static **"Need Help On Your Purchase?"** panel sits below related products, linking to customer service / store locator.
