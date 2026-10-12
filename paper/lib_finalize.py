#!/usr/bin/env python3
"""PAPER-ONLY finalize: ledger + per-rule stats + EOD tweaks. Idempotent per session date.

No rule parameter changes until that rule has at least 8 closed trades.
"""
import csv, json, os, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

CT = ZoneInfo("America/Chicago")


def main(date, live_dir, day_dir):
    live = Path(live_dir)
    day = Path(day_dir)
    now = datetime.now(CT).strftime("%Y-%m-%d %H:%M:%S %Z")
    if not day.exists():
        raise SystemExit(f"missing {day}")
    state_path = day / "state.json"
    if not state_path.exists():
        raise SystemExit(f"missing {state_path}")

    st = json.load(open(state_path))
    rules_day = json.load(open(day / "rules.json")) if (day / "rules.json").exists() else {}
    ver = rules_day.get("version", "")
    start_eq = float(rules_day.get("global", {}).get("budget_usd", 1000.0))
    end_eq = float(st.get("equity", start_eq))
    if not st.get("positions") and "realized_pnl" in st:
        end_eq = start_eq + float(st["realized_pnl"])
    pnl = end_eq - start_eq
    pnl_pct = (pnl / start_eq * 100.0) if start_eq else 0.0
    closed = st.get("closed") or []
    trades = len(closed)
    wins = sum(1 for c in closed if float(c.get("pnl", 0)) > 0)

    ledger_path = live / "ledger.csv"
    cols = ["date", "start_equity", "end_equity", "pnl_usd", "pnl_pct", "trades", "wins", "rules_version"]
    rows = list(csv.DictReader(ledger_path.open())) if ledger_path.exists() else []
    new_row = {
        "date": date,
        "start_equity": f"{start_eq:.4f}",
        "end_equity": f"{end_eq:.4f}",
        "pnl_usd": f"{pnl:.4f}",
        "pnl_pct": f"{pnl_pct:.4f}",
        "trades": str(trades),
        "wins": str(wins),
        "rules_version": str(ver),
    }
    already = any(r["date"] == date for r in rows)
    if already:
        print(f"ledger: {date} already present — leaving row unchanged (idempotent)")
    else:
        rows.append(new_row)
        with ledger_path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
        print(f"ledger: appended {date} start={start_eq:.2f} end={end_eq:.2f} pnl={pnl:.2f} trades={trades}")

    stats_path = live / "rule_stats.json"
    stats = json.load(open(stats_path)) if stats_path.exists() else {"rules": {}, "sessions_finalized": []}
    finalized = stats.setdefault("sessions_finalized", [])
    if date in finalized:
        print(f"rule_stats: {date} already merged — skipping trade re-add")
    else:
        for c in closed:
            rid = c.get("rule") or c.get("rule_id") or "?"
            slot = stats.setdefault("rules", {}).setdefault(
                rid, {"closed": 0, "wins": 0, "pnl": 0.0, "sum_r": 0.0, "avg_r": None, "sessions": []}
            )
            slot["closed"] = int(slot.get("closed", 0)) + 1
            if float(c.get("pnl", 0)) > 0:
                slot["wins"] = int(slot.get("wins", 0)) + 1
            slot["pnl"] = float(slot.get("pnl", 0)) + float(c.get("pnl", 0))
            slot["sum_r"] = float(slot.get("sum_r", 0)) + float(c.get("r", 0) or 0)
            n = slot["closed"]
            slot["avg_r"] = round(slot["sum_r"] / n, 4) if n else None
            if date not in slot["sessions"]:
                slot["sessions"].append(date)
        finalized.append(date)
        print(f"rule_stats: merged {trades} closed trades for {date}")

    stats["updated_ct"] = now
    json.dump(stats, open(stats_path, "w"), indent=2)

    rc_path = live / "rules_current.json"
    if not rc_path.exists():
        rc_path = live / "rules.json"
    rc = json.load(open(rc_path))
    rv = rc.get("review", {})
    mt = int(rv.get("min_trades_for_change", 8))
    changes = []

    def chg(rid, param, new, why):
        if rid not in rc.get("rules", {}):
            return
        rule = rc["rules"][rid]
        old = rule.get(param)
        if old == new:
            return
        rule[param] = new
        changes.append((rid, param, old, new, why))

    for rid, rule in rc.get("rules", {}).items():
        slot = stats.get("rules", {}).get(rid, {})
        n = int(slot.get("closed", 0))
        if n < mt:
            continue
        w = int(slot.get("wins", 0))
        wr = w / n if n else 0.0
        pnl_r = float(slot.get("pnl", 0.0))
        if rule.get("enabled") and n >= max(int(rv.get("drop_min_trades", 8)), mt) and wr < float(rv.get("drop_max_winrate", 0.35)) and pnl_r < 0:
            chg(rid, "enabled", False, f"EOD T1 cumulative: {n} trades, win {wr:.0%} < {float(rv.get('drop_max_winrate', 0.35)):.0%}, P&L ${pnl_r:.2f}")
            continue
        if rule.get("enabled") and n >= max(int(rv.get("promote_min_trades", 8)), mt) and wr >= float(rv.get("promote_min_winrate", 0.6)) and pnl_r > 0:
            nr = round(min(float(rule.get("risk_mult", 1.0)) + float(rv.get("risk_mult_step", 0.25)), float(rv.get("risk_mult_max", 1.5))), 2)
            if nr > float(rule.get("risk_mult", 1.0)):
                chg(rid, "risk_mult", nr, f"EOD T4 cumulative: {n} trades, win {wr:.0%}, P&L ${pnl_r:.2f} -> more risk")

    chg_path = live / "changes.csv"
    chg_cols = ["time_ct", "session_date", "rule_id", "param", "old_value", "new_value", "why"]
    if not chg_path.exists() or chg_path.stat().st_size == 0:
        with chg_path.open("w", newline="") as f:
            csv.writer(f).writerow(chg_cols)
    prior = list(csv.DictReader(chg_path.open())) if chg_path.exists() else []
    prior_keys = {(p.get("session_date"), p.get("rule_id"), p.get("param"), p.get("why")) for p in prior}
    wrote = 0
    if changes:
        rc["version"] = int(rc.get("version", 3)) + 1
        dest = live / "rules_current.json"
        tmp = dest.with_suffix(".tmp")
        json.dump(rc, open(tmp, "w"), indent=2)
        os.replace(tmp, dest)
        with chg_path.open("a", newline="") as f:
            wri = csv.writer(f)
            for rid, param, old, new, why in changes:
                key = (date, rid, param, why)
                if key in prior_keys:
                    print(f"change skip (already logged): {rid} {param}")
                    continue
                wri.writerow([now, date, rid, param, old, new, why])
                wrote += 1
                print(f"change: {rid} {param}: {old} -> {new} ({why})")
        day_chg = day / "changes.csv"
        if day_chg.exists():
            with day_chg.open("a", newline="") as f:
                wri = csv.writer(f)
                for rid, param, old, new, why in changes:
                    wri.writerow([now, rid, param, old, new, f"EOD cumulative: {why}"])
    else:
        print(f"EOD tweaks: none (need >= {mt} cumulative closed trades per rule, or thresholds not met)")

    json.dump(stats, open(day / "rule_stats_snapshot.json", "w"), indent=2)
    json.dump(
        {"finalized_ct": now, "ledger_row": new_row, "changes_written": wrote, "already_in_ledger": already},
        open(day / "finalized.json", "w"),
        indent=2,
    )
    print(f"finalize_day {date} done at {now}")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit("usage: lib_finalize.py YYYY-MM-DD LIVE_DIR DAY_DIR")
    main(sys.argv[1], sys.argv[2], sys.argv[3])
