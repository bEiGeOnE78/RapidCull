<!-- Context: project-intelligence/notes | Priority: high | Version: 2.13 | Updated: 2026-03-29 -->

# Living Notes

> Active issues, technical debt, open questions, and insights that don't fit elsewhere. Keep this alive.

## Quick Reference

- **Purpose**: Capture current state, problems, and open questions
- **Update**: Weekly or when status changes
- **Archive**: Move resolved items to bottom with status

## Technical Debt

| Item | Impact | Priority | Mitigation |
|------|--------|----------|------------|
| Python runtime not consistently pinned to 3.11 in local setup | Packaging/editable installs fail when using 3.10, causing avoidable setup churn | High | Enforce pyenv + project venv preflight in bootstrap and checklist |
| Bootstrap script creates a 3.10 venv when default python is 3.10 | FR implementation flow breaks despite valid code due to environment mismatch | High | Update bootstrap docs/script to prefer python3.11 and fail fast when unavailable |

### Technical Debt Details

**Environment preflight drift (3.10 vs 3.11)**  
*Priority*: High  
*Impact*: TDD cycles stall during tool setup (`pip install -e .[dev]`, pytest invocation) instead of validating requirements.  
*Root Cause*: Project metadata requires Python >=3.11, but local interpreter defaults can be 3.10.  
*Proposed Solution*: Add explicit environment preflight to docs + scripts: verify `.venv/bin/python --version` is 3.11+ before any development task.  
*Effort*: Small  
*Status*: Acknowledged

## Open Questions

| Question | Stakeholders | Status | Next Action |
|----------|--------------|--------|-------------|
| Should `scripts/bootstrap.sh` hard-fail when Python <3.11 is detected? | Engineering | Open | Decide strictness policy and update script accordingly |
| Should test/dev dependencies move into `[project.optional-dependencies] dev` as full source of truth for bootstrap? | Engineering | Open | Align bootstrap install path with pyproject extras |

### Open Question Details

**Bootstrap strictness for Python version**  
*Context*: Current process allows partial setup with 3.10, then fails later in editable installs and tooling alignment.  
*Stakeholders*: Engineering team  
*Options*: (a) hard-fail immediately on <3.11, (b) warn and continue, (c) auto-attempt pyenv path.  
*Timeline*: Before FR-004..005 implementation starts.  
*Status*: Open

## Known Issues

| Issue | Severity | Workaround | Status |
|-------|----------|------------|--------|
| `pytest` not found when shell PATH and venv diverge | Medium | Use `.venv/bin/python -m pytest` consistently | Known |
| pyenv Python build may miss ssl/readline/bz2 modules without OS build deps | High | Install required apt build dependencies and rebuild pyenv version | Known |

### Issue Details

**Editable install fails under Python 3.10**  
*Severity*: High  
*Impact*: Blocks formatter/linter/test setup and prevents predictable development flow.  
*Reproduction*: Create venv from 3.10 and run `pip install -e ".[dev]"` with `requires-python = ">=3.11"`.  
*Workaround*: Use pyenv 3.11.11, recreate `.venv`, reinstall dependencies.  
*Root Cause*: Interpreter/metadata mismatch.  
*Fix Plan*: Enforce 3.11 preflight in bootstrap/checklists and keep pyenv initialization documented.  
*Status*: Known

## Insights & Lessons Learned

### What Works Well
- Requirement-first RED tests (FR-scoped) keep implementation small and reviewable.
- Explicit approval gates before environment/code changes prevent hidden drift and rework.

### What Could Be Better
- Preflight checks should run before first RED execution to avoid non-functional blockers.
- Bootstrap behavior should align with project metadata (Python >=3.11) to prevent avoidable setup churn.

### Lessons Learned
- Use interpreter-bound commands (`.venv/bin/python -m pytest`, `-m black`, `-m ruff`) for deterministic tool execution.
- Treat environment compatibility as part of test readiness, not as post-failure cleanup.
- Keep FR slices narrow (FR-001..003) to isolate process risks from product logic risks.
- For strict mypy in `src/` layouts, set `mypy_path = "$MYPY_CONFIG_FILE_DIR/src"` alongside `explicit_package_bases = true` to avoid installed-package `py.typed` resolution drift during local checks.
- For FR-012 gallery lifecycle, land filesystem contract first (hard-link creation + master immutability), then layer source-selection modes in later slices.
- For FR-013 gallery source-selection, treat mode→asset resolution as a dedicated slice and keep hard-link execution delegated to the FR-012 baseline path.
- For FR-014 metadata lifecycle, implement deterministic single-gallery JSON rebuild (plus explicit missing-path error) before adding all-gallery orchestration.
- Use dual type-check strategy: keep mypy as blocking quality gate and pyright as advisory for strict-Pylance parity without adding merge friction.
- For FR-014 rebuild-all fanout, orchestrate via the single-gallery primitive to preserve deterministic payload semantics and avoid duplicated metadata logic.
- For FR-015 central index refresh, build one deterministic index artifact from gallery metadata files with stable ordering so UI/API consumers receive predictable state.
- For FR-015 hardening, continue rebuild on per-gallery metadata parse failures and return structured failure summaries for operator remediation.
- For FR-017..021, land query grammar as a parser+validator contract slice before adding execution, API, or UI integration.
- Exact dataclass-equality assertions are effective for locking boolean-precedence and actionable-error contracts in early grammar slices.
- Unknown-field suggestions should be covered explicitly in tests because close-match defaults may be too strict for expected operator guidance.
- For FR-019 numeric fields, apply value typing in semantic validation so grammar parsing stays simple while field contracts tighten incrementally.
- Standalone invalid punctuation should produce explicit invalid-token errors instead of relying on tokenizer fallthrough.
- For FR-021, prefer specific parser diagnostics over generic syntax failures when the intended correction is obvious.
- Trailing boolean operators should fail as missing-expression errors, not as generic EOF token noise.
- Before declaring a slice complete, run both the focused feature-area tests and the full repository pytest suite.
- Doubled operators should be diagnosed as malformed operators, not as missing-value cases.

## Patterns & Conventions

### Code Patterns Worth Preserving
- Small pure-ish functions in `src/rapidcull/foundation.py` with explicit inputs/outputs; easy to test and reason about.
- FR-marked integration tests in `tests/integration/ingest/test_foundation_requirements.py` directly map behavior to requirements.

### Gotchas for Maintainers
- Recreating `.venv` removes previously installed test tooling; reinstall pytest/playwright stack after venv recreation.
- pyenv install success alone is insufficient—verify `ssl`, `bz2`, and `readline` modules before relying on the interpreter.

## Active Projects

| Project | Goal | Owner | Timeline |
|---------|------|-------|----------|
| FR foundation implementation | Deliver FR-001..003 with passing tests and quality gates | Engineering | In progress |
| FR-004..005 planning | Extend ingest domain with stable IDs and failure reporting | Engineering | Next slice |
| FR-006..008 proxy baseline | Deliver thumbnail/HEIC/RAW proxy baseline behavior with actionable failure paths | Engineering | In progress |
| Foundation separation refactor | Split monolithic foundation module into focused components with parity guarantees | Engineering | In progress |
| FR-009 video proxy baseline | Deliver baseline playable video proxy output modeling | Engineering | In progress |
| FR-010 regeneration selection | Deliver selected-ID and bulk regeneration behavior with invalid-ID reporting | Engineering | In progress |
| Foundation removal + test split | Remove transitional facade and split integration tests by domain | Engineering | In progress |
| FR-011 orphan cleanup report | Deliver stale artifact cleanup with deterministic deletion report | Engineering | In progress |

## Archive (Resolved Items)

Moved here for historical reference. Current team should refer to current notes above.

### Resolved: FR-001..003 slice environment stabilization
- **Resolved**: 2026-03-07
- **Resolution**: Standardized on pyenv Python 3.11.11, recreated project venv, and reran formatting/lint/tests successfully.
- **Learnings**: Environment preflight should be a first-class gate in the workflow.

### Resolved: FR-004..005 lessons gate adoption
- **Resolved**: 2026-03-07
- **Resolution**: Added process requirement that lessons learned are captured before commit and verified before PR creation.
- **Learnings**: Documentation gates reduce process drift and preserve execution knowledge.

### Resolved: Foundation split refactor parity
- **Resolved**: 2026-03-07
- **Resolution**: Refactored `foundation.py` into focused modules while preserving behavior through compatibility re-exports and parity tests.
- **Learnings**: Structural cleanup is safest when treated as a dedicated slice with strict quality gates.

### Resolved: FR-009 video proxy baseline
- **Resolved**: 2026-03-07
- **Resolution**: Added baseline video proxy generation behavior and requirement-mapped integration test coverage.
- **Learnings**: Tight single-requirement slices maintain momentum while preserving quality gate stability.

### Resolved: FR-010 regeneration selection
- **Resolved**: 2026-03-07
- **Resolution**: Added selected-ID and bulk regeneration selection behavior with non-blocking invalid-ID reporting.
- **Learnings**: Explicit mode/result modeling keeps orchestration behavior clear and testable.

### Resolved: foundation facade removal and test split
- **Resolved**: 2026-03-07
- **Resolution**: Removed `src/rapidcull/foundation.py` and split monolithic integration tests into domain-focused files.
- **Learnings**: Temporary compatibility layers should be retired quickly once module boundaries stabilize.

### Resolved: FR-011 orphan cleanup report
- **Resolved**: 2026-03-07
- **Resolution**: Added orphan artifact cleanup behavior and report model with deleted counts/paths.
- **Learnings**: Explicit cleanup contracts simplify safe artifact lifecycle operations.

### Resolved: FR-012 hard-link gallery baseline
- **Resolved**: 2026-03-07
- **Resolution**: Added hard-link gallery creation baseline and integration verification that links share inode/device while masters remain unmodified.
- **Learnings**: Filesystem-contract-first slicing keeps gallery lifecycle requirements small, deterministic, and safe to extend.

### Resolved: FR-013 gallery source-selection modes
- **Resolved**: 2026-03-08
- **Resolution**: Added query/picks/face-samples gallery source-selection orchestration with valid empty-gallery behavior for no-match mode outputs.
- **Learnings**: Separating source selection from link creation keeps gallery lifecycle evolution modular and minimizes regression risk.

### Resolved: FR-014 single-gallery metadata rebuild
- **Resolved**: 2026-03-08
- **Resolution**: Added deterministic `gallery.json` rebuild for a single gallery with explicit missing-path error behavior.
- **Learnings**: Landing single-entity rebuild semantics first reduces risk and creates a stable primitive for later all-gallery fanout.

### Resolved: FR-014 rebuild-all galleries metadata
- **Resolved**: 2026-03-08
- **Resolution**: Added rebuild-all orchestration that iterates gallery directories and delegates to the single-gallery rebuild primitive.
- **Learnings**: Composed fanout over a tested primitive keeps behavior consistent and minimizes regression risk.

### Resolved: FR-015 galleries index refresh baseline
- **Resolved**: 2026-03-08
- **Resolution**: Added deterministic `galleries_index.json` rebuild from current per-gallery metadata files.
- **Learnings**: Treating the index as a derived artifact simplifies refresh logic and keeps central UI/API state consistent with gallery metadata.

### Resolved: FR-015 index hardening (invalid metadata continuation)
- **Resolved**: 2026-03-08
- **Resolution**: Added continue-on-error behavior for invalid gallery metadata JSON and expanded rebuild summaries with processed/skipped/failed counts plus per-gallery failures.
- **Learnings**: Non-blocking partial-failure handling preserves useful index output while still surfacing actionable remediation details.

### Resolved: FR-016 slice 1 gallery mutation security baseline
- **Resolved**: 2026-03-13
- **Resolution**: Added gallery rename/delete mutation primitives with allowlist enforcement and explicit traversal/out-of-scope rejection.
- **Learnings**: Enforcing scope validation before filesystem mutations keeps gallery lifecycle operations safe while preserving narrow, testable function boundaries.

### Resolved: FR-016 slice 2 gallery mutation structured error contracts
- **Resolved**: 2026-03-13
- **Resolution**: Standardized gallery rename/delete outcomes to deterministic typed success/error payloads and expanded FR-016 security edge-case coverage.
- **Learnings**: Structured rejection contracts (`ok` + code/message/path) improve operator clarity and reduce ambiguity compared with mixed exception-only signaling for expected policy rejections.

### Resolved: dependency alignment for bootstrap and system tooling
- **Resolved**: 2026-03-13
- **Resolution**: Aligned bootstrap with `pyproject.toml` dev extras, added Python 3.11 preflight, and introduced explicit Linux media/metadata system dependency verification script.
- **Learnings**: Using a single dependency source-of-truth plus explicit system-tool preflight prevents setup drift and reduces TDD friction.

### Resolved: FR-002 ExifTool batch-mode metadata extraction foundation (slice 1)
- **Resolved**: 2026-03-14
- **Resolution**: Added ExifTool batch extraction adapter foundation, ingest integration seam, real-tool integration coverage, and canonical metadata normalization (`file_type`, `capture_datetime`, `camera_make`, `camera_model`).
- **Learnings**: Critical system-tool tests should fail fast when dependencies are missing, and normalized canonical metadata contracts are more resilient than asserting raw ExifTool group-specific keys.

### Resolved: FR-002 ExifTool hardening (slice 2)
- **Resolved**: 2026-03-14
- **Resolution**: Added explicit per-request tag contract, bounded restart/retry behavior for persistent-process transport failures, and deterministic retry-exhausted failure accounting.
- **Learnings**: Transport timeout handling with buffered text streams should avoid fd-readiness polling shortcuts; marker-based blocking reads with bounded deadlines are more stable for this implementation phase.

### Resolved: FR-006/007/008 slice 1 real-tool adapter seams + HEIF preflight hardening
- **Resolved**: 2026-03-14
- **Resolution**: Added capability-aware ImageMagick/RawTherapee adapter seams in proxy execution, introduced HEIC success/failure deterministic test paths via explicit adapter injection, and hardened `scripts/verify_system_deps.sh` to fail fast when ImageMagick HEIC/HEIF capability is unavailable.
- **Learnings**: Runtime capability detection should drive production defaults, while tests should inject capability states directly to remain deterministic across environments.

### Resolved: FR-006/007/008 slice 2 batch accounting + per-tool summary contract
- **Resolved**: 2026-03-14
- **Resolution**: Added explicit unsupported-media proxy failure accounting (`unsupported_media_type`), extended proxy result contracts with deterministic per-tool summary counts/reasons, and expanded integration coverage for batch accounting and FR-050a reporting behavior.
- **Learnings**: Nested summary counters should use typed helper utilities to satisfy strict mypy gates, and deterministic sorted output ordering should remain explicit before introducing true parallel workers.

### Resolved: FR-006/007/008 slice 3 taxonomy normalization checkpoint
- **Resolved**: 2026-03-14
- **Resolution**: Normalized RAW unavailable failures to canonical reason `rawtherapee_pipeline_unavailable`, normalized still-generation failures to canonical `imagemagick_still_failed` at orchestration boundary, and expanded integration assertions to keep deterministic item/summary reconciliation intact.
- **Learnings**: Reason-taxonomy migrations should be validated at both item-level and tool-summary-level in the same slice to avoid drift.

### Resolved: FR-006/007/008 slice 3b RAW subprocess-detail normalization guardrail
- **Resolved**: 2026-03-15
- **Resolution**: Added RAW reason normalization guardrail so non-canonical adapter/tool detail reasons map to `rawtherapee_failed` while preserving canonical `rawtherapee_pipeline_unavailable`; tool-summary reason accounting now mirrors item-level normalized reasons.
- **Learnings**: Orchestration-level normalization is an effective boundary to prevent subprocess-detail leakage without constraining adapter-internal diagnostics.

### Resolved: FR-006/007/008 slice 3c RAW subprocess seam checkpoint
- **Resolved**: 2026-03-15
- **Resolution**: Added concrete RAW adapter subprocess seam (`_run_command`) with command-shape verification tests, preserved canonical non-zero mapping to `rawtherapee_failed`, and stabilized generic orchestration tests via deterministic adapter injection.
- **Learnings**: Adapter seam patching is more robust than module-level subprocess patching for incremental subprocess rollout under strict deterministic test contracts.

### Resolved: FR-006/007/008 slice 3d ImageMagick subprocess seam checkpoint
- **Resolved**: 2026-03-15
- **Resolution**: Added ImageMagick still-generation subprocess seam (`_run_command`) with adapter-level invocation tests, preserved canonical still-failure mapping (`imagemagick_still_failed`), and stabilized orchestration contract tests through deterministic still-success adapter injection.
- **Learnings**: For external-tool migrations, adapter-level subprocess tests and orchestration-level deterministic contract tests should be kept distinct to avoid environment-coupled false failures.

### Resolved: FR-006/007/008 slice 3e HEIC subprocess path + taxonomy hardening
- **Resolved**: 2026-03-15
- **Resolution**: Added ImageMagick HEIC subprocess execution path gated by HEIF capability, preserved `imagemagick_heif_unsupported` for capability-missing outcomes, and normalized HEIC runtime failures to canonical `imagemagick_heic_failed` across item-level and tool-summary reporting.
- **Learnings**: HEIF should remain fail-fast at preflight while orchestration maintains defensive canonical reason normalization to prevent subprocess-detail taxonomy drift.

### Resolved: FR-007 slice 3f HEIC adapter failure subclasses
- **Resolved**: 2026-03-15
- **Resolution**: Added HEIC adapter-level subprocess failure subclasses (`imagemagick_heic_nonzero_exit`, `imagemagick_heic_execution_error`, `imagemagick_heic_timeout`) while preserving capability-missing `imagemagick_heif_unsupported` behavior and unchanged orchestration-level canonicalization.
- **Learnings**: Adapter-level diagnostics can evolve independently when orchestration remains the canonical contract boundary for deterministic summary/reporting reason taxonomy.

### Resolved: FR-050 proxy run-summary contract baseline
- **Resolved**: 2026-03-15
- **Resolution**: Extended `ProxyGenerationResult` with deterministic run-summary fields (`processed_count`, `skipped_count`, `failed_count`, `elapsed_ms`) and updated proxy integration contracts while preserving FR-050a per-tool summary structure/taxonomy behavior.
- **Learnings**: Equality-heavy deterministic integration suites benefit from explicit stable baseline timing contracts; introducing real elapsed-time semantics should be isolated behind a dedicated seam/slice.

### Resolved: FR-017..021 query parser foundation
- **Resolved**: 2026-03-27
- **Resolution**: Added `rapidcull.query_grammar` with typed AST/result models, deterministic boolean parsing, and actionable validation for unknown fields, unsupported operators, bad dates, and mismatched parentheses.
- **Artifact**: `../../../docs/lessons-learned/20260327T000000--fr-017-021-query-parser-foundation-lessons-learned__projects.md`
- **Learnings**: Query should land as a parser+validator contract slice before execution, API, or UI integration.

### Resolved: FR-017..021 query value validation hardening
- **Resolved**: 2026-03-27
- **Resolution**: Added numeric value validation for `iso`, `fnumber`, and `focal`, plus explicit lone-`!` malformed-token handling with actionable `!=` guidance.
- **Artifact**: `../../../docs/lessons-learned/20260327T010000--fr-017-021-query-value-validation-lessons-learned__projects.md`
- **Learnings**: Field-type enforcement should stay in semantic validation, and invalid punctuation should never be allowed to stall tokenization.

### Resolved: FR-021 query error diagnostics hardening
- **Resolved**: 2026-03-27
- **Resolution**: Added dedicated actionable errors for missing values after operators, trailing `AND`/`OR`, and leading `AND`/`OR` placement mistakes.
- **Artifact**: `../../../docs/lessons-learned/20260327T020000--fr-021-query-error-diagnostics-lessons-learned__projects.md`
- **Learnings**: Parser diagnostics should name the exact recovery action when the malformed grammar pattern is obvious.

### Resolved: FR-021 query diagnostics hardening part 2
- **Resolved**: 2026-03-27
- **Resolution**: Added dedicated actionable errors for unmatched closing `)` and doubled-operator forms such as `==` and `>>`.
- **Artifact**: `../../../docs/lessons-learned/20260327T030000--fr-021-query-diagnostics-part-2-lessons-learned__projects.md`
- **Learnings**: Parser slices are only complete after both focused tests and the full repo pytest suite pass.

### Resolved: FR-022 query behavior documentation baseline
- **Resolved**: 2026-03-28
- **Resolution**: Added a baseline Query Grammar v1 behavior document covering the current parser/validator contract plus a docs-smoke test that verifies documented examples still match `parse_query` behavior.
- **Artifact**: `../../../docs/lessons-learned/20260328T223918--fr-022-query-behavior-docs-lessons-learned__projects.md`
- **Learnings**: Documentation requirements are safer when example queries are machine-checkable against the current parser contract instead of free-form prose alone.

### Resolved: FR-022 query behavior documentation expansion
- **Resolved**: 2026-03-29
- **Resolution**: Expanded the Query Grammar v1 behavior document with additional machine-checkable valid and invalid examples covering more of the current parser/validator contract, while keeping execution semantics out of scope.
- **Artifact**: `../../../docs/lessons-learned/20260329T070703--fr-022-query-docs-expansion-lessons-learned__projects.md`
- **Learnings**: Follow-up documentation slices are safest when they promote already-validated parser cases into executable examples rather than inventing new behavior in prose.

### Resolved: FR-022 query docs final invalid-example coverage
- **Resolved**: 2026-03-29
- **Resolution**: Added the remaining high-signal malformed-query examples to the Query Grammar v1 behavior document so `missing_value`, `missing_group_expression`, `unexpected_closing_parenthesis`, and `invalid_operator` are now machine-checkable documentation cases.
- **Artifact**: `../../../docs/lessons-learned/20260329T073252--fr-022-query-docs-final-invalid-examples-lessons-learned__projects.md`
- **Learnings**: Final documentation passes are safest when they promote already-validated parser diagnostics instead of widening scope into new behavior or execution semantics.

### Resolved: Query Evaluation Contract v1 baseline
- **Resolved**: 2026-03-29
- **Resolution**: Added a spec-only Query Evaluation Contract v1 document defining record-level evaluation semantics for the existing query AST, including comparison rules, boolean behavior, missing-field policy, and canonical match/non-match examples.
- **Artifact**: `../../../docs/lessons-learned/20260329T080544--query-evaluation-contract-v1-lessons-learned__projects.md`
- **Learnings**: Post-parser query work is safer when evaluator semantics are explicitly specified before implementation, keeping API/UI/runtime concerns out of scope until the contract is stable.

### Resolved: Query Evaluation Contract v1 semantics clarification
- **Resolved**: 2026-03-29
- **Resolution**: Clarified the evaluation contract for case-insensitive text comparisons, multi-value `person`/`keyword` handling, exact `~` substring semantics, and empty-vs-missing text-field behavior, with updated spec-smoke coverage and canonical examples.
- **Artifact**: `../../../docs/lessons-learned/20260329T082637--query-evaluation-semantics-v1-lessons-learned__projects.md`
- **Learnings**: A narrow follow-up decision slice is effective when a baseline contract exists but still leaves evaluator-critical semantics implicit.

### Resolved: Query evaluator baseline v1
- **Resolved**: 2026-03-29
- **Resolution**: Added the first pure single-record query evaluator baseline for the existing AST with boolean composition, case-insensitive text matching, multi-value text support, ordered comparisons, and missing/empty-field non-match behavior.
- **Artifact**: `../../../docs/lessons-learned/20260329T090557--query-evaluator-baseline-v1-lessons-learned__projects.md`
- **Learnings**: Once evaluator semantics are locked in the contract, a narrow pure-function implementation slice can land quickly with strong parser-aligned coverage and full validation gates.

### Resolved: Query stale doc cleanup v1
- **Resolved**: 2026-03-31
- **Resolution**: Corrected the stale canonical Query Evaluation Contract v1 example so `person=bob` now matches the approved and implemented any-value behavior for multi-value equality, and tightened the doc verification coverage around that example.
- **Artifact**: `../../../docs/lessons-learned/20260331T150919--query-stale-doc-cleanup-v1-lessons-learned__projects.md`
- **Learnings**: Doc-only cleanup slices still benefit from RED verification and full validation when the documentation is treated as a machine-checked contract artifact.

## Onboarding Checklist

- [ ] Review known technical debt and understand impact
- [ ] Know what open questions exist and who's involved
- [ ] Understand current issues and workarounds
- [ ] Be aware of patterns and gotchas
- [ ] Know active projects and timelines
- [ ] Understand the team's priorities

## Process Gates

- [ ] For each implementation slice, add/update lessons learned **before commit**.
- [ ] Before opening a PR, verify lessons learned are present in this file or linked from a `docs/lessons-learned/` entry.

## Related Files

- `decisions-log.md` - Past decisions that inform current state
- `business-domain.md` - Business context for current priorities
- `technical-domain.md` - Technical context for current state
- `business-tech-bridge.md` - Context for current trade-offs
- `../../../docs/lessons-learned/` - Detailed slice-level lessons learned artifacts
