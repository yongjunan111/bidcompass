# AGENTS.md

## Project
BidCompass unified UI implementation for a public bidding recommendation product.

## Mission
Use the provided UI kit as the approved visual baseline.
Do not redesign the product. Wire it into the existing app.

## Non-negotiable rules
1. Keep `AppShell` layout, design tokens, spacing rhythm, and card treatment.
2. Keep Korean copy formal and concise. Do not rewrite into casual tone.
3. Prefer adapting API responses in an adapter layer instead of changing page props.
4. Preserve the main page hierarchy:
   - Dashboard
   - Notice Search
   - Recommendation Result
   - Price Calculator
   - AI Report
   - History
   - Settings
5. Recommendation Result is the primary page. Do not change its core structure:
   - left navigation
   - center decision area
   - right AI summary / action area
   - three strategy cards
6. Do not add a heavy UI framework unless the repo already depends on one.
7. Keep class names starting with `bc-` when extending styles.
8. Support empty, loading, success, and error states.
9. When unsure, preserve the existing visual design and only modify the data layer.

## Technical preferences
- Reuse existing routing in the repo.
- Reuse existing state/data libraries if already installed.
- Prefer typed adapters and small, low-risk changes.
- Keep pages componentized.
- Avoid unnecessary refactors outside the affected UI area.

## Expected output from Codex
- changed files
- route mapping
- data adapter notes
- remaining TODOs
- test/build results
