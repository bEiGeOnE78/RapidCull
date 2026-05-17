# FR-022 Query Behavior Documentation Expansion Lessons Learned

Generated: 2026-03-29T07:07:03-05:00  
Branch: `feature/fr-022-query-docs-expansion`  
Scope: FR-022

## 1) Slice Goal

Expand the FR-022 Query Grammar v1 behavior document with more machine-checkable examples so the documented parser/validator contract covers additional valid and invalid query classes without introducing execution semantics.

---

## 2) What Worked

- Reusing the existing docs-smoke harness made the follow-up slice very small and deterministic.
- Promoting already-tested parser cases into the FR-022 document avoided inventing new behavior and kept the doc grounded in the current contract.
- Adding both valid and invalid examples increased coverage breadth while preserving the same simple machine-checkable format.

---

## 3) Friction and Fixes

1. **The baseline FR-022 doc was too thin for broader contract coverage**
   - The new RED assertions failed because the document did not yet include examples for numeric validation, trailing boolean errors, and malformed boolean-pair diagnostics.
   - Fix: expand the valid examples with `date`, `keyword~`, and `fnumber` coverage and expand invalid examples with `invalid_number`, `missing_expression`, and `invalid_boolean_pair` cases.

2. **A tiny docs-smoke assertion still triggered formatting gates**
   - Black required a formatting-only adjustment in the FR-022 docs test file after the new assertion was added.
   - Fix: reflow the long assertion and rerun the full validation suite.

---

## 4) Decisions Captured

- FR-022 documentation should expand by promoting already-validated parser cases rather than drafting speculative examples.
- The machine-checkable example format continues to scale for narrow documentation slices.
- Error-code-level verification remains a good stability point for documented invalid examples; it preserves behavior guarantees without over-binding docs to message wording.

---

## 5) Process Reinforcement

- Documentation slices can and should follow the same RED → GREEN → full-gates workflow as code slices when acceptance depends on executable examples.
- Use focused docs-smoke validation first, then run the full repository gates before calling the slice complete.
- Capture lessons learned before commit/PR even for follow-up documentation expansion slices.

---

## 6) Validation Snapshot

- Focused Pytest: pass (`.venv/bin/python -m pytest tests/integration/query/test_fr_022_query_behavior_docs.py` → `4 passed`)
- Full Pytest: pass (`.venv/bin/python -m pytest` → `84 passed`)
- Black: pass (`.venv/bin/python -m black --check .`)
- Ruff: pass (`.venv/bin/python -m ruff check .`)
- Mypy: pass (`.venv/bin/python -m mypy src`)

---

## 7) Next Slice Suggestions

1. Consider one final FR-022 example-expansion slice only if there are still important current-contract cases not yet documented.
2. If documentation coverage now feels sufficient, shift the next query-area planning discussion toward post-parser work while keeping execution semantics explicitly out of this document.
3. Update project intelligence/living notes before PR creation so the new FR-022 lessons artifact is discoverable through the normal process gates.
