# Task Context: FR-022 Query Docs Final Invalid Examples

Session ID: 2026-03-29-fr-022-query-docs-final-invalid-examples
Created: 2026-03-29T07:32:52-05:00
Status: in_progress

## Current Request
Continue the next narrow query slice using the existing project process. Create a new feature branch, then add RED docs-smoke tests only for a final FR-022 docs-only slice that promotes already-validated malformed query diagnostics into the Query Grammar v1 behavior document.

## Context Files (Standards to Follow)
- .opencode/context/core/standards/code-quality.md
- .opencode/context/core/standards/test-coverage.md
- .opencode/context/core/standards/documentation.md
- .opencode/context/project-intelligence/living-notes.md

## Reference Files (Source Material to Look At)
- docs/20260328T223918--query-grammar-v1-behavior__projects.md
- tests/integration/query/test_fr_022_query_behavior_docs.py
- tests/integration/query/test_fr_017_021_query_grammar_validation.py
- src/rapidcull/query_grammar.py

## External Docs Fetched
None.

## Components
- Final FR-022 invalid-example documentation expansion
- Docs-smoke validation for additional invalid documented examples
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
- [ ] RED docs-smoke tests added for final FR-022 invalid-example coverage
- [ ] No documentation implementation changes made yet
- [ ] Execution paused before running tests, awaiting approval
