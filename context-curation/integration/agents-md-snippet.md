# AGENTS.md — snippet to add

Add this to the pointer table so the agent knows the curation skill exists and when to
reach for it. Skills are not always auto-triggered by description alone; an explicit
pointer in the always-read layer makes the trigger reliable.

```markdown
## Read on demand
| Read this | When |
|---|---|
| skill `context-curation` | When this file exceeds its budget, when docs contradict each other, when a milestone closes, when no curation state exists after several sessions, or when 5+ sessions have passed since `docs/.curation-state.json` last_tuned |
```

Optionally add a budget note near the top of AGENTS.md so the constraint is visible at
the moment someone is tempted to add a line:

```markdown
<!-- L0 budget: 2000 tokens. Adding a line here requires removing one.
     Run the context-curation skill when over. -->
```
