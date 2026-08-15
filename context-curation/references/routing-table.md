# Routing Table

Once a fact passes the promotion test, it needs exactly one home.

## Destinations

| The fact is... | Destination | Layer | AGENTS.md entry |
|---|---|---|---|
| A hard constraint ("never", "must always") | `docs/rules/<topic>-invariants.md` | L2 | **One line, verbatim** + link |
| A choice between alternatives, with reasoning | `docs/decisions.md` | L2 | Conditional pointer |
| System structure, module boundaries, data flow | `docs/architecture.md` | L2 | Conditional pointer |
| Odd behaviour of an external system | `docs/domain/gotchas.md` | L2 | Conditional pointer |
| Domain knowledge the agent lacks (physics, process, notation) | `docs/domain/<topic>.md` | L2 | Conditional pointer |
| Settled parameters, paths, magic numbers | `docs/reference/<topic>.md` | L2 | Conditional pointer |
| How to run something | `README.md` | L1 | Conditional pointer |
| Milestones and completion status | `plan.md` | L1 | Always-read pointer |
| Current position, blockers, next action | `handoff.md` | L1 | Always-read pointer |
| Raw session narrative | `docs/sessions/NNN-*.md` | L3 | None — grep only |

Invariants are the only category that gets content copied into AGENTS.md, because a rule
the agent never reads is a rule that doesn't exist. Keep those lines to one sentence each,
and cap them at roughly seven — beyond that they stop being read as rules and start being
read as prose.

## Choosing between neighbours

- **decisions vs. architecture** — decisions record *why this and not that*, at a point in time, immutable. Architecture records *what is true now*, and is rewritten as things change. If the entry has a rejected alternative, it's a decision.
- **gotchas vs. domain** — gotchas are surprises about tools and systems. Domain is knowledge about the subject matter. Both are "things the agent can't derive", but they're consulted at different moments.
- **reference vs. architecture** — reference is lookup tables you scan for one value. Architecture is prose you read to build a mental model.
- **rules vs. decisions** — if violating it damages something, it's a rule. If it just means a suboptimal choice, it's a decision.

## Formats

### Invariant

```markdown
## INV-03: Never write measured values that were not extracted from source data
**Rationale:** Fabricated measurements can reach a publication. Unrecoverable.
**Applies to:** any script or edit touching results tables or figures.
**Instead:** leave `[TBD: source]` and list it in handoff.md as a blocker.
**Source:** session 007
```

Every invariant needs the "instead" line. A rule without an alternative path gets worked
around rather than followed.

### Decision (ADR)

```markdown
## ADR-006: Structure-tensor + Gabor for stripe segmentation
**Date:** 2026-02-14 · **Status:** accepted · **Session:** 011

**Context:** Two surface orientations must be separated by texture.
**Decision:** Structure-tensor coherence combined with rotation-invariant Gabor energy, fed to KMeans(k=2).
**Rejected:** Coherence alone — crosshatched regions read as low-coherence and land in the wrong class.
**Consequences:** More parameters to tune; needs per-image scale estimation.
**Revisit if:** a labelled set large enough for supervised segmentation becomes available.
```

`Status` is `accepted` / `superseded by ADR-NNN` / `deprecated`. Never edit the body of an
accepted ADR — supersede it with a new one. Editing history is how a decision log stops
being trustworthy.

`Revisit if` matters more than it looks: it's what stops a decision made under old
constraints from being treated as permanent.

### Gotcha

```markdown
### Word COM: attach fails when Word is not already open
**Symptom:** `docx_to_md.py` raises on `GetActiveObject`.
**Cause:** DRM decrypts in-process; a fresh instance sees ciphertext.
**Workaround:** open the file in Word first, then run the extractor.
**Source:** session 004
```

Symptom first — that's the search key. The agent hits the symptom before it knows the cause.

### Reference entry

Tables, not prose. One row per value, with a `source` column so anything can be traced.

## Pointer syntax for AGENTS.md

Each L2 pointer is one row with a trigger condition specific enough to be actionable:

```markdown
| Read this | When |
|---|---|
| `docs/rules/measurement-invariants.md` | Before any code that reads, transforms, or reports measured data |
| `docs/decisions.md` | Before changing an algorithm, or when tempted by an approach that looks obviously better |
| `docs/domain/gotchas.md` | When a tool fails in a way that doesn't match its documentation |
```

"When working on this project" is not a trigger condition — it makes the pointer either
always-read (so it should be L1) or ignored. Write the condition as the situation the agent
will actually recognise itself to be in.
