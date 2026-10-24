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


if __name__ == "__main__":
    unittest.main()
