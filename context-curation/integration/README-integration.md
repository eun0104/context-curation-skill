# How the pieces fit

Curation has exactly two targets, and they are the two **control surfaces** of the project's
memory:

```
                    ┌─────────────────────────────────────────┐
                    │            READ PATH                    │
                    │   AGENTS.md  — what the agent reads,    │
                    │                and when                 │
                    └────────────────────┬────────────────────┘
                                         │ points to
                                         ▼
        ┌──────────────────────────────────────────────────────────┐
        │              L2 knowledge layer  (the medium)            │
        │   decisions · architecture · domain · rules · reference  │
        └──────────────────────────────────────────────────────────┘
                                         ▲
                                         │ writes into
                    ┌────────────────────┴────────────────────┐
                    │            WRITE PATH                   │
                    │   docs/handoff-spec.md — what handoff   │
                    │            captures, and how often      │
                    └─────────────────────────────────────────┘

                    ┌─────────────────────────────────────────┐
                    │   context-curation tunes BOTH surfaces  │
                    │   every ~5 sessions                     │
                    └─────────────────────────────────────────┘
```

The L2 layer is not a third target — it is the storage the two surfaces address. Tuning
AGENTS.md means deciding what it should point at, so the layer comes along necessarily.

## Division of labour

| Skill | Runs | Writes | Restructures |
|---|---|---|---|
| `session-context-init` | Session 1 only | `AGENTS.md`, `plan.md` | — |
| `session-handoff` | Every session end | `handoff.md`, `session-log.md`, whatever the spec lists | Never |
| `context-curation` | Every ~5 sessions | `AGENTS.md`, `handoff-spec.md`, L2 docs | **Only this one** |

Keeping restructuring in exactly one skill is what makes the doc layer reviewable: when
something changes shape, there is only one place it could have come from.

## Why init is out of scope

`session-context-init` has finished running before curation ever fires — there is no time window
in which curation could usefully adjust it, and the two never overlap on a project.

This is also why init should deliberately **not** create an L2 layer. At session 1 it is not yet
knowable whether a project needs a gotchas file, an invariants file, or a theory ledger; that
depends on what the project turns out to be like. Pre-creating empty docs is worse than leaving
them out — they get pointed at, read, found empty, and quietly stop being trusted. Curation's
bootstrap mode builds the layer later, from evidence, when the shape of the real friction is known.
