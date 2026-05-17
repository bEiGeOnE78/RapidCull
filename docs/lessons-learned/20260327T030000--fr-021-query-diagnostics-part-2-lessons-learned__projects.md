# FR-021 Query Diagnostics Part 2 Lessons Learned

Generated: 2026-03-27T03:00:00Z  
Branch: `feat/fr-021-query-diagnostics-part-2`  
Scope: FR-021

## 1) Slice Goal

Harden parser diagnostics further for unmatched closing parentheses and doubled-operator forms such as `person==alice` and `iso>>100`, while keeping the slice limited to actionable malformed-query errors.

---

## 2) What Worked

- The existing query test file scaled well for additional FR-021 error cases without needing a new harness.
- Special-casing operator tokens where values are expected made doubled-operator diagnostics easy to implement without broad parser rewrites.
- Running the full repository pytest suite after focused validation gave confidence that the parser changes did not regress unrelated areas.

---

## 3) Friction and Fixes

1. **Unmatched closing `)` fell through to a generic invalid-token error**
   - `person=alice)` produced a technically correct but weak diagnostic.
   - Fix: detect trailing unmatched `RPAREN` at parse tail and return a dedicated actionable error.

2. **Doubled operators were misclassified as missing values**
   - `person==alice` and `iso>>100` were treated like missing RHS values after the first operator.
   - Fix: when an operator appears where a value is expected, map it to an `invalid_operator` diagnostic with operator-specific guidance.

3. **Completion criteria needed clarification around test scope**
   - Focused query tests passed, but the broader expectation was to run the full repo test suite before calling the slice complete.
   - Fix: add explicit reinforcement that slice completion requires both focused tests and full `pytest`.

---

## 4) Decisions Captured

- Prefer dedicated malformed-operator diagnostics over reusing missing-value errors when the second token is itself an operator.
- Treat unmatched trailing `)` as a first-class parser diagnostic.
- Consider a slice incomplete until the full repository pytest suite has passed, not just the focused feature-area suite.

---

## 5) Process Reinforcement

- Run the focused feature-area tests first for quick feedback.
- Before declaring a slice complete, also run the full repository pytest suite.
- Keep parser hardening slices narrow and additive, with one artifacted lesson per merged slice.

---

## 6) Validation Snapshot

- Black: pass (`.venv/bin/black --check src/rapidcull/query_grammar.py tests/integration/query/test_fr_017_021_query_grammar_validation.py`)
- Ruff: pass (`.venv/bin/ruff check src/rapidcull/query_grammar.py tests/integration/query/test_fr_017_021_query_grammar_validation.py`)
- Mypy: pass (`.venv/bin/mypy src/rapidcull/query_grammar.py`)
- Focused Pytest: pass (`.venv/bin/python -m pytest tests/integration/query/test_fr_017_021_query_grammar_validation.py` → `15 passed`)
- Full Pytest: pass (`.venv/bin/python -m pytest` → `69 passed`)

---

## 7) Next Slice Suggestions

1. Add FR-021 coverage for malformed grouped expressions with missing RHS after boolean operators inside parentheses.
2. Consider extracting parser diagnostic helpers if `query_grammar.py` grows beyond its current narrow scope.
3. Add FR-022 documentation-example coverage once example queries are finalized.
