"""Allowlisted public fetch. Figures come only from parsed documents.

This module is not executed by the offline tests against the network.
A failed or unparsed response produces no financial claims.
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from urllib.request import Request, urlopen

from research_desk.constants import COMPANY_ISSUERS, CUTOFF_DATE
from research_desk.units import D, format_magnitude, q1
from research_desk.util import now_iso, parse_date

USER_AGENT = "research-desk/0.1 (evidence-first research; contact: research-desk@localhost)"
ALLOWLIST = {"data.sec.gov", "www.sec.gov", "www.nvidia.com", "investor.nvidia.com"}
DEFAULT_URLS = ("https://data.sec.gov/api/xbrl/companyfacts/CIK0001045810.json",)
TOTAL_REVENUE_CONCEPT = "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"


def fetch_url(url: str, opener=urlopen, timeout: int = 20) -> tuple[int, bytes]:
    from urllib.parse import urlparse

    host = urlparse(url).hostname or ""
    if host not in ALLOWLIST:
        raise ValueError(f"host not allowlisted: {host}")
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json,text/plain"})
    with opener(request, timeout=timeout) as response:
        body = response.read()
        status = getattr(response, "status", 200)
    return status, body


def documents_from_body(url: str, body: bytes, *, retrieved: str | None = None) -> list[dict]:
    """Parse a body into corpus-shaped documents. Unparsed bodies yield no facts."""
    retrieved = retrieved or now_iso()
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return [_empty_document(url, retrieved, "body_not_json")]
    if not isinstance(payload, dict) or "facts" not in payload:
        return [_empty_document(url, retrieved, "json_without_facts")]
    return [_companyfacts_document(url, payload, retrieved)]


def _empty_document(url: str, retrieved: str, reason: str) -> dict:
    return {
        "id": "WEB-001",
        "url": url,
        "path": "",
        "title": "Retrieved document was not parsed into facts",
        "publisher": url,
        "published": "unknown",
        "retrieved": retrieved,
        "event_time": "unknown",
        "applicable_period": "",
        "excerpt": f"No facts extracted ({reason}). No figure was filled from memory.",
        "locator": "body",
        "availability": "full_text",
        "version": "retrieved",
        "kind": "secondary",
        "synthetic": False,
        "issuer": "",
        "stance": "unparsed",
        "passages": [],
    }


def _companyfacts_document(url: str, payload: dict, retrieved: str) -> dict:
    cutoff = date.fromisoformat(CUTOFF_DATE)
    datacenter_rows: list[dict] = []
    total_rows: list[dict] = []
    omitted = 0
    facts = payload.get("facts") or {}
    for taxonomy, concepts in facts.items():
        if not isinstance(concepts, dict):
            continue
        for concept, body in concepts.items():
            qualified = f"{taxonomy}:{concept}"
            units = (body or {}).get("units") or {}
            for row in units.get("USD") or []:
                filed = parse_date(str(row.get("filed") or ""))
                if filed is None:
                    continue
                if filed > cutoff:
                    omitted += 1
                    continue
                if _is_datacenter(qualified, row):
                    datacenter_rows.append({**row, "concept": qualified})
                elif qualified == TOTAL_REVENUE_CONCEPT:
                    total_rows.append({**row, "concept": qualified})

    passages: list[dict] = []
    current, prior = _pick_datacenter_pair(datacenter_rows)
    if current:
        passages.append(_row_passage(current, role="dc_current", segment="Data Center", metric="revenue"))
    if prior:
        passages.append(_row_passage(prior, role="dc_prior", segment="Data Center", metric="revenue"))
    latest_total = _latest(total_rows)
    if latest_total:
        passages.append(_row_passage(latest_total, role="total_current", segment="Total", metric="revenue"))

    filed_dates = [parse_date(str(row.get("filed"))) for row in (current, prior, latest_total) if row]
    filed_dates = [item for item in filed_dates if item is not None]
    published = max(filed_dates).isoformat() if filed_dates else "unknown"
    excerpt_lines = [passage["text"] for passage in passages]
    excerpt_lines.append(f"Rows filed after {CUTOFF_DATE} were omitted: {omitted}. Their values were not copied.")
    entity = str(payload.get("entityName") or "SEC companyfacts")
    return {
        "id": "WEB-001",
        "url": url,
        "path": "",
        "title": f"SEC companyfacts extract — {entity}",
        "publisher": "U.S. Securities and Exchange Commission",
        "published": published,
        "retrieved": retrieved,
        "event_time": (current or {}).get("end") or "unknown",
        "applicable_period": (current or {}).get("period") or "",
        "excerpt": "\n".join(excerpt_lines),
        "locator": "companyfacts",
        "availability": "full_text",
        "version": "companyfacts",
        "kind": "primary",
        "synthetic": bool(payload.get("synthetic", False)),
        "issuer": "0001045810" if "0001045810" in COMPANY_ISSUERS else "nvidia",
        "stance": "supporting",
        "passages": passages,
    }


def _is_datacenter(qualified: str, row: dict) -> bool:
    compact = qualified.lower().replace("_", "").replace("-", "")
    if "datacenter" in compact:
        return True
    segment = str(row.get("segment") or row.get("member") or "")
    return "datacenter" in segment.lower().replace("_", "").replace("-", "")


def _period_label(row: dict) -> str:
    fy = row.get("fy")
    fp = row.get("fp") or ""
    if fy and str(fp).startswith("Q"):
        return f"FY{fy} {fp}"
    end = row.get("end") or "unknown-end"
    return f"ended {end}"


def _latest(rows: list[dict]) -> dict | None:
    dated = [row for row in rows if row.get("end")]
    if not dated:
        return None
    return sorted(dated, key=lambda row: str(row.get("end")))[-1]


def _pick_datacenter_pair(rows: list[dict]) -> tuple[dict | None, dict | None]:
    quarterly = [row for row in rows if str(row.get("fp") or "").startswith("Q") and row.get("fy") and row.get("end")]
    current = _latest(quarterly or rows)
    if not current:
        return None, None
    prior = None
    try:
        target_fy = int(current["fy"]) - 1
    except (TypeError, ValueError):
        target_fy = None
    if target_fy is not None:
        candidates = [
            row
            for row in quarterly
            if int(row["fy"]) == target_fy and row.get("fp") == current.get("fp")
        ]
        prior = _latest(candidates)
    current = {**current, "period": _period_label(current)}
    if prior:
        prior = {**prior, "period": _period_label(prior)}
    return current, prior


def _row_passage(row: dict, *, role: str, segment: str, metric: str) -> dict:
    raw = D(row["val"])
    billions = q1(raw / Decimal("1000000000"))
    amount = format_magnitude(billions, "USD_billions")
    period = row.get("period") or _period_label(row)
    concept = row["concept"]
    text = (
        f"Extracted {concept} form {row.get('form')} filed {row.get('filed')} "
        f"end {row.get('end')} value {row.get('val')} USD, which is {amount} "
        "after dividing by 1000000000."
    )
    end = str(row.get("end") or "")
    year = end[:4]
    quarter = str(row.get("fp") or "Q?")
    pretty = f"FY{row.get('fy')} {quarter}" if row.get("fy") and str(row.get("fp") or "").startswith("Q") else period
    if role == "dc_current":
        statement = f"Data Center revenue for {pretty} was {amount}."
    elif role == "dc_prior":
        statement = f"Data Center revenue for {pretty} was {amount}."
    else:
        statement = f"Total revenue for {pretty} was {amount}."
    return {
        "locator": f"{concept}:{row.get('accn') or ''}:{end}",
        "text": text,
        "value": str(billions),
        "unit": "USD_billions",
        "currency": "USD",
        "applicable_period": pretty,
        "period_left": "",
        "period_right": "",
        "segment": segment,
        "metric_class": metric,
        "relation": "supports_thesis" if segment == "Data Center" else "context",
        "role": role,
        "statement": statement,
        "raw_usd": str(raw),
    }
