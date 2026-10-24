import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "berlin-job-search" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from _common import salary_text


class CommonSalaryTests(unittest.TestCase):
    def test_salary_text_rejects_amountless_labels(self):
        self.assertIsNone(salary_text("EUR YEAR"))
        self.assertIsNone(salary_text({"label": "EUR YEAR"}))
        self.assertEqual(salary_text({"minValue": 50000, "maxValue": 65000}), "50000–65000 EUR")


if __name__ == "__main__":
    unittest.main()
