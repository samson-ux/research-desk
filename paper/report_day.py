#!/usr/bin/env python3
"""PAPER-ONLY daily report. Writes report.md and prints the same text."""
import csv, json, sys
from pathlib import Path


def build_report(date, live_dir, day_dir):
    live = Path(live_dir)
    day = Path(day_dir)
    lines = [f"# PAPER day report {date}", "", "No broker. No orders. No real money. Prices are Yahoo chart bars only.", ""]
    if not (day / "finalized.json").exists():
        lines.append("Interim report — this session is not finalized yet.")
        lines.append("")
    if not day.exists():
        lines.append(f"Missing folder {day}.")
        return "\n".join(lines) + "\n"
    st = json.load(open(day / "state.json")) if (day / "state.json").exists() else None
    rules = json.load(open(day / "rules.json")) if (day / "rules.json").exists() else {}
    start_eq = float(rules.get("global", {}).get("budget_usd", 1000))
    if st:
        end_eq = float(st.get("equity", start_eq))
        if not st.get("positions") and "realized_pnl" in st:
            end_eq = start_eq + float(st["realized_pnl"])
        closed = st.get("closed") or []
        wins = sum(1 for c in closed if float(c.get("pnl", 0)) > 0)
        lines.append(f"Day P&L: ${end_eq - start_eq:+.2f} ({(end_eq / start_eq - 1) * 100:+.3f}%)  |  equity ${start_eq:.2f} -> ${end_eq:.2f}")
        lines.append(f"Trades: {len(closed)}  wins: {wins}  win rate: {(wins / len(closed) * 100 if closed else 0):.0f}%")
        lines.append(f"Rules version (day): {rules.get('version')}  mode: {st.get('mode')}  job: {st.get('job')}  jobs: {st.get('jobs_seen')}  halted: {st.get('halted')}")
        lines.append(f"Open positions at report time: {len(st.get('positions') or {})}")
        if st.get("yahoo_blocked"):
            lines += ["", "YAHOO_BLOCKED: at least one chart request was rejected or rate-limited. Missing bars were not invented."]
        warns = st.get("startup_warnings") or []
        if warns:
            lines += ["", "## Startup", ""]
            lines += [f"- {w}" for w in warns]
        stalls = st.get("stalls") or []
        if stalls or st.get("missed_entry_window"):
            lines += ["", "## Stall / missed window (no backfill)", ""]
            if not stalls:
                lines.append(f"- missed_entry_window={st.get('missed_entry_window')} (no stall records)")
            for s in stalls:
                lines.append(
                    f"- STALL: {s.get('minutes')} min gap ({s.get('start')}–{s.get('end')} CT) "
                    f"missed_windows={s.get('missed_windows') or []}"
                )
            lines.append(f"- missed_entry_window: {bool(st.get('missed_entry_window'))}")
        lines += ["", "## Trades", ""]
        if closed:
            for c in closed:
                tag = ""
                rule = rules.get("rules", {}).get(c.get("rule") or "", {})
                if rule.get("experimental"):
                    tag = " EXPERIMENTAL"
                lines.append(
                    f"- {c.get('entry_time', '?')}->{c.get('exit_time', '?')}  {c.get('side')} {c.get('ticker')}  "
                    f"rule={c.get('rule')}{tag}  pnl=${float(c.get('pnl', 0)):.2f}  R={float(c.get('r', 0)):.2f}  "
                    f"exit={c.get('reason')}  hold={float(c.get('hold_min', 0)):.1f}m"
                )
        else:
            lines.append("None.")
        lines += ["", "## Per-rule this session", ""]
        lines.append("| rule | experimental | trades | wins | P&L |")
        lines.append("|---|---|---|---|---|")
        for rid, rule in (rules.get("rules") or {}).items():
            if not isinstance(rule, dict):
                continue
            bucket = [c for c in closed if c.get("rule") == rid]
            if not bucket and not rule.get("enabled"):
                continue
            pnl = sum(float(c.get("pnl", 0)) for c in bucket)
            w = sum(1 for c in bucket if float(c.get("pnl", 0)) > 0)
            lines.append(f"| {rid} | {bool(rule.get('experimental'))} | {len(bucket)} | {w} | {pnl:.2f} |")
    else:
        lines.append("No state.json yet.")

    lines += ["", "## Cumulative paper account", ""]
    ledger = list(csv.DictReader(open(live / "ledger.csv"))) if (live / "ledger.csv").exists() else []
    if not ledger:
        lines.append("Ledger empty — finalize has not run.")
    else:
        te = float(ledger[-1]["end_equity"])
        ts = float(ledger[0]["start_equity"])
        tt = sum(int(r["trades"]) for r in ledger)
        tw = sum(int(r["wins"]) for r in ledger)
        lines.append(f"Sessions: {len(ledger)}  start ${ts:.2f} -> ${te:.2f}  total P&L ${te - ts:+.2f} ({(te / ts - 1) * 100:+.3f}%)")
        lines.append(f"Cumulative trades: {tt}  wins: {tw}  win rate: {(tw / tt * 100 if tt else 0):.0f}%")
        for r in ledger:
            lines.append(
                f"- {r['date']}: ${float(r['pnl_usd']):+.2f} ({float(r['pnl_pct']):+.3f}%)  "
                f"trades={r['trades']} wins={r['wins']}  end=${float(r['end_equity']):.2f}  rules_v={r['rules_version']}"
            )

    lines += ["", "## Per-rule cumulative (separate buckets)", ""]
    stats_path = live / "rule_stats.json"
    if stats_path.exists():
        stats = json.load(open(stats_path))
        rule_meta = (rules.get("rules") or {})
        for rid, s in (stats.get("rules") or {}).items():
            meta = rule_meta.get(rid) or {}
            if not meta.get("enabled") and int(s.get("closed", 0)) == 0 and rid not in ("R8", "NR7", "R6", "R7"):
                continue
            n = int(s.get("closed", 0))
            w = int(s.get("wins", 0))
            exp = " EXPERIMENTAL" if meta.get("experimental") else ""
            lines.append(
                f"- {rid}{exp}: n={n} wins={w} wr={(w / n * 100 if n else 0):.0f}%  "
                f"pnl=${float(s.get('pnl', 0)):.2f}  avgR={s.get('avg_r')}  sessions={s.get('sessions')}"
            )
    lines.append("")
    lines.append("Paper only.")
    return "\n".join(lines) + "\n"


def main(date, live_dir, day_dir):
    text = build_report(date, live_dir, day_dir)
    out = Path(day_dir) / "report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    sys.stdout.write(text)
    return text


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit("usage: report_day.py YYYY-MM-DD LIVE_DIR DAY_DIR")
    main(sys.argv[1], sys.argv[2], sys.argv[3])
