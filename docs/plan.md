# MISS CLOVER — Brand E-commerce Site

## Context

MISS CLOVER is a new Singapore handbag brand launching with two designs (**Classic** in cream and **Maroon** in burgundy). The brand owner has on disk:

- `MISS CLOVER LOGO.png` — wordmark with a four-leaf clover mark, black-on-white, 1748×1240 px.
- `bag_image_ref/classic.jpg` and `bag_image_ref/maroon.jpg` — technical spec sheets (front view + interior + side detail) showing dimensions 8″H × 11″L, double handles, gold hardware, suede lining, lipstick + key holders.
- Two reference Flask + Jinja2 projects to lift UX patterns from:
  - `ref/bloomburrow/` — boutique booking site with a polished 3-step checkout (auth-card, order-summary sidebar, file-upload, progress-steps), but **no guest checkout**.
  - `ref/quantiesunite/` — Singapore education platform that uses **HitPay** as a local payment gateway accepting cards / PayNow / GrabPay; clean login template (email-or-username) and a payment-success page.
- `html_ref/` — a 10-document teardown of `singapore.katespade.com` covering its Magento 2 / Magezon / Amasty page templates, header/footer/nav structure, asset bundles, and a 157-URL sitemap. The brand owner wants the site to *feel* like Kate Spade Singapore.

The asks the user has made explicit:
1. **Aesthetic of Kate Spade Singapore** — three-row header, mega-nav, large editorial banners, serif + sans pair, generous whitespace, neutral palette. We can't ship Magento; we replicate the structure in Flask/Jinja2.
2. **Borrow purchase + login UX from the two reference projects.** Adopt Bloomburrow's `.auth-card`, `.progress-steps`, and `.order-summary`; adopt QuantiesUnite's HitPay integration.
3. **"Continue as Guest" option at checkout** — neither reference has this; we add it.
4. **Singapore-first commerce** — SGD pricing, +65 phone, Singapore postal addresses, HitPay (PayNow / cards / GrabPay).
5. Plus the user-confirmed shape: **Flask + Jinja2**, **full e-commerce with real HitPay payments**, **placeholder zones for future photography** (the spec sheets become PDP imagery only).

This plan turns the empty `/Users/crashjonaw/Desktop/missclover/` working directory into a runnable Flask storefront the user can demo end-to-end with HitPay sandbox before commissioning real photography.

---

## Architecture overview

Flask 3 + Jinja2 monolith, SQLAlchemy + SQLite (Postgres-ready), Flask-Login, Flask-Mail, Flask-Migrate (Alembic). Server-rendered pages with sprinkles of vanilla JS for the cart, swatches, and quantity controls. Same pattern as both reference projects so familiarity carries over.

```
missclover/
├── app.py                       Flask factory + blueprint registration
├── extensions.py                db, login_manager, mail, migrate (singletons)
├── config.py                    env-driven config (dev/prod), HitPay keys, mail
├── models.py                    SQLAlchemy models (see Schema below)
├── seed.py                      seeds Classic + Maroon products + variants
├── hitpay.py                    HitPay client: create_payment_request, verify_webhook
├── email_service.py             Flask-Mail templates (lifted from ref/bloomburrow)
│
├── blueprints/
│   ├── shop.py                  /, /handbags, /handbags/<slug>, /collections/<key>, /about
│   ├── auth.py                  /login, /register, /logout, /forgot, /reset/<token>
│   ├── cart.py                  /cart, /cart/add, /cart/update, /cart/remove
│   ├── checkout.py              /checkout/start, /shipping, /payment, /return, /success
│   ├── account.py               /account, /account/orders/, /orders/<id>, /profile
│   └── orders_guest.py          /order/lookup  (guest tracker by email + order #)
│
├── templates/
│   ├── base.html                <head>, header partial, flash, footer partial, GTM stub
│   ├── partials/
│   │   ├── header.html          three rows: promo strip / centered-logo / nav (KS pattern)
│   │   ├── footer.html          two columns + newsletter (KS pattern, simplified)
│   │   ├── newsletter.html      Magezon-style inline form
│   │   ├── flash.html           flash messages (lifted from ref/bloomburrow)
│   │   └── progress_steps.html  3-step indicator (lifted from ref/bloomburrow)
│   ├── home.html                hero + 2-tile category split + trending placeholder
│   ├── about.html
│   ├── shop/{listing,product,collection}.html
│   ├── auth/{login,register,forgot,reset}.html
│   ├── cart/cart.html
│   ├── checkout/
│   │   ├── start.html           sign-in / register / **continue-as-guest** trifecta
│   │   ├── shipping.html
│   │   ├── payment.html         order summary + HitPay redirect button
│   │   └── success.html
│   └── account/{dashboard,orders,order_detail,profile,addresses}.html
│
├── static/
│   ├── css/
│   │   ├── tokens.css           :root design tokens (see Design System below)
│   │   ├── base.css             reset, typography, layout primitives
│   │   ├── components.css       buttons, cards, forms, badges, swatches, .auth-card,
│   │   │                         .progress-steps, .order-summary, .product-item
│   │   └── pages.css            home hero, PDP gallery, checkout, account
│   ├── js/{main,cart,checkout,product}.js
│   └── img/
│       ├── logo.png             copied from MISS CLOVER LOGO.png
│       ├── products/{classic,maroon}.jpg   from bag_image_ref/
│       └── placeholders/        hero / category-tile placeholders (cream + maroon
│                                colour blocks with logo overlay; tagged for replacement)
│
├── instance/                    SQLite DB (gitignored)
├── migrations/                  Alembic
├── requirements.txt
└── .env.example                 SECRET_KEY, HITPAY_API_KEY, HITPAY_SALT, MAIL_*, etc.
```

---

## Design system (Kate Spade Singapore × MISS CLOVER)

Locked in `static/css/tokens.css`. Replicates the structural feel without copying KS verbatim — palette is keyed off the actual MISS CLOVER bag colours and the black-and-white logo.

| Token | Value | Source / rationale |
|---|---|---|
| `--bg` | `#FBFAF7` | Soft cream — matches the Classic bag colourway |
| `--surface` | `#FFFFFF` | Card / sheet surfaces |
| `--ink` | `#111111` | Primary text — matches the all-black logo |
| `--ink-muted` | `#5C5C5C` | Body text |
| `--ink-faint` | `#9A9A9A` | Captions, disabled |
| `--accent-maroon` | `#6E1A2D` | Pulled directly from the Maroon bag — primary accent |
| `--accent-maroon-soft` | `#F2E8EA` | Backgrounds, badges |
| `--gold` | `#B89668` | Subtle hardware accent (echoes the bag clip) |
| `--rule` | `#E8E2D8` | Hairline rules, sub-headers |
| `--success` / `--error` | `#0F7A4D` / `#B42E2E` | Form states |
| `--radius-sm` / `--radius` | `2px` / `4px` | KS uses sharp corners; we follow |
| `--shadow-card` | `0 1px 2px rgba(0,0,0,.04), 0 8px 24px rgba(0,0,0,.06)` | Soft, premium |
| `--font-display` | `"Cormorant Garamond", "Playfair Display", serif` | Headings |
| `--font-body` | `"Inter", system-ui, sans-serif` | Body / UI |
| `--container` | `1280px` | KS uses ~1320 |

Layout primitives (in `base.css`):
- `.page-wrapper` / `.page-main` mirroring KS's `<main id="maincontent">`.
- `.container` / `.container--narrow` (560px for forms — matches Bloomburrow's auth-card width).
- A three-row header (`header-top` promo strip / centered-logo `logo-row` / horizontal `navbar-row`) directly modelled on `html_ref/02-header-and-navigation.md`.

Components (in `components.css`):
- `.btn` + `.btn--primary` (solid black → maroon on hover), `.btn--ghost`, `.btn--lg`, `.btn--full`.
- `.product-item` card matching the anatomy in `html_ref/05-category-listing.md` (image + label container + name + price + swatches).
- `.swatch-opt` for the two designs (Classic / Maroon).
- `.auth-card` — directly adapted from `ref/quantiesunite/templates/login.html` and `ref/bloomburrow/templates/auth/login.html`.
- `.progress-steps` — directly lifted from `ref/bloomburrow/templates/payment.html` (3 circles + connectors).
- `.order-summary` — adapted from `ref/bloomburrow/templates/book.html`.
- `.flash-success`/`.flash-error`/`.flash-info` from Bloomburrow's CSS.

---

## Page set & Kate-Spade analogue

| Route | Template | KS pattern reproduced |
|---|---|---|
| `/` | `home.html` | `cms-home cms-index-index page-layout-1column` (`html_ref/04-homepage.md`): hero strip → two-tile category split (Classic / Maroon) → trending placeholder grid → lookbook spacer → newsletter |
| `/handbags` | `shop/listing.html` | `catalog-category-view page-layout-2columns-left` (`html_ref/05`): left filter sidebar (Color, Collection — static for now), toolbar (Sort: Position / Price asc / Price desc / Just Added), product grid |
| `/handbags/<slug>` | `shop/product.html` | `catalog-product-view page-layout-1column` (`html_ref/06`): gallery + `product-info-main` + variant swatch + qty + add-to-cart + "if you like this" placeholder + breadcrumbs + schema.org Offer microdata |
| `/collections/classic`, `/collections/maroon` | `shop/collection.html` | Single-product editorial landing |
| `/about` | `about.html` | KS `cms-page-view` |
| `/cart` | `cart/cart.html` | Standard cart table; line items with thumbnail, name, variant, qty stepper, line total, remove |
| `/checkout/start` | `checkout/start.html` | **Custom — not in either ref.** Three-card trifecta: *Sign in* (email + password), *Create account* (name + email + password), *Continue as guest* (just an email + "Continue" button) |
| `/checkout/shipping` | `checkout/shipping.html` | Bloomburrow pattern: full address form, phone with `+65` prefix `.phone-input-group`, optional newsletter checkbox |
| `/checkout/payment` | `checkout/payment.html` | Order summary card + "Pay with HitPay" → redirect to HitPay hosted page |
| `/checkout/return` | (server) | HitPay's redirect_url; reads `?reference=` and shows status |
| `/checkout/success/<order_no>` | `checkout/success.html` | KS-style confirmation; if guest, shows the unique guest-tracking link |
| `/auth/login` | `auth/login.html` | QuantiesUnite layout, Kate Spade colours |
| `/auth/register` | `auth/register.html` | Same |
| `/auth/forgot`, `/auth/reset/<token>` | `auth/forgot.html`, `auth/reset.html` | Bloomburrow pattern, Kate Spade colours |
| `/account` | `account/dashboard.html` | Recent orders + profile summary |
| `/account/orders`, `/orders/<id>` | `account/orders.html`, `account/order_detail.html` | Order list + detail |
| `/account/profile` | `account/profile.html` | Update name / email / password |
| `/account/addresses` | `account/addresses.html` | Saved shipping addresses |
| `/order/lookup` | `account/order_lookup.html` | **Guest tracker** — email + order number → readonly order detail |

---

## Database schema (SQLAlchemy)

```python
User(id, email[unique], password_hash, first_name, last_name, phone,
     newsletter_opt_in, created_at)

Address(id, user_id[nullable for guest], recipient_name,
        line1, line2, postcode, country='SG', phone)

Product(id, slug[unique], name, description, design_code,
        base_price_cents, currency='SGD')                         # seeded: classic, maroon

ProductVariant(id, product_id, name, sku[unique], stock_qty,
               price_cents)                                        # 1 variant per product to start

Cart(id, user_id[nullable], session_token, created_at, updated_at)
CartItem(id, cart_id, variant_id, qty, unit_price_cents_snapshot)

Order(id, order_number[unique, e.g. MC-2026-00001], user_id[nullable],
      guest_email[nullable], guest_lookup_token[nullable],
      status[pending|paid|fulfilled|cancelled],
      subtotal_cents, shipping_cents, total_cents, currency='SGD',
      shipping_address_id, hitpay_payment_request_id, hitpay_reference,
      created_at, paid_at)

OrderItem(id, order_id, variant_id, qty,
          unit_price_cents, name_snapshot, design_snapshot)

PasswordResetToken(id, user_id, token_hash, expires_at, used_at)
```

Either `user_id` **or** (`guest_email` + `guest_lookup_token`) is set on `Order`. Guests get a one-time URL `https://…/order/lookup?email=…&token=…` in their confirmation email — that's the guest-checkout completion the references don't have.

---

## Auth + guest flow (the new bit)

`/checkout/start` shows three options as visually equal cards:

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Sign in       │  │ Create account  │  │ Continue as     │
│   ──────        │  │   ──────        │  │ guest           │
│ Email           │  │ First / Last    │  │   ──────        │
│ Password        │  │ Email           │  │ Email           │
│                 │  │ Password        │  │ (we'll email    │
│ [ Sign In → ]   │  │ [ Create → ]    │  │  your receipt)  │
│                 │  │                 │  │ [ Continue → ]  │
│ Forgot pwd?     │  │ Newsletter ☐    │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

Behind the scenes the guest path:
1. Stores `guest_email` on the Order (no password, no User row).
2. Generates a `guest_lookup_token` (URL-safe random).
3. After payment, emails a magic-link `…/order/lookup?email=…&token=…` that opens the order detail in read-only.
4. Optional: at success page, prompt *"Save this order to a free account? Set a password →"* — converts guest order to a real User by hashing the password and back-filling `user_id`.

This keeps frictionless guest checkout *and* a clear conversion path — neither Bloomburrow nor QuantiesUnite has this; it's the addition the user explicitly asked for.

---

## Checkout + HitPay integration (lifted from QuantiesUnite's gateway choice)

`hitpay.py`:
- `create_payment_request(order, return_url, webhook_url)` — POST to HitPay `/v1/payment-requests` with `amount`, `currency=SGD`, `email`, `reference_number=order.order_number`, `redirect_url`, `webhook` and the configured payment methods (`paynow_online`, `card`, `grabpay`). Stores the returned `id` on `Order.hitpay_payment_request_id` and the hosted URL.
- `verify_webhook(payload, signature, salt)` — HMAC-SHA256 verification per HitPay docs. Required before mutating order status.
- Sandbox vs live keys via `HITPAY_API_KEY` and `HITPAY_API_BASE` env vars (see `.env.example`).

Webhook handler `/checkout/webhook` (POST) flips `Order.status` to `paid`, stamps `paid_at`, sends order confirmation email via `email_service.py`, and decrements `ProductVariant.stock_qty`.

---

## Critical files to reuse / adapt

These should be copied (and rebranded) rather than rewritten:

- **CSS tokens, button system, badge, flash, form-group** → derive `static/css/components.css` from `ref/bloomburrow/static/css/style.css`. Replace blush-pink palette with the design tokens above; replace the flower cursor / emoji headings (drop them — they conflict with the Kate Spade aesthetic the user asked for).
- **Auth card markup** → `templates/auth/login.html` derived from `ref/quantiesunite/templates/login.html` (cleaner email-or-username field) and `ref/bloomburrow/templates/auth/login.html` (better visual structure).
- **Progress-steps partial** → `templates/partials/progress_steps.html` lifted directly from `ref/bloomburrow/templates/payment.html`.
- **Phone input** with `+65` prefix and `.phone-input-group` class → from Bloomburrow's `book.html`.
- **Drag-drop file upload** → not needed (we have a real payment gateway, no screenshot proof) — *do not* port this from Bloomburrow.
- **Header / footer / mega-nav HTML structure** → modelled on `html_ref/02-header-and-navigation.md` and `html_ref/03-footer-and-newsletter.md`. We render plain `<ul><li>` instead of Magezon NinjaMenus' `<div>`-based mega-nav.
- **Product card anatomy** → modelled on `html_ref/05-category-listing.md` § "Product card anatomy".

The flower-cursor JS, emoji icons, blush-pink backgrounds, real-time-availability AJAX, weekend-only Flatpickr, and screenshot-upload pattern from Bloomburrow are all **out of scope** — they don't fit the brand or the use case.

---

## Verification

End-to-end steps the user runs locally to confirm the build is correct:

1. **Bootstrap**
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env   # then fill in HITPAY sandbox keys + MAIL_* (Mailtrap is fine)
   flask --app app.py db upgrade
   python seed.py         # creates Classic + Maroon products
   flask --app app.py run --debug
   ```
2. **Visual / structural** — open `/`, `/handbags`, `/handbags/classic-tote`, `/handbags/maroon-tote`, `/about` and confirm the header/footer/nav match the Kate-Spade-inspired tokens.
3. **Auth** — register a user, log out, log in, log out, password-reset round-trip (Mailtrap shows the email).
4. **Cart** — add Classic to cart, change qty, remove, add Maroon, view `/cart` totals (SGD).
5. **Guest checkout** — fresh incognito session: cart → `/checkout/start` → "Continue as guest" → enter email → `/checkout/shipping` → fill SG address → `/checkout/payment` → click "Pay with HitPay" → complete payment in **HitPay sandbox** → webhook fires → land on `/checkout/success/MC-2026-00001` showing the guest tracker link → open the link in another tab → order detail visible read-only.
6. **Logged-in checkout** — same path but signed in; order appears at `/account/orders`.
7. **Stock** — confirm `ProductVariant.stock_qty` decremented after webhook.
8. **Pytest** — `pytest tests/` for: cart math (subtotal + shipping = total), HitPay webhook signature verification (HMAC-SHA256), guest-lookup-token security (token must match for the email).
9. **Build hygiene** — `flask --app app.py routes` lists every route above; no dead links from header/footer; `python -m http.server` on `static/` shows all assets resolvable.

Once verified, the site is launch-ready *as soon as photography arrives* — the placeholders in `static/img/placeholders/` are the only swap-out before going live.
