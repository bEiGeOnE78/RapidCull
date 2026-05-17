# FR-021 Query Error Diagnostics Lessons Learned

Generated: 2026-03-27T02:00:00Z  
Branch: `feat/fr-021-query-error-diagnostics`  
Scope: FR-021

## 1) Slice Goal

Harden malformed-query diagnostics so the parser returns more actionable errors for missing values after operators, trailing boolean operators, and invalid leading boolean placement, while keeping execution, API, and UI out of scope.

---

## 2) What Worked

- Exact dataclass-based error assertions made it straightforward to upgrade parser diagnostics without changing unrelated grammar behavior.
- The existing parser structure allowed targeted improvements in a few narrow branches instead of a full rewrite.
- Keeping the slice limited to FR-021 error clarity preserved stable green coverage for the earlier grammar and numeric-validation work.

---

## 3) Friction and Fixes

1. **Generic syntax errors were too coarse for FR-021 acceptance quality**
   - `person=` returned a generic `invalid_syntax` error without guidance.
   - Fix: introduce a dedicated `missing_value` error with `<value>` suggestion.

2. **Trailing boolean operators fell through to EOF token noise**
   - `person=alice AND` produced `Unexpected token ''`, which is technically true but not user-helpful.
   - Fix: detect EOF immediately after `AND`/`OR` and return `missing_expression` with expression-start guidance.

3. **Leading boolean operators were misinterpreted as fields**
   - `AND person=alice` previously behaved like a malformed comparison instead of a boolean-placement mistake.
   - Fix: reject leading `AND`/`OR` explicitly in primary-expression parsing with actionable alternatives.

---

## 4) Decisions Captured

- Prefer specific parser diagnostics over generic syntax failures when the intended correction is obvious.
- Treat boolean placement errors as grammar-position issues, not field/operator validation issues.
- Reuse the existing typed `QueryValidationError` contract rather than introducing special exception paths.

---

## 5) Process Reinforcement

- Add the narrowest RED tests possible for each diagnostic improvement.
- Validate only the touched query test file first, then run formatter/linter/type-check gates.
- Keep follow-up parser slices on separate feature branches with their own lessons artifacts.

---

## 6) Validation Snapshot

- Black: pass (`.venv/bin/black --check src/rapidcull/query_grammar.py tests/integration/query/test_fr_017_021_query_grammar_validation.py`)
- Ruff: pass (`.venv/bin/ruff check src/rapidcull/query_grammar.py tests/integration/query/test_fr_017_021_query_grammar_validation.py`)
- Mypy: pass (`.venv/bin/mypy src/rapidcull/query_grammar.py`)
- Pytest: pass (`.venv/bin/python -m pytest tests/integration/query/test_fr_017_021_query_grammar_validation.py` → `12 passed`)

---

## 7) Next Slice Suggestions

1. Add FR-021 coverage for unmatched closing parentheses and double-operator cases.
2. Consider extracting parser-specific diagnostic helpers if `query_grammar.py` keeps growing.
3. Add FR-022 documentation-example coverage once query examples are settled.
