"""Render the report and countercase from claims only.

Prose is a template over claim statements. It does not introduce dollar
amounts or percents that are not already on a claim.
"""

from __future__ import annotations

from research_desk.constants import CUTOFF_DATE, TIMEZONE
from research_desk.units import same_dollars
from research_desk.util import render_sections


def _roles(claims: list[dict]) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for claim in claims:
        role = claim.get("role") or ""
        if role:
            found[role] = claim
    return found


def cite(claim: dict) -> str:
    tokens = " ".join(f"[{source}]" for source in claim.get("source_ids") or [])
    statement = (claim.get("statement") or "").rstrip()
    if tokens:
        return f"{statement} {tokens}"
    return statement


def _have(roles: dict[str, dict], *names: str) -> bool:
    return all(name in roles for name in names)


def render_outputs(claims: list[dict], sources: list[dict], mandate: dict, *, synthetic: bool) -> dict:
    roles = _roles(claims)
    report_sections = {
        "Thesis": _thesis(roles, mandate, synthetic=synthetic),
        "Supporting evidence": _supporting(roles, sources),
        "Opposing evidence": _opposing(claims),
        "Alternatives": _alternatives(roles),
        "Invalidation": _invalidation(roles),
        "Unknowns": _unknowns(sources, roles),
        "Monitoring": _monitoring_lines(claims),
    }
    countercase_sections = {
        "Strongest contrary evidence": _contrary(claims),
        "Alternatives": _alternatives(roles),
        "Balance note": _balance(claims),
    }
    if synthetic:
        preamble = [
            "SYNTHETIC FIXTURE. Not an NVIDIA Corporation filing. No web retrieval was performed for this run.",
            "The gate score measures rubric compliance. It is not a forecast and it is not position advice.",
            "No figure in this note is filled from memory. Every dollar amount and percent is tied to a claim.",
        ]
        counter_preamble = [
            "SYNTHETIC FIXTURE countercase. Contrary points are limited to claims already in the table.",
        ]
    else:
        preamble = [
            "Figures appear only when a retrieved document supplied them.",
            "The gate score measures rubric compliance. It is not a forecast and it is not position advice.",
            "No figure in this note is filled from memory.",
        ]
        counter_preamble = [
            "Countercase limited to claims extracted from retrieved documents.",
        ]
    report_md = render_sections("NVDA research note", preamble, list(report_sections.items()))
    counter_md = render_sections(
        "NVDA countercase",
        counter_preamble,
        list(countercase_sections.items()),
    )
    return {
        "report_sections": report_sections,
        "countercase_sections": countercase_sections,
        "monitoring": _monitoring_items(claims),
        "report_md": report_md,
        "countercase_md": counter_md,
    }


def _thesis(roles: dict[str, dict], mandate: dict, *, synthetic: bool) -> list[str]:
    cutoff = mandate["cutoff_date"]
    horizon = mandate["horizon_end"]
    timezone = mandate["timezone"]
    identity = "AI-driven revenue means the disclosed Data Center segment, not total revenue."
    if not _have(roles, "dc_current", "dc_prior", "yoy", "share", "total_current", "thesis"):
        return [
            "Judgment: unavailable. The latest eligible Data Center revenue fact is missing, so no durability judgment is stated.",
            f"Cutoff date: {cutoff} ({timezone}). Horizon end: {horizon}. The horizon question is blocked.",
            identity,
            "The critical input is missing. No figure was filled from memory.",
        ]
    lines = [
        "Judgment: conditionally durable. This judgment is an inference, not a fact.",
        f"Cutoff date: {cutoff} ({timezone}). Horizon end: {horizon}.",
        identity,
        cite(roles["dc_current"]),
        cite(roles["dc_prior"]),
        cite(roles["yoy"]),
        f"{roles['share']['statement']} {roles['total_current']['statement']} "
        + " ".join(
            f"[{source}]"
            for source in _union_sources(roles["share"], roles["total_current"])
        ),
    ]
    if roles["thesis"].get("status") == "disputed":
        lines.append(
            "The skeptic disputes the forward judgment. Historical figures above stay sourced; "
            "the forward judgment is not a fact."
        )
    if synthetic:
        lines.append("This note is a synthetic fixture and is not a live reading of NVIDIA Corporation.")
    else:
        lines.append("This note uses only figures extracted from retrieved documents.")
    return lines


def _union_sources(*claims: dict) -> list[str]:
    found: list[str] = []
    for claim in claims:
        for source in claim.get("source_ids") or []:
            if source not in found:
                found.append(source)
    return found


def _supporting(roles: dict[str, dict], sources: list[dict]) -> list[str]:
    lines: list[str] = []
    for role in (
        "dc_current",
        "dc_prior",
        "total_current",
        "gross_margin",
        "yoy",
        "share",
        "scale_millions",
        "inventory",
        "inventory_prior",
        "commitments",
    ):
        if role in roles:
            lines.append(cite(roles[role]))
    if _have(roles, "dc_current", "scale_millions"):
        lines.append(
            "The million figure is the code conversion of the billion figure, not a second observation. "
            + " ".join(f"[{source}]" for source in _union_sources(roles["dc_current"], roles["scale_millions"]))
        )
    by_id = {source["id"]: source for source in sources}
    if "SRC-001" in by_id and by_id["SRC-001"].get("used"):
        src = by_id["SRC-001"]
        lines.append(
            f"Event time {src['event_time']} is the period end recorded on SRC-001. "
            f"Availability time {src['published']} is that source's publication date. "
            "The two fields are not interchangeable [SRC-001]."
        )
    if not lines:
        lines.append("No supporting claim survived the cutoff and the unit checks.")
    return lines


def _opposing(claims: list[dict]) -> list[str]:
    rows = [claim for claim in claims if claim.get("relation") == "opposes_thesis"]
    if not rows:
        return ["No opposing claim is present in the claim table. None was invented."]
    return [cite(claim) for claim in rows]


def _alternatives(roles: dict[str, dict]) -> list[str]:
    lines: list[str] = []
    if _have(roles, "units", "asp", "compound"):
        lines.append(
            "Alternative A. Price rather than units. "
            + " ".join(cite(roles[name]) for name in ("units", "asp", "compound"))
        )
    if _have(roles, "networking", "compute", "mix_sum"):
        lines.append(
            "Alternative B. Mix inside Data Center. "
            + " ".join(cite(roles[name]) for name in ("networking", "compute", "mix_sum"))
        )
    if _have(roles, "compound", "yoy"):
        if roles["compound"]["value"] == roles["yoy"]["value"] and roles["compound"]["unit"] == roles["yoy"]["unit"]:
            lines.append(
                "The unit reconciler finds that the compounded figure matches the Data Center "
                "year-over-year figure. "
                + " ".join(f"[{source}]" for source in _union_sources(roles["compound"], roles["yoy"]))
            )
    if _have(roles, "mix_sum", "dc_current") and same_dollars(
        roles["mix_sum"]["value"],
        roles["mix_sum"]["unit"],
        roles["dc_current"]["value"],
        roles["dc_current"]["unit"],
    ):
        lines.append(
            "The unit reconciler finds that the mix sum matches the Data Center revenue fact. "
            + " ".join(f"[{source}]" for source in _union_sources(roles["mix_sum"], roles["dc_current"]))
        )
    if not lines:
        return ["Two evidenced alternatives are not available. None was invented."]
    return lines


def _invalidation(roles: dict[str, dict]) -> list[str]:
    lines: list[str] = []
    if "dc_current" in roles:
        lines.append(
            "Condition 1. Metric: Data Center revenue. Direction: below. "
            f"Threshold: {cite(roles['dc_current'])} "
            "A later primary print below that FY2027 Q2 level invalidates the durability judgment."
        )
    else:
        lines.append(
            "Condition 1 cannot be stated because the Data Center revenue fact is missing. "
            "No threshold was filled from memory."
        )
    if "exposure" in roles:
        lines.append(
            "Condition 2. Metric: export-license exposure share. Direction: above. "
            f"Threshold: {cite(roles['exposure'])} "
            "A later figure above that sourced share invalidates the durability judgment."
        )
    else:
        lines.append("Condition 2 cannot be stated because the exposure fact is missing.")
    return lines


def _unknowns(sources: list[dict], roles: dict[str, dict]) -> list[str]:
    lines = []
    for source in sources:
        if source.get("used"):
            continue
        reason = source.get("exclusion_reason") or "unused"
        lines.append(f"{source['id']} is unused ({reason}). Its contents are not claims.")
    lines.append("Customer orders after the spending-pause note are not quantified in the admitted documents.")
    if "dc_current" not in roles:
        lines.append("Latest eligible Data Center revenue is unknown in the admitted documents.")
    lines.append("Unknown publication dates stay unknown.")
    lines.append(f"The evidence cutoff is {CUTOFF_DATE} ({TIMEZONE}). Older admitted sources keep their own dates.")
    return lines


def _monitoring_lines(claims: list[dict]) -> list[str]:
    rows = [claim for claim in claims if claim.get("relation") == "monitoring"]
    if not rows:
        return ["No monitoring item was present in the admitted documents."]
    return [f"Monitor: {cite(claim)}" for claim in rows]


def _monitoring_items(claims: list[dict]) -> list[dict]:
    items = []
    for claim in claims:
        if claim.get("relation") != "monitoring":
            continue
        items.append(
            {
                "date": claim.get("applicable_period") or "",
                "text": claim.get("statement") or "",
                "source_ids": list(claim.get("source_ids") or []),
                "claim_id": claim.get("claim_id") or "",
            }
        )
    return items


def _contrary(claims: list[dict]) -> list[str]:
    rows = [claim for claim in claims if claim.get("relation") == "opposes_thesis"]
    if not rows:
        return ["No contrary claim is available. The skeptic does not invent one."]
    lines = [cite(claim) for claim in rows]
    lines.append(
        "These are the strongest contrary claims in the table. "
        "The skeptic does not add a contrary figure that has no source."
    )
    return lines


def _balance(claims: list[dict]) -> list[str]:
    opposing = [claim for claim in claims if claim.get("relation") == "opposes_thesis"]
    supporting = [
        claim
        for claim in claims
        if claim.get("relation") == "supports_thesis" and claim.get("claim_type") == "fact"
    ]
    return [
        f"Opposing claim-table count: {len(opposing)}.",
        f"Supporting fact claim-table count: {len(supporting)}.",
        "This countercase does not treat opposition and support as a tie. No unsupported balance was added.",
        "Claim-table counts are counts of rows, not market data.",
    ]
