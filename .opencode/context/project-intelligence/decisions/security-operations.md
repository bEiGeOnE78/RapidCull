<!-- Context: project-intelligence/decisions/security-operations | Priority: high | Version: 1.0 | Updated: 2026-03-27 -->

# Security and Operations Decisions

> Stable decisions about safe execution boundaries, path handling, and operator-facing safeguards.

## Quick Reference

- **Purpose**: Capture durable safety and operational-boundary decisions
- **Update When**: Path rules, mutation controls, or execution safeguards change
- **Scope**: Security-sensitive and operationally critical behavior

## Decision: Validated normalized paths only

**Date**: 2026-03-13  
**Status**: Decided  
**Owner**: Engineering

### Context
RapidCull works directly with local filesystem paths and external tools, so unsafe path handling would be high risk.

### Decision
Normalize and validate all file/path inputs before use.

### Rationale
This reduces traversal risk, ambiguity, and incorrect out-of-scope mutations.

### Impact
- **Positive**: Safer file operations and clearer policy enforcement
- **Negative**: More explicit validation code is required
- **Risk**: Incomplete normalization would create hidden boundary bugs

## Decision: Safe subprocess execution only

**Date**: 2026-03-14  
**Status**: Decided  
**Owner**: Engineering

### Context
ExifTool, ImageMagick, RawTherapee, and FFmpeg are invoked from the app.

### Decision
Invoke external tools with argument-safe subprocess execution only; do not shell-interpolate user-provided values.

### Rationale
This preserves tool integration while minimizing injection risk.

### Impact
- **Positive**: Safer external-tool execution boundary
- **Negative**: Adapter APIs must stay explicit and disciplined
- **Risk**: Convenience shortcuts would weaken the security model

## Decision: Allowlist-based gallery mutation boundaries

**Date**: 2026-03-13  
**Status**: Decided  
**Owner**: Engineering

### Context
Gallery rename/delete flows mutate filesystem state and must never act on out-of-scope paths.

### Decision
Enforce allowlist checks for gallery mutations and return structured rejection outcomes for invalid or out-of-scope paths.

### Rationale
This keeps destructive operations narrowly scoped and operator-visible.

### Impact
- **Positive**: Safer mutation flows and clearer failure behavior
- **Negative**: More explicit contract handling at API/CLI boundaries
- **Risk**: Policy drift would make filesystem mutations unsafe

## Related Files

- `../technical-domain.md` - Technical constraints and runtime posture
- `../living-notes.md` - FR-016 lessons and current state
- `../../../../docs/20260307T080227--photo-library-requirements__projects.md` - Security-related FRs
