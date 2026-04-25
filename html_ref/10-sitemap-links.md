# Internal sitemap

Every internal `https://singapore.katespade.com/...` link found in the 11 crawled pages, deduped and grouped by path prefix. **157 distinct URLs.**

The header mega-nav and the homepage merchandising tiles are the dominant sources of these links — each category page additionally exposes its own product detail URLs through the visible 12-product grid.

## URL conventions observed

- **Top-level taxonomy** — flat `/<category>.html` with `/<category>/<sub>.html` for sub-categories:
  - `/handbags.html`, `/handbags/totes.html`, `/handbags/collections/duo.html`
  - `/wallets.html`, `/wallets/cardholders.html`
  - `/clothing.html`, `/clothing/dresses-jumpsuits.html`
  - `/shoes.html`, `/shoes/sneakers.html`
  - `/jewelry.html`, `/jewelry/necklaces.html`
  - `/accessories.html`, `/accessories/charms-shop.html`
  - `/sales.html`, `/sales/<sub>.html` and `/sales/<product>.html` (sale items live under `/sales/`)
  - `/new.html`, `/new/<sub>.html` and `/new/<product>.html` (new arrivals)
- **Product detail** — three rewrite patterns coexist:
  1. `/<category>/<product-url-key>.html` — canonical (e.g. `/handbags/loop-shoulder-bag-kp086.html`)
  2. `/<product-url-key>.html` — bare-root form for a few legacy products (`/breezy-mesh-tote-bag-kn933.html`)
  3. `/catalog/product/view/id/<id>/s/<slug>/category/<id>/` — Magento default (a few links not yet rewritten, e.g. `/catalog/product/view/id/29060/s/novelty-button-nell-cardigan-ko019/category/106/`)
- **Custom modules** — `/storeinfo/storelocator/storelocator`, `/catalog/category/view/s/tech-accessories/id/277/`, `/sales/<id>` (legacy SKU-numeric routes such as `/sales/dash-canvas-tote-bag-196021728280.html`).

## By section

### Root
- `/` — Home

### Top-level taxonomy landing pages
- `/new.html` — New
- `/handbags.html` — Handbags
- `/wallets.html` — Wallets
- `/clothing.html` — Clothing
- `/shoes.html` — Shoes
- `/jewelry.html` — Jewelry
- `/accessories.html` — Accessories
- `/sales.html` — Sale

### `/handbags/...` (28 links)
Sub-categories:
- `/handbags/totes.html` — Tote Bags
- `/handbags/crossbodies.html` — Crossbody Bags
- `/handbags/shoulder-bags.html` — Shoulder Bags
- `/handbags/satchels.html` — Satchels & Top Handles
- `/handbags/backpacks-travel-bags.html` — Backpacks & Beltbags
- `/handbags/collections.html` — Collections (hub)

Collections: `/handbags/collections/{454,deco,duo,grace,halo,liv,loop,suite,the-spade-flower-shop,tilly}.html`

Sample products linked from category cards:
- `/handbags/loop-shoulder-bag-kp086.html`
- `/handbags/loop-suede-small-shoulder-bag-ko780.html` (+ `…-y24.html`, `…-z0y.html` colour variants)
- `/handbags/halo-mini-bucket-bag-km495-yrs.html`, `/handbags/halo-woven-mini-bucket-bag-kn925.html`
- `/handbags/duo-suede-crossbody-bag-km223.html`
- `/handbags/deco-suede-small-tulip-tote-bag-kn092.html`, `/handbags/deco-straw-tulip-tote-bag-kn902.html`
- `/handbags/liv-large-shoulder-bag-kl677-yci.html`, `/handbags/liv-hidden-garden-convertible-shoulder-bag-ko374.html`
- `/handbags/do-it-all-crinkle-patent-tote-bag-ko357.html`

### `/wallets/...` (16 links)
- Sub-categories: `/wallets/wallets.html`, `/wallets/cardholders.html`, `/wallets/wristlets-pouches.html`, `/wallets/crossbody-wallets.html`
- Sample products: `/wallets/devin-banana-bifold-wallet-ko774.html`, `/wallets/devin-vibrant-buds-zip-around-continental-wallet-ko591.html`, `/wallets/wink-banana-wristlet-ko793.html`, `/wallets/wink-strawberry-wristlet-kp109.html`

### `/clothing/...` (14 links)
- Sub-categories: `/clothing/dresses-jumpsuits.html`, `/clothing/tops.html`, `/clothing/skirts-pants.html` (Bottoms), `/clothing/jackets-coats.html`
- Sample products: `/clothing/breezy-voile-maxi-dress-ko008.html`, `/clothing/bubble-mini-dress-ko609.html`, `/clothing/scallop-shift-dress-ko612.html`, `/clothing/vibrant-buds-midi-slip-dress-ko607.html`, `/clothing/cropped-polo-sweater-kn477.html`

### `/shoes/...` (16 links)
- Sub-categories: `/shoes/flats.html`, `/shoes/heels.html`, `/shoes/sandals.html`, `/shoes/sneakers.html`
- Sample products: `/shoes/k-as-in-kate-runner-ko086.html`, `/shoes/ks-drift-sneaker-ko705.html` (×3 colour variants), `/shoes/halo-platform-clog-mule-ko073.html`, `/shoes/breezy-slide-sandal-ko217.html`, `/shoes/lily-thong-sandal-ko719.html`

### `/jewelry/...` (16 links)
- Sub-categories: `/jewelry/necklaces.html`, `/jewelry/earrings.html`, `/jewelry/rings.html`, `/jewelry/bracelets.html`
- Sample products: `/jewelry/spade-flower-pave-mini-pendant-kn451.html`, `/jewelry/secret-garden-charm-bracelet-ko259.html`, `/jewelry/summer-daze-flower-statement-earrings-ko885.html`, `/jewelry/one-in-a-million-strawberry-charm-ko306.html`

### `/accessories/...` (3 links)
- `/accessories/charms-shop.html`
- `/accessories/hats-scarves.html`
- `/catalog/category/view/s/tech-accessories/id/277/` — Tech Accessories (legacy non-rewritten URL)

### `/new/...` (mega-nav columns)
Sub-categories: `/new/handbags.html`, `/new/wallets.html`, `/new/clothing.html`, `/new/footwear.html` (Shoes), `/new/jewelry.html`, `/new/accessories.html`

Collections: `/new/handbags/{deco,duo,halo,liv,loop}.html` (note: `/new/handbags/liv.html` is currently mislabelled as "Deco" in the live HTML — likely a CMS authoring mistake).

Sample products: `/new/loop-small-shoulder-bag-ko768-x3x.html`, `/new/loop-shoulder-bag-kp086.html`, `/new/dot-trim-shell-top-kl713.html`, `/new/duo-banana-crossbody-bag-kp088.html`, `/new/suite-crossbody-tote-bag-kl642.html`, `/new/deco-glazed-soft-mini-shoulder-kn379.html`.

### `/sales/...` (18 links)
Sub-categories: `/sales/handbags.html`, `/sales/wallets.html`, `/sales/clothing.html`, `/sales/shoes.html`, `/sales/jewelry.html`, `/sales/accessories.html`.

Sample products (note the trailing UPC/EAN that some sale items still include): `/sales/dash-canvas-tote-bag-196021728280.html`, `/sales/deco-snake-embossed-mini-crossbody-bag-196021733857.html`, `/sales/loop-crossbody-bag.html`, `/sales/do-it-all-woven-tote-bag.html`.

### Customer service / brand
- `/who-we-are` — About / who we are
- `/ks-foundation` — the foundation
- `/ks-customer-service-landing` — Customer Care hub
  - `/ks-customer-service-landing/contact-information`
  - `/ks-customer-service-landing/item-care-warranty`
  - `/ks-customer-service-landing/ks-privacy-policy`
  - `/ks-customer-service-landing/ks-brand-protection`

### Operations
- `/storeinfo/storelocator/storelocator` — Find a Store / WhatsApp routing

### Catalog (legacy / non-rewritten URLs surfaced)
- `/catalog/category/view/s/tech-accessories/id/277/`
- `/catalog/product/view/id/29060/s/novelty-button-nell-cardigan-ko019/category/106/`
- `/catalog/product/view/id/29090/s/cross-back-peplum-top-kn989/category/106/`

These are blocked by `robots.txt` (`Disallow: /catalog/`) but still link-reachable from CMS content.

### External links from header/footer
- `https://www.tapestry.com/` (parent company), `/investors/`, `/responsibility/`
- `https://careers.tapestry.com`
- `https://www.instagram.com/katespade_singapore/`
- `https://www.tiktok.com/@katespadeasia`
- `https://linktr.ee/katespadesgstores` (chat / WhatsApp router)
- `https://online.flippingbook.com/view/613305494/` (lookbook iframe — homepage only)
