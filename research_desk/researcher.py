"""Researcher: bind admitted documents to claims and a first draft.

The researcher does not browse, and it does not type a number that is not on
an admitted passage or a formula over those passages.
"""

from __future__ import annotations

from research_desk.render import render_outputs
from research_desk.units import apply_formula, format_magnitude, q1, D
from research_desk.util import parse_date


class Researcher:
    def run(self, state: dict, docs: list[dict]) -> dict:
        mandate = state["mandate"]
        cutoff = parse_date(mandate["cutoff_date"])
        sources, claims = _bind(docs, cutoff)
        state["sources"] = sources
        state["claims"] = claims
        state["documents_inspected"] = [doc["id"] for doc in docs]
        _attach_render(state)
        state["queries"].append(
            {
                "id": "Q-001",
                "kind": "local_corpus" if state.get("synthetic", True) else "web",
                "web": not state.get("synthetic", True),
                "text": (
                    "NVDA Data Center revenue, prior-year base, concentration, "
                    "export exposure, mix, price versus units, calendar"
                ),
                "document_ids": [doc["id"] for doc in docs],
            }
        )
        if not state.get("synthetic", True):
            state["search_queries_used"] = sum(1 for query in state["queries"] if query.get("web"))
        return state


def _bind(docs: list[dict], cutoff) -> tuple[list[dict], list[dict]]:
    sources: list[dict] = []
    builder = _ClaimBuilder()
    for doc in docs:
        used, reason = _admit(doc, cutoff)
        sources.append(_source_row(doc, used, reason))
        if not used:
            continue
        for passage in doc.get("passages") or []:
            if passage.get("relation") == "excluded" or not passage.get("role"):
                continue
            builder.add_fact(doc, passage)
    _add_formulas(builder)
    _add_thesis(builder)
    return sources, builder.rows


def _admit(doc: dict, cutoff) -> tuple[bool, str]:
    published = doc.get("published") or "unknown"
    if published == "unknown":
        return False, "publication_date_unknown"
    published_date = parse_date(published)
    if published_date is None:
        return False, "publication_date_unparseable"
    if cutoff is not None and published_date > cutoff:
        return False, "published_after_cutoff"
    return True, ""


def _source_row(doc: dict, used: bool, reason: str) -> dict:
    return {
        "id": doc["id"],
        "url": doc.get("url", ""),
        "path": doc.get("path", ""),
        "title": doc.get("title", ""),
        "publisher": doc.get("publisher", ""),
        "published": doc.get("published", "unknown"),
        "retrieved": doc.get("retrieved", ""),
        "event_time": doc.get("event_time", ""),
        "applicable_period": doc.get("applicable_period", ""),
        "excerpt": doc.get("excerpt", ""),
        "locator": doc.get("locator", ""),
        "availability": doc.get("availability", "unavailable"),
        "version": doc.get("version", ""),
        "kind": doc.get("kind", ""),
        "synthetic": bool(doc.get("synthetic", False)),
        "issuer": doc.get("issuer", ""),
        "stance": doc.get("stance", ""),
        "used": used,
        "exclusion_reason": reason,
    }


class _ClaimBuilder:
    def __init__(self) -> None:
        self.rows: list[dict] = []
        self.by_role: dict[str, dict] = {}

    def add(self, role: str, **fields) -> dict:
        if role in self.by_role:
            raise ValueError(f"duplicate claim role {role}")
        claim = {
            "claim_id": f"CLM-{len(self.rows) + 1:03d}",
            "role": role,
            "statement": "",
            "statement_template": "",
            "claim_type": "fact",
            "status": "verified",
            "source_ids": [],
            "supporting_fact_ids": [],
            "locator": "",
            "passage": "",
            "value": "",
            "unit": "",
            "currency": "",
            "applicable_period": "",
            "period_left": "",
            "period_right": "",
            "event_time": "",
            "availability_time": "",
            "report_section": "",
            "formula": "",
            "formula_inputs": [],
            "raw_usd": "",
            "segment": "",
            "metric_class": "",
            "relation": "context",
            "issuer": "",
        }
        claim.update(fields)
        self.rows.append(claim)
        self.by_role[role] = claim
        return claim

    def add_fact(self, doc: dict, passage: dict) -> dict:
        value = passage.get("value") or ""
        unit = passage.get("unit") or ""
        template = passage.get("statement") or passage.get("text") or ""
        # Fact statements are already fully rendered in the corpus. Keep a
        # template only when the statement contains the formatted magnitude.
        statement = passage.get("statement") or passage.get("text") or ""
        amount = format_magnitude(value, unit) if value else ""
        if value and "{amount}" in (passage.get("statement_template") or ""):
            statement = passage["statement_template"].format(amount=amount)
        section = {
            "supports_thesis": "supporting",
            "opposes_thesis": "opposing",
            "alternative": "alternatives",
            "monitoring": "monitoring",
            "context": "supporting",
        }.get(passage.get("relation") or "", "supporting")
        return self.add(
            passage["role"],
            statement=statement,
            statement_template=passage.get("statement_template") or statement,
            claim_type="fact",
            status="verified",
            source_ids=[doc["id"]],
            supporting_fact_ids=[],
            locator=passage.get("locator") or "",
            passage=passage.get("text") or "",
            value=str(q1(D(value))) if value else "",
            unit=unit,
            currency=passage.get("currency") or "",
            applicable_period=passage.get("applicable_period") or "",
            period_left=passage.get("period_left") or "",
            period_right=passage.get("period_right") or "",
            event_time=doc.get("event_time") or "",
            availability_time=doc.get("published") or "",
            report_section=section,
            segment=passage.get("segment") or "",
            metric_class=passage.get("metric_class") or "",
            relation=passage.get("relation") or "context",
            issuer=doc.get("issuer") or "",
        )

    def add_formula(
        self,
        role: str,
        formula: str,
        input_roles: list[str],
        template: str,
        *,
        metric_class: str,
        relation: str,
        period: str,
        period_left: str = "",
        period_right: str = "",
        segment: str = "",
        report_section: str = "supporting",
    ) -> dict:
        inputs = [self.by_role[name] for name in input_roles]
        value, unit, currency = apply_formula(formula, inputs)
        amount = format_magnitude(value, unit)
        sources: list[str] = []
        for item in inputs:
            for source in item["source_ids"]:
                if source not in sources:
                    sources.append(source)
        fact_ids = [item["claim_id"] for item in inputs if item["claim_type"] == "fact"]
        return self.add(
            role,
            statement=template.format(amount=amount),
            statement_template=template,
            claim_type="inference",
            status="verified",
            source_ids=sources,
            supporting_fact_ids=fact_ids,
            locator=f"formula:{formula}",
            passage="",
            value=str(q1(D(value))),
            unit=unit,
            currency=currency,
            applicable_period=period,
            period_left=period_left,
            period_right=period_right,
            event_time=inputs[0].get("event_time") or "",
            availability_time=inputs[0].get("availability_time") or "",
            report_section=report_section,
            formula=formula,
            formula_inputs=[item["claim_id"] for item in inputs],
            segment=segment or inputs[0].get("segment") or "",
            metric_class=metric_class,
            relation=relation,
            issuer=inputs[0].get("issuer") or "",
        )


def _add_formulas(builder: _ClaimBuilder) -> None:
    roles = builder.by_role
    if "dc_current" in roles and "dc_prior" in roles:
        builder.add_formula(
            "yoy",
            "yoy_percent",
            ["dc_current", "dc_prior"],
            "Computed inference: Data Center revenue grew {amount} from FY2026 Q2 to FY2027 Q2.",
            metric_class="growth",
            relation="supports_thesis",
            period="FY2027 Q2 vs FY2026 Q2",
            period_left="FY2027 Q2",
            period_right="FY2026 Q2",
            segment="Data Center",
        )
    if "dc_current" in roles and "total_current" in roles:
        builder.add_formula(
            "share",
            "share_percent",
            ["dc_current", "total_current"],
            "Computed inference: Data Center revenue was {amount} of total revenue in FY2027 Q2.",
            metric_class="share",
            relation="supports_thesis",
            period="FY2027 Q2",
            segment="Data Center",
        )
    if "dc_current" in roles:
        builder.add_formula(
            "scale_millions",
            "billion_to_million",
            ["dc_current"],
            "Computed inference: the FY2027 Q2 Data Center revenue figure reconciles to {amount}.",
            metric_class="revenue",
            relation="supports_thesis",
            period="FY2027 Q2",
            segment="Data Center",
        )
    if "networking" in roles and "compute" in roles:
        builder.add_formula(
            "mix_sum",
            "sum_usd",
            ["networking", "compute"],
            "Computed inference: networking revenue plus compute revenue sums to {amount}.",
            metric_class="revenue",
            relation="alternative",
            period="FY2027 Q2",
            segment="Data Center",
            report_section="alternatives",
        )
    if "units" in roles and "asp" in roles:
        builder.add_formula(
            "compound",
            "compound_percent",
            ["units", "asp"],
            "Computed inference: compounding the unit change and the average selling price change produces {amount}.",
            metric_class="growth",
            relation="alternative",
            period="FY2027 Q2 vs FY2026 Q2",
            period_left="FY2027 Q2",
            period_right="FY2026 Q2",
            segment="Data Center",
            report_section="alternatives",
        )


def _add_thesis(builder: _ClaimBuilder) -> None:
    needed = ("dc_current", "dc_prior", "yoy", "share", "total_current")
    if not all(name in builder.by_role for name in needed):
        return
    support = [
        builder.by_role[name]["claim_id"]
        for name in ("dc_current", "dc_prior", "total_current")
    ]
    sources: list[str] = []
    for name in ("dc_current", "dc_prior", "total_current"):
        for source in builder.by_role[name]["source_ids"]:
            if source not in sources:
                sources.append(source)
    builder.add(
        "thesis",
        statement=(
            "Judgment: conditionally durable. This judgment is an inference, not a fact, "
            "and it covers the twelve months after the cutoff."
        ),
        statement_template=(
            "Judgment: conditionally durable. This judgment is an inference, not a fact, "
            "and it covers the twelve months after the cutoff."
        ),
        claim_type="inference",
        status="verified",
        source_ids=sources,
        supporting_fact_ids=support,
        locator="section:thesis",
        applicable_period="2026-10-05/2027-10-05",
        report_section="thesis",
        segment="Data Center",
        metric_class="judgment",
        relation="supports_thesis",
        issuer=builder.by_role["dc_current"].get("issuer") or "",
    )


def _attach_render(state: dict) -> None:
    rendered = render_outputs(
        state["claims"],
        state["sources"],
        state["mandate"],
        synthetic=bool(state.get("synthetic", True)),
    )
    state.update(rendered)
