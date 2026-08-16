# context-curation

English | [한국어](README.ko.md)

An opencode skill for **managing persistent context layers** in multi-session AI coding
agent projects.

If `session-handoff` carries work across session boundaries, this skill decides *what should
stop being session state and become project state*, then keeps that project state small,
reachable, and internally consistent.

## The problem

As a project grows, AGENTS.md expands, documentation becomes stale or duplicated, and orphaned
documents accumulate. An unreachable document is worse than no document at all because it creates
false confidence.

At setup time, you cannot know which documents the project will eventually need. Those needs
emerge as the project develops. This skill closes that gap.

## Layer model

Documents are classified by **read frequency**, not importance.

| Layer | Documents | When read | Budget |
|---|---|---|---|
| L0 | `AGENTS.md` | Every session | 2,000-token hard cap |
| L1 | `docs/handoff.md`, `plan.md` | At session start | ~1,500 each |
| L2 | `decisions` · `architecture` · `domain` · `rules` · `reference` | On demand | Unlimited, but must be linked |
| L3 | `docs/session-log.md`, `docs/archive/` | Never read wholesale; searched only | Append-only |

The L0 cap is not a spending limit. It is a **shape constraint**. If seven non-negotiable rules
compete for attention with paragraphs of ordinary facts, they stop reading like rules.

## How it works

1. Audit document budgets, pointers, reachability, duplication, freshness, and session-log size.
2. Search the full log for tags and read only the relevant session bodies. If no state file exists,
   use the latest five session entries as the bootstrap scope.
3. Evaluate durable-promotion candidates for recurrence, cost of loss, stability, and
   non-derivability.
4. Write a proposal that adjusts both the read path in `AGENTS.md` and the write path in
   `docs/handoff-spec.md`, then stop.
5. Apply only the items the user explicitly approves, then rerun the audit to verify the result.

A rejected candidate is not excluded forever. Reconsider it when it recurs or its evidence
changes.

## Installation

```bash
# Global installation (recommended)
cp -r context-curation ~/.config/opencode/skill/
cp context-curation/command/tune-docs.md ~/.config/opencode/command/

# For a project-local installation:
# cp -r context-curation <project>/.opencode/skill/
```

After installation, add the project-override hook from
`integration/session-handoff-snippet.md` to the shared `session-handoff` skill once, then add
`integration/agents-md-snippet.md` to the project's AGENTS.md. Do not create a placeholder state
file. The first approved run creates `docs/.curation-state.json` and `docs/handoff-spec.md` when
needed.

See [`context-curation/INSTALL.md`](context-curation/INSTALL.md) for the complete installation and
integration guide (Korean), and [`context-curation/SKILL.md`](context-curation/SKILL.md) for the
agent execution contract.

## Repository layout

```text
context-curation/
├── SKILL.md                       # Layer model, seven-step workflow, and guardrails
├── INSTALL.md                     # Installation and integration guide (Korean)
├── command/tune-docs.md           # Slash command for explicit invocation
├── scripts/docs_inventory.py      # Structural audit; standard library only, no network
├── references/
│   ├── promotion-test.md          # Four promotion criteria and examples
│   ├── routing-table.md           # Destination selection and document formats
│   ├── audit-checks.md            # Responses for each audit finding
│   ├── agents-md-contract.md      # What belongs in L0 and what does not
│   └── profiles/
│       └── physics-modeling.md    # Profile for physics modeling and data fitting
├── templates/                     # Templates for new documents
└── integration/                   # session-handoff integration snippets

tests/
├── test_docs_inventory.py         # Standard-library regression tests
└── fixtures/bootstrap-project/    # Anonymous forward-test project
```

## Design principles

**Propose, then stop.** At Step 5, write `docs/_tuning-proposal.md` and stop. Do not change any
project documentation before approval. Documentation restructuring is difficult to review after
the fact.

**Do not write outside the project.** Record findings that may belong in a shared skill only as
notes in proposal section G. A human applies them. Files shared across projects must be changed by
someone who can evaluate all affected projects.

**Do not delete durable documentation.** Move it to `docs/archive/` and record what replaced it.
Only the temporary review artifact `docs/_tuning-proposal.md` is removed after approved changes
are applied.

**Keep one source of truth.** State each fact in one place and point to it everywhere else. Copying
content into AGENTS.md is where drift begins.

**Keep change sets small.** Create at most two new durable L2 knowledge documents in one run. The
review proposal, curation state, and handoff control spec do not count toward this limit.

**Use two passes.** Pass A audits, harvests, and proposes; review happens at the approval boundary;
Pass B applies and verifies. This preserves context for the quality-critical final stage without
adding an artificial split.

## Audit script

To inspect a project without invoking the skill:

```bash
# From this repository
python context-curation/scripts/docs_inventory.py --root /path/to/project

# From a global installation
# python ~/.config/opencode/skill/context-curation/scripts/docs_inventory.py --root /path/to/project
```

The audit reports:

- L0/L1 token budgets and missing required startup documents
- documents unreachable from AGENTS.md and broken pointers in reachable documents
- freshness based on the last Git commit or file mtime together with
  `<!-- verified: YYYY-MM-DD -->`
- paragraph duplication, session-log size, and unharvested sessions
- the recent-session bootstrap scope when no state file exists

README files are conditional L2 documents; their filename alone does not add them to the
always-read cost. The script uses only the Python standard library and makes no network requests.
Python 3.8+ is required.

## Validation

Anonymous synthetic projects provide regression coverage for layer classification, reachability,
verification dates, first-run harvest scope, Git dates, and working-tree changes.

```bash
python -m unittest discover -s tests -v
```

All nine current regression tests pass. An independent forward test also preserved bootstrap
mode, the two-new-L2-file limit, duplicate-candidate rejection, and the propose-then-stop boundary.

## License

Not yet specified.
