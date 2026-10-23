import tempfile
import unittest
from pathlib import Path

from tools.sync_commands import check_commands, sync_commands

try:
    import tomllib
except ImportError:
    tomllib = None


class SyncCommandsTests(unittest.TestCase):
    def test_generates_agent_formats_and_preserves_arguments(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_dir = root / "commands"
            source_dir.mkdir()
            (source_dir / "fictional-search.md").write_text(
                "---\n"
                "description: Search fictional job data\n"
                "argument-hint: \"<role> [city]\"\n"
                "---\n\n"
                "Search only the fictional source for: $ARGUMENTS\n",
                encoding="utf-8",
            )
            self.assertEqual(sync_commands(source_dir, root), [])
            claude = (root / ".claude" / "commands" / "fictional-search.md").read_text(encoding="utf-8")
            opencode = (root / ".opencode" / "commands" / "fictional-search.md").read_text(encoding="utf-8")
            gemini = (root / ".gemini" / "commands" / "fictional-search.toml").read_text(encoding="utf-8")
            self.assertIn("# generated from commands/fictional-search.md, do not edit.", claude)
            self.assertIn('argument-hint: "<role> [city]"', claude)
            self.assertIn("$ARGUMENTS", claude)
            self.assertIn("description: Search fictional job data", opencode)
            self.assertIn("$ARGUMENTS", opencode)
            self.assertIn('description = "Search fictional job data"', gemini)
            self.assertIn("{{args}}", gemini)
            self.assertNotIn("$ARGUMENTS", gemini)
            if tomllib is not None:
                toml_data = tomllib.loads(gemini)
                self.assertEqual(toml_data["description"], "Search fictional job data")
                self.assertIn("{{args}}", toml_data["prompt"])
            self.assertEqual(sync_commands(source_dir, root, check=True), [])

    def test_check_reports_out_of_sync_and_stale_generated_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_dir = root / "commands"
            source_dir.mkdir()
            (source_dir / "fictional.md").write_text(
                "---\ndescription: Fictional\nargument-hint: [role]\n---\n\n$ARGUMENTS\n",
                encoding="utf-8",
            )
            sync_commands(source_dir, root)
            (root / ".claude" / "commands" / "fictional.md").write_text("out of date\n", encoding="utf-8")
            (root / ".gemini" / "commands" / "stale.toml").write_text(
                "# generated from commands/old.md, do not edit\n", encoding="utf-8",
            )
            errors = sync_commands(source_dir, root, check=True)
            self.assertTrue(any("out of sync" in error for error in errors))
            self.assertTrue(any("stale generated command" in error for error in errors))

    def test_validator_calls_sync_check(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(check_commands(root), [])


if __name__ == "__main__":
    unittest.main()
