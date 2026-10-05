"""Print the generated rubric and write the pending-approval copy."""

from __future__ import annotations

import json
from pathlib import Path

from research_desk.mandate import load_mandate, positive_weight_sum


def format_rubric(mandate: dict | None = None) -> str:
    mandate = mandate or load_mandate()
    rows = mandate["criteria"]
    lines = [
        "RUBRIC FOR HUMAN APPROVAL",
        "Generated for this desk. Not expert-validated. Not a ResearchRubrics benchmark rubric.",
        f"Asset: {mandate['asset']}",
        f"Question: {mandate['question']}",
        f"Cutoff: {mandate['cutoff_date']} ({mandate['timezone']})",
        f"Horizon end: {mandate['horizon_end']}",
        f"Mandate: {mandate['mandate_id']}",
        f"Rubric SHA256: {mandate['rubric_sha256']}",
        f"Mandate SHA256: {mandate['mandate_sha256']}",
        f"Criteria: {len(rows)}",
        f"Positive weight sum: {positive_weight_sum(rows)}",
        f"Gate: {mandate['gate']['formula']}",
        f"READY if score >= {mandate['gate']['threshold']}, every critical positive verdict is 1,",
        "every critical negative verdict is 0, and no critical criterion is unknown.",
        "Critical means absolute weight 4 or 5.",
        "Negative criteria score the occurrence of the bad behavior (verdict 1 means it occurred).",
        "LIVE RESEARCH: BLOCKED until approvals/rubric_approval.json matches this rubric hash.",
        "",
        f"{'ID':<32} {'W':>3} {'Crit':<5} Axis",
        f"{'-' * 32} {'-' * 3} {'-' * 5} {'-' * 12}",
    ]
    for row in rows:
        crit = "yes" if row["critical"] else "no"
        lines.append(f"{row['id']:<32} {row['weight']:>3} {crit:<5} {row['axis']}")
        lines.append(f"  test: {row['test']}")
    lines.append("")
    lines.append("Do not treat a READY gate as a return, a price target, or an order.")
    return "\n".join(lines) + "\n"


def write_pending(root: Path, mandate: dict | None = None) -> Path:
    mandate = mandate or load_mandate()
    dest = Path(root) / "runs" / "pending-approval"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "mandate.json").write_text(json.dumps(mandate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rubric = {
        "expert_validated": False,
        "note": "Pending human approval. Generated criteria. Not expert-validated.",
        "sha256": mandate["rubric_sha256"],
        "criteria": mandate["criteria"],
    }
    (dest / "rubric.json").write_text(json.dumps(rubric, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (dest / "RUBRIC_SHA256.txt").write_text(mandate["rubric_sha256"] + "\n", encoding="utf-8")
    text = format_rubric(mandate)
    (dest / "RUBRIC.txt").write_text(text, encoding="utf-8")
    (dest / "APPROVAL_GATE.md").write_text(_gate(mandate), encoding="utf-8")
    return dest


def _gate(mandate: dict) -> str:
    return "\n".join(
        [
            "# Approval gate",
            "",
            "Live web research is blocked until a human writes `approvals/rubric_approval.json`",
            "with the rubric hash below. This file is not that approval.",
            "",
            f"- Rubric SHA256: `{mandate['rubric_sha256']}`",
            f"- Mandate SHA256: `{mandate['mandate_sha256']}`",
            f"- Cutoff: `{mandate['cutoff_date']}` ({mandate['timezone']})",
            "- `expert_validated` must stay `false`.",
            "- `approved_by` must be a human name. The desk rejects `agent`.",
            "",
            "A changed rubric is a new mandate and needs a new approval. Historical",
            "evidence from before the cutoff remains usable; the cutoff does not erase it.",
            "",
            "This build has not executed live NVDA research.",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Show the generated NVDA rubric and stop before live research.")
    parser.add_argument("--root", default=".", help="Repository root. Pending copy is written under runs/pending-approval.")
    args = parser.parse_args(argv)
    mandate = load_mandate()
    write_pending(Path(args.root), mandate)
    print(format_rubric(mandate), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
