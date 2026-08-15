# AGENTS.md Contract

Read before editing AGENTS.md.

AGENTS.md is not documentation. It is a **routing table with a few rules attached**. Its job
is to get the agent to the right document in the fewest tokens, then get out of the way.
Every line competes for the same fixed budget on every session.

## Required sections, in order

```markdown
# <Project> — Agent Instructions

## Session start                  <- what to do, first, every time
## Invariants                     <- ≤7 one-line rules, verbatim, non-negotiable
## Read on demand                 <- the pointer table (the core of this file)
## Project shape                  <- ≤10 lines: what this is, where things live
## Conventions                    <- ≤10 lines: only project-specific, non-obvious ones
```

## Allowed

- Pointers with trigger conditions
- Invariants, one line each
- The session startup sequence
- A directory sketch, if navigation is genuinely non-obvious
- Conventions a competent agent would otherwise get wrong

## Not allowed

- Rationale or history → `decisions.md`
- Architecture prose → `architecture.md`
- Tutorials or step-by-step procedures → their own doc, or a script
- Anything already stated in a doc that AGENTS.md points to
- Status, progress, or current numbers → `plan.md` / `handoff.md`
- Lists over ~7 items → a reference doc

The status rule matters most in practice: numbers written into AGENTS.md go stale within a
session or two and then actively mislead, because nothing prompts anyone to update them.

## Section templates

### Session start

```markdown
## Session start
1. Read `docs/handoff.md` — current position and next action.
2. Read `plan.md` — milestone status.
3. Consult the pointer table below **before** starting work, not after getting stuck.
4. At session end, run the `session-handoff` skill.
```

Step 3's phrasing is deliberate. Without it the pointer table gets consulted only after
something has already gone wrong, which is exactly when the cost of not having read it has
already been paid.

### Invariants

```markdown
## Invariants
- Never invent or interpolate measured data. → `docs/rules/measurement-invariants.md`
- The vision model never computes final quantitative results. → same
- Never commit files under `data/raw/`.
```

One line, imperative, no hedging. If a rule needs a paragraph, the paragraph goes in the
rules file and the line here is its summary.

### Read on demand

```markdown
## Read on demand
| Read this | When |
|---|---|
| `docs/architecture.md` | Before changing module boundaries or the data flow |
| `docs/decisions.md` | Before replacing an algorithm or reversing an earlier approach |
| `docs/domain/gotchas.md` | When a tool fails in a way its docs don't explain |
| `docs/reference/params.md` | When you need a settled parameter value |
```

Sort by expected read frequency — the agent scans top-down and the table should front-load
what it most often needs.

## Budget enforcement

Cap: **2,000 tokens**, roughly 120 lines. Adjust for your context window, but keep it a
fixed number that gets checked, not a vague intention.

The rule that makes the cap work: **adding a line requires removing one**. Without it the
file grows monotonically, since every individual addition looks justified in isolation.

When it's genuinely full, don't raise the cap — group related pointers under an index doc.
An extra hop costs one read, and only for sessions that actually need that branch.

**Do not relax the cap because tokens are cheap.** The cap is not a spending limit; it is what
forces this file to stay a routing table. A 6,000-token AGENTS.md is affordable and still worse,
because the seven invariants that must be obeyed are now competing with several pages of things
that are merely true.
