"""Coordinator: freeze the mandate, enforce budgets, and open a run."""

from __future__ import annotations

import copy

from research_desk.util import now_iso


class Coordinator:
    def open_state(self, mandate: dict, *, mode: str, run_id: str, synthetic: bool) -> dict:
        return {
            "mandate": copy.deepcopy(mandate),
            "rubric": copy.deepcopy(mandate["criteria"]),
            "mode": mode,
            "run_id": run_id,
            "synthetic": synthetic,
            "live_research_executed": False,
            "created_at": now_iso(),
            "sources": [],
            "claims": [],
            "queries": [],
            "documents_inspected": [],
            "documents_skipped": [],
            "revision_cycles": 0,
            "revision_log": [],
            "audits": [],
            "search_queries_used": 0,
            "defect": None,
            "report_md": "",
            "countercase_md": "",
            "monitoring": [],
            "report_sections": {},
            "countercase_sections": {},
        }

    def select_documents(self, docs: list[dict], limit: int) -> tuple[list[dict], list[dict]]:
        inspected = list(docs[:limit])
        skipped = [
            {"id": doc.get("id", ""), "reason": "document_budget"}
            for doc in docs[limit:]
        ]
        return inspected, skipped
