# FR-016 Slice 2 Gallery Mutation Structured Errors Lessons Learned

Generated: 2026-03-13T13:00:00  
Branch: `main`  
Scope: FR-016 (slice 2)

## 1) Slice Goal

Harden FR-016 gallery mutation behavior by returning deterministic, structured success/error payloads for rename/delete operations and expanding security edge-case coverage.

---

## 2) What Worked

- Converting mutation APIs to typed result envelopes (`ok` + typed error object) made rejection behavior explicit and easy to assert.
- Keeping path/name validation and mutation execution separated preserved small, testable functions.
- Expanding FR-016 tests in one focused integration file preserved requirement traceability and reduced test sprawl.

---

## 3) Friction and Fixes

1. **Expected RED from contract expansion**
   - Introducing structured error assertions failed immediately because `GalleryMutationError` and expanded result fields did not exist.
   - Fix: add minimal typed models and update mutation return contracts.

2. **Mixed exception/result semantics in slice 1 baseline**
   - Slice 1 behavior raised exceptions for some rejection paths, conflicting with deterministic payload goals.
   - Fix: normalize rename/delete behavior to return structured failure payloads for invalid name, out-of-scope, conflict, and missing path cases.

---

## 4) Decisions Captured

- FR-016 slice 2 uses structured mutation outcomes:
  - success: `ok=True`, `error=None`
  - rejection/failure: `ok=False` with `GalleryMutationError {code,message,path}`
- Current rejection/error taxonomy includes: `invalid_name`, `outside_allowlist`, `conflict`, `not_found`, `operation_failed`.
- Deterministic error contracts are preferred over ad-hoc exception-only signaling for expected policy rejections.

---

## 5) Process Reinforcement

- Continue strict approval-first flow across implementation and git lifecycle gates.
- Preserve stop-on-failure behavior and request approval before any post-failure fix.
- Capture lessons before commit and verify living-notes continuity before PR creation.

---

## 6) Validation Snapshot

- Black: pass
- Ruff: pass
- Mypy: pass
- Pytest full suite: pass (`27 passed`)
