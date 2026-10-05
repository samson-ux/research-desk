"""Deterministic detectors for citation gaps, fabricated numbers, and rubric drift."""

from __future__ import annotations

import re

from research_desk.mandate import rubric_hash
from research_desk.units import (
    D,
    magnitude_matches_claim,
    parse_magnitudes,
    q1,
    reconciliation_status,
)

SOURCE_TOKEN = re.compile(r"\[(SRC-\d+|WEB-\d+)\]")

# Specific trading and advice phrases. The mandate may name these prohibitions;
# the scanner looks for instructions, not for the word "no".
_SCOPE_PATTERNS = (
    re.compile(r"\b(?:buy|sell|short)\s+\d+(?:\.\d+)?\s+shares\b", re.IGNORECASE),
    re.compile(r"\bprice target\b", re.IGNORECASE),
    re.compile(r"\bposition size\b", re.IGNORECASE),
    re.compile(r"\ballocate\s+\d+(?:\.\d+)?\s*%", re.IGNORECASE),
    re.compile(r"\bexpected return\b", re.IGNORECASE),
    re.compile(r"\bplace (?:an|the) order\b", re.IGNORECASE),
    re.compile(r"\bbrokerage account\b", re.IGNORECASE),
    re.compile(r"\baccount (?:number|access)\b", re.IGNORECASE),
    re.compile(r"\border ticket\b", re.IGNORECASE),
    re.compile(r"\binvented return\b", re.IGNORECASE),
    re.compile(r"\bshares to (?:buy|sell)\b", re.IGNORECASE),
)

_BALANCE_PATTERNS = (
    re.compile(r"\bequally\b", re.IGNORECASE),
    re.compile(r"\b50/50\b"),
    re.compile(r"\bequal weight\b", re.IGNORECASE),
    re.compile(r"\bevidence is balanced\b", re.IGNORECASE),
)


def source_ids_in(line: str) -> list[str]:
    return SOURCE_TOKEN.findall(line)


def find_uncited_magnitude_lines(text: str, claims: list[dict]) -> list[dict]:
    """Lines whose dollar or percent figures are not tied to a claim's sources."""
    hits: list[dict] = []
    for number, line in enumerate(text.splitlines(), start=1):
        magnitudes = parse_magnitudes(line)
        if not magnitudes:
            continue
        tokens = source_ids_in(line)
        if not tokens:
            hits.append(
                {
                    "line": number,
                    "text": line,
                    "kind": "missing_citation",
                    "detail": "magnitude without a source id",
                }
            )
            continue
        for unit, value in magnitudes:
            owners = [
                claim
                for claim in claims
                if magnitude_matches_claim(unit, value, claim)
            ]
            if not owners:
                continue
            attached = False
            for claim in owners:
                needed = list(claim.get("source_ids") or [])
                if needed and all(source in tokens for source in needed):
                    attached = True
                    break
            if not attached:
                hits.append(
                    {
                        "line": number,
                        "text": line,
                        "kind": "citation_does_not_own_number",
                        "detail": f"{value} {unit} is not owned by the source ids on the line",
                    }
                )
    return hits


def find_fabricated_report_magnitudes(text: str, claims: list[dict]) -> list[dict]:
    """Reported magnitudes that match no claim at all."""
    hits: list[dict] = []
    for number, line in enumerate(text.splitlines(), start=1):
        for unit, value in parse_magnitudes(line):
            if any(magnitude_matches_claim(unit, value, claim) for claim in claims):
                continue
            hits.append(
                {
                    "line": number,
                    "text": line,
                    "kind": "fabricated_magnitude",
                    "detail": f"{value} {unit} matches no claim",
                }
            )
    return hits


def find_fabricated_claims(claims: list[dict]) -> list[dict]:
    by_id = {claim["claim_id"]: claim for claim in claims}
    hits: list[dict] = []
    for claim in claims:
        if claim.get("value") in (None, ""):
            continue
        status = reconciliation_status(claim, by_id)
        if status != "reconciled":
            hits.append(
                {
                    "claim_id": claim["claim_id"],
                    "kind": "fabricated_or_unreconciled_claim",
                    "detail": f"value {claim.get('value')} {claim.get('unit')} is {status}",
                }
            )
    return hits


def rubric_mutated(mandate_criteria: list[dict], working_criteria: list[dict]) -> bool:
    return rubric_hash(mandate_criteria) != rubric_hash(working_criteria)


def scope_breaches(text: str) -> list[dict]:
    hits: list[dict] = []
    for number, line in enumerate(text.splitlines(), start=1):
        for pattern in _SCOPE_PATTERNS:
            match = pattern.search(line)
            if match:
                hits.append({"line": number, "text": line, "match": match.group(0)})
    return hits


def balance_language(text: str) -> list[dict]:
    hits: list[dict] = []
    for number, line in enumerate((text or "").splitlines(), start=1):
        for pattern in _BALANCE_PATTERNS:
            match = pattern.search(line)
            if match:
                hits.append({"line": number, "text": line, "match": match.group(0)})
    return hits


def inference_labeled_as_fact(text: str) -> list[dict]:
    hits: list[dict] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if "inference" not in line.lower() and "estimate" not in line.lower():
            continue
        if re.search(r"\bis a fact\b", line, re.IGNORECASE):
            hits.append({"line": number, "text": line})
    return hits


def claim_value_matches_passage(claim: dict) -> bool:
    from research_desk.units import passage_supports

    if claim.get("value") in (None, ""):
        return True
    try:
        return passage_supports(claim.get("passage") or "", claim["value"], claim["unit"])
    except Exception:
        return False


def quantize_match(left: object, right: object) -> bool:
    return q1(D(left)) == q1(D(right))
