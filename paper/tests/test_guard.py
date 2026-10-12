#!/usr/bin/env python3
"""Clock, holiday, and stall guards. No market data."""
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from session_guard import (  # noqa: E402
    CT,
    guard_live_start,
    in_start_window,
    late_start_warning,
    load_holidays,
    missed_windows_for_job,
    trading_day_reason,
)

HOL = Path(__file__).resolve().parents[1] / "nyse_holidays.txt"


def ct(y, mo, d, h, mi):
    return datetime(y, mo, d, h, mi, tzinfo=CT)


class GuardTests(unittest.TestCase):
    def test_weekend_and_holiday(self):
        hol = load_holidays(HOL)
        self.assertIn("2026-11-26", hol)
        self.assertEqual(trading_day_reason(ct(2026, 10, 10, 8, 0), hol), "weekend")
        self.assertEqual(trading_day_reason(ct(2026, 11, 26, 8, 0), hol), "NYSE holiday")
        self.assertEqual(trading_day_reason(ct(2026, 10, 9, 8, 0), hol), "")

    def test_job_a_offsets(self):
        hol = load_holidays(HOL)
        ok, _ = in_start_window("A", ct(2026, 10, 9, 7, 50))
        self.assertTrue(ok)
        self.assertIsNone(late_start_warning("A", ct(2026, 10, 9, 7, 50)))
        ok, why = in_start_window("A", ct(2026, 10, 9, 6, 50))
        self.assertFalse(ok, why)
        ok, _ = in_start_window("A", ct(2026, 10, 9, 8, 50))
        self.assertTrue(ok)
        self.assertIn("STARTUP", late_start_warning("A", ct(2026, 10, 9, 8, 50)))
        ok, _ = in_start_window("A", ct(2026, 10, 9, 11, 30))
        self.assertFalse(ok)
        action, msg = guard_live_start("A", ct(2026, 11, 26, 7, 50), hol, None)
        self.assertEqual(action, "skip")
        self.assertIn("holiday", msg)

    def test_job_b_offsets(self):
        ok, _ = in_start_window("B", ct(2026, 10, 9, 10, 25))
        self.assertFalse(ok)
        ok, _ = in_start_window("B", ct(2026, 10, 9, 11, 25))
        self.assertTrue(ok)
        self.assertIsNone(late_start_warning("B", ct(2026, 10, 9, 11, 25)))
        self.assertIn("STARTUP", late_start_warning("B", ct(2026, 10, 9, 12, 0)))
        ok, _ = in_start_window("B", ct(2026, 10, 9, 15, 0))
        self.assertFalse(ok)

    def test_done_marker_skips(self):
        hol = load_holidays(HOL)
        with tempfile.TemporaryDirectory() as td:
            marker = Path(td) / "job_a.done"
            marker.write_text("done")
            action, msg = guard_live_start("A", ct(2026, 10, 9, 7, 50), hol, marker)
            self.assertEqual(action, "skip")
            self.assertIn("already finished", msg)

    def test_job_b_does_not_own_morning_window(self):
        rules = {"R8": {"enabled": True, "window_ct": ["08:35", "08:40"]},
                 "R6": {"enabled": True, "window_ct": ["08:45", "14:30"]}}
        missed = missed_windows_for_job("B", rules, ct(2026, 10, 9, 11, 40))
        self.assertNotIn("R8", missed)
        self.assertNotIn("R6", missed)
        missed = missed_windows_for_job("A", rules, ct(2026, 10, 9, 8, 50))
        self.assertIn("R8", missed)
        self.assertNotIn("R6", missed)


class CarryTests(unittest.TestCase):
    def test_carried_equity_skips_same_day_row(self):
        from run_job import carried_equity
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ledger.csv"
            path.write_text(
                "date,start_equity,end_equity,pnl_usd,pnl_pct,trades,wins,rules_version\n"
                "2026-10-08,1000.0000,1000.0000,0,0,0,0,3\n"
                "2026-10-09,1000.0000,1000.0000,0,0,0,0,3\n"
            )
            self.assertEqual(carried_equity(path, datetime(2026, 10, 9).date()), 1000.0)
            self.assertEqual(carried_equity(path, datetime(2026, 10, 12).date()), 1000.0)


if __name__ == "__main__":
    unittest.main()
