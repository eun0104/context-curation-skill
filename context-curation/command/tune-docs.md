---
description: Audit and restructure the project's persistent doc layer (AGENTS.md, plan.md, docs/*)
---

Run the `context-curation` skill on this project.

Read `.opencode/skill/context-curation/SKILL.md` (or
`~/.config/opencode/skill/context-curation/SKILL.md` if installed globally) and follow its
run procedure from Step 0.

Two reminders that matter more than the rest:

- Step 5 ends with writing `docs/_tuning-proposal.md` and **stopping**. Do not create, edit,
  move, or archive any other file until the user approves item by item.
- Run `scripts/docs_inventory.py` rather than estimating counts by reading files. The numbers
  drive every decision in the run, and estimating them by eye wastes the context the audit is
  meant to save.

$ARGUMENTS
