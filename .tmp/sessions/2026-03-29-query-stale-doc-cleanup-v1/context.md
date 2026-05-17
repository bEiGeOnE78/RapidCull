# Task Context: Query Stale Doc Cleanup v1

Session ID: 2026-03-29-query-stale-doc-cleanup-v1
Created: 2026-03-31T15:09:19-05:00
Status: in_progress

## Current Request
Finish the current follow-up stale-doc cleanup slice after the query evaluator baseline. Keep the scope to the smallest safe documentation correction that reconciles the query evaluation contract with the approved and implemented any-value matching behavior for multi-value equality.

## Context Files (Standards to Follow)
- `.opencode/context/core/standards/documentation.md`
- `.opencode/context/core/standards/project-intelligence-management.md`
- `.opencode/context/project-intelligence/living-notes.md`
- `.opencode/context/project-intelligence/navigation.md`
- `.opencode/context/core/workflows/feature-breakdown.md`

## Reference Files (Source Material to Look At)
- `docs/20260329T080544--query-evaluation-contract-v1__projects.md`
- `docs/lessons-learned/20260329T090557--query-evaluator-baseline-v1-lessons-learned__projects.md`
- `docs/lessons-learned/20260329T082637--query-evaluation-semantics-v1-lessons-learned__projects.md`
- `.opencode/context/project-intelligence/living-notes.md`

## External Docs Fetched
- None

## Components
- Evaluation contract doc correction
- Minimal verification coverage
- Slice lessons/process updates

## Constraints
- Keep this slice doc-only and extremely narrow.
- Primary target is the stale canonical example in the Query Evaluation Contract v1 doc.
- Do not widen into evaluator implementation, parser docs, API/UI docs, or new semantics.
- Continue excluding unrelated local untracked artifacts from later commit/PR work.
- Before calling the slice complete, run the required validation gates.

## Exit Criteria
- [ ] The stale `person=bob` example in the evaluation contract matches the approved any-value multi-value equality rule.
- [ ] Minimal verification covers the corrected canonical example.
- [ ] Required validation gates pass.
