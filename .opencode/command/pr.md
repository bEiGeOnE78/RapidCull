---
description: Create pull requests with explicit approval gates
---

# PR Command (Approval-First)

## Main Branch Exception

If current branch is `main`, do not create a PR. Report that PR is not required on `main` and exit.

Follow this exact sequence:

1. Summarize branch changes and include lessons-learned artifact path.
2. Ask: **"Approve PR creation?"**
3. Only after approval, create the PR.
4. Ask: **"Approve merge and delete feature branch?"**
5. Only after approval:
   - merge the PR
   - delete local and remote feature branch
6. After branch cleanup:
   - propose the next FR/slice
   - ask: **"Approve starting next slice?"**

## Rules

- Never create PR without explicit approval.
- Never merge/delete branch without explicit approval.
- Always reference lessons-learned artifact in PR notes/checklist.
