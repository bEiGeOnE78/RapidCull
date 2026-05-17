<!-- Context: project-intelligence/decisions/architecture | Priority: high | Version: 1.0 | Updated: 2026-03-27 -->

# Architecture Decisions

> Stable decisions about RapidCull's overall shape and state model.

## Quick Reference

- **Purpose**: Capture durable architecture choices
- **Update When**: Deployment posture, app shape, or state model changes
- **Status Mix**: Mostly decided, high-impact choices

## Decision: Linux-first, local-first posture

**Date**: 2026-03-07  
**Status**: Decided  
**Owner**: Engineering

### Context
The product targets large personal/local media libraries and depends on Linux-native media tooling.

### Decision
RapidCull is built first for Linux and local/self-hosted execution, with localhost and LAN modes in scope.

### Rationale
This matches the product requirements and reduces platform/toolchain variability during early delivery.

### Impact
- **Positive**: Simpler support matrix and more predictable environment behavior
- **Negative**: No macOS/Windows baseline today
- **Risk**: Future platform expansion will require explicit portability work

## Decision: Modular local-first monolith

**Date**: 2026-03-07  
**Status**: Decided  
**Owner**: Engineering

### Context
The repo currently centers on file processing, metadata handling, and gallery workflows rather than independently deployable services.

### Decision
Keep the application as a modular Python package with focused modules, not early microservices.

### Rationale
This keeps complexity low while preserving clean seams for adapters, models, and orchestration code.

### Impact
- **Positive**: Faster iteration and simpler testing
- **Negative**: Less independent deployment isolation
- **Risk**: Module boundaries must stay disciplined as features grow

## Decision: SQLite + JSON + filesystem consistency model

**Date**: 2026-03-07  
**Status**: Decided  
**Owner**: Engineering

### Context
Requirements split responsibility across durable metadata, UI-friendly derived artifacts, and actual media files.

### Decision
Treat SQLite as canonical metadata state, JSON as derived UI/cache artifacts, and the filesystem as source of truth for media.

### Rationale
This model keeps source media handling safe while giving the UI/API predictable derived artifacts.

### Impact
- **Positive**: Clear boundaries between canonical state, derived state, and media assets
- **Negative**: Rebuild/reconciliation logic is required
- **Risk**: Drift must be detected and repaired explicitly

## Related Files

- `../technical-domain.md` - Current technical snapshot
- `../business-tech-bridge.md` - Why these choices match product goals
- `../living-notes.md` - Current pressure and implementation status
