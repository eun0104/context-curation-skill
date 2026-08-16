---
name: context-curation
description: >-
  Audit and restructure a project's persistent documentation layer — AGENTS.md, plan.md,
  decisions.md, and the architecture / domain / rules / reference docs beneath them. Use this
  skill whenever facts learned during recent sessions should be promoted into permanent project
  docs, when AGENTS.md has grown past its read budget, when docs have gone stale, contradictory,
  duplicated, or unreachable, when a milestone closes, when a project has session logs but no
  structured knowledge layer yet, or when the user says anything like "tune the docs",
  "restructure AGENTS.md", "the agent keeps forgetting X", "our docs have drifted", or "where
  should this fact live". Do NOT use for routine end-of-session handoff writing — that belongs
  to the session-handoff skill.
---

# Context Curation

## Where this sits

Three skills manage the project's memory. Keep the division sharp:

| Skill | Runs | Owns |
|---|---|---|
| `session-context-init` | Session 1 only | Creates `AGENTS.md`, `plan.md`. **Out of scope for this skill** — it has already finished running before curation ever fires. |
| `session-handoff` | Every session end | Appends to `docs/session-log.md`, rewrites `docs/handoff.md`, appends to `docs/decisions.md` |
| **`context-curation`** | Every ~5 sessions | **The doc layer, and `session-handoff`'s own behaviour** |

Handoff answers *where did we stop*. This skill answers *what should stop being session state
and become project state, is that state still healthy, and — critically — **is handoff still
capturing the right things**.*

That last part is why this skill exists. Which documents a project needs, and which fields
handoff must capture, cannot be known at session 1. They emerge from what the project turns out
to be like. Something has to adjust handoff as that becomes clear, and this is it.

The constraint behind every rule below: whatever sits in the always-read layer is paid for on
**every session, forever**. The goal is never "document more". It is to keep the always-read
layer minimal while making everything else findable at the moment it is needed.

## The layer model

Classify by **how often a doc is read**, not by how important it feels.

| Layer | Documents | Read when | Budget |
|---|---|---|---|
| **L0** | `AGENTS.md` | Every session, unconditionally | **2,000 tokens hard cap** |
| **L1** | `docs/handoff.md`, `plan.md` | Every session start, via pointer | ~1,500 tokens each |
| **L2** | `docs/decisions.md`, `architecture.md`, `domain/*.md`, `rules/*.md`, `reference/*.md` | **Conditionally**, only when the task matches | Unbounded, pointer mandatory |
| **L3** | `docs/session-log.md`, `docs/archive/` | Never read whole; grep only | Append-only |

Two failure modes this prevents: **L0 bloat**, where every session gets more expensive and the
important lines get buried; and **L2 orphans**, where a doc is correct but nothing points to it,
so it is never read. An unreachable doc is worse than no doc — it creates false confidence.

## Non-negotiables

1. **Never delete a persistent document.** Move it to `docs/archive/YYYY-MM-DD-<name>.md` with a note on what superseded it. The temporary `docs/_tuning-proposal.md` is the sole exception: remove it after approved changes are fully applied.
2. **One fact, one home.** State a fact in exactly one place; point at it everywhere else. Copying content into AGENTS.md is the most common cause of drift, because the copy never gets updated.
3. **Propose, then stop.** See Step 5. Doc restructuring is hard to review after the fact.
4. **Cite the source of every promoted fact** — session number, file path, or commit. Never promote something inferred rather than observed. A wrong fact in the persistent layer poisons every future session.
5. **Max 2 new durable L2 knowledge files per run.** The proposal, curation state, and handoff control spec do not count. If bootstrap needs more than two L2 files, split it across runs or request explicit approval for the larger document set.
6. **Follow the project's existing conventions** — language, heading style, numbering. If the docs are Korean, write Korean.

## How this run is structured

**Run this in a fresh session, and normally across two of them.**

This is not a normal-session activity. The audit reads the doc set, the harvest reads project
history, and the verification at the end re-reads everything that changed — a lot of context, and
none of it belongs on top of a session already half-full of code.

The natural split falls exactly where the approval boundary already is:

| Pass | Steps | Ends with |
|---|---|---|
| **A — Propose** | 0–5 | `docs/_tuning-proposal.md` written, session ends |
| **B — Apply** | 6–7 | Changes applied and verified, in a fresh session |

Pass B rereads the proposal rather than relying on Pass A's context, so it starts clean. Doing
both in one session is fine when the project is small, but check the headroom rule below first.

**Headroom rule:** Steps 5–7 need room to work — the proposal, the adversarial re-read, and the
final verification pass are where quality is won or lost, and they come last. If harvesting has
consumed more than roughly half the window, stop at the end of Pass A regardless. A rushed
verification is worse than a deferred one, because it reports success either way.

## Run procedure

### Step 0 — Determine the mode

Check whether an L2 layer exists at all (anything under `docs/` beyond `handoff.md`,
`session-log.md`, and `decisions.md`).

- **None → bootstrap mode.** The project has been running on session logs alone. Build the minimum viable L2 set *from what the logs actually contain*, not from a fixed list — creating docs the project has no material for produces empty files that then rot.

  Check `references/profiles/` for a profile matching this project's type (e.g. `physics-modeling.md` for physical-model development and data fitting). A profile lists the doc set, invariants, and handoff fields that this class of project reliably needs, and saves rediscovering them over several tuning rounds. Still confirm each one against the logs: a profile is a prior, not a checklist.
- **Some exists → tune mode.** Proceed normally.

Announce which mode is in effect before continuing.

### Step 1 — Inventory

Resolve `<skill-dir>` as the directory containing the `SKILL.md` you loaded, then run from the
project root. Do not assume the skill is project-local; global installation is the default.

```bash
python <skill-dir>/scripts/docs_inventory.py --root .
```

Reports per-doc token counts, L0 budget status, orphans, broken pointers, stale docs,
duplicated passages, and how many sessions are pending harvest. If Python is unavailable,
approximate with `wc -l` and `grep -rn "docs/" AGENTS.md`.

For how to fix each finding, read `references/audit-checks.md` now.

### Step 2 — Harvest

Step 3's recurrence criterion asks whether something has appeared across *multiple* sessions, so
the harvest needs to see the whole history. But full-history **coverage** does not require
full-text **reading**, and conflating the two is how a curation run arrives at Step 5 with no room
left to think.

**First, extract across the entire log — always, regardless of size:**

```bash
grep -n "\[candidate\]\|\[gotcha\]\|\[decision\]" docs/session-log.md
```

This is complete recurrence coverage for a fraction of the cost, and it is why the handoff spec
asks for those tags. A fact surfacing in sessions 2, 9, and 14 shows up here; an incremental read
would have missed it entirely.

**Then read full text selectively**, in this priority order, stopping when roughly half the
window is consumed:

1. The sessions surrounding each tag hit — enough context to judge the candidate
2. The unharvested range since `harvested_through_session` in `docs/.curation-state.json`. If no usable checkpoint exists, read the latest five session entries.
3. Earlier sessions, only if room remains and the tag extraction looked thin

With a single append-only log, seek to a session by heading:

```bash
grep -n "^#\{1,4\} *[Ss]ession *0*7" docs/session-log.md
sed -n '<line>,$p' docs/session-log.md
```

If the whole log is small — the audit report gives its token count — reading it entirely is
simplest and best. The point is to decide that from the measured size rather than by starting to
read and finding out.

State what was read. If the tag extraction returns nothing, tagging is not happening; say so, note
it for the handoff spec, and fall back to reading the unharvested range.

Extract candidates: things learned, decided, discovered broken, or repeatedly re-explained.
Then scan `docs/handoff.md` — items that have survived several handoffs unchanged are usually
project state wearing a disguise.

Read `rejected_candidates` as prior decisions, not permanent suppression. Reconsider a rejected
candidate if it appeared again after rejection, its evidence changed, or its recorded
`reconsider_if` condition is now true. Recurrence is allowed to change the answer over time.
Treat legacy string entries as labels with unknown evidence; reconsider them on their next
appearance and migrate them to structured records when writing state.

### Step 3 — Classify

Score each candidate. **2 or more → promote.**

| Criterion | Passes when |
|---|---|
| **Recurrence** | Appeared in 2+ distinct sessions, or the user re-explained it |
| **Cost of loss** | Forgetting causes rework or a **wrong result** (not mere inconvenience) |
| **Stability** | Still true in 5 sessions (if volatile → leave in `handoff.md`) |
| **Non-derivability** | Not cheaply rediscovered by reading the code or data |

Promote without scoring: **invariants** ("never" / "must always"), **rejected alternatives**
("tried X, failed because Y" — otherwise the agent proposes X again, confidently), and
**external-system quirks** the agent cannot inspect.

Reject without scoring: task progress (→ `plan.md`), stopping point (→ `handoff.md`), anything
already stated elsewhere (→ add a pointer), anything inferred but unverified (→ open question).

Then route:

| The fact is… | Destination | AGENTS.md entry |
|---|---|---|
| A hard constraint | `docs/rules/<topic>-invariants.md` | **One line, verbatim** + link |
| A choice + reasoning | `docs/decisions.md` | Conditional pointer |
| System structure, data flow | `docs/architecture.md` | Conditional pointer |
| External-system oddity | `docs/domain/gotchas.md` | Conditional pointer |
| Domain knowledge the agent lacks | `docs/domain/<topic>.md` | Conditional pointer |
| Settled parameters, paths, numbers | `docs/reference/<topic>.md` | Conditional pointer |

Invariants are the **only** category whose content is copied into AGENTS.md — a rule the agent
never reads is a rule that does not exist. One sentence each, roughly seven maximum.

For borderline cases, worked examples, and the exact format of each doc type, read
`references/promotion-test.md` and `references/routing-table.md`.

### Step 4 — Structural fixes

Combine Step 1's findings with Step 3's additions: L0 over budget → demote content to L2, leave
a pointer; orphan → add a pointer or archive; duplication → pick the canonical home, replace the
rest with pointers.

Staleness flags from the script are suspicions based on the last commit (or filesystem mtime
outside Git) and the latest verification marker, not verdicts. Where context allows, **open the
code or data each flagged doc describes and check whether it still
holds** rather than asking the user. A doc confirmed accurate gets a `<!-- verified: DATE -->`
marker that resets its staleness clock; it becomes eligible again after the threshold. A doc
found wrong becomes a rewrite plus, usually, an ADR recording what changed.

Read `references/agents-md-contract.md` before touching AGENTS.md.

### Step 5 — Proposal, then STOP

Write `docs/_tuning-proposal.md` using `templates/tuning-proposal.md`, ordered by impact (L0
budget first, then invariants, then the rest). Each item needs its source citation, destination,
and a before/after. Changes to the handoff spec go in their own section — they alter what
happens every session from now on, so they deserve separate scrutiny from one-off doc edits.

Then **re-read the proposal as an adversary before showing it.** Re-apply the promotion test to
every item in section B and cut anything that no longer scores 2. Check that no item restates
content that already exists elsewhere in the doc set, and that every claimed source citation
actually says what the item claims. This pass is cheap and it protects the one thing that does
not scale: a proposal with twelve items, four of them weak, gets a worse review than one with
eight solid items, because the reviewer's scepticism is spent on the wrong ones.

State how many items were cut in this pass.

This is the end of Pass A. Unless the project is small and the window still has clear headroom,
end the session here — Pass B will reread the proposal and start clean.

**Do not create, edit, move, or archive any persistent project file in this step.** The temporary
proposal file is the only thing written. Present it and wait for explicit approval, item by item. Section G is
informational — there is nothing there to approve, because nothing there gets applied. If the user rejects an
item, ask whether the underlying rule should change — pushback usually generalizes.

### Step 6 — Apply

Only after approval, in this order:

1. Create or edit the destination docs, using `templates/` for new files.
2. Update the AGENTS.md pointer table. Every new L2 doc needs a trigger condition phrased as a situation the agent will recognise itself to be in — "when working on this project" is not one.
3. **Update the handoff spec** — see the next section. Classify each doc `per-session` / `on-event` / `frozen` and add only `per-session` docs to the checklist. Skipping this is how per-session cost grows silently and never shrinks.
4. Append an entry to `docs/decisions.md` describing the restructuring itself.
5. Update `docs/.curation-state.json`: date, session number, `harvested_through_session`, one-line summary, and structured rejected-candidate records. Store each as `{"label": ..., "rejected_at_session": ..., "reason": ..., "reconsider_if": ...}`.
6. Remove `docs/_tuning-proposal.md` — it is a temporary review artifact, not a persistent document. A stale proposal left in `docs/` becomes an orphan at the next audit.

### Step 7 — Self-check

Before reporting done, verify and state each:

- [ ] AGENTS.md token count: before → after, and whether it is under budget
- [ ] Every new doc has an inbound pointer with a real trigger condition
- [ ] No content was copied rather than pointed at
- [ ] No persistent document was deleted — only archived; the temporary proposal was removed
- [ ] `docs/.curation-state.json` updated
- [ ] Net change to per-session work stated explicitly

Re-run `docs_inventory.py` to confirm rather than asserting from memory. Then **re-read every
document that changed, plus AGENTS.md, in full**, and check that nothing now contradicts anything
else. Restructuring is exactly when contradictions get introduced — a fact moved to a new home
while an old summary of it survives elsewhere — and it is much cheaper to catch here than three
sessions later when a session has already acted on the wrong copy.

## Tuning the handoff spec

### Where a change goes

The question is not which directory a file sits in. It is **how many projects the change
affects**, and whether that blast radius was chosen deliberately rather than stumbled into.

| The change is… | Goes to | Who applies it |
|---|---|---|
| Project-specific — this project's doc set, cadences, fields | `docs/handoff-spec.md` | This skill, after approval |
| Generalizable — an improvement every project would want | Noted in section G | **The user, by hand** |

Default hard to the spec. A finding from one project is not evidence that it generalizes; it is
one data point. Mistaking a local need for a universal one is the cheap and common error here,
and it is the one whose consequences land somewhere you are not looking.

If `session-handoff` is installed **project-locally**, the distinction collapses — everything is
project-scoped and the spec file becomes optional. Editing its SKILL.md directly is fine there;
copy the original into `docs/archive/` first.

The spec hook (the line telling the shared skill to read `docs/handoff-spec.md`) is normally a
one-time setup step done before this skill ever runs. If it appears to be missing, note it in
section G — do not add it.

### When a finding generalizes

Occasionally a candidate is not about this project at all — it is an improvement the shared
`session-handoff` skill should have for every project.

**Note it in section G of the proposal and stop there. Write no file outside the project.**

This boundary is not about what the model can be trusted to edit. It is what keeps the shared
skill worth sharing. A file that several projects depend on should change when a person decides
it should, having considered those other projects — not as a side effect of one project's tuning
pass, where the evidence is one project wide and the reviewer is looking at this project's docs
rather than at whatever else depends on that file. A shared-file edit also leaves no trace in any
project's history, so it is the one change here that cannot be reconstructed afterwards.

Section G is therefore a note, not an action: what was observed, why it looks general, and the
exact edit if the user wants it. One or two lines. Applying it is theirs.

Reading shared files is unrestricted — comparing the spec's `Base skill version` against the
installed skill each run is how a project avoids sitting on defaults that were improved
centrally months ago.

### What the spec controls

- **Document set** — which files handoff writes each session
- **Cadence** — `per-session` / `on-event` / `frozen` per document
- **handoff.md fields** — the questions the next session actually needs answered
- **Tagging** — which markers to leave in the session log for the next harvest

### Reading the evidence

Symptoms come from the session log and from the harvest, not from taste:

| Symptom in the logs | Change to the spec |
|---|---|
| A session opened by re-deriving something the previous session knew | Add a required `handoff.md` field for it |
| A field reads "n/a" in most sessions | Remove it — noise crowds out the fields that matter |
| A doc is rewritten every session but rarely changes | Move to `on-event` |
| A doc changed materially and nobody noticed for several sessions | Move to `per-session` |
| The same `[gotcha]` tag keeps reappearing | The fact belongs in L2; promote it and stop re-logging it |
| Harvest found nothing taggable | Tagging is not happening — restate it in the spec with an example |

**Fields are a budget, not a wishlist.** Every added field is filled in at the end of every
session, when attention is lowest. A spec with fifteen fields produces fifteen shallow answers.
When adding one, name the one it replaces.

## When to run

Every session wastes context; never lets the docs rot. Trigger on: 5+ sessions since
`last_tuned` · AGENTS.md over budget · a `plan.md` milestone closing · 3+ accumulated
learned/gotcha items · entering a new subsystem · **the user reporting that the agent keeps
forgetting or re-deriving something**.

That last one deserves action even if nothing else has triggered — it is direct evidence that a
fact belongs in the persistent layer and is not there.

## Bundled resources

| Path | Read when |
|---|---|
| `references/promotion-test.md` | Step 3 — borderline promotion calls, worked examples |
| `references/routing-table.md` | Step 3 — destination choice and exact doc formats |
| `references/audit-checks.md` | Steps 1 and 4 — interpreting each inventory finding |
| `references/agents-md-contract.md` | Steps 4 and 6 — before editing AGENTS.md |
| `references/profiles/*.md` | Step 0 — bootstrap, when a profile matches the project type |
| `templates/handoff-spec.md` | When changing what handoff captures |
| `templates/*.md` | Step 6 — creating a new persistent doc |
| `scripts/docs_inventory.py` | Step 1 — run it, no need to read it |
| `integration/` | First-time setup only |
