# Search results page

URL pattern: `/catalogsearch/result/?q=<term>`. Sample: `?q=tote` returned **54 results**.

## Body classes

```
page-products
page-with-filter
amsearch-search-page
catalogsearch-result-index
page-layout-2columns-left
```

The page reuses the **category-listing layout** (filter sidebar + grid + toolbar — see [05-category-listing.md](05-category-listing.md)) and adds the `amsearch-search-page` body class plus an Amasty-Xsearch-managed top region.

## Heading

```html
<h1 class="page-title"><span class="base">Search results for: 'tote'</span></h1>
```

## Filters available on search

The same Amasty filter forms render, with one omission compared to a Handbags category: the **Price** filter is not always shown (depends on the heterogeneity of the result set). Filters observed for `q=tote`:

- Color (`colorgroup`)
- Item Type (`item_type`)
- Material (`material`)
- Handbag Size (`handbag_size`)
- Collection (`collections`)

(There is no breadcrumb on the search results page — `<div class="breadcrumbs">` is absent.)

## Amasty Xsearch artefacts

The search results page contains the same Xsearch wrapper as the global header search bar plus an additional **search overlay** block:

```
amsearch-wrapper-block        ← form scope (×2: header desktop + mobile overlay)
amsearch-form-block
amsearch-input-wrapper
amsearch-input                 ← the actual <input name="q">
amsearch-button -loupe         ← submit
amsearch-button -close         ← reset
amsearch-result-section        ← live autocomplete results panel
amsearch-overlay-block         ← full-screen mobile overlay
amsearch-overlay
```

These selectors are bound to a Knockout viewmodel via `data-bind="scope: 'amsearch_wrapper'"`; the component is `Amasty_Xsearch/js/wrapper`.

## Toolbar / grid / pagination

Identical to the category template (sort options: Position / Price asc / Price desc / Just Added; per-page 12/24/36; bottom pagination with `?p=N`).
