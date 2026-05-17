# Task Context: Query Grammar v1 Parser Foundation

Session ID: 2026-03-27-query-parser-foundation
Created: 2026-03-27T00:00:00Z
Status: in_progress

## Current Request
Implement the next development step for RapidCull using the project development process. Start from a feature branch and build a narrow Query Grammar v1 slice for FR-017..FR-021: parser + validation foundation only, no execution/API/UI yet.

## Context Files (Standards to Follow)
- .opencode/context/core/standards/code-quality.md
- .opencode/context/core/standards/test-coverage.md
- .opencode/context/project-intelligence/technical-domain.md
- .opencode/context/project-intelligence/business-tech-bridge.md
- .opencode/context/project-intelligence/living-notes.md
- .opencode/context/project-intelligence/decisions/pipeline-contracts.md
- .opencode/context/project-intelligence/decisions/runtime-tooling.md

## Reference Files (Source Material to Look At)
- docs/20260307T080227--photo-library-requirements__projects.md
- docs/20260307T080227--photo-library-acceptance-tests__projects.md
- pyproject.toml
- src/rapidcull/models.py
- src/rapidcull/ingest.py
- src/rapidcull/galleries.py
- tests/integration/ingest/test_fr_001_005_ingest_identity_summary.py
- tests/integration/galleries/test_fr_013_gallery_source_selection_modes.py

## External Docs Fetched
- None

## Components
- Query models — typed AST nodes and validation error/result payloads
- Query parser — tokenization and parse flow for fields, operators, boolean logic, and parentheses
- Query validation — semantic checks for field support, operator compatibility, and value/date format errors
- Requirement-mapped tests — deterministic FR-017..FR-021 coverage for valid and invalid queries

## Constraints
- Parser + validation only; do not implement execution, DB filtering, API endpoints, or UI wiring
- Follow pure-function, small-module, explicit-input/output patterns
- Match existing typed dataclass conventions used in `src/rapidcull/models.py`
- Keep behavior deterministic and errors actionable
- Use pytest, black, ruff, and mypy as validation gates
- Treat FR-022 documentation/example execution as out of scope for this first slice

## Exit Criteria
- [ ] Typed query models exist for parser/validation output
- [ ] Valid grammar parses for required fields, operators, boolean logic, and parentheses
- [ ] Invalid queries return actionable validation errors for unknown fields, unsupported operators, malformed values, and bad dates
- [ ] Requirement-mapped tests cover FR-017..FR-021 foundation behavior
- [ ] Quality gates pass for the slice scope

## Progress
- [x] Session initialized
- [ ] RED tests written
- [ ] Parser/validation implementation complete
- [ ] Quality gates run
