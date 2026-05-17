# FR-021 Open-Group EOF Diagnostics Lessons Learned

Generated: 2026-03-28T22:08:39-05:00  
Branch: `feature/fr-021-open-group-eof-diagnostics`  
Scope: FR-021

## 1) Slice Goal

Harden FR-021 grouped-expression diagnostics so incomplete open-group inputs like `(` and `NOT(` return an actionable missing-group-expression error instead of a generic EOF token failure.

---

## 2) What Worked

- The existing FR-mapped query integration test file continued to support another narrow additive parser slice cleanly.
- RED tests for both bare `(` and `NOT(` confirmed that grouped EOF handling needed its own parser branch rather than more generic token fallback.
- A tiny guard inside grouped-expression parsing was enough to improve the diagnostic without widening the slice into other malformed families.

---

## 3) Friction and Fixes

1. **Open grouped expressions at EOF fell through to a generic EOF token error**
   - `(` and `NOT(` both returned `Unexpected token ''` instead of naming the missing grouped expression after `(`.
   - Fix: detect `EOF` immediately after `LPAREN` and return a dedicated `missing_group_expression` error with grouped-start guidance.

---

## 4) Decisions Captured

- Incomplete grouped starts at EOF deserve a grouped-specific diagnostic instead of generic invalid-token fallback.
- `NOT(` should share the same grouped-start EOF contract as bare `(` because the missing recovery action is identical after the parser enters grouped-expression parsing.
- Continue treating one malformed grammar family as one slice even when the parser change is only a few lines.

---

## 5) Process Reinforcement

- Keep exact dataclass assertions for parser diagnostics so code/message/token/suggestions evolve together.
- Validate the focused query test file first, then the full repository gates before calling the slice done.
- Capture the lessons artifact before commit/PR even for very small parser hardening slices.

---

## 6) Validation Snapshot

- Focused Pytest: pass (`.venv/bin/python -m pytest tests/integration/query/test_fr_017_021_query_grammar_validation.py` → `24 passed`)
- Full Pytest: pass (`.venv/bin/python -m pytest` → `78 passed`)
- Black: pass (`.venv/bin/python -m black --check .`)
- Ruff: pass (`.venv/bin/python -m ruff check .`)
- Mypy: pass (`.venv/bin/python -m mypy src`)

---

## 7) Next Slice Suggestions

1. Consider malformed boolean-pair diagnostics next, such as `person=alice AND OR person=bob`.
2. Consider grouped unary edge cases like `(NOT)` only if they still fall through to weaker generic errors.
3. Reassess whether parser-diagnostics hardening is now sufficiently complete to shift the next query slice toward FR-022 query behavior documentation or later execution integration planning.
