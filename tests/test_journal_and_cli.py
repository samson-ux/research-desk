"""Paper journal, daily report, check_latest, and show_rubric."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from research_desk.check_latest import main as check_main
from research_desk.daily_report import build_report
from research_desk.util import chicago_date
from research_desk.paper_journal import (
    fetch_public_price,
    log_call,
    main as journal_main,
    mark,
    parse_yahoo_chart,
    report,
)
from research_desk.pipeline import run_research
from research_desk.show_rubric import main as rubric_main
from research_desk.mandate import load_mandate


class _Response:
    def __init__(self, payload: bytes):
        self._payload = payload
        self.status = 200

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class JournalTest(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.run_dir = self.root / "runs" / "fixtures" / "synthetic-nvda-2026-10-05"
        run_research(self.run_dir, run_id="synthetic-nvda-2026-10-05")

    def tearDown(self):
        self.tmp.cleanup()

    def test_log_links_the_run_and_does_not_compute_pnl(self):
        record = log_call(
            self.root,
            run_id="synthetic-nvda-2026-10-05",
            asset="NVDA",
            stance="conditional",
            note="Synthetic fixture thesis only. Not an order.",
        )
        self.assertTrue(record["thesis_link"].endswith("report.md#thesis"))
        self.assertEqual(record["pnl"], "not_computed")
        self.assertEqual(record["investment_return"], "not_computed")
        self.assertEqual(record["price_observation_ratio"], "unavailable")
        with self.assertRaises(ValueError):
            log_call(self.root, run_id="synthetic-nvda-2026-10-05", asset="NVDA", stance="buy", note="no")

    def test_cli_rejects_shares(self):
        code = journal_main(
            [
                "--root",
                str(self.root),
                "log",
                "--run-id",
                "synthetic-nvda-2026-10-05",
                "--stance",
                "conditional",
                "--note",
                "no",
                "--shares",
                "10",
            ]
        )
        self.assertEqual(code, 2)
        self.assertFalse((self.root / "journal" / "paper_trades.csv").exists())

    def test_missing_price_does_not_invent_a_mark(self):
        log_call(
            self.root,
            run_id="synthetic-nvda-2026-10-05",
            asset="NVDA",
            stance="unresolved",
            note="No price yet.",
        )
        rows = mark(self.root, fetch=False)
        self.assertEqual(rows[0]["mark_status"], "unavailable")
        self.assertEqual(rows[0]["mark_price"], "")
        self.assertEqual(rows[0]["pnl"], "not_computed")
        text = report(self.root)
        self.assertIn("not_computed", text)
        self.assertIn("unavailable", text)
        self.assertNotIn("P&L:", text)

    def test_two_fixture_marks_show_a_quote_change_and_still_no_pnl(self):
        log_call(
            self.root,
            run_id="synthetic-nvda-2026-10-05",
            asset="NVDA",
            stance="conditional",
            note="Synthetic.",
        )
        first = self.root / "price-a.json"
        second = self.root / "price-b.json"
        first.write_text(
            json.dumps({"asset": "NVDA", "price": "100.00", "currency": "USD", "source": "fixture://a", "synthetic": True}),
            encoding="utf-8",
        )
        second.write_text(
            json.dumps({"asset": "NVDA", "price": "110.00", "currency": "USD", "source": "fixture://b", "synthetic": True}),
            encoding="utf-8",
        )
        mark(self.root, fixture=first)
        rows = mark(self.root, fixture=second)
        self.assertEqual(rows[0]["price_observation_ratio"], "0.1000")
        self.assertEqual(rows[0]["pnl"], "not_computed")
        self.assertEqual(rows[0]["investment_return"], "not_computed")
        text = report(self.root)
        self.assertIn("not position P&L", text)
        self.assertIn("0.1000", text)

    def test_failed_fetch_records_unavailable(self):
        log_call(
            self.root,
            run_id="synthetic-nvda-2026-10-05",
            asset="NVDA",
            stance="conditional",
            note="Fetch will fail.",
        )

        def opener(*_args, **_kwargs):
            raise OSError("offline")

        rows = mark(self.root, fetch=True, opener=opener)
        self.assertEqual(rows[0]["mark_status"], "unavailable")
        self.assertEqual(rows[0]["mark_price"], "")
        self.assertEqual(rows[0]["pnl"], "not_computed")

    def test_yahoo_parser_reads_only_the_quoted_price(self):
        body = json.dumps({"chart": {"result": [{"meta": {"regularMarketPrice": 123.456}}]}}).encode()
        self.assertEqual(parse_yahoo_chart(body), "123.46")
        with self.assertRaises(ValueError):
            parse_yahoo_chart(b'{"chart": {"result": [{"meta": {}}]}}')

        def opener(_request, timeout=0):
            return _Response(body)

        price, source = fetch_public_price("NVDA", opener=opener)
        self.assertEqual(price, "123.46")
        self.assertIn("query1.finance.yahoo.com", source)
        self.assertIn("NVDA", source)


class ReportCliTest(unittest.TestCase):
    def test_daily_report_includes_gate_journal_and_open_monitoring(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_research(root / "runs" / "fixtures" / "synthetic-nvda-2026-10-05", run_id="synthetic-nvda-2026-10-05")
            log_call(
                root,
                run_id="synthetic-nvda-2026-10-05",
                asset="NVDA",
                stance="conditional",
                note="Daily fixture.",
            )
            manifest = json.loads((root / "runs" / "fixtures" / "synthetic-nvda-2026-10-05" / "manifest.json").read_text())
            text = build_report(root, chicago_date(manifest["created_at"]))
        self.assertIn("gate READY", text)
        self.assertIn("Live research approval: absent", text)
        self.assertIn("conditional", text)
        self.assertIn("not_computed", text)
        self.assertIn("2026-11-18", text)
        self.assertIn("pnl not_computed", text)

    def test_show_rubric_and_check_latest(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            code = rubric_main(["--root", tmp])
            self.assertEqual(code, 0)
            mandate = load_mandate()
            pending = (root / "runs" / "pending-approval" / "RUBRIC_SHA256.txt").read_text(encoding="utf-8").strip()
            self.assertEqual(pending, mandate["rubric_sha256"])
            gate = (root / "runs" / "pending-approval" / "APPROVAL_GATE.md").read_text(encoding="utf-8")
            self.assertIn("expert_validated", gate)
            self.assertIn("false", gate)
            rubric_txt = (root / "runs" / "pending-approval" / "RUBRIC.txt").read_text(encoding="utf-8")
            self.assertIn("Not expert-validated", rubric_txt)
            run_research(root / "runs" / "fixtures" / "synthetic-nvda-2026-10-05", run_id="synthetic-nvda-2026-10-05")
            self.assertEqual(check_main(["--root", tmp]), 0)


if __name__ == "__main__":
    unittest.main()
