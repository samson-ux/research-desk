"""Finalize and publish must not replace a paper-data day that already has trades."""
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import lib_finalize  # noqa: E402
from lib_finalize import day_folder_has_trades, ledger_trade_count, traded_overwrite_reason  # noqa: E402
from publish_paper_data import publish  # noqa: E402

LEDGER_HEADER = "date,start_equity,end_equity,pnl_usd,pnl_pct,trades,wins,rules_version\n"
DATE = "2026-10-15"


def _git(cwd, *args, env):
    subprocess.check_call(["git", *args], cwd=cwd, env=env)


def _git_env():
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "paper-test"
    env["GIT_AUTHOR_EMAIL"] = "paper-test@example.com"
    env["GIT_COMMITTER_NAME"] = env["GIT_AUTHOR_NAME"]
    env["GIT_COMMITTER_EMAIL"] = env["GIT_AUTHOR_EMAIL"]
    return env


class ReasonTests(unittest.TestCase):
    def test_trades_csv_and_ledger_row(self):
        with tempfile.TemporaryDirectory() as td:
            day = Path(td) / DATE
            day.mkdir()
            (day / "trades.csv").write_text("time_ct,action,ticker\n08:35:33,BUY,CRWD\n")
            self.assertTrue(day_folder_has_trades(day, DATE))
            self.assertIn("already has trades", traded_overwrite_reason(DATE, day_dir=day))

            empty = Path(td) / "empty"
            empty.mkdir()
            (empty / "trades.csv").write_text("time_ct,action,ticker\n")
            (empty / "state.json").write_text(json.dumps({"closed": [], "positions": {}}))
            self.assertFalse(day_folder_has_trades(empty, "empty"))

            ledger = Path(td) / "ledger.csv"
            ledger.write_text(LEDGER_HEADER + f"{DATE},1000,1000.8,0.8,0.08,8,3,4\n")
            self.assertEqual(ledger_trade_count(ledger, DATE), 8)
            self.assertIn("8 trades", traded_overwrite_reason(DATE, ledger_paths=[ledger]))
            ledger.write_text(LEDGER_HEADER + f"{DATE},1000,1000,0,0,0,0,4\n")
            self.assertIsNone(traded_overwrite_reason(DATE, day_dir=empty, ledger_paths=[ledger]))


class FinalizeTests(unittest.TestCase):
    def _day(self, root, closed):
        day = root / DATE
        day.mkdir()
        (day / "state.json").write_text(json.dumps({
            "equity": 1000.0, "realized_pnl": 0.0, "positions": {}, "closed": closed,
        }))
        (root / "rules_current.json").write_text(json.dumps({
            "version": 4, "review": {"min_trades_for_change": 8}, "rules": {},
        }))
        return day

    def test_refuses_traded_ledger_row(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            day = self._day(root, [])
            ledger = root / "ledger.csv"
            original = LEDGER_HEADER + f"{DATE},1000,1000.7988,0.7988,0.0799,8,3,4\n"
            ledger.write_text(original)
            with self.assertRaises(SystemExit) as raised:
                lib_finalize.main(DATE, str(root), str(day))
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(ledger.read_text(), original)
            self.assertFalse((day / "finalized.json").exists())

    def test_appends_when_the_date_is_new(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            day = self._day(root, [{"pnl": 3.38, "rule": "R8", "r": 0.43}])
            ledger = root / "ledger.csv"
            ledger.write_text(LEDGER_HEADER + "2026-10-12,1000,1000,0,0,0,0,4\n")
            lib_finalize.main(DATE, str(root), str(day))
            rows = list(csv.DictReader(ledger.open()))
            self.assertEqual(rows[-1]["date"], DATE)
            self.assertEqual(rows[-1]["trades"], "1")


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.env = _git_env()
        self.repo = self.root / "repo"
        self.bare = self.root / "remote.git"
        self.repo.mkdir()
        _git(self.repo, "init", "-b", "main", env=self.env)
        (self.repo / "README.md").write_text("hi\n")
        _git(self.repo, "add", "README.md", env=self.env)
        _git(self.repo, "commit", "-m", "init", env=self.env)
        _git(self.root, "init", "--bare", str(self.bare), env=self.env)
        _git(self.repo, "remote", "add", "origin", str(self.bare), env=self.env)

    def tearDown(self):
        subprocess.run(
            ["git", "worktree", "remove", "--force", "/tmp/paper-data-worktree"],
            cwd=self.repo, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        shutil.rmtree("/tmp/paper-data-worktree", ignore_errors=True)
        self.tmp.cleanup()

    def _commit_paper_data(self, trades_body, ledger_trades):
        _git(self.repo, "checkout", "--orphan", "paper-data", env=self.env)
        subprocess.run(["git", "rm", "-rf", "--cached", "--ignore-unmatch", "."], cwd=self.repo, check=False)
        for child in self.repo.iterdir():
            if child.name == ".git":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        day = self.repo / "paper-data" / DATE
        day.mkdir(parents=True)
        (day / "trades.csv").write_text("time_ct,action,ticker\n" + trades_body)
        (day / "state.json").write_text(json.dumps({"closed": [], "positions": {}}))
        (self.repo / "paper-data" / "ledger.csv").write_text(
            LEDGER_HEADER + f"{DATE},1000,1000,0,0,{ledger_trades},0,4\n"
        )
        _git(self.repo, "add", "paper-data", env=self.env)
        _git(self.repo, "commit", "-m", f"paper-data: {DATE}", env=self.env)
        _git(self.repo, "push", "-u", "origin", "paper-data", env=self.env)
        _git(self.repo, "checkout", "main", env=self.env)

    def _incoming(self, trades_body, ledger_trades):
        data = self.root / "incoming"
        day = data / DATE
        day.mkdir(parents=True)
        (day / "trades.csv").write_text("time_ct,action,ticker\n" + trades_body)
        (day / "report.md").write_text("incoming\n")
        (data / "ledger.csv").write_text(
            LEDGER_HEADER + f"{DATE},1000,1001,1,0.1,{ledger_trades},1,4\n"
        )
        return data

    def _remote_trades(self):
        return subprocess.check_output(
            ["git", "show", f"paper-data:paper-data/{DATE}/trades.csv"],
            cwd=self.bare, text=True,
        )

    def test_refuses_remote_day_that_has_trades(self):
        self._commit_paper_data("08:35:33,BUY,CRWD\n", 8)
        data = self._incoming("", 0)
        self.assertEqual(publish(self.repo, data, DATE), 2)
        self.assertIn("BUY,CRWD", self._remote_trades())

    def test_refuses_when_only_the_ledger_row_has_trades(self):
        self._commit_paper_data("", 8)
        data = self._incoming("08:35:33,BUY,AFRM\n", 1)
        self.assertEqual(publish(self.repo, data, DATE), 2)
        self.assertNotIn("AFRM", self._remote_trades())

    def test_replaces_an_empty_day(self):
        self._commit_paper_data("", 0)
        data = self._incoming("08:35:33,BUY,NVDA\n", 1)
        self.assertEqual(publish(self.repo, data, DATE), 0)
        self.assertIn("BUY,NVDA", self._remote_trades())


if __name__ == "__main__":
    unittest.main()
