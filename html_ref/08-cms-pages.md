# CMS & informational pages

## About Us — `/about-us`

- **Body classes**: `cms-about-us cms-page-view page-layout-1column page-layout-cms-full-width`
- A standard Magento CMS page rendered through the `cms-page-view` template. Content lives inside `<div class="column main">` and is editable in the Magento admin.
- The page surface is otherwise identical to the homepage shell: header, `<main id="maincontent">`, breadcrumbs, CMS body, footer.
- `<h1>` is **not** present (the title sits in the breadcrumb / `<title>` only).

## Other CMS pages linked from header & footer

These all use the same `cms-page-view` template (the body class follows the page's URL key, e.g. `cms-who-we-are`, `cms-ks-customer-service-landing`):

| URL | Title (from footer) |
|---|---|
| `/who-we-are` | About Us / who we are |
| `/ks-foundation` | the foundation |
| `/ks-customer-service-landing` | Customer Care landing |
| `/ks-customer-service-landing/item-care-warranty` | warranty |
| `/ks-customer-service-landing/contact-information` | contact us |
| `/ks-customer-service-landing/ks-privacy-policy` | privacy policy |
| `/ks-customer-service-landing/ks-brand-protection` | brand protection |

(External legal pages — investors, tapestry, responsibilities, careers — point to `tapestry.com` rather than the Magento store.)

## Store Locator — `/storeinfo/storelocator/storelocator`

This is **not** a CMS page; it is rendered by a custom Magento module (`StoreInfo_StoreLocator` or similar). Body class: `storeinfo-storelocator-storelocator page-layout-1column`.

### Page structure

```
<h1>Find a Store</h1>
<h2>Nearby Stores — Visit your nearest store or contact a store for free home delivery</h2>

<form>
  <!-- search box (location keyword, country / state filters) -->
</form>

<!-- For each store, repeating block: -->
<div class="store-card">
  <h3>{Store Name}</h3>
  …address / phone / contact CTA…
  <h3>STORE HOURS</h3>
  …weekday/weekend hours…
</div>
```

### Stores listed (Singapore)

The page's static list contains seven Kate Spade stores in Singapore:

1. **VivoCity**
2. **ION Orchard**
3. **Marina Bay Sands**
4. **Takashimaya Department Store**
5. **Jewel Changi Airport**
6. **IMM Outlet Mall**
7. **Changi City Point**

Each store has its own `<h3>STORE HOURS</h3>` heading underneath. There is also an empty-state heading template (`<h3>Sorry, there are no locations near "' + keyword + '" satisfying the selected fil…</h3>`) used as a JavaScript fallback message.

### Maps integration

The store locator loads `https://maps.googleapis.com/maps/api/js` (the only page in the crawl that does so). It uses Google Maps to plot each store as a pin. The page also has its own AddToAny share kit and the standard newsletter footer.

## Other observed routes (not deeply documented)

- **Account** — `/customer/account/login`, `/customer/account/create`, `/customer/account/forgotpassword` — gated by `robots.txt`. The login dialog is also pre-bootstrapped on every page as `<div id="authenticationPopup" data-bind="scope: 'authenticationPopup'">…` so a Knockout pop-up can prompt sign-in inline.
- **Cart / Checkout** — `/checkout/cart/`, `/checkout/` — standard Magento Onepage checkout, gated by `robots.txt`.
- **Wishlist** — Magento standard, accessible to authenticated customers only.
- **Orders / RMAs** — `/sales/order/...` (admin-protected).
