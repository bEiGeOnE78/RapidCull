<!-- Context: project-intelligence/decisions/pipeline-contracts | Priority: high | Version: 1.0 | Updated: 2026-03-27 -->

# Pipeline Contract Decisions

> Stable decisions about ingest/proxy/gallery behavior and validation style.

## Quick Reference

- **Purpose**: Capture the cross-cutting rules pipelines must preserve
- **Update When**: Run summaries, failure handling, or contract testing strategy changes
- **Scope**: Behavior contracts, not implementation details

## Decision: Continue-on-error by default

**Date**: 2026-03-07  
**Status**: Decided  
**Owner**: Engineering

### Context
Large media libraries should not lose whole-run value because a subset of assets fail.

### Decision
Ingest and proxy pipelines should continue by default when individual assets or tools fail, while recording per-item reasons and final summaries.

### Rationale
This gives operators maximum useful output from long-running jobs.

### Impact
- **Positive**: Partial success remains useful
- **Negative**: Summary/result contracts become more complex
- **Risk**: Failure reporting must stay precise and actionable

## Decision: Deterministic result contracts

**Date**: 2026-03-14  
**Status**: Decided  
**Owner**: Engineering

### Context
Pipeline outputs are heavily verified by integration tests and must remain predictable for operators and future UI/API consumers.

### Decision
Keep stable ordering, canonical reason taxonomy, and explicit processed/skipped/failed accounting in result contracts.

### Rationale
Deterministic outputs reduce flakiness and make failure investigation faster.

### Impact
- **Positive**: Reliable tests and predictable operator output
- **Negative**: Normalization logic must be maintained carefully
- **Risk**: Raw tool-detail leakage can erode contract stability

## Decision: Requirement-mapped integration tests as primary contract guard

**Date**: 2026-03-07  
**Status**: Decided  
**Owner**: Engineering

### Context
Most critical behavior is pipeline-oriented and easier to validate end-to-end than through isolated unit assertions alone.

### Decision
Use FR/NFR-oriented integration tests as the primary guard for externally visible pipeline behavior.

### Rationale
This keeps development aligned with requirements and catches orchestration regressions early.

### Impact
- **Positive**: Strong product-contract coverage
- **Negative**: Tests can be heavier than pure unit suites
- **Risk**: Suites must remain deterministic and environment-aware

## Related Files

- `../technical-domain.md` - Current behavior summary
- `../living-notes.md` - Lessons from completed slices
- `../../../../docs/20260307T080227--photo-library-requirements__projects.md` - Source FR/NFR contracts
