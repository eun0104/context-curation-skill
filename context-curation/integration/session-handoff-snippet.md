# session-handoff — the one edit it needs

`context-curation` tunes handoff's behaviour, but it does that through a project-local spec
file, not by rewriting the skill. So the skill itself needs exactly one permanent change.

## The hook

Add near the top of `session-handoff/SKILL.md`:

```markdown
## Project override

If `docs/handoff-spec.md` exists, read it first and follow it. It defines this project's
document set, cadences, `handoff.md` fields, and session-log entry format, and it overrides
the defaults in this skill wherever the two differ.

The spec is maintained by the `context-curation` skill. Do not edit it during a normal
session — changes there affect every future session and belong in a tuning proposal.
```

That is the whole integration. Everything project-specific lives in the project.

## Why the indirection

Project-specific instructions written into a shared skill leak into unrelated work, and the
leak stays invisible until some other project starts being asked for fields that make no sense
there — by which point the cause is several projects and many sessions away from the symptom.

So the routing is by **blast radius**:

- **Project-specific** (this project's doc set, cadences, fields) → `docs/handoff-spec.md`, written by curation
- **Generalizable** (something every project would want) → noted in the proposal's section G, **applied by you, by hand**

Curation never writes outside the project. That is what makes the shared skill safe to keep
shared: it changes when a person decides it should, having weighed the other projects that
depend on it — not as a side effect of one project's tuning run.

If `session-handoff` is installed project-locally under `.opencode/skill/`, none of this
applies: everything is project-scoped, the spec file is optional, and curation may edit the
SKILL.md directly after archiving the original.

## Defaults worth changing now

Two things in the current setup are worth revisiting at the first tuning run:

- **`decisions.md` is written every session.** A session with no real decision produces a filler entry, and filler entries are what make a decision log stop being worth reading. `on-event` fits it better.
- **Session-log entries are untagged.** Adding `[candidate]` / `[gotcha]` / `[decision]` markers costs nothing at write time and turns every future harvest from a full re-read into a `grep`. See `templates/handoff-spec.md` for the entry format.
