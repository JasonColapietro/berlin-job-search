import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "berlin-job-search" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import render_doc


class RenderDocTests(unittest.TestCase):
    def test_markdown_subset_escapes_html_and_rejects_unsafe_links(self):
        markup = render_doc.render_markdown(
            "# Heading\n\nText <script>alert(1)</script> **bold** *italic* "
            "[safe](https://example.test/path) [bad](javascript:alert(1)) raw <br> outside table.\n\n"
            "- Parent\n  - Child\n\n"
            "| Date | Work |\n|---|---|\n| 01/2020 | **Role**<br>Details |",
            "lebenslauf",
        )
        self.assertIn("&lt;script&gt;", markup)
        self.assertIn("<strong>bold</strong>", markup)
        self.assertIn("<em>italic</em>", markup)
        self.assertIn('href="https://example.test/path"', markup)
        self.assertNotIn('href="javascript:', markup)
        self.assertIn("&lt;br&gt;", markup)
        self.assertIn("<br>", markup)
        self.assertEqual(markup.count("<ul>"), 2)
        self.assertIn('<table class="cv-table">', markup)

    def test_cv_html_structures_for_both_styles(self):
        document = """---
name: Alex Example
title: Fictional Software Engineer
email: alex@example.com
phone: +49 30 5550 0100
location: Berlin, Germany
---

## Experience

### Platform Engineer — Northstar Example Labs

*01/2022 – Present · Berlin*

- Built fictional services.

## Education

| Period | Qualification |
|---|---|
| 09/2018–06/2021 | **Example degree**<br>Example Institute |
"""
        lebenslauf = render_doc.render_html(document, "cv", "lebenslauf", "de")
        self.assertIn('<html lang="de">', lebenslauf)
        self.assertIn('<table class="cv-table">', lebenslauf)
        self.assertIn("font-variant: small-caps", lebenslauf)
        self.assertIn(".cv-table thead { position: absolute;", lebenslauf)
        modern = render_doc.render_html(document, "cv", "modern", "en")
        self.assertIn('<html lang="en">', modern)
        self.assertNotIn("<table", modern)
        self.assertIn(
            '<div class="entry-heading"><h3 class="entry-role">Platform Engineer — Northstar Example Labs</h3>',
            modern,
        )
        self.assertIn(
            '<h3 class="entry-role">Platform Engineer — Northstar Example Labs</h3><p class="date-line">',
            modern,
        )
        self.assertIn('class="date-line"', modern)
        self.assertIn("justify-content: flex-end", modern)
        self.assertIn("flex-wrap: wrap", modern)
        self.assertIn("Alex Example", modern)

    def test_letter_has_sender_recipient_date_subject_and_body(self):
        document = """---
name: Alex Example
email: alex@example.com
phone: +49 30 5550 0100
recipient: Example Company
recipient: Hiring Team
date: 1 July 2026
subject: Application for Backend Engineer
---

Dear Hiring Team,

I am applying for this fictional role.

Kind regards,

Alex Example
"""
        rendered = render_doc.render_html(document, "letter", "modern", "en")
        self.assertIn("class=\"letter-sender\"", rendered)
        self.assertIn("Example Company<br>Hiring Team", rendered)
        self.assertIn("class=\"letter-date\"", rendered)
        self.assertIn("Subject: Application for Backend Engineer", rendered)
        self.assertIn("Dear Hiring Team", rendered)

    def test_photo_is_embedded_as_base64(self):
        with tempfile.TemporaryDirectory() as directory:
            photo = Path(directory) / "photo.png"
            photo.write_bytes(b"fictional-image-bytes")
            document = "---\nname: Alex Example\n---\n## Experience\n"
            rendered = render_doc.render_html(document, "cv", "lebenslauf", "de", str(photo))
        self.assertIn("data:image/png;base64,", rendered)
        self.assertNotIn(str(photo), rendered)

    def test_pdf_path_uses_stubbed_chromium_and_counts_pages(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "cv.md"
            html_path = Path(directory) / "cv.html"
            pdf_path = Path(directory) / "cv.pdf"
            input_path.write_text("---\nname: Alex Example\n---\n## Experience\n", encoding="utf-8")
            calls = []

            def fake_run(command, **kwargs):
                calls.append(command)
                destination = next(arg.split("=", 1)[1] for arg in command if arg.startswith("--print-to-pdf="))
                Path(destination).write_bytes(b"%PDF /Type /Page /Type /Page /Pages")
                return subprocess.CompletedProcess(command, 0, "", "")

            stdout, stderr = io.StringIO(), io.StringIO()
            with patch.object(render_doc, "find_chromium", return_value="/fake/chrome"), \
                    patch.object(render_doc.subprocess, "run", side_effect=fake_run), \
                    contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = render_doc.main([
                    str(input_path), "--type", "cv", "--lang", "en",
                    "--out", str(html_path), "--pdf", str(pdf_path),
                ])
            self.assertEqual(result, 0)
            self.assertTrue(html_path.is_file())
            self.assertTrue(pdf_path.is_file())
            self.assertEqual(len(calls), 1)
            self.assertIn("--headless=new", calls[0])
            self.assertIn("PDF: {} (2 pages)".format(pdf_path), stdout.getvalue())
            self.assertNotIn("warning:", stderr.getvalue())

    def test_pdf_retries_legacy_headless_after_new_mode_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "cv.md"
            pdf_path = Path(directory) / "cv.pdf"
            input_path.write_text("# Fictional CV\n", encoding="utf-8")
            calls = []

            def fake_run(command, **kwargs):
                calls.append(command)
                if len(calls) == 1:
                    return subprocess.CompletedProcess(command, 1, "", "new headless unavailable")
                destination = next(arg.split("=", 1)[1] for arg in command if arg.startswith("--print-to-pdf="))
                Path(destination).write_bytes(b"%PDF /Type /Page /Pages")
                return subprocess.CompletedProcess(command, 0, "", "")

            stdout = io.StringIO()
            with patch.object(render_doc, "find_chromium", return_value="/fake/chrome"), \
                    patch.object(render_doc.subprocess, "run", side_effect=fake_run), \
                    contextlib.redirect_stdout(stdout):
                result = render_doc.main([
                    str(input_path), "--type", "cv", "--pdf", str(pdf_path),
                ])
        self.assertEqual(result, 0)
        self.assertEqual(len(calls), 2)
        self.assertIn("--headless=new", calls[0])
        self.assertIn("--headless", calls[1])
        self.assertNotIn("--headless=new", calls[1])

    def test_missing_chromium_still_writes_html_and_prints_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "letter.md"
            html_path = Path(directory) / "letter.html"
            input_path.write_text("Dear Example,\n\nFictional letter.\n", encoding="utf-8")
            stdout, stderr = io.StringIO(), io.StringIO()
            with patch.object(render_doc, "find_chromium", return_value=None), \
                    contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = render_doc.main([
                    str(input_path), "--type", "letter", "--out", str(html_path),
                    "--pdf", str(Path(directory) / "letter.pdf"),
                ])
            self.assertEqual(result, 0)
            self.assertTrue(html_path.is_file())
            self.assertIn("Print → Save as PDF (A4, no headers/footers)", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
