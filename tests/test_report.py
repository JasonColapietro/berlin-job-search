import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "berlin-job-search" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import report
import tracker


class ReportTests(unittest.TestCase):
    def test_empty_data_renders_friendly_self_contained_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "report.html"
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(report.main(["--data-dir", directory, "--out", str(output)]), 0)
            text = output.read_text(encoding="utf-8")
        self.assertIn("Nothing due right now.", text)
        self.assertIn("No applications tracked yet.", text)
        self.assertIn("<svg", text)
        self.assertIn("prefers-color-scheme", text)
        self.assertIn("addEventListener", text)
        self.assertNotIn("<script src=", text)
        self.assertIn("No external resources are loaded.", text)

    def test_sample_report_escapes_untrusted_fields_and_links_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            row = tracker.normalized_row({
                "id": "sample1",
                "date_added": "2026-05-01",
                "company": "Northstar <script>alert(1)</script>",
                "title": '<img src=x onerror=alert(1)>',
                "url": "javascript:alert(1)",
                "location": "Berlin",
                "source": "fictional",
                "status": "applied",
            "score": "4",
                "applied_date": "2026-05-01",
                "last_event_date": "2026-05-02",
                "followup_count": "0",
            })
            tracker.write_rows(root / "tracker.csv", [row])
            event = {
                "id": "sample1",
                "date": "2026-05-01",
                "type": "applied",
                "note": "",
                "recorded_at": "2026-05-01T10:00:00+00:00",
            }
            (root / "events.jsonl").write_text(json.dumps(event) + "\n", encoding="utf-8")
            folder = tracker.archive_folder(root, row)
            folder.mkdir(parents=True)
            (folder / "outcome.md").write_text("# Fictional outcome\n", encoding="utf-8")
            (folder / "posting.md").write_text("# Fictional posting\n", encoding="utf-8")
            output = root / "report.html"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(report.main(["--data-dir", directory, "--out", str(output)]), 0)
            text = output.read_text(encoding="utf-8")
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", text)
        self.assertNotIn('<img src=x onerror=alert(1)>', text)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", text)
        self.assertNotIn('href="javascript:', text)
        self.assertIn("Outcome", text)
        self.assertIn("Posting archive", text)
        self.assertIn("company", text)
        self.assertIn("Last event", text)
        self.assertIn(">4.0</td>", text)

    def test_funnel_matches_tracker_stats_for_direct_offer_without_interview_event(self):
        row = tracker.normalized_row({
            "id": "offer-only",
            "company": "Northstar Example",
            "title": "Backend Engineer",
            "status": "offer",
            "source": "fictional",
        })
        rows = [row]
        events = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            summary = tracker.calculate_stats(rows, events)
            markup = report.build_report(rows, events, root, root / "report.html")
        stages = tracker.application_stage_counts(rows, events)
        self.assertEqual(summary["tracked"], stages["tracked"])
        self.assertEqual(summary["applied"], stages["applied"])
        self.assertEqual(summary["responded"], stages["responded"])
        self.assertEqual(summary["interviews"], stages["interview"])
        self.assertEqual(summary["offers"], stages["offer"])
        self.assertIn('data-stage="tracked" data-value="1"', markup)
        self.assertIn('data-stage="interview" data-value="1"', markup)
        self.assertIn('data-stage="offer" data-value="1"', markup)
        self.assertIn(">Tracked<", markup)
        self.assertNotIn("<td>saved</td>", markup)


if __name__ == "__main__":
    unittest.main()
