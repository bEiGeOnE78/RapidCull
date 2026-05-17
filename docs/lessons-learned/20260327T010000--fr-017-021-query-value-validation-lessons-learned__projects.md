# FR-017..021 Query Value Validation Lessons Learned

Generated: 2026-03-27T01:00:00Z  
Branch: `feat/fr-017-021-query-value-validation`  
Scope: FR-019, FR-021

## 1) Slice Goal

Harden the query grammar foundation with numeric value validation for `iso`, `fnumber`, and `focal`, plus actionable malformed-token handling for lone `!`, while keeping execution, API, and UI out of scope.

---

## 2) What Worked

- Extending the existing FR-mapped query test file preserved traceability and kept the hardening slice small.
- Numeric validation fit cleanly as semantic validation on top of the existing parser contract.
- Treating malformed standalone punctuation as an explicit invalid-token case avoided parser hangs and improved operator guidance.

---

## 3) Friction and Fixes

1. **Malformed `!` caused a hang-risk in tokenization**
   - The RED run timed out after two new failures because lone `!` produced no valid token progress.
   - Fix: emit an explicit `INVALID` token when no atom/operator is consumed, then map lone `!` to an actionable `!=` suggestion.

2. **Numeric field validation was previously too permissive**
   - `iso>=fast` and `fnumber<=wide` parsed without field-type enforcement.
   - Fix: add field-aware numeric validation with distinct integer vs numeric checks.

---

## 4) Decisions Captured

- Keep numeric value enforcement in semantic validation, not tokenizer parsing, so grammar structure remains simple.
- Treat `iso` as integer-only in this phase.
- Treat `fnumber` and `focal` as numeric fields accepting values parseable by `float()`.
- Return actionable malformed-token suggestions when the intended operator is clear (`!` → `!=`).

---

## 5) Process Reinforcement

- Start each follow-up slice on a new feature branch.
- Add RED tests first, then validate the narrow test file before implementation.
- Stop when a test run reveals failure or hang behavior, report it, and fix only the approved scope.
- Capture lessons learned before commit/PR.

---

## 6) Validation Snapshot

- Black: pass (`.venv/bin/black --check src/rapidcull/query_grammar.py tests/integration/query/test_fr_017_021_query_grammar_validation.py`)
- Ruff: pass (`.venv/bin/ruff check src/rapidcull/query_grammar.py tests/integration/query/test_fr_017_021_query_grammar_validation.py`)
- Mypy: pass (`.venv/bin/mypy src/rapidcull/query_grammar.py`)
- Pytest: pass (`.venv/bin/python -m pytest tests/integration/query/test_fr_017_021_query_grammar_validation.py` → `9 passed`)

---

## 7) Next Slice Suggestions

1. Add FR-021 coverage for additional malformed-token cases and missing-value diagnostics.
2. Consider splitting semantic validation helpers out of `query_grammar.py` if the query contract expands further.
3. Add FR-022 example coverage once documented query examples are finalized.
