# FR-021 NOT Diagnostic Hardening Lessons Learned

Generated: 2026-03-28T21:44:07-05:00  
Branch: `feature/fr-021-not-diagnostic-hardening`  
Scope: FR-021

## 1) Slice Goal

Harden FR-021 unary/grouped-start diagnostics so malformed `NOT)`-style input returns an actionable missing-expression error instead of a generic unexpected `)` token failure.

---

## 2) What Worked

- The existing query integration test file continued to scale well for another narrow FR-021 parser slice.
- RED tests for both `NOT)` and `NOT )` made it easy to lock whitespace-insensitive behavior before changing parser logic.
- A one-branch parser change in `_parse_not_expression` was enough to improve the diagnostic without disturbing the rest of the grammar.

---

## 3) Friction and Fixes

1. **Malformed `NOT)` input fell through to a generic token error**
   - `NOT)` and `NOT )` both produced `Unexpected token ')'` instead of naming the missing operand after `NOT`.
   - Fix: detect `EOF` and `RPAREN` immediately after matching `NOT` and reuse the existing `missing_expression` diagnostic helper.

---

## 4) Decisions Captured

- `NOT` should share the same `missing_expression` contract family already used for `AND` and `OR`.
- Whitespace-separated and non-whitespace forms (`NOT )` and `NOT)`) should produce the same diagnostic outcome.
- Keep follow-up FR-021 parser hardening slices narrowly scoped to one malformed pattern at a time.

---

## 5) Process Reinforcement

- Add the narrowest possible RED tests first, then validate focused behavior before running full repository gates.
- Reuse existing diagnostic helpers where the correction guidance is identical.
- Capture a lessons artifact before any commit or PR, even for very small parser slices.

---

## 6) Validation Snapshot

- Focused Pytest: pass (`.venv/bin/python -m pytest tests/integration/query/test_fr_017_021_query_grammar_validation.py` → `20 passed`)
- Full Pytest: pass (`.venv/bin/python -m pytest` → `74 passed`)
- Black: pass (`.venv/bin/python -m black --check .`)
- Ruff: pass (`.venv/bin/python -m ruff check .`)
- Mypy: pass (`.venv/bin/python -m mypy src`)

---

## 7) Next Slice Suggestions

1. Consider the next narrow grouped-start diagnostic case for `(` followed immediately by `AND` or `OR`.
2. Keep exact dataclass assertions for parser errors so diagnostic regressions remain obvious.
3. Continue avoiding execution/API integration work until the parser-diagnostics surface is stable enough.
