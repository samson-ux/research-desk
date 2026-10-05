"""The checked-in fixture runs stay internally consistent."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from research_desk.check_latest import main as check_main

ROOT = Path(__file__).resolve().parents[1]


class CommittedRunTest(unittest.TestCase):
    def test_check_latest_on_the_repo(self):
        self.assertEqual(check_main(["--root", str(ROOT)]), 0)

    def test_synthetic_ready_and_missing_primary_blocked(self):
        ready = json.loads((ROOT / "runs" / "fixtures" / "synthetic-nvda-2026-10-05" / "manifest.json").read_text())
        blocked = json.loads((ROOT / "runs" / "fixtures" / "blocked-missing-primary" / "manifest.json").read_text())
        self.assertEqual(ready["gate"], "READY")
        self.assertFalse(ready["live_research_executed"])
        self.assertTrue(ready["synthetic"])
        self.assertEqual(blocked["gate"], "BLOCKED")
        self.assertEqual(blocked["revision_cycles"], 2)
        report = (ROOT / "runs" / "fixtures" / "blocked-missing-primary" / "report.md").read_text()
        self.assertNotIn("Judgment: conditionally durable.", report)
        self.assertNotIn("999", report)

    def test_integrity_samples_detected_the_three_failures(self):
        sample_dir = ROOT / "runs" / "fixtures" / "integrity-samples"
        for name in ("missing_citation.json", "fabrication.json", "rubric_mutation.json"):
            payload = json.loads((sample_dir / name).read_text())
            self.assertTrue(payload["detected"], name)
            self.assertEqual(payload["gate_if_ungraded_away"], "BLOCKED")

    def test_journal_does_not_compute_pnl(self):
        text = (ROOT / "journal" / "paper_trades.csv").read_text()
        self.assertIn("not_computed", text)
        self.assertNotIn(",computed,", text)
        for line in text.splitlines()[1:]:
            self.assertTrue(line.endswith("not_computed,not_computed"))

    def test_approval_file_is_absent(self):
        self.assertFalse((ROOT / "approvals" / "rubric_approval.json").exists())


if __name__ == "__main__":
    unittest.main()
