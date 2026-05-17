# FR-006/007/008 Slice 3e Lessons Learned (HEIC Subprocess Path + Taxonomy Hardening)

Generated: 2026-03-15T13:37:23Z  
Branch: `feat/fr-006-008-slice-3e-heic-subprocess`  
Scope: FR-007a, FR-008b, FR-050a

## 1) Slice Goal

Implement ImageMagick HEIC conversion through adapter subprocess execution when HEIF capability exists, while preserving fail-fast preflight expectations and canonical deterministic failure taxonomy/reporting contracts.

---

## 2) What Worked

- Reused the existing adapter seam (`_run_command`) to add HEIC command execution with minimal surface-area change.
- Preserved explicit capability-missing behavior (`imagemagick_heif_unsupported`) while introducing canonical HEIC runtime failure mapping (`imagemagick_heic_failed`).
- Added orchestration-level normalization guardrail for HEIC reasons so subprocess-detail leakage cannot drift item-level vs tool-summary reason taxonomy.

---

## 3) Friction and Fixes

1. **Environment-coupled orchestration success test after enabling real HEIC subprocess path**
   - Existing FR-007a orchestration success test relied on default adapter behavior and became non-deterministic once subprocess execution was real.
   - Fix: stabilize orchestration success test with deterministic injected success adapter; keep subprocess behavior assertions in dedicated adapter-level tests.

2. **Workflow check: HEIF support requirement interpretation**
   - Clarified that HEIF remains a fail-fast system dependency at preflight (`scripts/verify_system_deps.sh`).
   - Runtime `imagemagick_heif_unsupported` behavior remains as a defensive contract path if execution bypasses preflight.

---

## 4) Decisions Captured

- `ImageMagickAdapter.generate_heic_proxy` now executes subprocess only when HEIF capability is available.
- HEIC subprocess non-zero/`OSError` outcomes map to canonical `imagemagick_heic_failed`.
- Proxy orchestration now normalizes HEIC reasons:
  - preserve `imagemagick_heif_unsupported`
  - map all other HEIC failures to `imagemagick_heic_failed`
- Deterministic per-item accounting and per-tool summary schema/contracts remain unchanged.

---

## 5) Process Reinforcement

- Branch created before implementation because starting branch was `main`.
- Approval-first and stop-on-failure flow observed across RED→GREEN loop.
- Lessons-learned artifact recorded before commit/PR.

---

## 6) Validation Snapshot

- `black --check .`: pass
- `ruff check .`: pass
- `mypy .`: pass
- full `pytest`: pass (`52 passed`)

---

## 7) Next Slice Suggestions

1. Expand HEIC adapter failure taxonomy only if product requirements call for more actionable classes (e.g., timeout vs decode) while preserving canonical summary mapping.
2. Add optional real-tool integration test fixture for HEIC happy-path command execution under controlled CI capability checks.
3. Keep orchestration tests adapter-injected by default for deterministic cross-environment reliability.
