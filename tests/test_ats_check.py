import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "berlin-job-search" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import ats_check
import render_doc


class AtsCheckTests(unittest.TestCase):
    def test_keyword_derivation_uses_repeated_terms_and_technical_tokens(self):
        jd = (
            "Python services use PostgreSQL, Docker, and Kubernetes. "
            "Build Python services with PostgreSQL. Work with Node.js and C#."
        )
        keywords = ats_check.derive_keywords(jd)
        self.assertIn("Python", keywords)
        self.assertIn("PostgreSQL", keywords)
        self.assertIn("Kubernetes", keywords)
        self.assertIn("Node.js", keywords)
        self.assertIn("C#", keywords)

    def test_keyword_bigrams_require_a_phrase_separator(self):
        keywords = ats_check.derive_keywords(
            "Python services support projects. Python services scale systems. "
            "PostgreSQL, Docker. PostgreSQL, Docker."
        )
        self.assertIn("python services", [item.casefold() for item in keywords])
        self.assertNotIn("postgresql docker", [item.casefold() for item in keywords])

    def test_keyword_derivation_omits_gender_tags_and_stopwords(self):
        keywords = ats_check.derive_keywords(
            "We need a Python engineer (m/w/d). Python engineers use C++."
        )
        self.assertNotIn("m/w/d", [item.casefold() for item in keywords])
        self.assertNotIn("we", [item.casefold() for item in keywords])
        self.assertIn("C++", keywords)

    def test_keyword_matching_uses_word_boundaries_and_reports_coverage(self):
        result = ats_check.keyword_check("Python and JavaScript", ["Java", "Python"])
        self.assertEqual(result["status"], "warn")
        self.assertEqual(result["detail"]["coverage_pct"], 50)
        self.assertEqual(result["detail"]["found"], ["Python"])
        self.assertEqual(result["detail"]["missing"], ["Java"])

    def test_cv_contact_sections_dates_and_gap_checks(self):
        text = """Alex Example
Email: alex@example.com
Phone: +49 30 5550 0100
## Experience
01/2020 – 12/2021
04/2022 – Present
## Education
2016 – 2019
## Skills
Python, Kubernetes
"""
        checks = {item["check"]: item for item in ats_check.analyze_document("".join(text), "cv", None, [])["checks"]}
        self.assertEqual(checks["contact"]["status"], "ok")
        self.assertEqual(checks["sections"]["status"], "ok")
        self.assertEqual(checks["dates"]["status"], "warn")
        self.assertIn("3 months", checks["dates"]["detail"]["gaps"][0])

    def test_dates_warn_on_mixed_formats(self):
        result = ats_check.check_dates("01/2020 – 12/2021; 2022 – Present")
        self.assertEqual(result["status"], "warn")
        self.assertTrue(result["detail"]["mixed_formats"])

    def test_letter_checks_subject_salutation_closing_and_page_limit(self):
        text = """Subject: Fictional role
Dear Hiring Team,
I am applying for a fictional job.
Kind regards,
Alex Example
"""
        checks = {item["check"]: item for item in ats_check.analyze_document(text, "letter", 1, [])["checks"]}
        self.assertEqual(checks["letter_subject"]["status"], "ok")
        self.assertEqual(checks["letter_salutation"]["status"], "ok")
        self.assertEqual(checks["letter_closing"]["status"], "ok")
        self.assertEqual(checks["letter_pages"]["status"], "ok")
        self.assertEqual(checks["keywords"]["status"], "info")

    def test_rendered_letter_html_subject_is_detected(self):
        cases = (
            ("en", "Application for a fictional role", "Dear Hiring Team,", "Kind regards,"),
            ("de", "Bewerbung um eine fiktive Stelle", "Sehr geehrte Damen und Herren,", "Mit freundlichen Grüßen"),
        )
        for lang, subject, salutation, closing in cases:
            document = """---
name: Alex Example
email: alex@example.test
subject: {subject}
---

{salutation}

I am applying for this fictional role.

{closing}

Alex Example
""".format(subject=subject, salutation=salutation, closing=closing)
            html_text = render_doc.render_html(document, "letter", "modern", lang)
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "letter.html"
                path.write_text(html_text, encoding="utf-8")
                text, pages = ats_check.extract_text(path)
            checks = {
                item["check"]: item
                for item in ats_check.analyze_document(text, "letter", pages, [])["checks"]
            }
            with self.subTest(lang=lang):
                self.assertEqual(checks["letter_subject"]["status"], "ok")

    def test_personal_data_check_is_informational(self):
        result = ats_check.check_personal_data(
            "Photo: present. Geburtsdatum: 01.01.1990. Familienstand: ledig. Nationality: fictional."
        )
        self.assertEqual(result["status"], "info")
        self.assertEqual(
            set(result["detail"]["present"]),
            {"photo", "birth_date", "marital_status", "nationality"},
        )

    def test_html_extraction_reuses_text_extractor(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.html"
            path.write_text("<p>Fictional <strong>Python</strong> role.</p><script>hidden()</script>", encoding="utf-8")
            text, pages = ats_check.extract_text(path)
        self.assertIn("Fictional Python role.", text)
        self.assertNotIn("hidden", text)
        self.assertIsNone(pages)

    def test_markdown_front_matter_contact_keeps_underscores(self):
        document = """---
name: Alex Example
email: alex_example@example.test
phone: +49 30 5550 0100
---

## Experience
"""
        text = ats_check.strip_markdown(document)
        self.assertIn("alex_example@example.test", text)
        self.assertEqual(ats_check.check_contact(text)["status"], "ok")

    def test_pdf_extraction_uses_importable_pypdf_when_available(self):
        class FakePage:
            images = []

            def extract_text(self):
                return "Fictional PDF text."

        class FakeReader:
            def __init__(self, _path):
                self.pages = [FakePage(), FakePage()]

        module = types.ModuleType("pypdf")
        module.PdfReader = FakeReader
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.pdf"
            path.write_bytes(b"fictional")
            with patch.dict(sys.modules, {"pypdf": module}):
                text, pages = ats_check.extract_pdf_text(path)
        self.assertEqual(text, "Fictional PDF text.\nFictional PDF text.")
        self.assertEqual(pages, 2)

    def test_pdf_extraction_has_clear_error_without_optional_tools(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.pdf"
            path.write_bytes(b"not a pdf")
            with patch.dict(sys.modules, {"pypdf": None}), patch.object(ats_check.shutil, "which", return_value=None):
                with self.assertRaisesRegex(
                    ValueError,
                    "install pypdf or poppler-utils, or check the HTML instead",
                ):
                    ats_check.extract_pdf_text(path)


if __name__ == "__main__":
    unittest.main()
