# Audit Checks

How to read `docs_inventory.py` output and what to do about each finding.
Findings are listed in the order they should be fixed — earlier ones change the shape of
later ones.

## 1. L0 over budget

**Report:** `AGENTS.md: 3,180 tokens (budget 2,000) — OVER by 1,180`

This is the highest-leverage fix, and the reason is signal rather than expense. An AGENTS.md
that has grown into prose still gets read — but the invariants in it stop reading as invariants,
because they now sit among paragraphs that are merely informative. Where tokens are cheap this
is the *only* cost of L0 bloat, and it is enough on its own.

Demote in this order until it fits:

1. **Prose explaining rationale** → `architecture.md` or `decisions.md`. AGENTS.md answers "what do I do"; rationale answers "why", which is only needed when something is being changed.
2. **Detailed procedures** → their own doc, or a script. A procedure written out in full is usually a script that hasn't been written yet.
3. **Lists longer than ~7 items** → a reference table.
4. **Duplicated content** → replace with a pointer.
5. **Domain background** → `domain/`.

What must never be demoted: the pointer table, the invariant one-liners, and the session
startup sequence. Those are why AGENTS.md exists.

If it still doesn't fit, the pointer table itself is too long — group related docs under a
single index doc and point at the index.

## 2. Unreachable documents

**Report:** `docs/domain/sb-growth.md — ORPHAN (no inbound pointer)`

Reachability is computed by following markdown links and backticked paths from AGENTS.md.
An orphan is never read, so it silently rots while looking maintained.

Three possible resolutions:

- Still relevant → add a pointer with a trigger condition.
- Superseded → archive it with a `superseded by` note.
- Never actually used → archive it. If it turns out to be needed, it's still there.

Ask which before assuming. An orphan is often a doc the *user* reads by hand, and archiving
it would be a surprise.

## 3. Broken pointers

**Report:** `AGENTS.md → docs/decisions.md (TARGET MISSING)`

The most damaging finding, because the agent reports having consulted a doc that isn't
there and proceeds with false confidence. Fix immediately: correct the path, or create the
doc from a template, or remove the pointer.

## 4. Duplicated passages

**Report:** `AGENTS.md ¶4 ≈ docs/architecture.md ¶2 (similarity 0.71)`

Duplication guarantees eventual contradiction, because only one copy gets updated. Worse,
the agent can't tell which copy is current.

Pick the canonical home using the routing table, replace the other with a pointer, and check
whether the copies **already disagree** — if they do, the divergence itself is a finding
worth reporting to the user, since one of the two has been guiding sessions incorrectly.

Similarity below ~0.5 is often legitimate: a one-line summary pointing to a fuller
treatment is the pattern this skill *wants*. Judge by whether both copies would need editing
if the underlying fact changed.

## 5. Stale documents

**Report:** `docs/architecture.md — last modified 118 days ago (threshold 90)`

Staleness is a suspicion, not a verdict — it is derived from modification time, which says
nothing about accuracy. A frozen spec should be old.

Check against the code or data it describes; read the actual implementation rather than asking
the user whether it is still true. Verification is the cheap half of this and guessing is the
expensive half. If it still holds, add
`<!-- verified: YYYY-MM-DD -->` so the next audit doesn't re-flag it. If it drifted, the fix
is a rewrite plus, usually, an ADR explaining what changed.

Stale invariants deserve extra care: a rule everyone quietly stopped following is worse than
no rule, because it teaches the agent that rules are advisory.

## 6. Session log volume

**Report:** `docs/sessions/: 34 files, 41,200 tokens total`

Logs are L3 and never read whole, so size alone is not a problem. But it does indicate
harvest debt — a lot of accumulated material that has never been considered for promotion.
If `last_tuned` is far behind, harvest in batches by milestone rather than trying to read
everything at once.

Consolidating logs older than the last closed milestone into a single summary file is
optional and only worth doing if grep results have become noisy.

## 7. Handoff bloat

Not detected by the script — check `handoff.md` by hand.

If an item has survived three or more handoffs unchanged, it is not session state. Either
it's project state that should be promoted, or it's a stalled task that belongs in `plan.md`
as an explicit blocker. Carrying it forward silently is how a handoff file turns into a
second, unmanaged AGENTS.md.
