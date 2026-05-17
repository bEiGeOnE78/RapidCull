# Task Context: FR-021 Grouped Expression Diagnostics Hardening

Session ID: 2026-03-28-fr-021-grouped-expression-diagnostics
Created: 2026-03-28T21:18:09-05:00
Status: in_progress

## Current Request
Continue work on RapidCull using the existing project process. Use ContextScout first, propose the narrow slice, get approval, check the current branch and create a new feature branch if on `main`, then add RED tests only for the next recommended slice: FR-021 grouped-expression diagnostics hardening. Stop before running the tests until approved.

## Context Files (Standards to Follow)
- .opencode/context/core/standards/code-quality.md
- .opencode/context/core/standards/test-coverage.md
- .opencode/context/project-intelligence/living-notes.md
- .opencode/context/project-intelligence/technical-domain.md
- .opencode/context/core/workflows/feature-breakdown.md
- .opencode/context/project-intelligence/navigation.md

## Reference Files (Source Material to Look At)
- src/rapidcull/query_grammar.py
- tests/integration/query/test_fr_017_021_query_grammar_validation.py
- docs/lessons-learned/20260327T030000--fr-021-query-diagnostics-part-2-lessons-learned__projects.md
- docs/lessons-learned/20260327T020000--fr-021-query-error-diagnostics-lessons-learned__projects.md
- docs/20260307T091500--photo-library-execution-checklist__projects.md
- docs/20260307T080227--photo-library-test-plan__projects.md

## External Docs Fetched
None.

## Components
- Query grammar grouped-expression diagnostics
- Requirement-mapped integration tests
- Lessons-learned artifact update before commit

## Constraints
- Approval required before any bash/write/edit step
- Create and work on a feature branch, not `main`
- Keep the slice narrow
- Write RED tests first
- After adding RED tests, stop before running them until approved
- Before calling the slice complete later, run focused tests, full pytest, black --check, ruff check, and mypy
- Capture lessons learned before commit/PR

## Exit Criteria
- [ ] RED tests added for `(person=alice AND)`, `(person=alice OR)`, and `()` grouped-expression diagnostics
- [ ] No implementation changes made yet
- [ ] Execution paused before running tests, awaiting approval
