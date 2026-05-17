# Task Context: Query Evaluation Contract v1

Session ID: 2026-03-29-query-evaluation-contract-v1
Created: 2026-03-29T08:05:44-05:00
Status: in_progress

## Current Request
After completing FR-021 parser-diagnostics hardening and FR-022 query behavior documentation, continue with the next narrow query slice using the existing project process. Create a new feature branch, then add RED spec-smoke tests only for a Query Evaluation Contract v1 planning/spec document that defines evaluator semantics for the existing query AST without implementing execution, API, or UI behavior.

## Context Files (Standards to Follow)
- .opencode/context/core/standards/code-quality.md
- .opencode/context/core/standards/test-coverage.md
- .opencode/context/core/standards/documentation.md
- .opencode/context/core/standards/project-intelligence.md
- .opencode/context/project-intelligence/living-notes.md
- .opencode/context/project-intelligence/technical-domain.md
- .opencode/context/project-intelligence/business-tech-bridge.md
- .opencode/context/project-intelligence/decisions/pipeline-contracts.md
- .opencode/context/project-intelligence/decisions/pending-decisions.md
- .opencode/context/core/workflows/feature-breakdown.md

## Reference Files (Source Material to Look At)
- docs/20260328T223918--query-grammar-v1-behavior__projects.md
- docs/20260307T080227--photo-library-requirements__projects.md

## External Docs Fetched
None.

## Components
- Query Evaluation Contract v1 spec doc
- Spec-smoke validation for required sections/examples
- Lessons-learned artifact before commit

## Constraints
- Approval required before any bash/write/edit step
- Create and work on a feature branch, not `main`
- Keep the slice narrow and spec-only
- Add RED tests first
- After adding RED tests, stop before running them until approved
- Do not implement evaluator code, API endpoints, UI behavior, job model, or storage/runtime design
- Before calling the slice complete later, run focused tests, full pytest, black --check, ruff check, and mypy
- Capture lessons learned before commit/PR

## Exit Criteria
- [ ] RED spec-smoke tests added for Query Evaluation Contract v1 document
- [ ] No evaluator implementation written
- [ ] Execution paused before running tests, awaiting approval
