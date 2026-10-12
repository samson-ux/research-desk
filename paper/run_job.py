#!/usr/bin/env python3
"""Run one paper-only job (A morning or B afternoon).

Live mode guards on the America/Chicago clock, weekdays, and NYSE holidays.
Replay mode walks Yahoo 1-minute bars for --date and does not sleep.
Job B finalizes the ledger and writes report.md. Job A leaves positions open.
"""
import argparse, csv, json, os, shutil, subprocess, sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

PAPER = Path(__file__).resolve().parent
CT = ZoneInfo("America/Chicago")
sys.path.insert(0, str(PAPER))

from engine import run_session  # noqa: E402
from lib_finalize import main as finalize_main  # noqa: E402
from report_day import main as report_main  # noqa: E402
from session_guard import guard_live_start, load_holidays  # noqa: E402


def carried_equity(ledger_path, session_date):
    """Last finalized end equity before session_date, else $1,000."""
    path = Path(ledger_path)
    if not path.exists():
        return 1000.0
    rows = list(csv.DictReader(path.open()))
    prior = [r for r in rows if r.get("date", "") < session_date.isoformat()]
    if not prior:
        return 1000.0
    return float(prior[-1]["end_equity"])


def _copy_if_missing(src, dest):
    if src.exists() and not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dest)


def seed_data_root(data_root, branch_seed):
    data_root = Path(data_root)
    data_root.mkdir(parents=True, exist_ok=True)
    seeds = []
    if branch_seed:
        seed = Path(branch_seed)
        seeds.extend([seed / "paper-data", seed])
    seeds.append(PAPER)
    for name in ("ledger.csv", "rule_stats.json", "changes.csv"):
        dest = data_root / name
        for root in seeds:
            _copy_if_missing(root / name, dest)
    rules_dest = data_root / "rules_current.json"
    if not rules_dest.exists():
        for root in seeds:
            if (root / "rules_current.json").exists():
                shutil.copy(root / "rules_current.json", rules_dest)
                break
            if (root / "rules.json").exists():
                shutil.copy(root / "rules.json", rules_dest)
                break


def import_branch_day(data_root, branch_seed, session_date):
    if not branch_seed:
        return
    dest = Path(data_root) / session_date.isoformat()
    for root in (Path(branch_seed) / "paper-data", Path(branch_seed)):
        src = root / session_date.isoformat()
        if not src.is_dir():
            continue
        if not (dest / "state.json").exists() and (src / "state.json").exists():
            shutil.copytree(src, dest, dirs_exist_ok=True)
            print(f"imported day folder from {src}")
            return


def write_day_rules(day, rules_src, session_date, budget):
    dest = day / "rules.json"
    if dest.exists():
        return
    rules = json.loads(Path(rules_src).read_text())
    rules["session_date"] = session_date.isoformat()
    rules["paper_only"] = True
    rules["global"]["budget_usd"] = float(budget)
    rules["global"]["max_position_notional_usd"] = 350.0
    rules["global"]["risk_pct"] = 1.0
    rules["global"]["max_positions"] = 4
    rules["global"]["daily_loss_halt_pct"] = 3.0
    tmp = dest.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(rules, indent=2) + "\n")
    os.replace(tmp, dest)
    (day / "rules_v3.json").write_text(dest.read_text())


def relock_rules(day, budget, session_date):
    path = day / "rules.json"
    rules = json.loads(path.read_text())
    rules["paper_only"] = True
    rules["session_date"] = session_date.isoformat()
    rules["global"]["budget_usd"] = float(budget)
    rules["global"]["max_position_notional_usd"] = 350.0
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(rules, indent=2) + "\n")
    os.replace(tmp, path)


def snapshot_books(data_root, day):
    """Copy the running ledger and per-rule stats into the day folder.

    changes.csv in the day folder is the session log written by the engine.
    The cumulative tweak book stays at the data-root changes.csv.
    """
    for name in ("ledger.csv", "rule_stats.json"):
        src = data_root / name
        if src.exists():
            shutil.copy(src, day / name)
    if not (day / "changes.csv").exists() and (data_root / "changes.csv").exists():
        shutil.copy(data_root / "changes.csv", day / "changes.csv")


def premarket(day):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PAPER)
    try:
        subprocess.run(
            [sys.executable, str(PAPER / "premarket_refresh.py")],
            cwd=day, env=env, timeout=480, check=False,
        )
    except subprocess.TimeoutExpired:
        print("premarket refresh timed out; keeping the carried watchlist")
    except Exception as e:
        print(f"premarket refresh failed ({e}); keeping the carried watchlist")


def run(args):
    data_root = Path(args.data_root).resolve()
    session_date = date.fromisoformat(args.date) if args.date else datetime.now(CT).date()
    seed_data_root(data_root, args.branch_seed)
    import_branch_day(data_root, args.branch_seed, session_date)
    (data_root / "SESSION_DATE").write_text(session_date.isoformat() + "\n")
    day = data_root / session_date.isoformat()
    day.mkdir(parents=True, exist_ok=True)
    done = day / f"job_{args.job.lower()}.done"
    holidays = load_holidays(PAPER / "nyse_holidays.txt")

    if not args.replay:
        if (day / "finalized.json").exists():
            msg = f"SKIP: {session_date} already finalized."
            print(msg)
            (data_root / "RUN_STATUS").write_text("skipped\n")
            return 0
        action, msg = guard_live_start(args.job, datetime.now(CT), holidays, done)
        print(msg)
        if action == "skip":
            (data_root / "RUN_STATUS").write_text("skipped\n")
            return 0
    elif done.exists() and not args.force:
        print(f"SKIP: replay Job {args.job} already finished for {session_date}.")
        (data_root / "RUN_STATUS").write_text("skipped\n")
        return 0

    if args.job == "B" and not (day / "state.json").exists():
        print("WARNING: Job B has no Job A state.json. Afternoon starts flat. No backfill of the morning.")

    budget = carried_equity(data_root / "ledger.csv", session_date)
    print(f"carried start equity for {session_date}: ${budget:.2f}")
    rules_src = data_root / "rules_current.json"
    write_day_rules(day, rules_src, session_date, budget)
    if args.job == "A" and not args.replay and not args.skip_premarket:
        premarket(day)
        relock_rules(day, budget, session_date)

    eng = run_session(args.job, session_date, str(day), replay=args.replay)
    if args.job == "B":
        finalize_main(session_date.isoformat(), str(data_root), str(day))
        # keep the carried rule book next to the seed name the next session reads
        if (data_root / "rules_current.json").exists() and (day / "rules.json").exists():
            pass
    report_main(session_date.isoformat(), str(data_root), str(day))
    snapshot_books(data_root, day)
    done.write_text(datetime.now(CT).isoformat() + "\n")
    (data_root / "RUN_STATUS").write_text("ran\n")
    blocked = bool(eng.state.get("yahoo_blocked"))
    print("YAHOO_BLOCKED" if blocked else "YAHOO_OK")
    print(json.dumps({
        "job": args.job,
        "date": session_date.isoformat(),
        "replay": args.replay,
        "equity": round(eng.equity(), 2),
        "realized": round(eng.state.get("realized_pnl", 0.0), 2),
        "closed": len(eng.state.get("closed") or []),
        "open": len(eng.state.get("positions") or {}),
        "yahoo_blocked": blocked,
        "errors": eng.state.get("errors", 0),
        "day": str(day),
    }, indent=2))
    return 0


def parse_args(argv):
    ap = argparse.ArgumentParser(description="PAPER-ONLY job runner (no broker)")
    ap.add_argument("--job", choices=("A", "B"), required=True)
    ap.add_argument("--date", help="YYYY-MM-DD (default: today America/Chicago)")
    ap.add_argument("--replay", action="store_true")
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--branch-seed", help="unpacked paper-data branch (optional)")
    ap.add_argument("--force", action="store_true", help="re-run even if this job already finished")
    ap.add_argument("--skip-premarket", action="store_true")
    return ap.parse_args(argv)


if __name__ == "__main__":
    try:
        raise SystemExit(run(parse_args(sys.argv[1:])))
    except Exception:
        import traceback
        traceback.print_exc()
        raise SystemExit(1)
