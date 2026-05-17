<!-- Context: project-intelligence/decisions/runtime-tooling | Priority: high | Version: 1.0 | Updated: 2026-03-27 -->

# Runtime and Tooling Decisions

> Stable decisions about runtime baseline, toolchain choices, and validation gates.

## Quick Reference

- **Purpose**: Explain why the runtime and toolchain look the way they do
- **Update When**: Python baseline, toolchain, or quality gates change
- **Scope**: Runtime requirements and development validation

## Decision: Python 3.11+ baseline

**Date**: 2026-03-07  
**Status**: Decided  
**Owner**: Engineering

### Context
Project metadata, typing expectations, and validation tooling assume a modern Python baseline.

### Decision
Require Python 3.11+ for development and runtime.

### Rationale
This keeps local validation aligned with `pyproject.toml` and reduces compatibility drift.

### Impact
- **Positive**: Consistent tooling behavior and modern typing support
- **Negative**: Older local Python installs fail setup
- **Risk**: Bootstrap drift causes wasted setup time if preflight is weak

## Decision: External media tools behind adapter seams

**Date**: 2026-03-14  
**Status**: Decided  
**Owner**: Engineering

### Context
Metadata extraction and proxy generation depend on mature Linux-native tools.

### Decision
Use ExifTool, ImageMagick, RawTherapee CLI, and FFmpeg behind explicit Python adapter/orchestration boundaries.

### Rationale
This preserves the strengths of those tools while keeping contract normalization and accounting in Python.

### Impact
- **Positive**: Strong media capability without reimplementation
- **Negative**: System dependency preflight is mandatory
- **Risk**: Tool-specific failure details must be normalized at orchestration boundaries

## Decision: Strict validation gates in normal development flow

**Date**: 2026-03-07  
**Status**: Decided  
**Owner**: Engineering

### Context
The repo relies on deterministic behavior and typed contracts across evolving pipeline slices.

### Decision
Treat black, ruff, mypy, and pytest as routine blocking quality gates for implementation slices.

### Rationale
Strict validation catches drift early and supports stable integration-heavy development.

### Impact
- **Positive**: Higher confidence and fewer hidden regressions
- **Negative**: More up-front discipline required
- **Risk**: Environment/setup drift can block productive feedback if not preflighted well

## Related Files

- `../technical-domain.md` - Runtime summary and validation commands
- `../living-notes.md` - Environment and setup debt
- `../../../../pyproject.toml` - Current Python and tool configuration
