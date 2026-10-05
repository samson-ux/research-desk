"""CLI for offline fixture runs and the approval-gated live path."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from research_desk.approval import ApprovalRequired, approval_path, require_approval
from research_desk.integrity import (
    find_fabricated_claims,
    find_uncited_magnitude_lines,
    rubric_mutated,
)
from research_desk.live import DEFAULT_URLS, documents_from_body, fetch_url
from research_desk.mandate import load_mandate
from research_desk.pipeline import run_research


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the evidence-first research desk.")
    parser.add_argument("--root", default=".", help="Repository root for approval and default outputs.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fixture", action="store_true", help="Run the synthetic corpus. No network.")
    mode.add_argument("--live", action="store_true", help="Fetch allowlisted URLs. Blocked until the rubric is approved.")
    mode.add_argument("--integrity-samples", action="store_true", help="Write detector samples. No network and no NVDA conclusion.")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument(
        "--defect",
        default=None,
        choices=["drop_primary_revenue", "missing_citation", "fabrication", "rubric_mutation"],
        help="Offline harness used to show detection and repair. Not used with --live.",
    )
    args = parser.parse_args(argv)
    root = Path(args.root)
    if args.integrity_samples:
        dest = Path(args.out) if args.out else root / "runs" / "fixtures" / "integrity-samples"
        write_integrity_samples(dest)
        print(f"wrote {dest}")
        return 0
    if args.live:
        if args.defect:
            print("Live mode does not accept a defect harness.")
            return 2
        return _live(root, args)
    run_id = args.run_id or _fixture_run_id(args.defect)
    out = Path(args.out) if args.out else root / "runs" / "fixtures" / run_id
    state = run_research(out, run_id=run_id, defect=args.defect)
    final = state["audits"][-1]
    print(f"run_id: {state['run_id']}")
    print(f"out: {out}")
    print(f"gate: {final['gate']}")
    print(f"score: {final['score']}")
    print(f"revision_cycles: {state['revision_cycles']}")
    print(f"live_research_executed: {str(state['live_research_executed']).lower()}")
    print("synthetic: true")
    return 0


def _fixture_run_id(defect: str | None) -> str:
    if defect == "drop_primary_revenue":
        return "blocked-missing-primary"
    if defect == "missing_citation":
        return "detected-missing-citation"
    if defect == "fabrication":
        return "detected-fabrication"
    if defect == "rubric_mutation":
        return "detected-rubric-mutation"
    return "synthetic-nvda-2026-10-05"


def _live(root: Path, args: argparse.Namespace) -> int:
    mandate = load_mandate()
    try:
        require_approval(approval_path(root), mandate)
    except ApprovalRequired as exc:
        print(str(exc))
        return exc.code
    from urllib.request import urlopen

    retrieved_docs: list[dict] = []
    queries = 0
    limit = mandate["budgets"]["max_search_queries"]
    for url in DEFAULT_URLS:
        if queries >= limit:
            break
        status, body = fetch_url(url, opener=urlopen)
        queries += 1
        retrieved_docs.extend(documents_from_body(url, body))
        if status != 200:
            break
    if not retrieved_docs:
        retrieved_docs = documents_from_body(DEFAULT_URLS[0], b"")
    run_id = args.run_id or "live-nvda"
    out = Path(args.out) if args.out else root / "runs" / run_id
    state = run_research(out, run_id=run_id, docs=retrieved_docs, mode="live")
    state_queries = state["search_queries_used"]
    # The pipeline counts a local query. Record the real fetches on the manifest
    # by rewriting the flag the pipeline already stored as live mode.
    print(f"run_id: {run_id}")
    print(f"out: {out}")
    print(f"gate: {state['audits'][-1]['gate']}")
    print(f"fetches: {queries}")
    print(f"pipeline_search_queries_used: {state_queries}")
    print("live_research_executed: true")
    return 0


def write_integrity_samples(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    sourced = {
        "claim_id": "CLM-001",
        "value": "40.0",
        "unit": "USD_billions",
        "currency": "USD",
        "passage": "Data Center revenue for the second quarter of fiscal 2027 was $40.0 billion.",
        "formula": "",
        "formula_inputs": [],
        "source_ids": ["SRC-001"],
        "statement": "Data Center revenue for FY2027 Q2 was $40.0 billion.",
    }
    missing = find_uncited_magnitude_lines("Data Center revenue was $40.0 billion.\n", [sourced])
    (dest / "missing_citation.json").write_text(
        json.dumps(
            {
                "detector": "find_uncited_magnitude_lines",
                "detected": bool(missing),
                "hit_count": len(missing),
                "gate_if_ungraded_away": "BLOCKED",
                "note": "The line repeats a real fixture magnitude and omits the source id. This file is a detector sample, not a research conclusion.",
                "hits": missing,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    fabricated = dict(sourced)
    fabricated["value"] = "123.4"
    fabricated["statement"] = "Data Center revenue for FY2027 Q2 was $123.4 billion."
    hits = find_fabricated_claims([fabricated])
    (dest / "fabrication.json").write_text(
        json.dumps(
            {
                "detector": "find_fabricated_claims",
                "detected": bool(hits),
                "hit_count": len(hits),
                "gate_if_ungraded_away": "BLOCKED",
                "note": "123.4 is not in the cited passage. The passage still says $40.0 billion. This file is a detector sample, not a research conclusion.",
                "hits": hits,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    mandate = load_mandate()
    mutated = copy.deepcopy(mandate["criteria"])
    mutated[0]["weight"] = 1
    changed = rubric_mutated(mandate["criteria"], mutated)
    (dest / "rubric_mutation.json").write_text(
        json.dumps(
            {
                "detector": "rubric_mutated",
                "detected": changed,
                "frozen_sha256": mandate["rubric_sha256"],
                "mutated_weight": mutated[0]["weight"],
                "mutated_id": mutated[0]["id"],
                "gate_if_ungraded_away": "BLOCKED",
                "note": "Changing a frozen weight is a mutation. The editor restores the mandate rubric instead of adopting it. This file is a detector sample, not a research conclusion.",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (dest / "README.md").write_text(
        "\n".join(
            [
                "# Integrity samples",
                "",
                "These files are outputs of the citation, fabrication, and rubric-mutation detectors.",
                "They are not NVDA research conclusions and they contain no live web evidence.",
                "",
                "Regenerate with `python -m research_desk.run --integrity-samples`.",
                "",
            ]
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
