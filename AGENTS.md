# BTB Agent Rules (must-follow)

## Non-negotiables
- Follow VISION_v1.md as the source of truth.
- No architecture changes without an explicit GitHub Issue.
- Keep functions small, typed, and documented.
- Degraded-mode is mandatory: never crash silently; always return structured outputs + reason codes.
- No fragile scraping HTML. Use stable APIs only.
- Windows/PowerShell first: every command must work on Windows.
- Prefer clean rewrites over patchy edits.

## PR discipline
- One issue per PR.
- Add/adjust tests for any parsing, DB schema, or critical logic change.
- Keep changes minimal and reversible.
