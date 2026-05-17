# Task Context: Query Evaluation Semantics v1

Session ID: 2026-03-29-query-evaluation-semantics-v1
Created: 2026-03-29T08:26:37-05:00
Status: in_progress

## Current Request
Continue work on RapidCull using the existing project process. Use ContextScout first, propose a narrow next slice, and—if approved and on `main`—create a new feature branch before implementation. Recommended next step: a small decision/spec slice to resolve remaining evaluator ambiguities before implementation, especially text case sensitivity for `=`, `!=`, `~`, whether `keyword` / `person` evaluation is single-value or multi-value, exact `~` matching semantics, and missing-vs-empty metadata semantics if relevant.

## Context Files (Standards to Follow)
- `.opencode/context/core/standards/code-quality.md`
- `.opencode/context/core/standards/test-coverage.md`
- `.opencode/context/core/standards/documentation.md`
- `.opencode/context/project-intelligence/technical-domain.md`
- `.opencode/context/project-intelligence/living-notes.md`
- `.opencode/context/project-intelligence/decisions-log.md`
- `.opencode/context/project-intelligence/decisions/runtime-tooling.md`
- `.opencode/context/project-intelligence/decisions/pipeline-contracts.md`
- `.opencode/context/core/workflows/feature-breakdown.md`
- `.opencode/context/core/workflows/component-planning.md`

## Reference Files (Source Material to Look At)
- `src/rapidcull/query_grammar.py`
- `tests/integration/query/test_fr_017_021_query_grammar_validation.py`
- `tests/integration/query/test_fr_022_query_behavior_docs.py`
- `tests/integration/query/test_query_evaluation_contract_v1.py`
- `docs/20260328T223918--query-grammar-v1-behavior__projects.md`
- `docs/20260329T080544--query-evaluation-contract-v1__projects.md`
- `docs/lessons-learned/20260329T080544--query-evaluation-contract-v1-lessons-learned__projects.md`

## External Docs Fetched
- None

## Components
- Query evaluator semantics decisions
- Query evaluation contract doc updates
- Query spec-smoke test updates

## Constraints
- Spec-only slice; do not implement evaluator runtime behavior in this slice.
- Keep parser grammar/diagnostics behavior unchanged unless a doc-test gap requires clarification only.
- Write RED spec-smoke coverage first.
- Do not include unrelated untracked artifacts such as `.tmp/` noise or stray external paths in later commit/PR staging.
- Before calling the slice complete, run focused query tests, full pytest, `black --check .`, `ruff check .`, and `mypy src`.
- Capture lessons learned before commit/PR and update `.opencode/context/project-intelligence/living-notes.md` before PR creation when required.

## Exit Criteria
- [ ] Evaluation contract explicitly defines text case sensitivity for `=`, `!=`, and `~`.
- [ ] Evaluation contract explicitly defines whether `person` and `keyword` are single-value or multi-value fields.
- [ ] Evaluation contract explicitly defines exact `~` semantics.
- [ ] Evaluation contract explicitly clarifies missing-vs-empty metadata behavior if relevant.
- [ ] Focused spec-smoke tests cover the new semantics.
