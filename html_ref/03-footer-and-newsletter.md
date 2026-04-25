# Footer & newsletter

The footer is rendered by **Magezon Header/Footer Builder** as a `<div class="hfb hfb-footer hfb-footer4">` block — there is **no semantic `<footer>` tag** wrapping it. It is the last child of `.page-wrapper`.

## Vertical structure (rows)

| `mgz-element-row` | Purpose |
|---|---|
| `footer-row-level-1` | Outer container for all footer rows |
| `footer-top` | Newsletter signup (full-width, single column) |
| `footer-middle2` | Three columns: ABOUT US, CUSTOMER CARE, social |
| `footer-bottom` | Copyright line |
| `sticky-icon-row` | Bottom-right floating helpers: WhatsApp/Linktree CTA + scroll-to-top arrow |

## Newsletter (Magezon Newsletter)

Full-width above the rest of the footer, anchored at `#newsletter` (the in-page link in the navbar promo strip).

```html
<form class="form…  mgz-newsletter-form mgz-newsletter-form-inline2"
      action="https://singapore.katespade.com/mgznewsletter/subscriber/new/"
      method="post" novalidate
      data-mage-init='{"Magezon_Newsletter/js/form": { "emailAjaxUrl": "https://singapore.katespade.com/…" }}'>

  <h2 class="newsletter-title">get special offers, new arrivals and more, right in your inbox.</h2>
  <div class="newsletter-description"> … </div>

  <div class="mgz-newsletter-fields custom-newsletter-fields">
    <div class="mgz-newsletter-field firstname required">
      <input name="firstname" type="text" placeholder="first name" required/>
    </div>
    <div class="mgz-newsletter-field lastname required">
      <input name="lastname"  type="text" placeholder="last name" required/>
    </div>
    <div class="mgz-newsletter-field gender required">
      <select name="gender" required>
        <option value="">Select Gender</option>
        <option value="Female">Female</option>
        <option value="Male">Male</option>
        <option value="Others">Others</option>
      </select>
    </div>
    <div class="mgz-newsletter-field email required">
      <input name="email" type="email" placeholder="email address" required/>
    </div>
    <div class="mgz-newsletter-field phone">
      <input name="phone" type="tel" placeholder="phone number"
             data-mage-init='{"…/intlTelInput": …}'/>
    </div>
  </div>
  <button type="submit" class="mgz-newsletter-submit">SIGN UP NOW &gt;</button>
</form>
```

The phone input is enhanced by **intlTelInput** (CSS bundled in `Magezon_Newsletter/css/intlTelInput.min.css`).

## Footer middle: three columns

The middle row is `mgz-element-row footer-middle2` containing three `mgz-col-md-4` columns. Their content (extracted from the live HTML):

### About Us
- ABOUT US → `/who-we-are`
- who we are → `/who-we-are`
- the foundation → `/ks-foundation`
- investors → `https://www.tapestry.com/investors/`
- tapestry → `https://www.tapestry.com/`
- responsibilities → `https://www.tapestry.com/responsibility/`
- careers → `https://careers.tapestry.com`

### Customer Care
- CUSTOMER CARE → `/ks-customer-service-landing`
- warranty → `/ks-customer-service-landing/item-care-warranty`
- contact us → `/ks-customer-service-landing/contact-information`
- privacy policy → `/ks-customer-service-landing/ks-privacy-policy`
- brand protection → `/ks-customer-service-landing/ks-brand-protection`

### Social (column-social)
The third column carries the social icons. Only two outbound brand handles are linked:

- Instagram → `https://www.instagram.com/katespade_singapore/`
- TikTok → `https://www.tiktok.com/@katespadeasia`

(There is **no** Facebook, X/Twitter, YouTube, Pinterest or WeChat link in this region — Pinterest is referenced only via the `p:domain_verify` meta tags.)

## Footer bottom (copyright)

```html
<div class="ofmq8i8 mgz-element mgz-element-row footer-bottom full_width_row">
  …
  <p>2025 kate spade | all rights reserved.</p>
</div>
```

There is no terms-of-service or accessibility link here; legal links live under "Customer Care".

## Sticky icon row (bottom-right helpers)

A floating row attached at the page bottom-right:

```html
<div class="… mgz-element-row sticky-icon-row …">
  <a href="https://linktr.ee/katespadesgstores" target="_blank">…Chat with Us…</a>
  <i class="fas mgz-fa-angle-up stt-icon"></i>   <!-- Magezon scroll-to-top -->
</div>
```

- The chat CTA links out to **Linktree** (`linktr.ee/katespadesgstores`), which routes to the brand's WhatsApp / store contacts.
- The up-arrow is the Magezon ScrollToTop module (CSS: `Magezon_ScrollToTop/css/animate.css`).
