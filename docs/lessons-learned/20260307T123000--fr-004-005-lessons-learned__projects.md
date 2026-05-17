# FR-004..005 Lessons Learned

Generated: 2026-03-07T12:30:00  
Branch: `feat/fr-004-005-image-id-and-failure-summary`  
Scope: FR-004, FR-005

## 1) Slice Goal

Deliver stable image identity behavior and explicit ingest failure summary behavior with full TDD and quality gates.

---

## 2) What Worked

- Extending the existing integration test file kept requirement traceability tight.
- RED first (import failures), then narrow GREEN implementation prevented over-scoping.
- Black + Ruff + Mypy + Pytest gates caught issues quickly and in the right order.

---

## 3) Friction and Fixes

1. **Formatter/linter ordering friction**
   - After Black, Ruff import-order check failed.
   - Fix: always run Ruff (with `--fix` when approved) after Black in the quality sequence.

2. **Schema evolution placement**
   - New table creation needed to coexist with existing schema-version checks.
   - Fix: keep schema setup idempotent inside `create_or_validate_schema`.

3. **Tool/file-type mismatch during quality step**
   - Black was accidentally run against markdown files, causing avoidable failure interruption.
   - Fix: restrict Black/Ruff/Mypy commands to Python targets (`src`, `tests`) and use markdown-specific tooling separately when needed.

---

## 4) Design Decisions Captured

- Use deterministic `image_id` generation from normalized path for this slice baseline.
- Keep failure reporting as explicit typed structures (`FailedIngestItem`, `IngestRunSummary`).
- Preserve functional, small-unit structure in foundation module for easy follow-on refactors.

---

## 5) Process Update Reinforced

For every feature slice:

1. Create/update lessons learned **before commit**.
2. Verify lessons learned artifact exists **before PR creation**.
3. Link the artifact in PR notes.
4. Verify tool/file-type compatibility before running formatters and linters.

---

## 6) Validation Snapshot

- Black: pass
- Ruff: pass
- Mypy: pass
- Pytest integration slice: pass (`6 passed`)
