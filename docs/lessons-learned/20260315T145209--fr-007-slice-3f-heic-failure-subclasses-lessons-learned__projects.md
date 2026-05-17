# FR-007 Slice 3f Lessons Learned (HEIC Adapter Failure Subclasses)

Generated: 2026-03-15T14:52:09Z  
Branch: `feat/fr-007-slice-3f-heic-failure-subclasses`  
Scope: FR-007a, FR-008b, FR-050a

## 1) Slice Goal

Refine HEIC adapter failure handling into explicit subprocess-detail subclasses while preserving canonical orchestration/reporting outputs for deterministic per-item and per-tool accounting.

---

## 2) What Worked

- Introduced explicit adapter detail reasons for HEIC conversion failure classes (`nonzero_exit`, `execution_error`, `timeout`) with minimal code-surface change.
- Preserved fail-fast semantics for missing HEIF capability (`imagemagick_heif_unsupported`).
- Existing orchestration normalization guardrail continued to map detail reasons to canonical external reason `imagemagick_heic_failed`, preventing contract drift.

---

## 3) Friction and Fixes

1. **Need for internal detail without changing outward taxonomy**
   - Requirement: increase operational diagnosability while keeping deterministic external reason schema stable.
   - Fix: keep detail at adapter boundary only; preserve orchestration canonicalization as the external contract boundary.

---

## 4) Decisions Captured

- `ImageMagickAdapter.generate_heic_proxy` now returns detailed HEIC failure reasons:
  - `imagemagick_heic_nonzero_exit`
  - `imagemagick_heic_execution_error`
  - `imagemagick_heic_timeout`
- `imagemagick_heif_unsupported` remains unchanged for capability-absent path.
- Orchestration canonicalization remains unchanged:
  - preserve `imagemagick_heif_unsupported`
  - normalize all other HEIC failures to `imagemagick_heic_failed`

---

## 5) Process Reinforcement

- Feature branch created before implementation (starting point was `main`).
- Approval-first + stop-on-failure workflow maintained.
- RED→GREEN completed via targeted adapter-detail tests before full quality gates.
- Lessons learned recorded before commit/PR.

---

## 6) Validation Snapshot

- `black --check .`: pass
- `ruff check .`: pass
- `mypy .`: pass
- full `pytest`: pass (`53 passed`)

---

## 7) Next Slice Suggestions

1. If needed, add bounded subprocess timeout policy at adapter seam invocation layer (currently timeout handling is mapping-only).
2. Add optional diagnostic logging hook for adapter-detail failure classes (without altering deterministic result payload contracts).
3. Consider mirrored detail taxonomy for still-path failures if operational debugging needs parity.
