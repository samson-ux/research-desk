"""Gate math. The score is rubric compliance, not a forecast and not a return."""

from __future__ import annotations

from decimal import Decimal

from research_desk.constants import READY_THRESHOLD, SCORE_FORMULA

VERDICT_VALUES = {Decimal("0"), Decimal("0.5"), Decimal("1")}


def _verdict_decimal(row: dict) -> Decimal | None:
    if row.get("unknown"):
        return None
    value = Decimal(str(row["verdict"]))
    if value not in VERDICT_VALUES:
        raise ValueError(f"verdict {value} is not 0, 0.5, or 1")
    return value


def score_verdicts(criteria: list[dict], verdicts: list[dict]) -> dict:
    """Apply sum(weight * verdict) / sum(positive weights).

    Weights come from the frozen mandate criteria, not from the verdict rows.
    Unknown verdicts contribute 0. A critical unknown, a critical positive
    verdict below 1, or a critical negative verdict above 0 blocks the gate.
    """
    by_id = {row["id"]: row for row in verdicts}
    missing = [row["id"] for row in criteria if row["id"] not in by_id]
    if missing:
        raise ValueError(f"missing verdicts for {missing}")

    positive = sum(row["weight"] for row in criteria if row["weight"] > 0)
    if positive <= 0:
        raise ValueError("positive weight sum must be > 0")

    weighted = Decimal("0")
    critical_failures: list[str] = []
    reasons: list[str] = []
    for row in criteria:
        verdict = by_id[row["id"]]
        value = _verdict_decimal(verdict)
        if value is None:
            reasons.append(f"{row['id']} unknown")
            if row["critical"]:
                critical_failures.append(row["id"])
            continue
        weighted += Decimal(row["weight"]) * value
        if row["critical"] and row["weight"] > 0 and value != Decimal("1"):
            critical_failures.append(row["id"])
            reasons.append(f"{row['id']} critical positive verdict {value}")
        if row["critical"] and row["weight"] < 0 and value != Decimal("0"):
            critical_failures.append(row["id"])
            reasons.append(f"{row['id']} critical bad behavior verdict {value}")

    score = weighted / Decimal(positive)
    if critical_failures:
        gate = "BLOCKED"
    elif score < Decimal(READY_THRESHOLD):
        gate = "PARTIAL"
        reasons.append(f"score {score} is below {READY_THRESHOLD}")
    else:
        gate = "READY"
    return {
        "formula": SCORE_FORMULA,
        "threshold": READY_THRESHOLD,
        "positive_weight_sum": positive,
        "weighted_sum": format(weighted, "f"),
        "score": format(score, "f"),
        "gate": gate,
        "critical_failures": critical_failures,
        "reasons": reasons,
        "unknown_contributes_zero": True,
    }
