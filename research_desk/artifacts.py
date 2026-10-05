"""Write the required run folder."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from research_desk.util import canonical, sha256_bytes

CLAIM_FIELDS = [
    "claim_id",
    "statement",
    "claim_type",
    "status",
    "source_ids",
    "supporting_fact_ids",
    "locator",
    "passage",
    "value",
    "unit",
    "currency",
    "applicable_period",
    "period_left",
    "period_right",
    "event_time",
    "availability_time",
    "report_section",
    "formula",
    "formula_inputs",
    "raw_usd",
    "segment",
    "metric_class",
    "relation",
    "issuer",
]


def write_run(state: dict, out_dir: Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    final = state["audits"][-1]
    mandate_bytes = _dump(state["mandate"])
    rubric_doc = {
        "expert_validated": False,
        "note": (
            "Generated for this desk and frozen from the mandate. "
            "Not expert-validated. Not a ResearchRubrics benchmark rubric."
        ),
        "sha256": final["rubric_sha256"],
        "criteria": state["rubric"],
    }
    rubric_bytes = _dump(rubric_doc)
    sources_bytes = _sources(state["sources"])
    claims_bytes = _claims(state["claims"])
    report_bytes = state["report_md"].encode("utf-8")
    counter_bytes = state["countercase_md"].encode("utf-8")
    audit_doc = {"cycles": state["audits"], "final": final}
    audit_bytes = _dump(audit_doc)
    revision_bytes = _revision(state).encode("utf-8")
    readme_bytes = _readme(state, final).encode("utf-8")

    files = {
        "README.md": readme_bytes,
        "mandate.json": mandate_bytes,
        "rubric.json": rubric_bytes,
        "sources.jsonl": sources_bytes,
        "claims.csv": claims_bytes,
        "report.md": report_bytes,
        "countercase.md": counter_bytes,
        "audit.json": audit_bytes,
        "revision_log.md": revision_bytes,
    }
    manifest = {
        "run_id": state["run_id"],
        "mode": state["mode"],
        "synthetic": state["synthetic"],
        "live_research_executed": state["live_research_executed"],
        "created_at": state["created_at"],
        "cutoff_date": state["mandate"]["cutoff_date"],
        "timezone": state["mandate"]["timezone"],
        "asset": state["mandate"]["asset"],
        "question": state["mandate"]["question"],
        "mandate_sha256": state["mandate"]["mandate_sha256"],
        "rubric_sha256": final["rubric_sha256"],
        "expert_validated": False,
        "score": final["score"],
        "gate": final["gate"],
        "threshold": final["threshold"],
        "formula": final["formula"],
        "positive_weight_sum": final["positive_weight_sum"],
        "weighted_sum": final["weighted_sum"],
        "critical_failures": final["critical_failures"],
        "unresolved": _unresolved(final),
        "search_queries_used": state["search_queries_used"],
        "search_query_limit": state["mandate"]["budgets"]["max_search_queries"],
        "documents_inspected": len(state["documents_inspected"]),
        "document_ids": state["documents_inspected"],
        "documents_skipped": state["documents_skipped"],
        "document_limit": state["mandate"]["budgets"]["max_unique_documents"],
        "revision_cycles": state["revision_cycles"],
        "revision_cycle_limit": state["mandate"]["budgets"]["max_revision_cycles"],
        "monitoring": state.get("monitoring") or [],
        "defect": state.get("defect"),
        "approval_required_before_live_research": True,
        "artifact_sha256": {name: sha256_bytes(payload) for name, payload in files.items()},
    }
    files["manifest.json"] = _dump(manifest)
    for name, payload in files.items():
        (out_dir / name).write_bytes(payload)
    return out_dir


def _dump(obj: object) -> bytes:
    return (json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def _sources(sources: list[dict]) -> bytes:
    lines = [canonical(source) for source in sources]
    text = "\n".join(lines)
    if text:
        text += "\n"
    return text.encode("utf-8")


def _claims(claims: list[dict]) -> bytes:
    from io import StringIO

    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CLAIM_FIELDS, lineterminator="\n")
    writer.writeheader()
    for claim in claims:
        row = {}
        for field in CLAIM_FIELDS:
            value = claim.get(field, "")
            if isinstance(value, list):
                value = "|".join(value)
            row[field] = value
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8")


def _unresolved(final: dict) -> list[str]:
    unresolved = []
    for verdict in final["verdicts"]:
        if verdict["unknown"]:
            unresolved.append(verdict["id"])
            continue
        value = float(verdict["verdict"])
        if verdict["weight"] > 0 and value < 1:
            unresolved.append(verdict["id"])
        if verdict["weight"] < 0 and value > 0:
            unresolved.append(verdict["id"])
    return unresolved


def _revision(state: dict) -> str:
    lines = [
        "# Revision log",
        "",
        f"Run: {state['run_id']}",
        f"Revision cycles used: {state['revision_cycles']} of {state['mandate']['budgets']['max_revision_cycles']}",
        f"Search queries used: {state['search_queries_used']} of {state['mandate']['budgets']['max_search_queries']}",
        f"Documents inspected: {len(state['documents_inspected'])} of {state['mandate']['budgets']['max_unique_documents']}",
        "",
    ]
    if state["documents_skipped"]:
        lines.append("Documents not inspected because the unique-document budget was exhausted:")
        for item in state["documents_skipped"]:
            lines.append(f"- {item['id']}: {item['reason']}")
        lines.append("")
    for entry in state["revision_log"]:
        lines.append(f"## Cycle {entry['cycle']}")
        lines.append("")
        lines.append(f"Gate: {entry['gate']}")
        lines.append(f"Score: {entry['score']}")
        lines.append(
            "Critical failures: " + (", ".join(entry["critical_failures"]) if entry["critical_failures"] else "none")
        )
        lines.append("Failed criteria: " + (", ".join(entry["failed"]) if entry["failed"] else "none"))
        if entry["editor_actions"]:
            lines.append("Editor:")
            for action in entry["editor_actions"]:
                lines.append(f"- {action}")
        else:
            lines.append("Editor: not run.")
        lines.append("")
    final = state["audits"][-1]
    unresolved = _unresolved(final)
    lines.append("## Unresolved at limit")
    lines.append("")
    if unresolved and final["gate"] != "READY":
        lines.append("Unresolved failures kept at the revision limit: " + ", ".join(unresolved))
    else:
        lines.append("No unresolved failures.")
    lines.append("")
    return "\n".join(lines)


def _readme(state: dict, final: dict) -> str:
    synthetic = "synthetic fixture" if state["synthetic"] else "live attempt"
    return "\n".join(
        [
            f"# Run {state['run_id']}",
            "",
            f"Mode: {synthetic} ({state['mode']}).",
            f"Gate: {final['gate']}. Score: {final['score']}.",
            "The score measures rubric compliance. It is not a forecast and it is not a return.",
            "Generated criteria in this run are not expert-validated.",
            f"Live research executed: {str(state['live_research_executed']).lower()}.",
            f"Defect harness: {state.get('defect') or 'none'}.",
            "",
            "Artifacts: mandate.json, rubric.json, sources.jsonl, claims.csv, report.md,",
            "countercase.md, audit.json, revision_log.md, manifest.json.",
            "",
            "Live web research stays blocked until a human approval file matches the",
            "rubric hash from `python -m research_desk.show_rubric`.",
            "",
        ]
    )
