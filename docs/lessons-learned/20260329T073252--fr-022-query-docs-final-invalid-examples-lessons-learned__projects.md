# FR-022 Query Docs Final Invalid Examples Lessons Learned

Generated: 2026-03-29T07:32:52-05:00  
Branch: `feature/fr-022-query-docs-final-invalid-examples`  
Scope: FR-022

## 1) Slice Goal

Finish the FR-022 Query Grammar v1 behavior documentation by promoting the remaining high-signal malformed-query diagnostics into machine-checkable invalid examples, without changing parser behavior or drifting into execution semantics.

---

## 2) What Worked

- Reusing the existing docs-smoke harness kept the slice extremely narrow and deterministic.
- Promoting already-validated FR-021 parser diagnostics into the FR-022 document avoided speculative examples.
- Adding only invalid examples let the slice close an obvious documentation gap without reopening broader coverage questions.

---

## 3) Friction and Fixes

1. **The FR-022 doc still omitted several important malformed-query cases**
   - The new RED test showed the doc was missing machine-checkable examples for `missing_value`, `missing_group_expression`, `unexpected_closing_parenthesis`, and `invalid_operator`.
   - Fix: add `person=`, `(`, `person=alice)`, and `person==alice` to the invalid examples section.

---

## 4) Decisions Captured

- The final FR-022 documentation pass should prioritize high-signal invalid examples that represent common recovery guidance.
- Error-code-level checks remain the right contract for invalid examples in docs-smoke validation.
- This slice stays docs-only; parser implementation is already sufficiently stable for the documented cases.

---

## 5) Process Reinforcement

- Documentation completion can be driven by promotion of existing requirement-mapped tests into machine-checkable examples.
- Focused docs-smoke tests remain the fastest way to detect doc/behavior drift before full-repo validation.
- Capture the lessons artifact before commit/PR even for a final polishing slice.

---

## 6) Validation Snapshot

- Focused Pytest: pass (`.venv/bin/python -m pytest tests/integration/query/test_fr_022_query_behavior_docs.py` → `5 passed`)
- Full Pytest: pass (`.venv/bin/python -m pytest` → `85 passed`)
- Black: pass (`.venv/bin/python -m black --check .`)
- Ruff: pass (`.venv/bin/python -m ruff check .`)
- Mypy: pass (`.venv/bin/python -m mypy src`)

---

## 7) Next Slice Suggestions

1. Reassess whether FR-022 documentation is now complete enough to stop expanding query behavior examples.
2. If query docs are considered complete, the next query-related slice should likely be planning/spec work for post-parser behavior rather than more parser/documentation churn.
3. Update project intelligence/living notes before PR creation so the final FR-022 lessons artifact is discoverable through normal process gates.
