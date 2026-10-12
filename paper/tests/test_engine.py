#!/usr/bin/env python3
"""Rule behavior on fixture bars. These bars are not market data and are not fetched."""
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine import Engine  # noqa: E402

CT = ZoneInfo("America/Chicago")
UTC = ZoneInfo("UTC")


def _engine(job="A"):
    td = tempfile.TemporaryDirectory()
    eng = Engine("REPLAY", datetime(2026, 10, 9).date(), td.name, job=job)
    eng._td = td
    return eng


class EngineRuleTests(unittest.TestCase):
    def tearDown(self):
        if hasattr(self, "eng"):
            self.eng._td.cleanup()

    def test_nr7_fires_only_on_the_breaking_bar(self):
        self.eng = _engine()
        base = int(datetime(2026, 10, 9, 13, 30, tzinfo=UTC).timestamp())
        bars = []
        for i in range(6):
            bars.append({"t": base + i * 60, "o": 99.0, "h": 99.4, "l": 98.6, "c": 99.0, "v": 1000})
        bars[-2]["h"] = 100.0
        bars[-1]["o"] = 100.2
        bars[-1]["h"] = 101.0
        bars[-1]["c"] = 100.8
        self.eng.ctx = {"NVDA": {
            "prev_close": 99.0, "prev_high": 100.0, "prev_low": 95.0, "atr14": 2.0,
            "flags": ["NR7"], "slot_vol14": {},
        }}
        s5 = [{"t": base, "o": 99, "h": 99.4, "l": 98.6, "c": 99, "v": 6000, "ema20": 99, "vwap": 99}]
        ind = {"price": 100.8, "last": bars[-1], "vwap": 99.5, "s5": s5, "ema20": 99, "atr5": 1.0, "sess": bars}
        now_ts = bars[-1]["t"] + 60
        now_ct = datetime.fromtimestamp(now_ts, CT)
        sigs = self.eng.signals("NVDA", {"NVDA": ind}, now_ts, now_ct)
        nr = [s for s in sigs if s["rule"] == "NR7"]
        self.assertEqual(len(nr), 1)
        self.assertEqual(nr[0]["side"], "long")
        self.assertEqual(nr[0]["level"], 100.0)
        quiet = [dict(b) for b in bars]
        quiet[-1]["h"] = 100.0
        ind2 = dict(ind, last=quiet[-1], sess=quiet, price=100.0)
        sigs2 = self.eng.signals("NVDA", {"NVDA": ind2}, now_ts, now_ct)
        self.assertFalse([s for s in sigs2 if s["rule"] == "NR7"])

    def test_eight_trade_minimum_blocks_then_allows_tweak(self):
        self.eng = _engine()
        self.assertTrue(self.eng.rules["rules"]["R6"]["enabled"])
        self.assertEqual(self.eng.rules["global"]["max_position_notional_usd"], 350.0)
        self.assertEqual(self.eng.rules["review"]["min_trades_for_change"], 8)
        now = datetime(2026, 10, 9, 10, 32, tzinfo=CT)
        self.eng.review("10:32", now)
        self.assertEqual(self.eng.rules["rules"]["R6"]["vol_mult"], 1.2)
        self.eng.state["closed"] = [
            {"rule": "R6", "pnl": -1.0, "r": -1.0, "reason": "STOP", "hold_min": 10} for _ in range(7)
        ]
        self.eng.review("11:32", now)
        self.assertTrue(self.eng.rules["rules"]["R6"]["enabled"])
        self.eng.state["closed"].append(
            {"rule": "R6", "pnl": -1.0, "r": -1.0, "reason": "STOP", "hold_min": 10}
        )
        self.eng.review("12:32", now)
        self.assertFalse(self.eng.rules["rules"]["R6"]["enabled"])
        rules = json.loads(Path(self.eng.p["rules"]).read_text())
        self.assertFalse(rules["rules"]["R6"]["enabled"])
        self.assertTrue(self.eng.rules["rules"]["R8"]["enabled"])
        self.assertTrue(self.eng.rules["rules"]["NR7"]["enabled"])

    def test_stall_guard_records_overlap_and_does_not_invent_trades(self):
        self.eng = _engine()
        self.eng.state["last_loop_ct"] = datetime(2026, 10, 9, 8, 36, tzinfo=CT).isoformat()
        trades_before = Path(self.eng.p["trades"]).read_text()
        rec = self.eng.detect_stall(datetime(2026, 10, 9, 8, 41, tzinfo=CT))
        self.assertIsNotNone(rec)
        self.assertIn("R8", rec["missed_windows"])
        self.assertTrue(self.eng.state["missed_entry_window"])
        self.assertEqual(Path(self.eng.p["trades"]).read_text(), trades_before)
        self.assertIsNone(self.eng.detect_stall(datetime(2026, 10, 9, 8, 42, tzinfo=CT)))


if __name__ == "__main__":
    unittest.main()
