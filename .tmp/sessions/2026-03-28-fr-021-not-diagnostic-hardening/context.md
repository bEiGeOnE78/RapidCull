# Task Context: FR-021 NOT Diagnostic Hardening

Session ID: 2026-03-28-fr-021-not-diagnostic-hardening
Created: 2026-03-28T21:44:07-05:00
Status: in_progress

## Current Request
After merging the grouped-expression diagnostics slice, continue the next narrow RapidCull query-grammar slice using the existing project process. Create a new feature branch, then add RED tests only for malformed unary/grouped-start diagnostics centered on `NOT)`.

## Context Files (Standards to Follow)
- .opencode/context/core/standards/code-quality.md
- .opencode/context/core/standards/test-coverage.md
- .opencode/context/project-intelligence/living-notes.md
- docs/lessons-learned/20260328T211809--fr-021-grouped-expression-diagnostics-hardening-lessons-learned__projects.md

## Reference Files (Source Material to Look At)
- src/rapidcull/query_grammar.py
- tests/integration/query/test_fr_017_021_query_grammar_validation.py

## External Docs Fetched
None.

## Components
- Query grammar unary/grouped-start diagnostics
- Requirement-mapped integration tests
- Lessons-learned artifact before commit

## Constraints
- Approval required before any bash/write/edit step
- Create and work on a feature branch, not `main`
- Keep the slice narrow
- Write RED tests first
- After adding RED tests, stop before running them until approved
- Before calling the slice complete later, run focused tests, full pytest, black --check, ruff check, and mypy
- Capture lessons learned before commit/PR

## Exit Criteria
- [ ] RED tests added for `NOT)` malformed unary/grouped-start diagnostics
- [ ] No implementation changes made yet
- [ ] Execution paused before running tests, awaiting approval
