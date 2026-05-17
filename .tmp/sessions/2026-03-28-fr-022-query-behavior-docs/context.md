# Task Context: FR-022 Query Behavior Documentation Baseline

Session ID: 2026-03-28-fr-022-query-behavior-docs
Created: 2026-03-28T22:39:18-05:00
Status: in_progress

## Current Request
After completing the FR-021 parser-diagnostics sequence, start the next narrow query slice using the existing project process. Create a new feature branch, then add RED docs-smoke tests only for an FR-022 baseline query behavior document covering currently implemented parser/validator behavior.

## Context Files (Standards to Follow)
- .opencode/context/core/standards/code-quality.md
- .opencode/context/core/standards/test-coverage.md
- .opencode/context/core/standards/project-intelligence-management.md
- .opencode/context/project-intelligence/living-notes.md

## Reference Files (Source Material to Look At)
- docs/20260307T080227--photo-library-requirements__projects.md
- docs/20260307T080227--photo-library-acceptance-tests__projects.md
- src/rapidcull/query_grammar.py
- tests/integration/query/test_fr_017_021_query_grammar_validation.py

## External Docs Fetched
None.

## Components
- FR-022 query behavior document
- Docs-smoke validation for documented examples
- Lessons-learned artifact before commit

## Constraints
- Approval required before any bash/write/edit step
- Create and work on a feature branch, not `main`
- Keep the slice narrow
- Add RED tests first
- After adding RED tests, stop before running them until approved
- Document current parser/validator behavior only; do not invent query execution semantics
- Before calling the slice complete later, run focused tests, full pytest, black --check, ruff check, and mypy
- Capture lessons learned before commit/PR

## Exit Criteria
- [ ] RED tests added for FR-022 docs-smoke coverage of documented query examples
- [ ] No documentation implementation written yet
- [ ] Execution paused before running tests, awaiting approval
