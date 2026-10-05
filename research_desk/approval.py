"""Human approval gate. Live research does not run until this file matches the rubric."""

from __future__ import annotations

import json
from pathlib import Path

from research_desk.mandate import load_mandate


class ApprovalRequired(Exception):
    """Live research is blocked. Exit code 2."""

    code = 2


def approval_path(root: Path) -> Path:
    return Path(root) / "approvals" / "rubric_approval.json"


def read_approval(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def approval_matches(approval: dict | None, mandate: dict | None = None) -> bool:
    mandate = mandate or load_mandate()
    if not approval:
        return False
    approved_by = str(approval.get("approved_by") or "").strip()
    return (
        approval.get("approved") is True
        and approval.get("expert_validated") is False
        and bool(approved_by)
        and approved_by.lower() not in {"agent", "research_desk", "assistant"}
        and approval.get("rubric_sha256") == mandate["rubric_sha256"]
        and approval.get("mandate_sha256") == mandate["mandate_sha256"]
        and approval.get("cutoff_date") == mandate["cutoff_date"]
    )


def require_approval(path: Path, mandate: dict) -> dict:
    approval = read_approval(path)
    if approval_matches(approval, mandate):
        return approval
    raise ApprovalRequired(
        "LIVE RESEARCH BLOCKED. A human has not approved this generated rubric. "
        f"Expected approvals file: {path}. "
        f"Rubric SHA256: {mandate['rubric_sha256']}. "
        "Run python -m research_desk.show_rubric and approve that hash before any live fetch. "
        "These criteria are not expert-validated."
    )
