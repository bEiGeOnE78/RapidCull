# Task Context: Query Evaluator Baseline v1

Session ID: 2026-03-29-query-evaluator-baseline-v1
Created: 2026-03-29T09:05:57-05:00
Status: in_progress

## Current Request
Continue with the next slice after merging the query evaluation semantics clarification. The next narrow slice is the first evaluator implementation baseline against the clarified Query Evaluation Contract v1. Keep the scope to a pure single-record evaluator and follow the existing approval-first process.

## Context Files (Standards to Follow)
- `.opencode/context/core/standards/code-quality.md`
- `.opencode/context/core/standards/test-coverage.md`
- `.opencode/context/project-intelligence/living-notes.md`
- `.opencode/context/project-intelligence/technical-domain.md`
- `.opencode/context/project-intelligence/decisions/pipeline-contracts.md`
- `.opencode/context/project-intelligence/decisions/pending-decisions.md`

## Reference Files (Source Material to Look At)
- `src/rapidcull/query_grammar.py`
- `src/rapidcull/models.py`
- `tests/integration/query/test_fr_017_021_query_grammar_validation.py`
- `tests/integration/query/test_query_evaluation_contract_v1.py`
- `docs/20260328T223918--query-grammar-v1-behavior__projects.md`
- `docs/20260329T080544--query-evaluation-contract-v1__projects.md`

## External Docs Fetched
- None

## Components
- Pure single-record evaluator core
- Focused evaluator integration tests
- Slice lessons/process updates

## Constraints
- Keep this slice to record-by-record boolean evaluation only.
- Do not add collection filtering, API wiring, UI wiring, job orchestration, or ranking behavior.
- Trust the existing parser AST and do not reinterpret grammar precedence.
- Start with RED tests.
- Keep functions small, pure, and easily testable.
- Continue excluding unrelated untracked artifacts from any later commit/PR work.
- Before calling the slice complete, run focused query tests, full pytest, `black --check .`, `ruff check .`, and `mypy src`.

## Exit Criteria
- [ ] A pure public evaluator API exists for one query AST and one normalized record.
- [ ] Evaluator supports `QueryComparison`, `AND`, `OR`, and `NOT`.
- [ ] Evaluator matches the clarified text semantics for `person`, `keyword`, `camera`, and `lens`.
- [ ] Evaluator matches ordered comparison semantics for `date`, `iso`, `fnumber`, and `focal`.
- [ ] Missing and empty-field behavior matches the evaluation contract.
- [ ] Focused evaluator tests cover canonical contract examples.
