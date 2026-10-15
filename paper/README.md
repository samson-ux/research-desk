# Paper engine

Always-on **paper-only** US intraday simulator. No broker, no orders, no accounts. Every fill is a real [Yahoo Finance chart](https://query1.finance.yahoo.com) 1-minute bar: the completed close, or a stop, target, or breakout level only when that bar traded through it. Nothing is backfilled after a stall.

The carried book starts at **$1,000** (`ledger.csv`: 2026-10-08 and 2026-10-09 are flat). Risk is **1%** of equity per trade, notional is capped at **$350**, at most **4** positions, and a **−3%** day loss halts new entries. A rule is not dropped, promoted, loosened, or retuned until it has **8 closed trades**. Stats are kept **per rule**.

## Rules

| id | status | window (CT) |
|---|---|---|
| R8 gap fade | primary | 08:35–08:40 |
| NR7 inside / NR7 breakout | EXPERIMENTAL, negative OOS | 08:35–14:30 |
| R6 VWAP reclaim | EXPERIMENTAL, negative OOS (rules v2) | 08:45–14:30 |
| R7 RVOL spike | EXPERIMENTAL, negative OOS (rules v2) | 08:45–14:30 |

R1–R5 stay in `rules.json` and stay disabled. Out-of-sample numbers are in each rule's `oos` field (`backtest_results.csv`: NR7_inside_breakout OOS −$4.59; V2_full, which adds R6 and R7, OOS −$105.28).

## Schedule

A daily routine starts the live session. This workflow has no `schedule` trigger. A late GitHub cron used to publish an empty day over a finished one. `workflow_dispatch` remains for a manual live run or a Yahoo replay. The runner still checks `America/Chicago` and exits on weekends and dates in `nyse_holidays.txt`.

Chicago and Pacific stay two hours apart all year.

| | Chicago | Pacific |
|---|---|---|
| Job A trades | 08:20–11:30 | 06:20–09:30 |
| Job B | 11:25–15:00 | 09:25–13:00 |
| Flatten | 14:55 | 12:55 |

Each job has `timeout-minutes: 330` (under 360). Concurrency group `paper-engine` makes a second run wait instead of trading the same session twice.

A job that starts after its entry window logs `STARTUP` and does not invent the missed trades. A loop gap over 3 minutes logs `STALL` and records overlapping windows in `state.json`.

## State

Job A commits the open book. Job B checks out that book and continues it. Files land on branch `paper-data`:

- `paper-data/YYYY-MM-DD/state.json`
- `paper-data/YYYY-MM-DD/trades.csv`
- `paper-data/YYYY-MM-DD/ledger.csv`
- `paper-data/YYYY-MM-DD/rule_stats.json`
- `paper-data/YYYY-MM-DD/changes.csv` (that session's log)
- `paper-data/YYYY-MM-DD/journal.xlsx`
- `paper-data/YYYY-MM-DD/report.md`

The running ledger, rule stats, tweak book, and `rules_current.json` also sit at `paper-data/` so the next morning can carry the balance. Publish refuses to replace a `paper-data/YYYY-MM-DD` folder that already has trades. Finalize and publish both refuse to replace a ledger row for that date once its trade count is above zero. An empty day can still be replaced. The workflow uses `GITHUB_TOKEN` with `permissions: contents: write`.

## Commands

```bash
pip install -r paper/requirements.txt
python3 -m unittest discover -s paper/tests -v

# Replay one session from Yahoo bars (no sleep). Job B resumes Job A's files.
python3 paper/run_job.py --job A --date 2026-10-09 --replay --data-root /tmp/paper-replay
python3 paper/run_job.py --job B --date 2026-10-09 --replay --data-root /tmp/paper-replay
```

GitHub Actions → paper-engine → Run workflow:

- `replay_date`: `YYYY-MM-DD` or empty for the live session
- `dry_run`: run the engine, do not push `paper-data`
- `job`: `both`, `A`, or `B`

Nothing starts on a timer. Use Run workflow when a replay or a manual session is needed.

## What has to be turned on in the repo

Pushing `paper-data` needs these settings:

1. **Actions enabled** for the repository (Settings → Actions → General → allow actions).
2. **Workflow permissions: Read and write** (Settings → Actions → General → Workflow permissions). A workflow `contents: write` grant cannot exceed this setting, and the default read-only token cannot push `paper-data`.
3. **No ruleset blocking `paper-data`.** The branch is created by `github-actions[bot]` on the first session. It must be able to push with `GITHUB_TOKEN`.

Do not add a broker token. This job never places orders.
