# FR-022 Query Behavior Documentation Baseline Lessons Learned

Generated: 2026-03-28T22:39:18-05:00  
Branch: `feature/fr-022-query-behavior-docs`  
Scope: FR-022

## 1) Slice Goal

Establish a narrow FR-022 baseline by documenting the currently implemented Query Grammar v1 parser/validator behavior and adding a docs-smoke check to keep documented examples aligned with the real parser contract.

---

## 2) What Worked

- Reusing the existing query parser contract made it possible to document behavior without inventing execution semantics.
- A tiny dedicated docs-smoke test file was sufficient to verify the document exists, includes core sections, and keeps valid/invalid examples aligned with `parse_query`.
- Keeping the document explicitly scoped to parser/validator behavior avoided accidental drift into query execution or result-set promises.

---

## 3) Friction and Fixes

1. **The FR-022 artifact did not exist yet**
   - The initial RED tests failed because there was no query behavior document to validate.
   - Fix: add a focused baseline doc with supported fields/operators, boolean behavior, and executable examples.

2. **Documentation needed a machine-checkable example format**
   - Free-form prose would be harder to verify against parser behavior over time.
   - Fix: use a simple example format (`- `query` -> ok` / `- `query` -> error:code`) that a smoke test can parse deterministically.

---

## 4) Decisions Captured

- FR-022 should document **current parser/validator behavior**, not future query execution or filtering semantics.
- Documented invalid examples should lock to stable error codes rather than full message text to reduce unnecessary doc churn while preserving behavioral truth.
- A lightweight docs-smoke test is appropriate for FR-022 because the acceptance source explicitly expects documentation examples to execute as advertised.

---

## 5) Process Reinforcement

- Transitioning from FR-021 parser hardening to FR-022 documentation works best when the docs remain anchored to already-validated behavior.
- RED-first still adds value for documentation requirements when acceptance depends on executable examples.
- Capture the lessons artifact before commit/PR even for documentation-focused slices.

---

## 6) Validation Snapshot

- Focused Pytest: pass (`.venv/bin/python -m pytest tests/integration/query/test_fr_022_query_behavior_docs.py` → `2 passed`)
- Full Pytest: pass (`.venv/bin/python -m pytest` → `82 passed`)
- Black: pass (`.venv/bin/python -m black --check .`)
- Ruff: pass (`.venv/bin/python -m ruff check .`)
- Mypy: pass (`.venv/bin/python -m mypy src`)

---

## 7) Next Slice Suggestions

1. Consider a follow-up FR-022 slice that expands the behavior doc with more example coverage while staying parser/validator-only.
2. Consider updating project intelligence/living notes to reflect that the FR-021 parser-diagnostics sequence is complete and FR-022 baseline docs are now present.
3. Only shift into query execution planning after the team agrees the documented parser contract is stable enough to build on.
