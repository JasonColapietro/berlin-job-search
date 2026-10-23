import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.build_chatgpt_plugin import BuildError, build_plugin, validate_skill


def write_skill(path, name):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\nname: {}\ndescription: Fictional test skill.\n---\n\nFictional instructions.\n".format(name),
        encoding="utf-8",
    )


def make_fake_repository(root):
    plugin_source = root / "chatgpt" / "plugin-src"
    (plugin_source / "assets").mkdir(parents=True)
    (plugin_source / "assets" / "logo.png").write_bytes(b"fictional logo")
    (plugin_source / "assets" / "icon.png").write_bytes(b"fictional icon")
    (plugin_source / "plugin.json").write_text(json.dumps({
        "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        "name": "berlin-job-search",
        "version": "0.1.0",
        "description": "Fictional test plugin.",
        "extensions": {
            "com.openai": {
                "interface": {
                    "displayName": "Berlin Job Search",
                    "shortDescription": "Find German jobs",
                    "category": "Productivity",
                    "defaultPrompt": ["Find a fictional job."],
                    "websiteURL": "{BASE_URL}",
                    "privacyPolicyURL": "{BASE_URL}/privacy",
                    "termsOfServiceURL": "{BASE_URL}/terms",
                },
                "onboardingSkill": "./skills/setup/SKILL.md",
            },
        },
    }), encoding="utf-8")
    (plugin_source / "mcp.json").write_text(json.dumps({
        "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
        "mcpServers": {
            "berlin-job-search": {
                "type": "streamable-http",
                "url": "{BASE_URL}/mcp",
            },
        },
    }), encoding="utf-8")
    write_skill(plugin_source / "skills" / "setup" / "SKILL.md", "setup")
    write_skill(plugin_source / "skills" / "berlin-job-search" / "SKILL.md", "berlin-job-search")

    main_skill = root / "skills" / "berlin-job-search"
    (main_skill / "references").mkdir(parents=True)
    (main_skill / "references" / "fictional-reference.md").write_text("Fictional reference.\n", encoding="utf-8")
    (main_skill / "assets").mkdir()
    (main_skill / "assets" / "companies.json").write_text("[]\n", encoding="utf-8")
    (main_skill / "scripts").mkdir()
    for name in ("analyze_jd.py", "ats_check.py", "render_doc.py", "tracker.py", "report.py",
                 "search.py", "linkedin.py", "job_detail.py"):
        (main_skill / "scripts" / name).write_text("# fictional\n", encoding="utf-8")
    return plugin_source, main_skill


class ChatGPTPluginBuildTests(unittest.TestCase):
    def test_build_replaces_urls_and_creates_single_root_plugin_zip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            plugin_source, _ = make_fake_repository(root)
            output = Path(directory) / "dist"
            package_dir, archive_path = build_plugin(
                "https://berlin-job-search.example", output, repo_root=root,
            )
            manifest = json.loads((package_dir / "plugin.json").read_text(encoding="utf-8"))
            mcp_config = json.loads((package_dir / "mcp.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["extensions"]["com.openai"]["interface"]["websiteURL"],
                             "https://berlin-job-search.example")
            self.assertEqual(
                mcp_config["mcpServers"]["berlin-job-search"]["url"],
                "https://berlin-job-search.example/mcp",
            )
            with zipfile.ZipFile(archive_path) as archive:
                names = archive.namelist()
            self.assertTrue(names)
            self.assertTrue(all(name.startswith("berlin-job-search-plugin/") for name in names))
            self.assertIn("berlin-job-search-plugin/skills/setup/SKILL.md", names)
            self.assertIn("berlin-job-search-plugin/skills/berlin-job-search/assets/companies.json", names)
            self.assertIn(
                "berlin-job-search-plugin/skills/berlin-job-search/scripts/analyze_jd.py",
                names,
            )
            self.assertFalse(any(name.endswith(("/search.py", "/linkedin.py", "/job_detail.py")) for name in names))
            self.assertFalse(any("__pycache__" in name for name in names))
            self.assertTrue((plugin_source / "skills" / "berlin-job-search" / "SKILL.md").is_file())

    def test_skill_file_count_and_size_limits_are_enforced(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / "skill"
            write_skill(skill / "SKILL.md", "skill")
            for index in range(100):
                (skill / "support-{}.md".format(index)).write_text("Fictional.\n", encoding="utf-8")
            with self.assertRaisesRegex(BuildError, "maximum is 100"):
                validate_skill(skill)

            oversized = Path(directory) / "oversized"
            oversized.mkdir()
            (oversized / "SKILL.md").write_text(
                "---\nname: oversized\ndescription: Fictional.\n---\n" + ("x" * (256 * 1024)),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(BuildError, "256 KiB"):
                validate_skill(oversized)

    def test_build_fails_if_a_lead_authored_skill_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            plugin_source, _ = make_fake_repository(root)
            (plugin_source / "skills" / "setup" / "SKILL.md").unlink()
            with self.assertRaisesRegex(BuildError, "required plugin source is missing"):
                build_plugin("https://berlin-job-search.example", Path(directory) / "dist", root)
