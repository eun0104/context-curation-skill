#!/usr/bin/env python3
"""
docs_inventory.py - structural audit of a project's persistent documentation layer.

Standard library only. No network access. Safe for restricted corporate environments.

Reports:
  1. Inventory        - every persistent doc with line/token counts and age
  2. Budget           - whether AGENTS.md / L1 docs exceed their read budget
  3. Reachability     - docs with no inbound pointer, and pointers to missing files
  4. Staleness        - docs untouched for longer than the threshold
  5. Duplication      - near-identical paragraphs across different docs
  6. Session logs     - volume of the L3 layer

Usage:
    python docs_inventory.py --root .
    python docs_inventory.py --root . --json
    python docs_inventory.py --root . --stale-days 60 --l0-budget 1500
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# --------------------------------------------------------------------------
# Configuration defaults
# --------------------------------------------------------------------------

ENTRY_DOC = "AGENTS.md"

INCLUDE_GLOBS = [
    "*.md",
    "docs/**/*.md",
    ".omo/rules/**/*.md",
]

EXCLUDE_PARTS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "archive", "sessions", ".opencode",
}

# Session logs may be one append-only file or one file per session. Both supported.
SESSION_GLOBS = [
    "docs/session-log.md",
    "docs/session_log.md",
    "docs/sessions/**/*.md",
    "docs/session-logs/**/*.md",
]

# Matches "## Session 007", "### session-12", "## 세션 3"
SESSION_MARKER_RE = re.compile(
    r"^#{1,4}\s*(?:session|세션)\s*[-#:]?\s*(\d+)", re.IGNORECASE | re.MULTILINE)

L1_DOCS = {"plan.md", "handoff.md", "README.md", "readme.md", "PLAN.md"}

STATE_FILE = "docs/.curation-state.json"

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
BACKTICK_PATH_RE = re.compile(r"`([^`\s]+\.md)`")
BARE_PATH_RE = re.compile(r"(?<![\w`(/])((?:docs|\.omo)/[\w./-]+\.md)")


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def estimate_tokens(text: str) -> int:
    """Rough token estimate for mixed ASCII / CJK text.

    ASCII prose runs about 4 characters per token; Korean and other CJK text
    is far denser, closer to 1.5 characters per token. This is an estimate,
    not a measurement - treat it as +/- 20%.
    """
    ascii_chars = sum(1 for ch in text if ord(ch) < 128)
    wide_chars = len(text) - ascii_chars
    return int(ascii_chars / 4.0 + wide_chars / 1.5)


def is_excluded(path: Path, root: Path) -> bool:
    try:
        rel_parts = path.relative_to(root).parts
    except ValueError:
        return True
    return any(part in EXCLUDE_PARTS for part in rel_parts)


def session_stats(paths):
    """Count session entries across the session-log layer, however it is split."""
    numbers, tokens = [], 0
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        tokens += estimate_tokens(text)
        numbers += [int(n) for n in SESSION_MARKER_RE.findall(text)]
    return {
        "files": len(paths),
        "tokens": tokens,
        "entries": len(numbers),
        "latest": max(numbers) if numbers else None,
    }


def collect(root: Path, globs, apply_exclusions: bool = True):
    found = {}
    for pattern in globs:
        for path in root.glob(pattern):
            if not path.is_file():
                continue
            if apply_exclusions and is_excluded(path, root):
                continue
            found[path.resolve()] = path
    return sorted(found.values(), key=lambda p: str(p.relative_to(root)))


def git_last_commit(root: Path, path: Path):
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ad|%h", "--date=short", "--", str(path)],
            cwd=str(root), capture_output=True, text=True, timeout=10,
        )
        if out.returncode == 0 and out.stdout.strip():
            date, _, sha = out.stdout.strip().partition("|")
            return date, sha
    except (OSError, subprocess.SubprocessError):
        pass
    return None, None


def days_since(mtime: float) -> int:
    return int((time.time() - mtime) / 86400)


def extract_links(text: str):
    """All .md paths referenced from a document, however they are written."""
    links = set()
    for match in LINK_RE.findall(text):
        target = match.split("#")[0].strip()
        if target and not target.startswith(("http://", "https://", "mailto:")):
            links.add(target)
    links.update(BACKTICK_PATH_RE.findall(text))
    links.update(BARE_PATH_RE.findall(text))
    return {link for link in links if link.endswith(".md")}


def resolve_link(link: str, source: Path, root: Path):
    candidates = []
    if not link.startswith("/"):
        candidates.append((source.parent / link).resolve())
        candidates.append((root / link).resolve())
    else:
        candidates.append((root / link.lstrip("/")).resolve())
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


# --------------------------------------------------------------------------
# Duplication detection
# --------------------------------------------------------------------------

def paragraphs(text: str, min_words: int = 20):
    blocks, current, in_code = [], [], False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if line.strip():
            current.append(line.strip())
        elif current:
            blocks.append(" ".join(current))
            current = []
    if current:
        blocks.append(" ".join(current))
    return [b for b in blocks if len(b.split()) >= min_words]


def shingles(text: str, size: int = 5):
    words = re.findall(r"\w+", text.lower())
    if len(words) < size:
        return set()
    return {tuple(words[i:i + size]) for i in range(len(words) - size + 1)}


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def find_duplicates(docs_text, threshold: float):
    indexed = []
    for name, text in docs_text.items():
        for i, para in enumerate(paragraphs(text), start=1):
            sh = shingles(para)
            if sh:
                indexed.append((name, i, para, sh))

    hits = []
    for i in range(len(indexed)):
        for j in range(i + 1, len(indexed)):
            if indexed[i][0] == indexed[j][0]:
                continue
            score = jaccard(indexed[i][3], indexed[j][3])
            if score >= threshold:
                hits.append({
                    "a": f"{indexed[i][0]} para {indexed[i][1]}",
                    "b": f"{indexed[j][0]} para {indexed[j][1]}",
                    "similarity": round(score, 2),
                    "excerpt": indexed[i][2][:110],
                })
    return sorted(hits, key=lambda h: -h["similarity"])


# --------------------------------------------------------------------------
# Main audit
# --------------------------------------------------------------------------

def audit(root: Path, args) -> dict:
    sessions = collect(root, SESSION_GLOBS, apply_exclusions=False)
    session_paths = {p.resolve() for p in sessions}
    # A single-file session log lives inside docs/ and would otherwise be audited
    # as an L2 doc, producing noise in every other check.
    docs = [p for p in collect(root, INCLUDE_GLOBS)
            if p.resolve() not in session_paths]

    texts, records = {}, []
    for path in docs:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"warning: cannot read {path}: {exc}", file=sys.stderr)
            continue
        rel = str(path.relative_to(root)).replace(os.sep, "/")
        texts[rel] = text
        commit_date, sha = git_last_commit(root, path)
        records.append({
            "path": rel,
            "lines": text.count("\n") + 1,
            "tokens": estimate_tokens(text),
            "age_days": days_since(path.stat().st_mtime),
            "git_date": commit_date,
            "git_sha": sha,
            "layer": ("L0" if rel == ENTRY_DOC
                      else "L1" if path.name in L1_DOCS
                      else "L2"),
        })

    by_path = {r["path"]: r for r in records}

    # -- budgets ---------------------------------------------------------
    budget_findings = []
    if ENTRY_DOC in by_path:
        tok = by_path[ENTRY_DOC]["tokens"]
        budget_findings.append({
            "path": ENTRY_DOC, "tokens": tok, "budget": args.l0_budget,
            "over": max(0, tok - args.l0_budget),
        })
    else:
        budget_findings.append({"path": ENTRY_DOC, "tokens": None,
                                "budget": args.l0_budget, "missing": True})
    for rel, rec in by_path.items():
        if rec["layer"] == "L1" and rec["tokens"] > args.l1_budget:
            budget_findings.append({
                "path": rel, "tokens": rec["tokens"], "budget": args.l1_budget,
                "over": rec["tokens"] - args.l1_budget,
            })

    # -- reachability ----------------------------------------------------
    broken, edges = [], {}
    for rel, text in texts.items():
        source = root / rel
        targets = set()
        for link in extract_links(text):
            resolved = resolve_link(link, source, root)
            if resolved is None:
                broken.append({"from": rel, "link": link})
            else:
                try:
                    targets.add(str(resolved.relative_to(root)).replace(os.sep, "/"))
                except ValueError:
                    pass
        edges[rel] = targets

    reached, queue = set(), [ENTRY_DOC] if ENTRY_DOC in texts else []
    while queue:
        node = queue.pop()
        if node in reached:
            continue
        reached.add(node)
        queue.extend(edges.get(node, ()))

    orphans = [rel for rel in texts
               if rel not in reached
               and rel != ENTRY_DOC
               and rel.rsplit("/", 1)[-1] not in L1_DOCS]

    # -- staleness -------------------------------------------------------
    stale = [
        {"path": r["path"], "age_days": r["age_days"]}
        for r in records
        if r["age_days"] > args.stale_days
        and "<!-- verified:" not in texts.get(r["path"], "")
    ]

    duplicates = find_duplicates(texts, args.dup_threshold)

    # -- session logs ----------------------------------------------------
    sess = session_stats(sessions)

    # -- curation state --------------------------------------------------
    state = None
    state_path = root / STATE_FILE
    if state_path.is_file():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            state = {"error": f"unreadable: {exc}"}

    return {
        "root": str(root),
        "docs": records,
        "budget": budget_findings,
        "broken_links": broken,
        "orphans": sorted(orphans),
        "stale": sorted(stale, key=lambda s: -s["age_days"]),
        "duplicates": duplicates,
        "sessions": sess,
        "curation_state": state,
    }


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------

def report(result: dict, args) -> str:
    out = ["# Documentation Inventory", ""]
    state = result["curation_state"]
    if state and "last_tuned" in state:
        out.append(f"Last tuned: **{state['last_tuned']}** "
                   f"(session {state.get('last_tuned_session', '?')})")
    else:
        out.append("Last tuned: **never** - no `docs/.curation-state.json` found.")
    out.append("")

    out += ["## 1. Inventory", "",
            "| Doc | Layer | Lines | ~Tokens | Age (d) | Last commit |",
            "|---|---|---:|---:|---:|---|"]
    for r in sorted(result["docs"], key=lambda x: (x["layer"], x["path"])):
        commit = f"{r['git_date']} {r['git_sha']}" if r["git_date"] else "-"
        out.append(f"| `{r['path']}` | {r['layer']} | {r['lines']} | "
                   f"{r['tokens']} | {r['age_days']} | {commit} |")
    total = sum(r["tokens"] for r in result["docs"]
                if r["layer"] in ("L0", "L1"))
    out += ["", f"**Always-read cost (L0+L1): ~{total} tokens per session.**", ""]

    out += ["## 2. Budget", ""]
    problems = False
    for b in result["budget"]:
        if b.get("missing"):
            out.append(f"- `{b['path']}` **NOT FOUND** - no entry point for the doc layer.")
            problems = True
        elif b.get("over", 0) > 0:
            out.append(f"- `{b['path']}`: {b['tokens']} tokens "
                       f"(budget {b['budget']}) - **OVER by {b['over']}**")
            problems = True
        else:
            out.append(f"- `{b['path']}`: {b['tokens']} / {b['budget']} tokens - ok")
    if problems:
        out.append("")
        out.append("See `references/audit-checks.md` section 1 for the demotion order.")
    out.append("")

    out += ["## 3. Reachability", ""]
    if result["broken_links"]:
        out.append("**Broken pointers (fix first):**")
        for b in result["broken_links"]:
            out.append(f"- `{b['from']}` -> `{b['link']}` (target missing)")
    else:
        out.append("No broken pointers.")
    out.append("")
    if result["orphans"]:
        out.append("**Unreachable from AGENTS.md:**")
        for o in result["orphans"]:
            out.append(f"- `{o}`")
    else:
        out.append("No orphan docs.")
    out.append("")

    out += ["## 4. Staleness", ""]
    if result["stale"]:
        for s in result["stale"]:
            out.append(f"- `{s['path']}` - {s['age_days']} days "
                       f"(threshold {args.stale_days})")
        out.append("")
        out.append("Verify against the code, then add `<!-- verified: YYYY-MM-DD -->` "
                   "to suppress future flags.")
    else:
        out.append("Nothing stale.")
    out.append("")

    out += ["## 5. Duplication", ""]
    if result["duplicates"]:
        for d in result["duplicates"][:15]:
            out.append(f"- {d['a']} ~ {d['b']} (similarity {d['similarity']})")
            out.append(f"  > {d['excerpt']}...")
    else:
        out.append("No near-duplicate passages above threshold.")
    out.append("")

    s = result["sessions"]
    out += ["## 6. Session log (L3)", ""]
    if s["files"] == 0:
        out.append("No session log found. Expected `docs/session-log.md` "
                   "or `docs/sessions/`.")
    else:
        out.append(f"{s['files']} file(s), {s['entries']} session entries, "
                   f"latest session {s['latest'] or '?'}, ~{s['tokens']} tokens.")
        pct = 100.0 * s["tokens"] / max(1, args.context_window)
        out.append("")
        out.append(f"That is ~{pct:.0f}% of a {args.context_window:,}-token window.")
        if pct < 20:
            out.append("**Harvest: read the whole log.** It fits with room to spare.")
        elif pct < 40:
            out.append("**Harvest: tag-extract first**, then read full text around the hits "
                       "and the unharvested range. Reading it all would leave too little "
                       "room for Steps 5-7.")
        else:
            out.append("**Harvest: tag extraction only**, plus full text for the "
                       "unharvested range. Do not read the whole log — and plan on "
                       "splitting the run into Pass A and Pass B.")
        harvested = (state or {}).get("harvested_through_session")
        if harvested is not None and s["latest"] is not None:
            gap = s["latest"] - harvested
            if gap > 0:
                out.append("")
                out.append(f"State says harvested through session {harvested} -> "
                           f"**{gap} session(s) pending harvest.** "
                           f"Read only sessions {harvested + 1}-{s['latest']}.")
            else:
                out.append("")
                out.append("Harvest is up to date.")
    out.append("")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".", help="project root (default: .)")
    parser.add_argument("--json", action="store_true", help="emit raw JSON")
    parser.add_argument("--l0-budget", type=int, default=2000,
                        help="token budget for AGENTS.md (default: 2000)")
    parser.add_argument("--l1-budget", type=int, default=1500,
                        help="token budget for plan.md / handoff.md (default: 1500)")
    parser.add_argument("--stale-days", type=int, default=90,
                        help="flag docs older than this (default: 90)")
    parser.add_argument("--dup-threshold", type=float, default=0.45,
                        help="paragraph similarity to flag, 0-1 (default: 0.45)")
    parser.add_argument("--context-window", type=int, default=200000,
                        help="session context window, for harvest sizing (default: 200000)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 1

    result = audit(root, args)
    text = (json.dumps(result, indent=2, ensure_ascii=False) if args.json
            else report(result, args))
    try:
        print(text)
    except BrokenPipeError:  # output piped into head/less
        os.close(sys.stdout.fileno())
    return 0


if __name__ == "__main__":
    sys.exit(main())
