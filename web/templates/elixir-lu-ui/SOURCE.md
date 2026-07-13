# Vendored from @elixir-lu/ui

`tokens.css` is a vendored copy of the shared LCSB/UNI design system
(https://github.com/elixir-luxembourg/elixir-lu-ui), the same one Data Catalog
uses.

- **Upstream commit:** 162fe27d165b757907440b6577e7a35e161af103
  (tokens.css unchanged since; confirm on next re-copy)

## How DAISY consumes the design system — PURE UTILITIES (2026-06-25)

DAISY loads **only `tokens.css`** (the semantic tier: `primary` / `danger` /
`info` / `on-primary` + fonts), inlined via `{% include %}` into the
`<style type="text/tailwindcss">` block in `_includes/tailwind_setup.html`.

**`components.css` is deliberately NOT vendored or loaded.** Templates carry
the expanded Tailwind utility strings directly, matching the upstream
`styleguide-utilities.html` reference (the pure-utility mirror of
`styleguide.html`). When the upstream design changes, update the affected
utility strings in the templates — `styleguide-utilities.html` shows the
canonical string for every component.

## Updating tokens

Re-copy from upstream and bump the commit SHA above:

    cp ../../../elixir-lu-ui/tokens.css .   # from this dir

Fonts/brand assets are NOT vendored here — DAISY still uses its own copies
under web/static/ (see Phase 4 dedup in doc/redesign-migration-plan.md).
