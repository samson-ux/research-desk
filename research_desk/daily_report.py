"""End-of-day summary of research runs, the paper journal, gates, and monitoring."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path

from research_desk.approval import approval_matches, approval_path, read_approval
from research_desk.check_latest import collect_runs
from research_desk.mandate import load_mandate
from research_desk.util import chicago_date, now_chicago, parse_date


def build_report(root: Path, day: date) -> str:
    mandate = load_mandate()
    approved = approval_matches(read_approval(approval_path(root)), mandate)
    runs = [run for run in collect_runs(root) if _on_day(run.get("created_at"), day)]
    journal_path = root / "journal" / "paper_trades.csv"
    journal_rows = []
    if journal_path.is_file():
        with journal_path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if _on_day(row.get("timestamp"), day):
                    journal_rows.append(row)
    lines = [
        f"# Daily research desk report {day.isoformat()}",
        "",
        f"Timezone: America/Chicago. Cutoff in force: {mandate['cutoff_date']}.",
        f"Live research approval: {'present' if approved else 'absent — live research blocked'}.",
        "This report does not compute P&L or an investment return.",
        "",
        "## Research runs",
        "",
    ]
    if not runs:
        lines.append("No research runs were created on this date.")
    else:
        for run in runs:
            lines.append(
                f"- {run.get('run_id')}: gate {run.get('gate')}, score {run.get('score')}, "
                f"mode {run.get('mode')}, synthetic {str(run.get('synthetic')).lower()}, "
                f"live_executed {str(run.get('live_research_executed')).lower()}"
            )
    lines.extend(["", "## Gate status", ""])
    if not runs:
        lines.append("No gate to summarize.")
    else:
        counts: dict[str, int] = {}
        for run in runs:
            gate = str(run.get("gate"))
            counts[gate] = counts.get(gate, 0) + 1
        for gate, count in sorted(counts.items()):
            lines.append(f"- {gate}: {count}")
    lines.extend(["", "## Paper journal", ""])
    if not journal_rows:
        lines.append("No paper-journal rows were timestamped on this date.")
    else:
        for row in journal_rows:
            lines.append(
                f"- {row['record_id']} {row['asset']} stance {row['stance']} "
                f"run {row['run_id']} mark {row['mark_status']} "
                f"pnl {row['pnl']} investment_return {row['investment_return']}"
            )
    lines.extend(["", "## Open monitoring", ""])
    open_items = []
    for run in collect_runs(root):
        for item in run.get("monitoring") or []:
            item_day = parse_date(str(item.get("date") or ""))
            if item_day is None or item_day <= day:
                continue
            open_items.append((item_day, run.get("run_id"), item))
    if not open_items:
        lines.append("No monitoring item is still ahead of this report date.")
    else:
        grouped: dict[tuple[str, str, str], set[str]] = {}
        for item_day, run_id, item in open_items:
            sources = " ".join(item.get("source_ids") or [])
            key = (item_day.isoformat(), item.get("text") or "", sources)
            grouped.setdefault(key, set()).add(str(run_id))
        for (item_day, text, sources), run_ids in sorted(grouped.items()):
            lines.append(f"- {item_day} ({', '.join(sorted(run_ids))}) {text} [{sources}]")
    lines.extend(
        [
            "",
            "Rubric compliance is not a forecast. The journal is not a broker.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(root: Path, day: date) -> Path:
    text = build_report(root, day)
    dest = root / "runs" / "daily" / f"{day.isoformat()}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    return dest


def _on_day(stamp: str | None, day: date) -> bool:
    if not stamp:
        return False
    try:
        if "T" in stamp:
            return chicago_date(stamp) == day
        return parse_date(stamp) == day
    except ValueError:
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize one Chicago day's research desk activity.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--date", default=None, help="YYYY-MM-DD in America/Chicago. Defaults to today there.")
    parser.add_argument("--stdout-only", action="store_true")
    args = parser.parse_args(argv)
    day = date.fromisoformat(args.date) if args.date else now_chicago().date()
    root = Path(args.root)
    if args.stdout_only:
        print(build_report(root, day), end="")
        return 0
    dest = write_report(root, day)
    print(dest.read_text(encoding="utf-8"), end="")
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
