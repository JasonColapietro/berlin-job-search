import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SkillAssetTests(unittest.TestCase):
    def test_profile_template_does_not_assume_citizenship(self):
        template = (ROOT / "skills" / "berlin-job-search" / "assets" / "profile.template.yml").read_text(
            encoding="utf-8",
        )
        self.assertRegex(template, re.compile(r"(?m)^citizenship:\s*null\s+#.*eu.*non_eu", re.I))

    def test_profile_template_does_not_assume_work_preferences_or_student_plan(self):
        template = (ROOT / "skills" / "berlin-job-search" / "assets" / "profile.template.yml").read_text(
            encoding="utf-8",
        )
        self.assertRegex(template, re.compile(r"(?m)^  relocate:\s*null\s+#.*true.*false", re.I))
        self.assertRegex(template, re.compile(r"(?m)^remote_preference:\s*null\s+#.*remote.*hybrid", re.I))
        self.assertRegex(template, re.compile(
            r"(?ms)^student:[ \t]*\n[ \t]+graduation:[ \t]*null\b.*?\n[ \t]+wants:[ \t]*null[ \t]*#.*werkstudent.*full_time.*both",
        ))

if __name__ == "__main__":
    unittest.main()
