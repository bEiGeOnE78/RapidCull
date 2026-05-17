# Task Context: FR-021 Malformed Boolean-Pair Diagnostics

Session ID: 2026-03-28-fr-021-malformed-boolean-pairs
Created: 2026-03-28T22:17:02-05:00
Status: in_progress

## Current Request
Finish the last narrow RapidCull query-grammar parser-diagnostics slice using the existing project process. Create a new feature branch, then add RED tests only for malformed consecutive boolean operators after a valid left-hand expression.

## Context Files (Standards to Follow)
- .opencode/context/core/standards/code-quality.md
- .opencode/context/core/standards/test-coverage.md
- .opencode/context/project-intelligence/living-notes.md
- docs/lessons-learned/20260328T220839--fr-021-open-group-eof-diagnostics-lessons-learned__projects.md
- docs/lessons-learned/20260328T215531--fr-021-grouped-start-boolean-diagnostics-lessons-learned__projects.md

## Reference Files (Source Material to Look At)
- src/rapidcull/query_grammar.py
- tests/integration/query/test_fr_017_021_query_grammar_validation.py

## External Docs Fetched
None.

## Components
- Query grammar malformed boolean-pair diagnostics
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
- [ ] RED tests added for malformed consecutive boolean-operator sequences after a valid left-hand expression
- [ ] No implementation changes made yet
- [ ] Execution paused before running tests, awaiting approval
