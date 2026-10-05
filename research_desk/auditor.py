"""Auditor: grade every frozen criterion from the artifacts alone.

Grades are 1, 0.5, or 0. Negative criteria score the occurrence of the bad
behavior. Weights used for the gate always come from the frozen mandate.
"""

from __future__ import annotations

import re
from datetime import date

from research_desk.constants import CUTOFF_DATE, HORIZON_END
from research_desk.integrity import (
    balance_language,
    find_fabricated_claims,
    find_fabricated_report_magnitudes,
    find_uncited_magnitude_lines,
    inference_labeled_as_fact,
    rubric_mutated,
    scope_breaches,
    source_ids_in,
)
from research_desk.mandate import rubric_hash
from research_desk.scoring import score_verdicts
from research_desk.units import reconciliation_status
from research_desk.util import parse_date, section_body

_PRIMARY_METRICS = {"revenue", "growth", "margin", "concentration"}
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_CONDITION = re.compile(r"^Condition \d+\.", re.IGNORECASE)


class Auditor:
    def grade(self, state: dict) -> dict:
        mandate = state["mandate"]
        frozen = mandate["criteria"]
        claims = state["claims"]
        sources = state["sources"]
        report = state.get("report_md") or ""
        countercase = state.get("countercase_md") or ""
        combined = report + "\n" + countercase
        by_id = {claim["claim_id"]: claim for claim in claims}
        by_source = {source["id"]: source for source in sources}
        ctx = {
            "mandate": mandate,
            "claims": claims,
            "sources": sources,
            "report": report,
            "countercase": countercase,
            "combined": combined,
            "by_id": by_id,
            "by_source": by_source,
            "thesis": section_body(report, "Thesis"),
            "opposing": section_body(report, "Opposing evidence"),
            "alternatives": section_body(report, "Alternatives"),
            "invalidation": section_body(report, "Invalidation"),
            "monitoring": section_body(report, "Monitoring"),
        }
        graders = {
            "C01-THESIS": _c01,
            "C02-PRIMARY-SOURCES": _c02,
            "C03-SEGMENT": _c03,
            "C04-PERIODS": _c04,
            "C05-INVALIDATION": _c05,
            "C06-OPPOSING": _c06,
            "C07-ALTERNATIVES": _c07,
            "C08-UNITS": _c08,
            "C09-INFERENCE": _c09,
            "C10-TIMESTAMPS": _c10,
            "C11-MONITORING": _c11,
            "C12-CUTOFF": _c12,
            "C13-LOCATORS": _c13,
            "C14-UNCITED": _c14,
            "C15-FABRICATION": _c15,
            "C16-RUBRIC-MUTATION": _c16,
            "C17-SCOPE": _c17,
            "C18-SNIPPET-AS-VERIFICATION": _c18,
        }
        verdicts = []
        for criterion in frozen:
            produced = graders[criterion["id"]](ctx, state)
            if not produced.get("justification") or not produced.get("report_location"):
                produced = {
                    "verdict": None,
                    "unknown": True,
                    "report_location": produced.get("report_location") or "audit",
                    "evidence_ids": produced.get("evidence_ids") or ["missing-justification"],
                    "justification": "Auditor could not justify this grade.",
                }
            if not produced.get("evidence_ids"):
                produced = {
                    **produced,
                    "verdict": None,
                    "unknown": True,
                    "justification": produced["justification"] + " Evidence ids were empty.",
                    "evidence_ids": ["missing-evidence-ids"],
                }
            verdicts.append(
                {
                    "id": criterion["id"],
                    "test": criterion["test"],
                    "weight": criterion["weight"],
                    "critical": criterion["critical"],
                    "verdict": produced["verdict"],
                    "unknown": bool(produced.get("unknown")),
                    "report_location": produced["report_location"],
                    "evidence_ids": list(produced["evidence_ids"]),
                    "justification": produced["justification"],
                }
            )
        scored = score_verdicts(frozen, verdicts)
        return {
            **scored,
            "rubric_sha256": rubric_hash(frozen),
            "working_rubric_sha256": rubric_hash(state["rubric"]),
            "verdicts": verdicts,
        }


def _ok(verdict: float, location: str, evidence: list[str], justification: str) -> dict:
    return {
        "verdict": verdict,
        "unknown": False,
        "report_location": location,
        "evidence_ids": evidence,
        "justification": justification,
    }


def _ids(claims: list[dict], limit: int = 8) -> list[str]:
    found: list[str] = []
    for claim in claims:
        if claim["claim_id"] not in found:
            found.append(claim["claim_id"])
        for source in claim.get("source_ids") or []:
            if source not in found:
                found.append(source)
        if len(found) >= limit:
            break
    return found or ["none"]


def _c01(ctx: dict, _state: dict) -> dict:
    thesis = ctx["thesis"]
    ok = (
        "Judgment: conditionally durable." in thesis
        and ctx["mandate"]["cutoff_date"] in thesis
        and HORIZON_END in thesis
        and ("inference" in thesis.lower() or "estimate" in thesis.lower())
        and "not a fact" in thesis.lower()
    )
    thesis_claim = next((claim for claim in ctx["claims"] if claim.get("role") == "thesis"), None)
    evidence = _ids([thesis_claim] if thesis_claim else [])
    if ok:
        return _ok(1, "report.md#thesis", evidence, "Thesis states the conditional inference, the cutoff, and the horizon end.")
    return _ok(0, "report.md#thesis", evidence, "Thesis does not state the required conditional inference with cutoff and horizon.")


def _c02(ctx: dict, _state: dict) -> dict:
    issuers = set(ctx["mandate"]["company_issuers"])

    def good(source_id: str) -> bool:
        source = ctx["by_source"].get(source_id)
        if not source:
            return False
        return (
            source.get("used") is True
            and source.get("kind") == "primary"
            and source.get("availability") == "full_text"
            and source.get("issuer") in issuers
        )

    dc = [claim for claim in ctx["claims"] if claim.get("role") == "dc_current" and claim.get("status") == "verified"]
    has_dc = bool(dc) and all(good(source) for claim in dc for source in claim["source_ids"]) and all(
        claim.get("locator") for claim in dc
    )
    bad: list[str] = []
    checked: list[dict] = []
    for claim in ctx["claims"]:
        if claim.get("metric_class") not in _PRIMARY_METRICS:
            continue
        if claim.get("value") in (None, ""):
            continue
        checked.append(claim)
        sources = claim.get("source_ids") or []
        if not sources or not all(good(source) for source in sources) or not claim.get("locator"):
            bad.append(claim["claim_id"])
    evidence = _ids(dc or checked)
    if has_dc and not bad:
        return _ok(1, "claims.csv#metric_class", evidence, "Latest Data Center revenue and every primary-metric claim cite a full-text primary company source.")
    detail = "missing latest Data Center revenue" if not has_dc else "primary-metric claims failed the source test: " + ", ".join(bad)
    return _ok(0, "claims.csv#metric_class", evidence, detail)


def _c03(ctx: dict, _state: dict) -> dict:
    thesis = ctx["thesis"]
    identified = "Data Center" in thesis and "not total revenue" in thesis
    bad = False
    for line in ctx["report"].splitlines():
        low = line.lower()
        if "total revenue is ai" in low:
            bad = True
        if "ai-driven" in low and "total revenue" in low and "not total" not in low:
            bad = True
    evidence = ["report.md#thesis"]
    if identified and not bad:
        return _ok(1, "report.md#thesis", evidence, "AI-driven revenue is identified with Data Center and total revenue is not renamed to AI revenue.")
    return _ok(0, "report.md#thesis", evidence, "Segment identification is missing or total revenue is treated as AI-driven revenue.")


def _c04(ctx: dict, _state: dict) -> dict:
    bad: list[str] = []
    numeric = []
    for claim in ctx["claims"]:
        if claim.get("value") in (None, ""):
            continue
        numeric.append(claim)
        period = claim.get("applicable_period") or ""
        if not period:
            bad.append(claim["claim_id"] + ":no-period")
        retrieved_bits = []
        for source_id in claim.get("source_ids") or []:
            source = ctx["by_source"].get(source_id) or {}
            if source.get("retrieved"):
                retrieved_bits.append(source["retrieved"])
        if any(bit and bit in period for bit in retrieved_bits):
            bad.append(claim["claim_id"] + ":period-is-retrieval-time")
        if "T09:00" in period:
            bad.append(claim["claim_id"] + ":period-contains-timestamp")
        comparison = bool(claim.get("formula") in {"yoy_percent", "compound_percent"} or claim.get("period_left") or claim.get("period_right"))
        if comparison:
            left = claim.get("period_left") or ""
            right = claim.get("period_right") or ""
            if not left or not right or left == right:
                bad.append(claim["claim_id"] + ":comparison-periods")
    evidence = _ids(numeric)
    if numeric and not bad:
        return _ok(1, "claims.csv#applicable_period", evidence, "Numeric claims have applicable periods, and comparisons name two different periods.")
    if not numeric:
        return _ok(0, "claims.csv#applicable_period", evidence, "No numeric claim is available to check periods.")
    return _ok(0, "claims.csv#applicable_period", evidence, "Period problems: " + ", ".join(bad))


def _c05(ctx: dict, _state: dict) -> dict:
    valid = []
    for line in ctx["invalidation"].splitlines():
        if not _CONDITION.match(line.strip()):
            continue
        low = line.lower()
        if "metric:" in low and "direction:" in low and "threshold:" in low and source_ids_in(line):
            from research_desk.units import parse_magnitudes

            if parse_magnitudes(line):
                valid.append(line)
    evidence = source_ids_in(ctx["invalidation"]) or ["report.md#invalidation"]
    if len(valid) >= 2:
        return _ok(1, "report.md#invalidation", evidence, f"{len(valid)} invalidation conditions name a metric, direction, sourced threshold, and source id.")
    if len(valid) == 1:
        return _ok(0.5, "report.md#invalidation", evidence, "Only one complete invalidation condition is present.")
    return _ok(0, "report.md#invalidation", evidence, "Fewer than two complete invalidation conditions are present.")


def _c06(ctx: dict, _state: dict) -> dict:
    opposing = [claim for claim in ctx["claims"] if claim.get("relation") == "opposes_thesis"]
    shown = [
        claim
        for claim in opposing
        if any(f"[{source}]" in ctx["opposing"] for source in claim.get("source_ids") or [])
    ]
    balance = balance_language(ctx["countercase"])
    evidence = _ids(shown or opposing)
    if balance:
        return _ok(0, "countercase.md#balance-note", evidence, "Countercase asserts an equal weighting the evidence does not support.")
    if len(shown) >= 2:
        return _ok(1, "report.md#opposing-evidence", evidence, f"{len(shown)} opposing claims are shown with source ids, without an invented tie.")
    if len(shown) == 1:
        return _ok(0.5, "report.md#opposing-evidence", evidence, "Only one opposing claim is shown.")
    return _ok(0, "report.md#opposing-evidence", evidence, "Opposing evidence is missing.")


def _c07(ctx: dict, _state: dict) -> dict:
    lines = [line for line in ctx["alternatives"].splitlines() if line.startswith("Alternative ")]
    cited = [line for line in lines if source_ids_in(line)]
    evidence = source_ids_in(ctx["alternatives"]) or ["report.md#alternatives"]
    if len(cited) >= 2:
        return _ok(1, "report.md#alternatives", evidence, "Two alternatives are stated with source ids.")
    if len(cited) == 1:
        return _ok(0.5, "report.md#alternatives", evidence, "Only one alternative is stated.")
    return _ok(0, "report.md#alternatives", evidence, "Two evidenced alternatives are not present.")


def _c08(ctx: dict, _state: dict) -> dict:
    bad = []
    numeric = []
    for claim in ctx["claims"]:
        if claim.get("value") in (None, ""):
            continue
        numeric.append(claim)
        if reconciliation_status(claim, ctx["by_id"]) != "reconciled":
            bad.append(claim["claim_id"])
    evidence = _ids(numeric)
    if numeric and not bad:
        return _ok(1, "claims.csv#unit", evidence, "Every numeric claim reconciled in code, including million/billion conversion.")
    return _ok(0, "claims.csv#unit", evidence, "Unreconciled numeric claims: " + (", ".join(bad) if bad else "none present"))


def _c09(ctx: dict, _state: dict) -> dict:
    bad = []
    inferences = [claim for claim in ctx["claims"] if claim.get("claim_type") in {"inference", "estimate"}]
    for claim in inferences:
        support = claim.get("supporting_fact_ids") or []
        if not support:
            bad.append(claim["claim_id"])
            continue
        for fact_id in support:
            fact = ctx["by_id"].get(fact_id)
            if fact is None or fact.get("claim_type") != "fact":
                bad.append(claim["claim_id"])
    prose = inference_labeled_as_fact(ctx["report"])
    evidence = _ids(inferences)
    if inferences and not bad and not prose:
        return _ok(1, "report.md", evidence, "Inferences cite fact claims and the report does not call an inference a fact.")
    if not inferences:
        return _ok(0, "report.md", evidence, "No inference claim is present.")
    return _ok(0, "report.md", evidence, "Inference support problems: " + ", ".join(bad) + ("; prose labels an inference as a fact" if prose else ""))


def _c10(ctx: dict, _state: dict) -> dict:
    bad = []
    for source in ctx["sources"]:
        if not source.get("id") or not source.get("title") or not source.get("publisher"):
            bad.append(source.get("id") or "missing-id")
        retrieved = source.get("retrieved") or ""
        if "T" not in retrieved:
            bad.append((source.get("id") or "source") + ":retrieved")
        published = source.get("published") or ""
        if published != "unknown" and parse_date(published) is None:
            bad.append((source.get("id") or "source") + ":published")
    evidence = [source["id"] for source in ctx["sources"][:8]] or ["none"]
    if ctx["sources"] and not bad:
        return _ok(1, "sources.jsonl", evidence, "Sources keep id, title, publisher, retrieval time, and a publication date or unknown.")
    return _ok(0, "sources.jsonl", evidence, "Timestamp problems: " + ", ".join(bad))


def _c11(ctx: dict, _state: dict) -> dict:
    cutoff = date.fromisoformat(ctx["mandate"]["cutoff_date"])
    good = []
    for line in ctx["monitoring"].splitlines():
        if not line.startswith("Monitor:"):
            continue
        if not source_ids_in(line):
            continue
        dates = [date.fromisoformat(match) for match in _DATE.findall(line)]
        if any(item > cutoff for item in dates):
            good.append(line)
    evidence = source_ids_in(ctx["monitoring"]) or ["report.md#monitoring"]
    if len(good) >= 3:
        return _ok(1, "report.md#monitoring", evidence, f"{len(good)} monitoring items are dated after the cutoff and cited.")
    if len(good) == 2:
        return _ok(0.5, "report.md#monitoring", evidence, "Only two monitoring items are dated after the cutoff.")
    return _ok(0, "report.md#monitoring", evidence, "Fewer than two cited monitoring items are dated after the cutoff.")


def _c12(ctx: dict, _state: dict) -> dict:
    cutoff = date.fromisoformat(ctx["mandate"]["cutoff_date"])
    used = [source for source in ctx["sources"] if source.get("used")]
    bad = []
    dated: list[date] = []
    for source in used:
        published = parse_date(source.get("published") or "")
        if published is None:
            bad.append(source["id"])
            continue
        dated.append(published)
        if published > cutoff:
            bad.append(source["id"])
    predates = any(item < cutoff for item in dated)
    evidence = [source["id"] for source in used[:8]] or ["none"]
    if used and not bad and predates and CUTOFF_DATE in ctx["thesis"]:
        return _ok(1, "sources.jsonl#used", evidence, "Used sources are dated on or before the cutoff, and at least one predates it.")
    return _ok(0, "sources.jsonl#used", evidence, "Cutoff screen failed or the thesis does not state the cutoff.")


def _c13(ctx: dict, _state: dict) -> dict:
    bad = []
    checked = []
    for claim in ctx["claims"]:
        if claim.get("status") != "verified" or claim.get("value") in (None, ""):
            continue
        checked.append(claim)
        if not claim.get("locator"):
            bad.append(claim["claim_id"])
            continue
        if reconciliation_status(claim, ctx["by_id"]) != "reconciled":
            bad.append(claim["claim_id"])
    evidence = _ids(checked)
    if checked and not bad:
        return _ok(1, "claims.csv#locator", evidence, "Verified numeric claims have locators and reconcile to a passage or a formula.")
    return _ok(0, "claims.csv#locator", evidence, "Locator problems: " + (", ".join(bad) if bad else "no verified numeric claims"))


def _c14(ctx: dict, _state: dict) -> dict:
    hits = find_uncited_magnitude_lines(ctx["combined"], ctx["claims"])
    evidence = [f"line:{hit['line']}" for hit in hits[:6]] or ["scan:report.md", "scan:countercase.md"]
    if hits:
        return _ok(1, "report.md", evidence, f"{len(hits)} magnitude line(s) lack a source id that owns the amount.")
    return _ok(0, "report.md", evidence, "Every dollar amount and percent in the report and countercase is owned by a cited claim.")


def _c15(ctx: dict, _state: dict) -> dict:
    claim_hits = find_fabricated_claims(ctx["claims"])
    prose_hits = find_fabricated_report_magnitudes(ctx["combined"], ctx["claims"])
    evidence = [hit["claim_id"] for hit in claim_hits[:6]]
    evidence += [f"line:{hit['line']}" for hit in prose_hits[:6]]
    if not evidence:
        evidence = ["scan:claims.csv", "scan:report.md"]
    if claim_hits or prose_hits:
        return _ok(
            1,
            "claims.csv",
            evidence,
            f"Fabricated or unreconciled numbers: {len(claim_hits)} claim(s), {len(prose_hits)} report magnitude(s).",
        )
    return _ok(0, "claims.csv", evidence, "No numeric claim or reported magnitude failed the passage and formula checks.")


def _c16(ctx: dict, state: dict) -> dict:
    mutated = rubric_mutated(ctx["mandate"]["criteria"], state["rubric"])
    evidence = [
        "mandate:" + rubric_hash(ctx["mandate"]["criteria"])[:12],
        "working:" + rubric_hash(state["rubric"])[:12],
    ]
    if mutated:
        return _ok(1, "rubric.json", evidence, "Working rubric differs from the frozen mandate rubric.")
    return _ok(0, "rubric.json", evidence, "Working rubric matches the frozen mandate rubric.")


def _c17(ctx: dict, _state: dict) -> dict:
    hits = scope_breaches(ctx["combined"])
    evidence = [f"line:{hit['line']}" for hit in hits[:6]] or ["scan:report.md", "scan:countercase.md"]
    if hits:
        return _ok(1, "report.md", evidence, "Scope breach: " + "; ".join(hit["match"] for hit in hits))
    return _ok(0, "report.md", evidence, "Report and countercase contain no order, sizing, account, or invented-return instruction.")


def _c18(ctx: dict, _state: dict) -> dict:
    bad = []
    for claim in ctx["claims"]:
        if claim.get("status") != "verified":
            continue
        sources = claim.get("source_ids") or []
        if not sources:
            bad.append(claim["claim_id"])
            continue
        for source_id in sources:
            source = ctx["by_source"].get(source_id)
            if source is None or source.get("availability") != "full_text":
                bad.append(claim["claim_id"])
    evidence = bad[:8] or ["scan:claims.csv"]
    if bad:
        return _ok(1, "claims.csv#status", evidence, "A verified claim cites a missing source or a source that is not full text.")
    return _ok(0, "claims.csv#status", evidence, "Every verified claim cites full text.")
