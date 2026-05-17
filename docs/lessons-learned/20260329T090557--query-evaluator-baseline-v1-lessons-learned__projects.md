# Query Evaluator Baseline v1 Lessons Learned

Generated: 2026-03-29T09:05:57-05:00  
Branch: `feature/query-evaluator-baseline-v1`  
Scope: Query evaluator implementation baseline

## 1) Slice Goal

Implement the first runtime evaluator baseline for Query Grammar v1 as a pure single-record boolean evaluator, strictly against the clarified Query Evaluation Contract v1 and without expanding into collection filtering, API, UI, or job orchestration.

---

## 2) What Worked

- Starting from the already-clarified evaluation contract kept the implementation seam small and deterministic.
- A pure `evaluate_query(...) -> bool` entry point made the evaluator easy to test against AST fixtures without parser or storage coupling.
- Focused integration tests built directly from canonical contract examples provided high-signal coverage for both text and ordered comparisons.

---

## 3) Friction and Fixes

1. **The merged contract contained a stale example for multi-value equality**
   - Record A showed `"person": ["alice", "bob"]` while still claiming `person=bob -> non-match`, which contradicted the approved any-value matching rule.
   - Fix: stop and confirm the intended behavior before implementation; lock evaluator tests to any-value matching for multi-value fields.

2. **Initial ordered-comparison helper shape was too broad for strict mypy**
   - A shared helper that accepted `str | int | float` for both sides caused mypy to reject possible cross-type ordered comparisons.
   - Fix: split ordered comparison helpers by type domain so date comparisons stay text-to-text and numeric comparisons stay number-to-number.

3. **Formatter and linter gates still mattered for a small pure module**
   - Black and Ruff surfaced minor formatting/import-order issues after the evaluator and tests were added.
   - Fix: treat style gates as part of the same implementation loop and resolve them before final type-check confirmation.

---

## 4) Decisions Captured

- The first evaluator baseline should consume the existing typed AST directly rather than reparsing query text.
- The evaluator input record can remain a normalized mapping baseline for now; a dedicated record model is not required for this first implementation slice.
- Multi-value text equality uses any-value matching.
- Missing fields and empty text fields both evaluate as non-matches in runtime behavior, not just in documentation.
- Boolean evaluation should strictly follow parser-established AST grouping and precedence.

---

## 5) Process Reinforcement

- Contract contradictions should be resolved explicitly before implementation tests are treated as authoritative.
- Even small pure-function slices benefit from full-gate validation because typing and style issues can appear after behavior is already green.
- Approval-first execution remains useful for incremental runtime rollout: branch/session setup, RED tests, implementation, and post-slice documentation all stayed narrowly scoped.

---

## 6) Validation Snapshot

- Focused Pytest: pass (`.venv/bin/python -m pytest tests/integration/query` → `42 passed`)
- Full Pytest: pass (`.venv/bin/python -m pytest` → `96 passed`)
- Black: pass (`.venv/bin/python -m black --check .`)
- Ruff: pass (`.venv/bin/python -m ruff check .`)
- Mypy: pass (`.venv/bin/python -m mypy src`)

---

## 7) Next Slice Suggestions

1. Reconcile the stale canonical contract example so the documentation explicitly matches the approved any-value multi-value equality rule.
2. Add parser-to-evaluator end-to-end coverage that starts from query text, parses it, and evaluates it against normalized records.
3. Only after record-level behavior is stable, consider a collection-filtering slice that applies the evaluator across sets of records with deterministic output behavior.
