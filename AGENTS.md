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
