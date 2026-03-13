# Agent Working Rules

## Cross-Check Quality Gate (Mandatory)

When the user asks for plan review, cross-check, or validation:

1. Always review the full provided text first.
2. Report results using exactly 3 sections:
   - `유지` (kept as-is)
   - `변경` (updated correctly)
   - `미반영` (missing or inconsistent)
3. For every `미반영` item, include:
   - direct quote/snippet from the latest user text
   - exact reason it is inconsistent
   - concrete fix
4. Do not claim “not reflected” without evidence from the latest full text.
5. Re-check the user’s most recent revision before sending conclusions.
6. Do not re-open already validated items unless new evidence appears.
7. If uncertain, mark as `확인 필요` instead of guessing.

## Output Discipline for Cross-Checks

1. Prioritize factual consistency over style suggestions.
2. Keep verdicts binary where possible: `반영됨` / `미반영`.
3. If previously raised issues are now fixed, explicitly acknowledge closure.
4. Avoid introducing new requirements unrelated to the requested diff.

## Tool Boundary

1. Prefer native Codex tools and directly connected MCP servers first.
2. If an external bridge/client is needed (for example `claude` CLI or another agent runtime), state that explicitly before use and get user approval first.

## Unified UI Rules

### Project
BidCompass unified UI implementation for a public bidding recommendation product.

### Mission
Use the provided UI kit as the approved visual baseline.
Do not redesign the product. Wire it into the existing app.

### Non-negotiable rules
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

### Technical preferences
- Reuse existing routing in the repo.
- Reuse existing state/data libraries if already installed.
- Prefer typed adapters and small, low-risk changes.
- Keep pages componentized.
- Avoid unnecessary refactors outside the affected UI area.
