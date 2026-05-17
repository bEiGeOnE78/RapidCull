<!-- Context: project-intelligence/decisions | Priority: high | Version: 2.0 | Updated: 2026-03-27 -->

# Decisions Log

> Index of RapidCull decision records. Start here, then follow the topic files for full rationale.

## Quick Reference

- **Purpose**: Point readers to the right decision area quickly
- **Use When**: You need the why behind a technical or product-shaping choice
- **Statuses**: Decided | Pending | Under Review | Deprecated

## Decision Areas

| Area | File | Covers |
|------|------|--------|
| Architecture | `decisions/architecture.md` | Deployment posture, architecture shape, state model |
| Runtime & Tooling | `decisions/runtime-tooling.md` | Python baseline, external tools, validation gates |
| Pipeline Contracts | `decisions/pipeline-contracts.md` | Determinism, continue-on-error, testing contracts |
| Security & Operations | `decisions/security-operations.md` | Path safety, subprocess safety, mutation boundaries |
| Pending / Under Review | `decisions/pending-decisions.md` | Open choices not yet locked |

## Quick Routes

| What You Need | Path |
|---------------|------|
| **Start with detailed navigation** | `decisions/navigation.md` |
| **Architecture decisions** | `decisions/architecture.md` |
| **Runtime/tooling choices** | `decisions/runtime-tooling.md` |
| **Pipeline behavior contracts** | `decisions/pipeline-contracts.md` |
| **Security/operational boundaries** | `decisions/security-operations.md` |
| **Open decision backlog** | `decisions/pending-decisions.md` |

## Current High-Signal Decisions

- Linux-first, local-first product posture
- Modular Python monolith instead of early service decomposition
- SQLite + JSON + filesystem consistency model
- External media tools behind safe adapter boundaries
- Continue-on-error batch processing with deterministic summaries
- Validated normalized paths and allowlist-based mutation boundaries

## Maintenance Rules

- Add or update a decision when a lasting cross-cutting choice is made
- Keep unresolved questions in `decisions/pending-decisions.md`
- When a decision changes, mark the old one deprecated instead of deleting history
- Update `technical-domain.md` when stack, architecture, or runtime posture changes
- Reflect active uncertainty and follow-up pressure in `living-notes.md`

## Structure

```text
project-intelligence/
├── decisions-log.md          # This file - decision index
└── decisions/
    ├── navigation.md         # Decisions entrypoint
    ├── architecture.md
    ├── runtime-tooling.md
    ├── pipeline-contracts.md
    ├── security-operations.md
    └── pending-decisions.md
```

## Onboarding Checklist

- [ ] Start with `decisions/navigation.md`
- [ ] Know which file holds which class of decision
- [ ] Understand the major architecture and runtime choices
- [ ] Know where pending decisions live
- [ ] Update the relevant topic file when a new decision lands

## Related Files

- `decisions/navigation.md` - Detailed navigation for the decision records
- `technical-domain.md` - Technical implementation affected by these decisions
- `business-tech-bridge.md` - How decisions connect business and technical
- `living-notes.md` - Current open questions that may become decisions
