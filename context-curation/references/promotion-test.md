# Promotion Test

Deciding whether a fact from a session earns a permanent home.

The bias to fight here is over-promotion. Everything discovered during a session *feels*
important while it's fresh. But each promoted fact costs context on future sessions and
becomes something that can go stale and mislead. When genuinely unsure, do not promote —
the fact stays in the session log and will resurface on its own if it actually matters.

## The four criteria

Score each candidate. **2 or more → promote.**

### 1. Recurrence
Has this come up in **two or more distinct sessions**? Did the user have to re-explain it,
or did the agent re-derive it?

Recurrence is the strongest single signal, because it is observed rather than predicted.
One-time discoveries are usually incidental to the task that produced them.

### 2. Cost of loss
If this is forgotten, does it cause **rework or a wrong result**?

"Wrong result" outranks "inconvenience". A tool flag that must be set or the output is
silently incorrect passes. A tool flag that saves thirty seconds does not.

### 3. Stability
Will this still be true in five sessions?

If it will likely change soon, it is session state, not project state — leave it in
`handoff.md`. Promoting volatile facts is how docs start contradicting the code.

### 4. Non-derivability
Can the agent cheaply rediscover this by reading the code or data?

Something obvious from one glance at a file does not need documenting; the file *is* the
documentation. Promote what is **not** visible from the artifacts: reasons, constraints
imposed from outside, things that were tried and failed.

## Automatic promotion, no scoring needed

- **Invariants** — anything phrased as "never" / "must always". These prevent damage, so the cost of missing one is asymmetric. → `rules/*-invariants.md` **and** a one-line entry in AGENTS.md.
- **A rejected alternative** — "we tried X, it failed because Y". Without this, the agent will propose X again, confidently.
- **External-system quirks** — behaviour of a system the agent cannot inspect (DRM, licensed tools, internal APIs, lab instruments). Non-derivable by definition.

## Automatic rejection

- Task progress → belongs in `plan.md`
- "Where I stopped" → belongs in `handoff.md`
- Anything already stated in another persistent doc → add a pointer, don't restate
- Anything the agent inferred but did not verify → not a fact yet; note it as an open question in `handoff.md`

## Worked examples

**Candidate:** "Word must already be running for the COM extractor to attach and bypass DRM."
Recurrence ✓ (broke twice) · Loss ✓ (script fails outright) · Stability ✓ · Non-derivable ✓
→ **Promote** to `docs/domain/gotchas.md`.

**Candidate:** "Used `--watch` on the budget script today."
Recurrence ✗ · Loss ✗ · Stability ✓ · Non-derivable ✗ (it's in `--help`)
→ **Reject.** Score 1.

**Candidate:** "Chose structure-tensor + Gabor over pure coherence because crosshatched
stripes get misclassified by coherence alone."
Recurrence ✗ · Loss ✓ (agent would re-propose the simpler wrong approach) · Stability ✓ ·
Non-derivable ✓ (the rejected alternative is invisible in the code)
→ **Promote** to `decisions.md` as an ADR. Score 3.

**Candidate:** "The vision model must never compute the final measured ratio directly."
→ **Promote** immediately as an invariant, no scoring. Rules file + one AGENTS.md line.

**Candidate:** "Abstract is 7 words over the limit."
Recurrence ✗ · Loss ✗ (a script measures it) · Stability ✗ (fixed next session) · Non-derivable ✗
→ **Reject.** This is current state, not project knowledge. → `handoff.md` or `plan.md`.
