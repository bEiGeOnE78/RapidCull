# Query Evaluation Semantics v1 Lessons Learned

Generated: 2026-03-29T08:26:37-05:00  
Branch: `feature/query-evaluation-semantics-v1`  
Scope: Query post-parser semantics clarification

## 1) Slice Goal

Clarify the remaining evaluator semantics in the Query Evaluation Contract v1 before runtime implementation, specifically text case handling, multi-value `person` / `keyword` behavior, exact `~` semantics, and missing-vs-empty text-field behavior.

---

## 2) What Worked

- A narrow spec-only slice kept the work focused and avoided drifting into evaluator implementation.
- RED spec-smoke assertions were effective for exposing exactly which semantics were still implicit in the contract.
- Using canonical multi-value record examples made the new semantics easier to express and review.

---

## 3) Friction and Fixes

1. **The initial contract update broke existing spec-smoke wording expectations**
   - The first doc edit replaced older semantic labels such as `text equality` and `contains`, which caused previously passing contract assertions to fail.
   - Fix: keep the established semantic labels while expanding the document underneath them with the clarified rules.

2. **Validation required both Black and Ruff follow-through on test-only changes**
   - After the doc and test updates, Black reformatted the query contract test file and Ruff then surfaced line-length violations that Black alone did not resolve acceptably.
   - Fix: treat formatter and linter feedback as sequential gates and make small readability-preserving test refactors instead of forcing brittle long-line assertions.

---

## 4) Decisions Captured

- Text comparisons (`=`, `!=`, `~`) are case-insensitive.
- `person` and `keyword` are evaluated as multi-value text fields.
- `camera` and `lens` remain single-value text fields.
- `=` matches when any normalized candidate value equals the query value.
- `!=` matches only when the field is present and no normalized candidate value equals the query value.
- `~` is a case-insensitive substring match against any normalized candidate value.
- Missing fields and empty text fields both evaluate as non-matches.

---

## 5) Process Reinforcement

- Contract-clarification slices benefit from the same RED → GREEN → full-gates flow as code slices because wording drift can still break enforceable behavior contracts.
- When extending an existing spec, preserve already-tested terminology unless the slice intentionally migrates the test contract too.
- Lessons learned and living-notes updates remain part of done-ness even for documentation-led slices.

---

## 6) Validation Snapshot

- Focused Pytest: pass (`.venv/bin/python -m pytest tests/integration/query` → `36 passed`)
- Full Pytest: pass (`.venv/bin/python -m pytest` → `90 passed`)
- Black: pass (`.venv/bin/python -m black --check .`)
- Ruff: pass (`.venv/bin/python -m ruff check .`)
- Mypy: pass (`.venv/bin/python -m mypy src`)

---

## 7) Next Slice Suggestions

1. Start the first evaluator implementation baseline strictly against the clarified Query Evaluation Contract v1.
2. Keep the implementation slice record-by-record and boolean-only before expanding into collection filtering, API, or UI concerns.
3. Preserve the new multi-value and case-insensitive semantics in runtime tests so evaluator behavior cannot regress silently.
