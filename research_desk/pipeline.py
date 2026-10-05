"""Researcher → Skeptic → Auditor → Editor, with a two-cycle cap."""

from __future__ import annotations

from pathlib import Path

from research_desk.artifacts import write_run
from research_desk.auditor import Auditor
from research_desk.coordinator import Coordinator
from research_desk.editor import Editor
from research_desk.fixture_corpus import documents, drop_roles
from research_desk.mandate import load_mandate
from research_desk.researcher import Researcher, _attach_render
from research_desk.skeptic import Skeptic


def run_research(
    out_dir: Path | str,
    *,
    run_id: str,
    defect: str | None = None,
    docs: list[dict] | None = None,
    mode: str = "synthetic_fixture",
) -> dict:
    """Run the offline desk. `docs` overrides the fixture corpus (tests and live extracts)."""
    mandate = load_mandate()
    coordinator = Coordinator()
    synthetic = mode != "live"
    state = coordinator.open_state(mandate, mode=mode, run_id=run_id, synthetic=synthetic)
    if mode == "live":
        state["live_research_executed"] = True
    state["defect"] = defect
    corpus = documents() if docs is None else docs
    if defect == "drop_primary_revenue":
        corpus = drop_roles(corpus, {"dc_current"})
    limit = mandate["budgets"]["max_unique_documents"]
    inspected, skipped = coordinator.select_documents(corpus, limit)
    state["documents_skipped"] = skipped
    Researcher().run(state, inspected)
    Skeptic().run(state)
    _apply_defect(state, defect)
    _audit_loop(state)
    write_run(state, Path(out_dir))
    return state


def _audit_loop(state: dict) -> None:
    auditor = Auditor()
    editor = Editor()
    limit = state["mandate"]["budgets"]["max_revision_cycles"]
    while True:
        audit = auditor.grade(state)
        state["audits"].append(audit)
        entry = {
            "cycle": len(state["audits"]) - 1,
            "gate": audit["gate"],
            "score": audit["score"],
            "critical_failures": list(audit["critical_failures"]),
            "reasons": list(audit["reasons"]),
            "failed": _failed_ids(audit),
            "editor_actions": [],
            "working_rubric_sha256": audit["working_rubric_sha256"],
        }
        if audit["gate"] == "READY" or state["revision_cycles"] >= limit:
            state["revision_log"].append(entry)
            break
        entry["editor_actions"] = editor.revise(state)
        state["revision_log"].append(entry)
        state["revision_cycles"] += 1


def _failed_ids(audit: dict) -> list[str]:
    failed = []
    for verdict in audit["verdicts"]:
        if verdict["unknown"]:
            failed.append(verdict["id"])
            continue
        value = float(verdict["verdict"])
        if verdict["weight"] > 0 and value < 1:
            failed.append(verdict["id"])
        if verdict["weight"] < 0 and value > 0:
            failed.append(verdict["id"])
    return failed


def _apply_defect(state: dict, defect: str | None) -> None:
    if defect == "missing_citation":
        line = "Data Center revenue was $40.0 billion."
        state["report_md"] = state["report_md"].rstrip() + "\n" + line + "\n"
        state["report_sections"]["Supporting evidence"].append(line)
        return
    if defect == "fabrication":
        for claim in state["claims"]:
            if claim.get("role") == "dc_current":
                claim["value"] = "123.4"
                claim["statement"] = claim["statement"].replace("$40.0 billion", "$123.4 billion")
        _attach_render(state)
        return
    if defect == "rubric_mutation":
        state["rubric"][0]["weight"] = 1
        return
