<!-- Context: project-intelligence/nav | Priority: high | Version: 2.0 | Updated: 2026-03-27 -->

# Project Intelligence

> Start here for quick project understanding. These files bridge business and technical domains.

## Structure

```
.opencode/context/project-intelligence/
├── navigation.md              # This file - quick overview
├── business-domain.md         # Business context and problem statement
├── technical-domain.md        # Stack, architecture, technical decisions
├── business-tech-bridge.md    # How business needs map to solutions
├── decisions-log.md           # Decision index and handoff page
├── decisions/                 # Topic-based decision records
│   ├── navigation.md
│   ├── architecture.md
│   ├── runtime-tooling.md
│   ├── pipeline-contracts.md
│   ├── security-operations.md
│   └── pending-decisions.md
└── living-notes.md            # Active issues, debt, open questions
```

## Quick Routes

| What You Need | File | Description |
|---------------|------|-------------|
| Understand the "why" | `business-domain.md` | Problem, users, value proposition |
| Understand the "how" | `technical-domain.md` | Stack, architecture, integrations |
| See the connection | `business-tech-bridge.md` | Business → technical mapping |
| Decision overview | `decisions-log.md` | Decision index and maintenance rules |
| Detailed decision records | `decisions/navigation.md` | Topic-based decision discovery |
| Current state | `living-notes.md` | Active issues and open questions |
| Detailed implementation lessons | `../../../docs/lessons-learned/` | Timestamped slice-level lessons learned artifacts |
| All of the above | Read all files in order | Full project intelligence |

## Usage

**New Team Member / Agent**:
1. Start with `navigation.md` (this file)
2. Read all files in order for complete understanding
3. Follow onboarding checklist in each file

**Quick Reference**:
- Business focus → `business-domain.md`
- Technical focus → `technical-domain.md`
- Decision context → `decisions-log.md`
- Detailed decisions → `decisions/navigation.md`

## Integration

This folder is referenced from:
- `.opencode/context/core/standards/project-intelligence.md` (standards and patterns)
- `.opencode/context/core/system/context-guide.md` (context loading)

See `.opencode/context/core/context-system.md` for the broader context architecture.

## Maintenance

Keep this folder current:
- Update when business direction changes
- Document decisions in `decisions/` and keep `decisions-log.md` as the index
- Review `living-notes.md` regularly
- Keep pending choices current in `decisions/pending-decisions.md`

**Management Guide**: See `.opencode/context/core/standards/project-intelligence-management.md` for complete lifecycle management including:
- How to update, add, and remove files
- How to create new subfolders
- Version tracking and frontmatter standards
- Quality checklists and anti-patterns
- Governance and ownership

See `.opencode/context/core/standards/project-intelligence.md` for the standard itself.
