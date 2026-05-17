# Task Context: FR-006/007/008 Slice 1 (Real-tool proxy adapters)

Session ID: 2026-03-14-fr-006-007-008-slice-1
Created: 2026-03-14T00:00:00Z
Status: in_progress

## Current Request
Implement FR-006/007/008 slice 1 using TDD (red → green → refactor): introduce real-tool adapters for ImageMagick (still + HEIC proxy generation) and RawTherapee (RAW proxy generation), enforce deterministic per-item failure accounting with actionable reason codes, follow approval-first workflow, and run quality gates (black + ruff + mypy + full pytest) before merge checkpoints.

## Context Files (Standards to Follow)
- .opencode/context/core/standards/code-quality.md
- .opencode/context/core/standards/test-coverage.md
- .opencode/context/core/standards/security-patterns.md
- .opencode/context/project-intelligence/living-notes.md
- docs/20260307T080227--photo-library-requirements__projects.md
- docs/20260307T080227--photo-library-acceptance-tests__projects.md
- docs/20260307T080227--photo-library-test-plan__projects.md
- docs/20260307T093000--rapidcull-dependencies__projects.md
- docs/lessons-learned/20260307T130500--fr-006-008-lessons-learned__projects.md

## Reference Files (Source Material to Look At)
- src/rapidcull/proxies.py
- src/rapidcull/models.py
- src/rapidcull/exiftool_adapter.py
- tests/integration/proxies/test_fr_006_010_proxy_generation.py
- tests/integration/ingest/test_fr_002_exiftool_metadata_batch_mode.py
- scripts/verify_system_deps.sh

## External Docs Fetched
- None for this step (existing project requirements and dependency docs loaded).

## Components
- ImageMagick adapter component (still + HEIC conversion contract)
- RawTherapee adapter component (RAW conversion contract)
- Proxy orchestration component (deterministic per-item accounting)
- Proxy integration test component (FR-mapped RED/GREEN coverage)

## Constraints
- Approval required before implementation commands and edits
- TDD required: RED tests first
- Continue-on-error accounting must be deterministic and reconcilable
- External tools are critical path dependencies with actionable failures
- Stop on failures and ask before any fixes

## Exit Criteria
- [ ] RED tests added for FR-006/007/008 slice-1 contracts and failing as expected
- [ ] GREEN implementation passes targeted proxy integration suite
- [ ] Deterministic per-item failure reason accounting implemented for proxy run outcomes
- [ ] Quality gates pass: black + ruff + mypy + full pytest
- [ ] Lessons learned updated before commit and before PR
