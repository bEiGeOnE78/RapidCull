# FR-006/007/008 Slice 2 Lessons Learned (Batch Accounting + Tool Summary)

Generated: 2026-03-14T22:30:00  
Branch: `feature/fr-006-007-008-slice-2-batch-accounting`  
Scope: FR-006a, FR-007a, FR-008a, FR-008b, FR-050a, NFR-007, NFR-008

## 1) Slice Goal

Extend proxy execution toward batch-style deterministic orchestration by guaranteeing per-item accounting (including unsupported inputs) and introducing deterministic per-tool summary reporting.

---

## 2) What Worked

- RED-first integration tests surfaced accounting gaps quickly (unsupported media previously not represented in failed outcomes).
- Preserving sorted path processing retained deterministic ordering guarantees for generated/failed outputs.
- Adding tool summary as an explicit contract (`tool_summary`) made FR-050a reporting behavior testable and stable.

---

## 3) Friction and Fixes

1. **Ordering expectation mismatch during batch accounting RED/GREEN loop**
   - Initial expectation did not match deterministic lexical sorted path processing.
   - Fix: align assertion order to stable sorted processing contract and document why.

2. **Mypy type inference failures for nested summary dictionary counters**
   - Increment operations on mixed nested dict values inferred as `object` caused blocking type errors.
   - Fix: introduce typed aliases for summary structures and small typed helper functions for counter/reason updates.

3. **Process mistake: implementation started on `main` after previous merge**
   - Work briefly continued on `main` before branch creation.
   - Fix: immediately created dedicated slice branch and continued there; reinforced branch check before coding.

---

## 4) Decisions Captured

- Unsupported media in proxy runs is now explicitly accounted as failure with reason `unsupported_media_type`.
- Proxy run result contract now includes deterministic `tool_summary` with per-tool `processed/generated/failed/reasons` counts.
- Keep deterministic sorted output ordering as an explicit behavior contract to protect future parallel worker evolution.

---

## 5) Process Reinforcement

- Approval-first flow maintained for each implementation and fix step.
- Stop-on-failure honored for test/type-check failures.
- Lessons learned recorded prior to commit/PR per required workflow.

---

## 6) Validation Snapshot

- `black`: pass
- `ruff`: pass
- `mypy`: pass
- full `pytest`: pass (`42 passed`)

---

## 7) Follow-up Suggestions

1. Introduce dedicated batch executor abstraction (worker pool/chunking) while preserving canonical output sorting.
2. Expand reason taxonomy normalization across adapter stderr/exit-code mappings for real tool execution.
3. Add integration tests validating summary reconciliation invariants under simulated parallel execution order variance.
