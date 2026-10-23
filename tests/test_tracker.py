import contextlib
import csv
import datetime as dt
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from argparse import Namespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "berlin-job-search" / "scripts"
SCRIPT = SCRIPTS / "tracker.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(SCRIPTS))

import tracker


class TrackerCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp.name)
        self.env = os.environ.copy()
        self.env["GJS_DATA_DIR"] = str(self.data_dir)

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            env=self.env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_add_list_status_duplicate_and_due(self):
        add = self.run_cli(
            "add", "--company", "Example GmbH", "--title", "Engineer",
            "--url", "https://example.com/jobs/1?utm_source=mail",
            "--location", "Berlin", "--source", "ba",
        )
        self.assertEqual(add.returncode, 0, add.stderr)
        tracker_csv = self.data_dir / "tracker.csv"
        with tracker_csv.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 1)
        identifier = rows[0]["id"]
        self.assertEqual(rows[0]["status"], "saved")
        self.assertEqual(len(rows[0]), 15)

        duplicate = self.run_cli(
            "add", "--company", "Example GmbH", "--title", "Engineer",
            "--url", "https://example.com/jobs/1/",
        )
        self.assertEqual(duplicate.returncode, 2)
        self.assertIn("already tracked", duplicate.stderr)

        listing = self.run_cli("list", "--status", "saved")
        self.assertEqual(listing.returncode, 0)
        self.assertIn("Example GmbH", listing.stdout)

        status = self.run_cli("status", identifier, "applied", "--note", "Application reviewed")
        self.assertEqual(status.returncode, 0, status.stderr)
        listing = self.run_cli("list", "--status", "applied")
        self.assertIn("Engineer", listing.stdout)

        with tracker_csv.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        rows[0]["next_action"] = "Follow up"
        rows[0]["next_action_date"] = "2000-01-01"
        with tracker_csv.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        due = self.run_cli("due")
        self.assertIn("Follow up", due.stdout)
        events = tracker.read_events(self.data_dir / "events.jsonl")
        self.assertEqual(events[-1]["type"], "note")
        self.assertEqual(events[-1]["note"], "status → applied")
        self.assertEqual(rows[0]["applied_date"], dt.date.today().isoformat())

    def test_add_from_search_json(self):
        search_json = self.data_dir / "search.json"
        search_json.write_text(
            '{"jobs":[{"company":"Acme","title":"Analyst","url":"https://acme.test/role/1","location":"Hamburg","source":"arbeitnow"}]}',
            encoding="utf-8",
        )
        result = self.run_cli("add", "--from-json", str(search_json), "--index", "0", "--score", "2.5")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Acme", self.run_cli("list").stdout)
        self.assertEqual(tracker.read_rows(self.data_dir / "tracker.csv")[0]["score"], "2.5")
        invalid = self.run_cli("add", "--from-json", str(search_json), "--index", "0", "--score", "5.1")
        self.assertEqual(invalid.returncode, 2)
        self.assertIn("0.0 to 5.0", invalid.stderr)

    def test_score_validation_range_and_one_decimal_normalization(self):
        self.assertEqual(tracker.normalize_score("0"), "0.0")
        self.assertEqual(tracker.normalize_score("4.5"), "4.5")
        self.assertEqual(tracker.normalize_score("5"), "5.0")
        for value in ("-0.1", "5.1", "1.25", "NaN", "excellent"):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "0.0 to 5.0"):
                tracker.normalize_score(value)
        accepted = self.run_cli(
            "add", "--company", "Fictional Orbit Labs", "--title", "Example Role",
            "--url", "https://orbit.example.test/role", "--score", "0",
        )
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        self.assertEqual(tracker.read_rows(self.data_dir / "tracker.csv")[-1]["score"], "0.0")
        rejected = self.run_cli(
            "add", "--company", "Fictional Orbit Labs", "--title", "Other Role",
            "--url", "https://orbit.example.test/other", "--score", "5.5",
        )
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("0.0 to 5.0", rejected.stderr)

    def test_old_csv_migrates_new_fields_and_rewrites_full_header(self):
        path = self.data_dir / "tracker.csv"
        old_fields = [
            "id", "date_added", "company", "title", "url", "location",
            "source", "status", "score", "next_action", "next_action_date", "notes",
        ]
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=old_fields)
            writer.writeheader()
            writer.writerow({
                "id": "fiction1", "date_added": "2026-01-02", "company": "Northstar Example",
                "title": "Backend Engineer", "url": "https://jobs.example.test/1",
                "location": "Berlin", "source": "sample", "status": "applied",
            })
        rows = tracker.read_rows(path)
        self.assertEqual(rows[0]["applied_date"], "")
        self.assertEqual(rows[0]["last_event_date"], "")
        self.assertEqual(rows[0]["followup_count"], "0")
        tracker.write_rows(path, rows)
        with path.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            self.assertEqual(reader.fieldnames, tracker.FIELDS)
            self.assertEqual(len(next(reader)), len(tracker.FIELDS))

    def test_event_updates_state_dates_and_followup_count(self):
        path = self.data_dir / "tracker.csv"
        identifier = tracker.add_job(path, {
            "company": "Northstar Example", "title": "Backend Engineer",
            "url": "https://jobs.example.test/backend", "source": "fictional",
        })
        applied = tracker.record_event(
            path, identifier, "applied", event_date="2026-02-01", note="Sent the fictional application",
        )
        self.assertEqual(applied["date"], "2026-02-01")
        self.assertEqual(tracker.read_rows(path)[0]["status"], "applied")
        self.assertEqual(tracker.read_rows(path)[0]["applied_date"], "2026-02-01")
        tracker.record_event(path, identifier, "screen", event_date="2026-02-04")
        tracker.record_event(path, identifier, "followup_sent", event_date="2026-02-16")
        row = tracker.read_rows(path)[0]
        self.assertEqual(row["status"], "interview")
        self.assertEqual(row["last_event_date"], "2026-02-16")
        self.assertEqual(row["followup_count"], "1")
        self.assertEqual(
            [event["type"] for event in tracker.read_events(self.data_dir / "events.jsonl")],
            ["applied", "screen", "followup_sent"],
        )

    def test_all_state_event_mappings(self):
        expected = {
            "applied": "applied", "screen": "interview", "interview": "interview",
            "assessment": "interview", "offer": "offer", "accepted": "accepted",
            "rejected": "rejected", "withdrawn": "withdrawn", "ghosted": "ghosted",
        }
        for event_type, status in expected.items():
            with self.subTest(event_type=event_type):
                path = self.data_dir / "{}.csv".format(event_type)
                identifier = tracker.add_job(path, {
                    "company": "Example Orbit", "title": "Fictional Role",
                    "url": "https://jobs.example.test/{}".format(event_type),
                })
                tracker.record_event(path, identifier, event_type, event_date="2026-03-01")
                self.assertEqual(tracker.read_rows(path)[0]["status"], status)

    def test_archive_is_idempotent_and_stubbed_fetch_writes_posting(self):
        path = self.data_dir / "tracker.csv"
        identifier = tracker.add_job(path, {
            "company": "Northstar Example", "title": "Backend Engineer",
            "url": "https://jobs.example.test/backend", "source": "fictional", 
        }, score="4.0")
        tracker.record_event(path, identifier, "applied", event_date="2026-04-01")
        fixture = FIXTURES / "fictional-posting.md"
        args = Namespace(id=identifier, cv=None, letter=None, posting=str(fixture), fetch_posting=True)
        detail = {
            "title": "Backend Engineer",
            "company": "Northstar Example",
            "location": "Berlin",
            "url": "https://jobs.example.test/backend",
            "description_text": "A fictional posting description.",
        }
        with patch.object(tracker, "tracker_path", return_value=path), \
                patch.object(tracker, "fetch_posting", return_value=detail) as fetch, \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            tracker.command_archive(args)
            folder = tracker.archive_folder(self.data_dir, tracker.read_rows(path)[0])
            outcome_before = (folder / "outcome.md").read_text(encoding="utf-8")
            files_before = sorted(item.name for item in folder.iterdir())
            tracker.command_archive(args)
        self.assertEqual(fetch.call_count, 2)
        self.assertEqual(sorted(item.name for item in folder.iterdir()), files_before)
        self.assertEqual((folder / "outcome.md").read_text(encoding="utf-8"), outcome_before)
        self.assertTrue((folder / "fictional-posting.md").is_file())
        self.assertTrue((folder / "posting.json").is_file())
        self.assertTrue((folder / "posting.md").is_file())
        self.assertIn("applied", outcome_before)

    def test_followups_and_stats_zero_division_and_rates(self):
        rows = [
            tracker.normalized_row({
                "id": "applied1", "company": "Northstar Example", "title": "Engineer",
                "source": "fictional", "status": "interview", "applied_date": "2026-01-01",
                "last_event_date": "2026-01-01", "followup_count": "0",
            }),
            tracker.normalized_row({
                "id": "applied2", "company": "Orbit Example", "title": "Analyst",
                "source": "sample", "status": "applied", "applied_date": "2026-01-02",
                "last_event_date": "2026-01-02", "followup_count": "2",
            }),
        ]
        due, ghosted = tracker.followup_candidates(
            rows, today=dt.date(2026, 2, 1), days=10, maximum=2,
        )
        self.assertEqual(due[0]["suggested_action"], "follow-up #1")
        self.assertEqual(ghosted[0]["suggested_action"], "mark ghosted")
        events = [
            {"id": "applied1", "date": "2026-01-01", "type": "applied", "recorded_at": "2026-01-01T09:00:00Z"},
            {"id": "applied1", "date": "2026-01-04", "type": "screen", "recorded_at": "2026-01-04T09:00:00Z"},
            {"id": "applied2", "date": "2026-01-02", "type": "applied", "recorded_at": "2026-01-02T09:00:00Z"},
            {"id": "applied2", "date": "2026-01-10", "type": "offer", "recorded_at": "2026-01-10T09:00:00Z"},
        ]
        stats = tracker.calculate_stats(rows, events)
        self.assertEqual(stats["applied"], 2)
        self.assertEqual(stats["responded"], 2)
        self.assertEqual(stats["response_rate_pct"], 100)
        self.assertEqual(stats["interviews"], 2)
        self.assertEqual(stats["interview_rate_pct"], 100)
        self.assertEqual(stats["offers"], 1)
        self.assertEqual(stats["median_days_to_first_response"], 5.5)
        self.assertEqual(stats["by_source"]["fictional"]["applied"], 1)
        empty = tracker.calculate_stats([], [])
        self.assertEqual(empty["response_rate_pct"], 0)
        self.assertEqual(empty["interview_rate_pct"], 0)
        self.assertEqual(empty["offer_rate_pct"], 0)
        self.assertIsNone(empty["median_days_to_first_response"])

    def test_application_stages_are_cumulative_for_direct_offer(self):
        rows = [tracker.normalized_row({
            "id": "offer-only",
            "company": "Northstar Example",
            "title": "Backend Engineer",
            "source": "fictional",
            "status": "offer",
        })]
        stages = tracker.application_stage_counts(rows, [])
        stats = tracker.calculate_stats(rows, [])
        self.assertEqual(stages, {
            "tracked": 1, "applied": 1, "responded": 1, "interview": 1, "offer": 1,
        })
        self.assertGreaterEqual(stages["tracked"], stages["applied"])
        self.assertGreaterEqual(stages["applied"], stages["responded"])
        self.assertGreaterEqual(stages["responded"], stages["interview"])
        self.assertGreaterEqual(stages["interview"], stages["offer"])
        self.assertEqual(stats["interviews"], stages["interview"])
        self.assertEqual(stats["offers"], stages["offer"])
        self.assertEqual(stats["by_status"], {"offer": 1})


if __name__ == "__main__":
    unittest.main()
