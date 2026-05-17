# FR-021 Malformed Boolean-Pair Diagnostics Lessons Learned

Generated: 2026-03-28T22:17:02-05:00  
Branch: `feature/fr-021-malformed-boolean-pairs`  
Scope: FR-021

## 1) Slice Goal

Finish the last narrow FR-021 parser-diagnostics hardening slice so malformed consecutive boolean-operator sequences return an actionable boolean-pair error instead of reusing the generic expression-start diagnostic.

---

## 2) What Worked

- The existing FR-mapped query integration test file continued to scale for another small additive parser slice.
- RED tests for both `AND OR` and `OR AND` made the current fallback behavior explicit before changing parser logic.
- A tiny parser guard plus a small helper function was enough to specialize the diagnostic without affecting valid boolean parsing.

---

## 3) Friction and Fixes

1. **Consecutive boolean operators reused the generic expression-start error**
   - `person=alice AND OR person=bob` and `person=alice OR AND person=bob` both returned `invalid_boolean_position` for the second operator.
   - Fix: detect a second boolean operator immediately after matching `AND` or `OR` and return a dedicated `invalid_boolean_pair` error.

2. **Quality gates still caught a tiny style regression after logic was complete**
   - The new helper signature exceeded line length and failed `black --check` and `ruff check`.
   - Fix: reflow the function signature and rerun the full validation gates.

---

## 4) Decisions Captured

- Consecutive boolean operators deserve their own parser diagnostic instead of borrowing the top-level expression-start error.
- The second operator should be the reported token because it is the actionable malformed element in the pair.
- Keep the suggestions aligned with expression-start recovery guidance (`NOT`, field comparison, grouped expression).

---

## 5) Process Reinforcement

- Keep parser-diagnostics slices focused on one malformed grammar family at a time.
- Expect style gates to matter even for very small parser helpers.
- Capture the lessons artifact before commit/PR even when the slice appears to be the final polish step.

---

## 6) Validation Snapshot

- Focused Pytest: pass (`.venv/bin/python -m pytest tests/integration/query/test_fr_017_021_query_grammar_validation.py` → `26 passed`)
- Full Pytest: pass (`.venv/bin/python -m pytest` → `80 passed`)
- Black: pass (`.venv/bin/python -m black --check .`)
- Ruff: pass (`.venv/bin/python -m ruff check .`)
- Mypy: pass (`.venv/bin/python -m mypy src`)

---

## 7) Next Slice Suggestions

1. Reassess whether FR-021 parser-diagnostics hardening is now complete enough to stop slicing this area.
2. Shift the next query-related work toward FR-022 query behavior documentation if parser coverage now feels sufficient.
3. If any parser edge remains, keep it truly optional and narrowly justified rather than expanding diagnostics by default.
