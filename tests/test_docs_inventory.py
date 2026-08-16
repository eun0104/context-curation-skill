import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import time
import types
import unittest
from datetime import date, timedelta
from pathlib import Path


SCRIPT = (Path(__file__).resolve().parents[1]
          / "context-curation" / "scripts" / "docs_inventory.py")
SPEC = importlib.util.spec_from_file_location("docs_inventory", SCRIPT)
inventory = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(inventory)


def args(**overrides):
    values = {
        "l0_budget": 2000,
        "l1_budget": 1500,
        "stale_days": 90,
        "dup_threshold": 0.45,
        "context_window": 200000,
        "bootstrap_sessions": 5,
    }
    values.update(overrides)
    return types.SimpleNamespace(**values)


def write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class InventoryTests(unittest.TestCase):
    def test_only_contract_paths_are_l1_and_all_docs_need_reachability(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write(root, "AGENTS.md", "[plan](plan.md)\n")
            write(root, "plan.md", "# Plan\n")
            write(root, "docs/handoff.md", "# Handoff\n")
            write(root, "README.md", "# How to run\n")
            write(root, "docs/subsystem/README.md", "# Subsystem\n")

            result = inventory.audit(root, args())
            layers = {record["path"]: record["layer"] for record in result["docs"]}

            self.assertEqual("L0", layers["AGENTS.md"])
            self.assertEqual("L1", layers["plan.md"])
            self.assertEqual("L1", layers["docs/handoff.md"])
            self.assertEqual("L2", layers["README.md"])
            self.assertEqual("L2", layers["docs/subsystem/README.md"])
            self.assertIn("docs/handoff.md", result["orphans"])
            self.assertIn("README.md", result["orphans"])

    def test_missing_required_l1_docs_are_reported(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write(root, "AGENTS.md", "# Agent instructions\n")

            result = inventory.audit(root, args())
            missing = {item["path"] for item in result["budget"]
                       if item.get("missing")}

            self.assertEqual({"plan.md", "docs/handoff.md"},
                             missing - {"AGENTS.md"})

    def test_verification_marker_resets_but_does_not_disable_staleness(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write(root, "AGENTS.md",
                  "[plan](plan.md) [handoff](docs/handoff.md) "
                  "[old](docs/old.md) [fresh](docs/fresh.md)\n")
            write(root, "plan.md", "# Plan\n")
            write(root, "docs/handoff.md", "# Handoff\n")
            old_date = (date.today() - timedelta(days=180)).isoformat()
            old_doc = write(root, "docs/old.md", f"<!-- verified: {old_date} -->\n")
            fresh_doc = write(root, "docs/fresh.md",
                              f"<!-- verified: {date.today().isoformat()} -->\n")
            old_epoch = (date.today() - timedelta(days=200)).strftime("%Y-%m-%d")
            old_value = time.mktime(time.strptime(old_epoch, "%Y-%m-%d"))
            os.utime(old_doc, (old_value, old_value))
            os.utime(fresh_doc, (old_value, old_value))

            result = inventory.audit(root, args())
            stale = {item["path"] for item in result["stale"]}

            self.assertIn("docs/old.md", stale)
            self.assertNotIn("docs/fresh.md", stale)

    def test_bootstrap_uses_latest_five_actual_session_entries(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write(root, "AGENTS.md", "[plan](plan.md) [handoff](docs/handoff.md)\n")
            write(root, "plan.md", "# Plan\n")
            write(root, "docs/handoff.md", "# Handoff\n")
            headings = "\n".join(f"## Session {number}" for number in (1, 3, 7, 9, 10, 12))
            write(root, "docs/session-log.md", headings)

            result = inventory.audit(root, args())
            output = inventory.report(result, args())

            self.assertIn("latest 5 session entries (3, 7, 9, 10, 12)", output)

    def test_link_extraction_ignores_examples_globs_and_placeholders(self):
        text = """
`docs/real.md`
`docs/sessions/007-*.md`
`docs/domain/<topic>.md`

```markdown
[example](docs/not-real.md)
`docs/also-not-real.md`
```
"""
        self.assertEqual({"docs/real.md"}, inventory.extract_links(text))

    def test_broken_targets_in_unreachable_docs_do_not_create_noise(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write(root, "AGENTS.md", "[plan](plan.md) [handoff](docs/handoff.md)\n")
            write(root, "plan.md", "# Plan\n")
            write(root, "docs/handoff.md", "# Handoff\n")
            write(root, "docs/orphan.md", "[missing](missing.md)\n")

            result = inventory.audit(root, args())

            self.assertIn("docs/orphan.md", result["orphans"])
            self.assertEqual([], result["broken_links"])

    def test_broken_target_in_reachable_doc_is_reported(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write(root, "AGENTS.md",
                  "[plan](plan.md) [handoff](docs/handoff.md) [rules](docs/rules.md)\n")
            write(root, "plan.md", "# Plan\n")
            write(root, "docs/handoff.md", "# Handoff\n")
            write(root, "docs/rules.md", "[missing](missing.md)\n")

            result = inventory.audit(root, args())

            self.assertEqual([{"from": "docs/rules.md", "link": "missing.md"}],
                             result["broken_links"])

    @unittest.skipUnless(shutil.which("git"), "git is required for commit metadata test")
    def test_git_last_commit_uses_repo_relative_pathspec(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            tracked = write(root, "docs/tracked.md", "# Tracked\n")
            commands = [
                ["git", "init", "-q"],
                ["git", "config", "user.email", "fixture@example.invalid"],
                ["git", "config", "user.name", "Fixture"],
                ["git", "add", "docs/tracked.md"],
            ]
            for command in commands:
                subprocess.run(command, cwd=root, check=True, capture_output=True)
            commit_env = os.environ.copy()
            commit_env["GIT_AUTHOR_DATE"] = "2020-01-02T12:00:00Z"
            commit_env["GIT_COMMITTER_DATE"] = "2020-01-02T12:00:00Z"
            subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=root,
                           check=True, capture_output=True, env=commit_env)

            commit_date, sha = inventory.git_last_commit(root, tracked)
            fresh_age, _ = inventory.freshness(
                tracked.read_text(encoding="utf-8"), tracked.stat().st_mtime, commit_date)

            self.assertEqual("2020-01-02", commit_date)
            self.assertRegex(sha or "", r"^[0-9a-f]{7,}$")
            self.assertGreater(fresh_age, 90)

            tracked.write_text("# Tracked\n\nUpdated now.\n", encoding="utf-8")
            self.assertTrue(inventory.git_worktree_changed(root, tracked))
            dirty_age, _ = inventory.freshness(
                tracked.read_text(encoding="utf-8"), tracked.stat().st_mtime, None)
            self.assertLessEqual(dirty_age, 1)

    def test_state_template_is_valid_and_starts_without_fake_rejections(self):
        template = (SCRIPT.parents[1] / "templates" / "curation-state.json")
        state = json.loads(template.read_text(encoding="utf-8"))
        self.assertEqual(1, state["schema_version"])
        self.assertIsNone(state["last_tuned"])
        self.assertEqual([], state["rejected_candidates"])


if __name__ == "__main__":
    unittest.main()
