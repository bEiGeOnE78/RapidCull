# FR-021 Grouped-Start Boolean Diagnostics Lessons Learned

Generated: 2026-03-28T21:55:31-05:00  
Branch: `feature/fr-021-grouped-start-boolean-diagnostics`  
Scope: FR-021

## 1) Slice Goal

Harden FR-021 grouped-expression diagnostics so parenthesized queries that start with `AND` or `OR` return a dedicated grouped-start error instead of reusing the generic expression-start boolean diagnostic.

---

## 2) What Worked

- The existing FR-mapped query integration test file continued to support narrow additive parser slices without needing new fixtures.
- RED tests made the current fallback behavior explicit before the parser change.
- A tiny parser branch inside grouped-expression parsing was enough to specialize the error without affecting top-level boolean handling.

---

## 3) Friction and Fixes

1. **Grouped-start boolean misuse reused the top-level diagnostic**
   - `(AND person=alice)` and `(OR person=alice)` both returned `invalid_boolean_position` with “cannot start an expression,” which was accurate but not specific to grouped misuse.
   - Fix: detect `AND`/`OR` immediately after `(` and return a dedicated `invalid_group_start` error with grouped-specific wording.

---

## 4) Decisions Captured

- Grouped-start boolean misuse deserves its own parser diagnostic instead of borrowing the top-level expression-start error.
- The grouped-start contract should remain parser-only and keep the same actionable suggestion family (`NOT`, field comparison, nested group).
- Follow-up FR-021 slices should continue specializing only one malformed grammar family at a time.

---

## 5) Process Reinforcement

- Keep using exact dataclass assertions to lock error code, message, token, and suggestions together.
- Land grouped-expression hardening incrementally instead of widening a single slice across many malformed cases.
- Capture a lessons artifact before commit/PR even when the parser change is very small.

---

## 6) Validation Snapshot

- Focused Pytest: pass (`.venv/bin/python -m pytest tests/integration/query/test_fr_017_021_query_grammar_validation.py` → `22 passed`)
- Full Pytest: pass (`.venv/bin/python -m pytest` → `76 passed`)
- Black: pass (`.venv/bin/python -m black --check .`)
- Ruff: pass (`.venv/bin/python -m ruff check .`)
- Mypy: pass (`.venv/bin/python -m mypy src`)

---

## 7) Next Slice Suggestions

1. Consider the next narrow open-group EOF diagnostic slice for `(` or `NOT(` if those still fall through to weaker generic errors.
2. Consider malformed boolean-pair sequences such as `person=alice AND OR person=bob` if grouped-start coverage is now sufficient.
3. Continue deferring query execution/API integration until parser diagnostics feel complete and stable.
