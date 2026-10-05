"""Report cutoff, approval, and the latest run. Recomputes the gate from artifacts."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from research_desk import __version__
from research_desk.approval import approval_matches, approval_path, read_approval
from research_desk.mandate import load_mandate
from research_desk.scoring import score_verdicts


def collect_runs(root: Path) -> list[dict]:
    found = []
    runs = root / "runs"
    if not runs.is_dir():
        return []
    for manifest_path in runs.glob("**/manifest.json"):
        if "pending-approval" in manifest_path.parts:
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["_path"] = str(manifest_path.parent)
        found.append(manifest)
    found.sort(key=lambda item: item.get("created_at") or "", reverse=True)
    return found


def verify_run(run_dir: Path) -> list[str]:
    """Return human-readable problems. Empty means the stored gate matches the verdicts."""
    problems = []
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    audit = json.loads((run_dir / "audit.json").read_text(encoding="utf-8"))
    mandate = json.loads((run_dir / "mandate.json").read_text(encoding="utf-8"))
    final = audit["final"]
    scored = score_verdicts(mandate["criteria"], final["verdicts"])
    if scored["gate"] != manifest["gate"]:
        problems.append(f"gate artifact {manifest['gate']} != recomputed {scored['gate']}")
    if Decimal(scored["score"]) != Decimal(manifest["score"]):
        problems.append(f"score artifact {manifest['score']} != recomputed {scored['score']}")
    if manifest.get("expert_validated") is not False:
        problems.append("run is marked expert-validated")
    return problems


def format_status(root: Path) -> tuple[str, list[str]]:
    mandate = load_mandate()
    approval = read_approval(approval_path(root))
    approved = approval_matches(approval, mandate)
    runs = collect_runs(root)
    problems: list[str] = []
    lines = [
        f"research_desk {__version__}",
        f"cutoff: {mandate['cutoff_date']} ({mandate['timezone']})",
        f"asset: {mandate['asset']}",
        f"question: {mandate['question']}",
        f"mandate: {mandate['mandate_id']}",
        f"rubric_sha256: {mandate['rubric_sha256']}",
        f"criteria: {len(mandate['criteria'])}",
        "expert_validated: false",
        f"live research: {'approved' if approved else 'blocked'}",
        "score measures rubric compliance, not a return",
    ]
    if not runs:
        lines.append("runs: none")
    else:
        lines.append(f"runs: {len(runs)}")
        latest = runs[0]
        lines.append(f"latest_run: {latest.get('run_id')} {latest.get('_path')}")
        lines.append(f"latest_gate: {latest.get('gate')} score {latest.get('score')} mode {latest.get('mode')}")
        lines.append(f"latest_live_research_executed: {str(latest.get('live_research_executed')).lower()}")
        for run in runs:
            problems.extend(prefix for prefix in (f"{run.get('run_id')}: {item}" for item in verify_run(Path(run["_path"]))))
            lines.append(
                f"- {run.get('run_id')}: gate {run.get('gate')} score {run.get('score')} "
                f"synthetic {str(run.get('synthetic')).lower()} live_executed {str(run.get('live_research_executed')).lower()}"
            )
    journal = root / "journal" / "paper_trades.csv"
    lines.append(f"paper_journal: {'present' if journal.is_file() else 'absent'}")
    if problems:
        lines.append("integrity: FAILED")
        lines.extend(f"problem: {item}" for item in problems)
    else:
        lines.append("integrity: ok")
    return "\n".join(lines) + "\n", problems


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Show cutoff, rubric approval, and the latest research run.")
    parser.add_argument("--root", default=".", help="Repository root containing runs/ and approvals/.")
    args = parser.parse_args(argv)
    text, problems = format_status(Path(args.root))
    print(text, end="")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
