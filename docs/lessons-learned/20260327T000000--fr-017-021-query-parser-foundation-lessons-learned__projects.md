# FR-017..021 Query Parser Foundation Lessons Learned

Generated: 2026-03-27T00:00:00Z  
Branch: `feat/fr-017-021-query-parser-foundation`  
Scope: FR-017, FR-018, FR-019, FR-020, FR-021

## 1) Slice Goal

Implement a narrow Query Grammar v1 foundation: parser + validation only, with typed AST/result models and actionable errors, while explicitly deferring execution, API, and UI concerns.

---

## 2) What Worked

- Requirement-mapped RED tests kept the slice narrow and prevented premature execution/API scope.
- Using typed dataclass result models made grammar precedence and validation outcomes easy to assert deterministically.
- Keeping the first implementation in a single pure-ish module allowed fast iteration without introducing unnecessary seams too early.

---

## 3) Friction and Fixes

1. **Interpreter invocation drift blocked the first RED run**
   - `python -m pytest` failed because `python` was not on PATH in this environment.
   - Fix: standardize on `.venv/bin/python -m pytest` for the slice.

2. **Expected RED failure started at import collection**
   - The first test run failed with `ModuleNotFoundError` because `rapidcull.query_grammar` did not exist yet.
   - Fix: add the minimal `query_grammar.py` module with typed AST/result/error dataclasses and parser entrypoint.

3. **Unknown-field suggestion matching was too strict**
   - `people=alice` initially returned no suggestion for `person`, weakening FR-018's actionable-error contract.
   - Fix: relax close-match suggestion threshold so near misses produce helpful guidance.

4. **Green tests still failed quality gates on formatting/import order**
   - After pytest passed, black/ruff still failed on import ordering and line wrapping.
   - Fix: apply targeted `ruff --fix` and `black` on the touched files, then rerun the same validation set.

---

## 4) Decisions Captured

- Keep this slice limited to parser + validation only; do not mix in query execution, DB filtering, API endpoints, or UI behavior.
- Return a typed `QueryParseResult` contract with `ok`, `expression`, and `errors` rather than relying on exception-only signaling for expected validation failures.
- Preserve explicit boolean precedence as `NOT` > `AND` > `OR` with deterministic AST construction.
- Enforce field-aware operator validation and actionable format errors at the parser boundary.

---

## 5) Process Reinforcement

- Create the feature branch before implementation.
- Follow Discover → Propose → Approve before any writes.
- Use targeted RED → GREEN validation on the requirement-scoped test file first.
- Stop on failures and request approval before each fix cycle.
- Capture lessons learned before commit/PR.

---

## 6) Validation Snapshot

- Black: pass (`.venv/bin/black --check src/rapidcull/query_grammar.py tests/integration/query/test_fr_017_021_query_grammar_validation.py`)
- Ruff: pass (`.venv/bin/ruff check src/rapidcull/query_grammar.py tests/integration/query/test_fr_017_021_query_grammar_validation.py`)
- Mypy: pass (`.venv/bin/mypy src/rapidcull/query_grammar.py`)
- Pytest: pass (`.venv/bin/python -m pytest tests/integration/query/test_fr_017_021_query_grammar_validation.py` → `6 passed`)

---

## 7) Next Slice Suggestions

1. Add validation for malformed numeric values on numeric fields (`iso`, `fnumber`, `focal`).
2. Separate semantic validation from parsing if the query module expands materially in the next slice.
3. Add FR-022 example coverage once documented query examples are finalized.
