import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "berlin-job-search" / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(SCRIPTS))

from linkedin import (
    LinkedInRequestError,
    build_search_url,
    normalize_job_id,
    parse_job_cards,
    parse_job_detail,
    search_jobs_with_errors,
)


class LinkedInParsingTests(unittest.TestCase):
    def test_search_card_fixture(self):
        cards = parse_job_cards((FIXTURES / "linkedin_card.html").read_text(encoding="utf-8"))
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["id"], "4356507350")
        self.assertEqual(cards[0]["title"], "Senior Software Engineer (f/m/d)")
        self.assertEqual(cards[0]["company"], "Upvest")
        self.assertEqual(cards[0]["location"], "Berlin, Germany")
        self.assertEqual(cards[0]["date"], "2026-10-22")

    def test_detail_fixture_extracts_description_and_criteria(self):
        detail = parse_job_detail(
            (FIXTURES / "linkedin_detail.html").read_text(encoding="utf-8"),
            "4385092199",
        )
        self.assertEqual(detail["title"], "Data Engineer - Digital Health Excellence Center (w/m/d)")
        self.assertEqual(detail["company"], "EY")
        self.assertEqual(detail["seniority"], "Mid-Senior level")
        self.assertEqual(detail["employment_type"], "Full-time")
        self.assertEqual(detail["industries"], "Professional Services")
        self.assertIn("Gemeinsam die Welt", detail["description"])
        self.assertIn("german_required", detail["analysis"])
        self.assertTrue(detail["is_active"])

    def test_job_id_normalization_accepts_id_urn_and_linkedin_url(self):
        self.assertEqual(normalize_job_id("4385092199"), "4385092199")
        self.assertEqual(normalize_job_id("urn:li:jobPosting:4385092199"), "4385092199")
        self.assertEqual(
            normalize_job_id("https://de.linkedin.com/jobs/view/data-engineer-at-ey-4385092199?position=1"),
            "4385092199",
        )
        self.assertIsNone(normalize_job_id("https://linkedin.com.evil.test/jobs/view/4385092199"))

    def test_search_parameter_mapping(self):
        url = build_search_url(
            "Berlin, Germany", "data engineer", 7, None, "hybrid",
            "internship,mid-senior", "full-time,contract", True, "103035651", 2,
        )
        params = parse_qs(urlsplit(url).query)
        self.assertEqual(params["keywords"], ["data engineer"])
        self.assertEqual(params["location"], ["Berlin, Germany"])
        self.assertEqual(params["geoId"], ["103035651"])
        self.assertEqual(params["f_TPR"], ["r604800"])
        self.assertEqual(params["f_WT"], ["3"])
        self.assertEqual(params["f_E"], ["1,4"])
        self.assertEqual(params["f_JT"], ["F,C"])
        self.assertEqual(params["f_AL"], ["true"])
        self.assertEqual(params["start"], ["10"])

    def test_search_retains_first_page_when_later_page_fails(self):
        with patch(
            "linkedin.fetch_html",
            side_effect=["page-one", LinkedInRequestError("page two timed out")],
        ), patch("linkedin.parse_job_cards", return_value=[
            {"id": str(index), "title": "Engineer", "location": "Berlin"}
            for index in range(10)
        ]):
            results, errors = search_jobs_with_errors(
                "Berlin", pages=2, limit=20,
            )
        self.assertEqual(len(results), 10)
        self.assertEqual(errors, ["page 2: page two timed out"])


if __name__ == "__main__":
    unittest.main()
