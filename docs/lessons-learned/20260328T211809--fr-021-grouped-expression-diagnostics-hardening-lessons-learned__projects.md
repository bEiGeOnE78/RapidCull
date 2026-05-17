# FR-021 Grouped Expression Diagnostics Hardening Lessons Learned

Generated: 2026-03-28T21:18:09-05:00  
Branch: `feature/fr-021-grouped-expression-diagnostics`  
Scope: FR-021

## 1) Slice Goal

Harden grouped-expression parser diagnostics for malformed boolean expressions inside parentheses by adding actionable errors for missing RHS expressions after `AND`/`OR` and for empty grouped expressions `()`.

---

## 2) What Worked

- Reusing the existing FR-mapped query integration test file kept the slice small and easy to validate.
- Adding RED tests first made the current fallback behavior explicit before touching parser logic.
- A small parser change was enough to improve grouped-expression diagnostics without broader grammar refactoring.

---

## 3) Friction and Fixes

1. **Grouped trailing boolean operators fell through to a generic `)` token error**
   - `(person=alice AND)` and `(person=alice OR)` produced `Unexpected token ')'` instead of naming the missing grouped RHS.
   - Fix: treat both `EOF` and `RPAREN` immediately after `AND`/`OR` as `missing_expression`.

2. **Empty grouped expressions were not distinguished from generic invalid-token failures**
   - `()` produced `Unexpected token ')'`, which was technically true but not actionable enough for FR-021 expectations.
   - Fix: detect `RPAREN` immediately after `LPAREN` and return a dedicated `empty_group` diagnostic.

3. **Validation gates caught style drift even after logic was correct**
   - The new tests passed functionally, but `black --check` and `ruff check` failed on overlong test names.
   - Fix: shorten the test names and rerun the full validation suite.

---

## 4) Decisions Captured

- Grouped-expression boolean RHS omissions should reuse the existing `missing_expression` contract rather than introducing a grouped-only variant.
- Empty `()` should be a first-class parser diagnostic with a dedicated `empty_group` code.
- Full slice completion still requires formatting/lint/type gates even when focused and full tests already pass.

---

## 5) Process Reinforcement

- Keep parser hardening slices narrow and additive.
- Stop on any validation failure and fix only after approval.
- Run focused RED/green validation first, then the full repository gates before calling the slice complete.

---

## 6) Validation Snapshot

- Focused Pytest: pass (`.venv/bin/python -m pytest tests/integration/query/test_fr_017_021_query_grammar_validation.py` → `18 passed`)
- Full Pytest: pass (`.venv/bin/python -m pytest` → `72 passed`)
- Black: pass (`.venv/bin/python -m black --check .`)
- Ruff: pass (`.venv/bin/python -m ruff check .`)
- Mypy: pass (`.venv/bin/python -m mypy src`)

---

## 7) Next Slice Suggestions

1. Add the optional narrow malformed grouped-start case such as `NOT)` if still desired for FR-021 coverage.
2. Consider whether grouped-expression diagnostics should also special-case `(` followed immediately by `AND`/`OR` with more targeted guidance.
3. Continue keeping parser diagnostics as exact dataclass assertions to preserve actionable error contracts.
