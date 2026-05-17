# Query Evaluation Contract v1 Lessons Learned

Generated: 2026-03-29T08:05:44-05:00  
Branch: `feature/query-evaluation-contract-v1`  
Scope: Query post-parser planning

## 1) Slice Goal

Define a narrow, spec-only Query Evaluation Contract v1 for the existing query AST so future implementation work can proceed from explicit semantics instead of inferred behavior, while keeping API/UI/job/storage concerns out of scope.

---

## 2) What Worked

- Treating the slice as a documentation/spec artifact kept it small and avoided premature evaluator implementation.
- A lightweight spec-smoke test file was enough to enforce required sections, semantic points, and canonical examples.
- Anchoring the spec to the already-complete parser/validator contract made the new document easier to keep consistent and deterministic.

---

## 3) Friction and Fixes

1. **The evaluation contract did not exist yet**
   - The initial RED tests failed because there was no evaluator-semantics document to validate.
   - Fix: add a dedicated Query Evaluation Contract v1 spec with scope, input/output contract, comparison semantics, boolean semantics, missing-field policy, and canonical examples.

2. **Manual import edits were less reliable than tool-driven formatting**
   - The new spec-smoke test file repeatedly failed Black/Ruff import ordering despite manual fixes.
   - Fix: run Black and Ruff directly on the file and treat formatter/linter output as the source of truth for import normalization.

---

## 4) Decisions Captured

- Query evaluation semantics should be documented before evaluator implementation to avoid semantic drift.
- The minimum evaluator contract for v1 is record-by-record boolean `match` / `non-match`, not collection behavior or transport shape.
- Missing metadata fields should evaluate as non-matches instead of raising evaluator-time validation errors, because malformed queries are already rejected earlier.

---

## 5) Process Reinforcement

- Spec-only slices still benefit from RED → GREEN → full-gates flow when the document is meant to act as a stable contract.
- Keep post-parser planning slices explicitly separated from implementation/API/UI/runtime work.
- Capture the lessons artifact before commit/PR even when the slice is documentation-led rather than code-led.

---

## 6) Validation Snapshot

- Focused Pytest: pass (`.venv/bin/python -m pytest tests/integration/query/test_query_evaluation_contract_v1.py` → `3 passed`)
- Full Pytest: pass (`.venv/bin/python -m pytest` → `88 passed`)
- Black: pass (`.venv/bin/python -m black --check .`)
- Ruff: pass (`.venv/bin/python -m ruff check .`)
- Mypy: pass (`.venv/bin/python -m mypy src`)

---

## 7) Next Slice Suggestions

1. Consider a follow-up decision/spec slice for unresolved evaluator semantics such as text case-sensitivity and multi-value keyword/person matching policy, if those are still ambiguous.
2. If the team is satisfied with the contract, the next query-area slice can move into evaluator implementation planning or an execution baseline slice built strictly against this spec.
3. Update project intelligence/living notes before PR creation so the new evaluation-contract lessons artifact is discoverable through the standard process gates.
