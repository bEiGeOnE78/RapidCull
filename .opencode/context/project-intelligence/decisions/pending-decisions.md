<!-- Context: project-intelligence/decisions/pending | Priority: high | Version: 1.0 | Updated: 2026-03-27 -->

# Pending Decisions

> Open choices that are important enough to track but not yet locked.

## Quick Reference

- **Purpose**: Keep unresolved decisions visible and actionable
- **Update When**: A new major open choice appears or an item is resolved
- **Rule**: Move decided items into the appropriate topic file

## Current Pending Decisions

| Topic | Status | Why It Matters | Next Action |
|------|--------|----------------|-------------|
| API runtime/framework | Pending | Needed for `/api/v1`, envelopes, and job endpoints | Choose implementation approach when service layer work begins |
| Job orchestration model | Pending | Long-running ingest/proxy/gallery operations require durable status handling | Define job execution/storage strategy before API orchestration slice |
| Adaptive parallelism rollout | Under Review | NFRs call for configurable worker behavior and deterministic accounting | Decide execution model and contract boundaries before parallel worker implementation |
| Face-recognition runtime rollout | Pending | InsightFace/onnxruntime and CV pipeline choices affect runtime footprint and hardware assumptions | Confirm first implementation slice and dependency posture |
| CI/CD baseline | Pending | The repo needs clean-environment validation and repeatable automation | Decide minimal workflow once local implementation slices stabilize |

## Maintenance Notes

- Keep this file short and current
- When a choice is made, copy the final rationale into the correct decision file
- If an item becomes obsolete, remove it rather than leaving stale backlog noise

## Related Files

- `navigation.md` - Decision-area routes
- `../living-notes.md` - Current pressure, debt, and open questions
- `../technical-domain.md` - Current-state technical picture
