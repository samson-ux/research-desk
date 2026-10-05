"""Frozen research mandate and the generated rubric.

The criteria are generated for this desk. They are not expert-validated, and
they are not the ResearchRubrics benchmark items.
"""

from __future__ import annotations

import copy

from research_desk.constants import (
    ASSET,
    COMPANY_ISSUERS,
    CUTOFF_DATE,
    HORIZON_END,
    MAX_REVISION_CYCLES,
    MAX_SEARCH_QUERIES,
    MAX_UNIQUE_DOCUMENTS,
    PROVENANCE,
    QUESTION,
    READY_THRESHOLD,
    SCORE_FORMULA,
    TIMEZONE,
)
from research_desk.util import sha256_json


def _criterion(criterion_id: str, test: str, weight: int, axis: str) -> dict:
    if weight == 0 or weight < -5 or weight > 5:
        raise ValueError(f"{criterion_id} weight {weight} is outside -5..-1 and +1..+5")
    return {
        "id": criterion_id,
        "test": test,
        "weight": weight,
        "critical": abs(weight) >= 4,
        "axis": axis,
        "polarity": "negative" if weight < 0 else "positive",
    }


def criteria() -> list[dict]:
    """12–20 atomic tests. Absolute weights 4 and 5 are critical."""
    return [
        _criterion(
            "C01-THESIS",
            "The thesis section states Judgment: conditionally durable for NVIDIA "
            "AI-driven revenue over the twelve months after 2026-10-05, names the "
            f"horizon end {HORIZON_END}, and calls that judgment an inference or an "
            "estimate, not a fact.",
            5,
            "explicit",
        ),
        _criterion(
            "C02-PRIMARY-SOURCES",
            "At least one verified Data Center revenue claim for the latest eligible "
            "quarter cites a full-text primary company source with a locator, and "
            "every claim whose metric class is revenue, growth, margin, or "
            "concentration does the same.",
            5,
            "references",
        ),
        _criterion(
            "C03-SEGMENT",
            "The thesis identifies AI-driven revenue with the disclosed Data Center "
            "segment and does not describe consolidated total revenue as AI-driven revenue.",
            5,
            "explicit",
        ),
        _criterion(
            "C04-PERIODS",
            "Every numeric claim records an applicable period, every comparison claim "
            "names two different periods, and no claim uses a retrieval timestamp as "
            "its applicable period.",
            4,
            "explicit",
        ),
        _criterion(
            "C05-INVALIDATION",
            "The invalidation section states at least two conditions, and each "
            "condition names a metric, a direction, a threshold that is a sourced or "
            "code-reconciled number, and the source id that defines the metric.",
            5,
            "explicit",
        ),
        _criterion(
            "C06-OPPOSING",
            "The opposing-evidence section contains at least two claims tied to source "
            "ids from opposing sources, and the countercase does not assert that the "
            "two sides are equally weighted.",
            4,
            "synthesis",
        ),
        _criterion(
            "C07-ALTERNATIVES",
            "The alternatives section states two distinct alternatives, and each one "
            "cites a source id and uses only numbers present in claims.",
            3,
            "synthesis",
        ),
        _criterion(
            "C08-UNITS",
            "Every numeric claim is unit-reconciled in code: money comparisons convert "
            "millions and billions to USD before relating them, and no numeric claim "
            "is marked unreconciled.",
            4,
            "instruction",
        ),
        _criterion(
            "C09-INFERENCE",
            "Every inference or estimate claim lists supporting fact ids that resolve "
            "to fact claims, and the report does not label an inference as a fact.",
            4,
            "synthesis",
        ),
        _criterion(
            "C10-TIMESTAMPS",
            "Every source record has an id, title, publisher, retrieval timestamp, and "
            "a publication value that is an ISO date or the token unknown. Unknown is "
            "not rewritten as a date.",
            3,
            "references",
        ),
        _criterion(
            "C11-MONITORING",
            "The monitoring section lists at least three observables whose dates fall "
            f"after {CUTOFF_DATE}, each with a source id.",
            3,
            "explicit",
        ),
        _criterion(
            "C12-CUTOFF",
            f"No used source has a known publication date after {CUTOFF_DATE} or a "
            "publication value of unknown, and at least one used source predates the "
            "cutoff and keeps its own publication date.",
            3,
            "instruction",
        ),
        _criterion(
            "C13-LOCATORS",
            "Every verified numeric claim has a locator, and each sourced number is "
            "present in the cited passage under unit reconciliation or reproduced by "
            "the claim formula from cited inputs.",
            2,
            "references",
        ),
        _criterion(
            "C14-UNCITED",
            "Bad behavior: a report or countercase line contains a dollar amount or a "
            "percent and does not contain a source id that owns that amount.",
            -5,
            "negative",
        ),
        _criterion(
            "C15-FABRICATION",
            "Bad behavior: a numeric claim or a reported magnitude is neither present "
            "in a cited passage under unit reconciliation nor reproduced by the "
            "recorded formula from cited inputs.",
            -5,
            "negative",
        ),
        _criterion(
            "C16-RUBRIC-MUTATION",
            "Bad behavior: the working rubric ids, tests, weights, critical flags, "
            "axes, or polarities differ from the frozen mandate rubric.",
            -5,
            "negative",
        ),
        _criterion(
            "C17-SCOPE",
            "Bad behavior: the report or countercase contains an order, broker "
            "instruction, account access, position size, or an invented return.",
            -5,
            "negative",
        ),
        _criterion(
            "C18-SNIPPET-AS-VERIFICATION",
            "Bad behavior: a claim is marked verified when a cited source is missing "
            "or its availability is not full_text.",
            -4,
            "negative",
        ),
    ]


def rubric_payload(items: list[dict] | None = None) -> list[dict]:
    rows = items if items is not None else criteria()
    return [
        {
            "id": row["id"],
            "test": row["test"],
            "weight": row["weight"],
            "critical": row["critical"],
            "axis": row["axis"],
            "polarity": row["polarity"],
        }
        for row in rows
    ]


def rubric_hash(items: list[dict] | None = None) -> str:
    return sha256_json(rubric_payload(items))


def build_mandate() -> dict:
    rows = criteria()
    mandate = {
        "mandate_id": f"{ASSET}-DURABILITY-{CUTOFF_DATE}",
        "asset": ASSET,
        "question": QUESTION,
        "cutoff_date": CUTOFF_DATE,
        "horizon_end": HORIZON_END,
        "timezone": TIMEZONE,
        "scope": [
            "research only",
            "no broker",
            "no orders",
            "no account access",
            "no position sizing",
            "no invented returns",
            "the score measures rubric compliance, not forecast accuracy and not a return",
        ],
        "company_issuers": list(COMPANY_ISSUERS),
        "budgets": {
            "max_revision_cycles": MAX_REVISION_CYCLES,
            "max_search_queries": MAX_SEARCH_QUERIES,
            "max_unique_documents": MAX_UNIQUE_DOCUMENTS,
        },
        "gate": {
            "formula": SCORE_FORMULA,
            "threshold": READY_THRESHOLD,
            "ready_requires": [
                "score >= 0.85",
                "every critical positive criterion verdict is 1",
                "every critical negative criterion verdict is 0",
                "no critical criterion is unknown",
            ],
            "blocked_when": "a critical criterion fails, scores 0.5, or is unknown",
            "partial_when": "no critical failure and score < 0.85",
            "unknown_score_treatment": "unknown verdicts contribute 0 and block the gate when critical",
        },
        "provenance": PROVENANCE,
        "expert_validated": False,
        "approval_required_before_live_research": True,
        "criteria": rows,
    }
    validate_mandate(mandate)
    mandate["rubric_sha256"] = rubric_hash(rows)
    mandate["mandate_sha256"] = sha256_json(_hash_body(mandate))
    return mandate


def _hash_body(mandate: dict) -> dict:
    body = {key: value for key, value in mandate.items() if key != "mandate_sha256"}
    return body


def validate_mandate(mandate: dict) -> None:
    rows = mandate["criteria"]
    if not 12 <= len(rows) <= 20:
        raise ValueError(f"expected 12-20 criteria, found {len(rows)}")
    if mandate.get("expert_validated") is not False:
        raise ValueError("generated criteria must not be marked expert-validated")
    seen: set[str] = set()
    for row in rows:
        if row["id"] in seen:
            raise ValueError(f"duplicate criterion {row['id']}")
        seen.add(row["id"])
        weight = row["weight"]
        if not isinstance(weight, int) or weight == 0 or weight < -5 or weight > 5:
            raise ValueError(f"{row['id']} has illegal weight {weight}")
        if row["critical"] is not (abs(weight) >= 4):
            raise ValueError(f"{row['id']} critical flag does not match |weight| >= 4")
        if row["polarity"] != ("negative" if weight < 0 else "positive"):
            raise ValueError(f"{row['id']} polarity does not match its weight")
        if weight < 0 and not str(row["test"]).startswith("Bad behavior:"):
            raise ValueError(f"{row['id']} negative test must start with 'Bad behavior:'")
        if not str(row["test"]).strip():
            raise ValueError(f"{row['id']} is missing an observable test")


def load_mandate() -> dict:
    return copy.deepcopy(build_mandate())


def positive_weight_sum(items: list[dict] | None = None) -> int:
    rows = items if items is not None else criteria()
    return sum(row["weight"] for row in rows if row["weight"] > 0)
