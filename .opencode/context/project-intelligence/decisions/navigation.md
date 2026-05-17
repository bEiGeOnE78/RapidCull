<!-- Context: project-intelligence/decisions/nav | Priority: high | Version: 1.0 | Updated: 2026-03-27 -->

# Decisions Navigation

> Quick routes through RapidCull decision records.

## Structure

```text
project-intelligence/decisions/
├── navigation.md              # This file
├── architecture.md            # Architecture and state model
├── runtime-tooling.md         # Runtime and toolchain choices
├── pipeline-contracts.md      # Pipeline behavior contracts
├── security-operations.md     # Safety and mutation boundaries
└── pending-decisions.md       # Open decisions and next actions
```

## Quick Routes

| Task | Path |
|------|------|
| **Architecture rationale** | `architecture.md` |
| **Python/tooling choices** | `runtime-tooling.md` |
| **Pipeline behavior rules** | `pipeline-contracts.md` |
| **Security boundaries** | `security-operations.md` |
| **Pending choices** | `pending-decisions.md` |

## By Concern

**Architecture** → Deployment posture, monolith shape, data/state model  
**Runtime & Tooling** → Python baseline, system tools, validation gates  
**Pipeline Contracts** → Determinism, failure handling, testing contract  
**Security & Operations** → Path safety, subprocess safety, mutation controls  
**Pending** → Under-review choices and next actions

## Related Context

- **Decision index** → `../decisions-log.md`
- **Technical domain** → `../technical-domain.md`
- **Current state** → `../living-notes.md`
