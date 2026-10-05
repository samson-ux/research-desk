"""Allowlisted public fetch. Figures come only from parsed documents.

This module is not executed by the offline tests against the network.
A failed or unparsed response produces no financial claims.
"""

from __future__ import annotations

import json
import re
from datetime import date
from decimal import Decimal
from html import unescape
from urllib.request import Request, urlopen

from research_desk.constants import COMPANY_ISSUERS, CUTOFF_DATE
from research_desk.units import D, format_magnitude, q1
from research_desk.util import now_iso, parse_date

USER_AGENT = "research-desk/0.1 (evidence-first research; contact: research-desk@localhost)"
ALLOWLIST = {"data.sec.gov", "www.sec.gov", "www.nvidia.com", "investor.nvidia.com"}
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK0001045810.json"
COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK0001045810.json"
DEFAULT_URLS = (SUBMISSIONS_URL, COMPANYFACTS_URL)
TOTAL_REVENUE_CONCEPT = "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"
_CIK = "0001045810"


def fetch_url(url: str, opener=urlopen, timeout: int = 20) -> tuple[int, bytes]:
    from urllib.parse import urlparse

    host = urlparse(url).hostname or ""
    if host not in ALLOWLIST:
        raise ValueError(f"host not allowlisted: {host}")
    request = Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json,text/html,text/plain,*/*"},
    )
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


def collect_live(opener=urlopen, *, limit: int = 15, timeout: int = 30, fetch=None) -> tuple[list[dict], int]:
    """Fetch the submissions index and the latest pre-cutoff 10-Q.

    Companyfacts is a fallback only when the 10-Q has no quarterly Data Center
    revenue fact. The returned count is the number of HTTP fetches.
    """
    fetch = fetch or fetch_url
    fetched = 0
    retrieved = now_iso()
    docs: list[dict] = []
    filing = None
    if fetched < limit:
        status, body = fetch(SUBMISSIONS_URL, opener=opener, timeout=timeout)
        fetched += 1
        if status == 200:
            filing = latest_10q(body)
    if filing and fetched < limit:
        status, body = fetch(filing["url"], opener=opener, timeout=timeout)
        fetched += 1
        if status == 200:
            docs = documents_from_ixbrl(
                filing["url"],
                body,
                published=filing["filed"],
                retrieved=retrieved,
                accession=filing["accession"],
            )
    if not _has_role(docs, "dc_current") and fetched < limit:
        status, body = fetch(COMPANYFACTS_URL, opener=opener, timeout=timeout)
        fetched += 1
        if status == 200:
            docs = documents_from_body(COMPANYFACTS_URL, body, retrieved=retrieved)
    if not docs:
        docs = [_empty_document(SUBMISSIONS_URL, retrieved, "no_pre_cutoff_10q_facts")]
    return docs, fetched


def latest_10q(body: bytes, *, cutoff: date | None = None) -> dict | None:
    """Latest Form 10-Q whose filing date is on or before the cutoff."""
    cutoff = cutoff or date.fromisoformat(CUTOFF_DATE)
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    recent = ((payload.get("filings") or {}).get("recent") or {}) if isinstance(payload, dict) else {}
    forms = recent.get("form") or []
    dates = recent.get("filingDate") or []
    accessions = recent.get("accessionNumber") or []
    primaries = recent.get("primaryDocument") or []
    cik = str(payload.get("cik") or _CIK) if isinstance(payload, dict) else _CIK
    best: dict | None = None
    for form, filed, accession, primary in zip(forms, dates, accessions, primaries):
        if form != "10-Q" or not accession or not primary:
            continue
        filed_date = parse_date(str(filed))
        if filed_date is None or filed_date > cutoff:
            continue
        if best is None or filed_date > best["filed_date"]:
            best = {
                "filed": filed_date.isoformat(),
                "filed_date": filed_date,
                "accession": str(accession),
                "primary": str(primary),
                "url": _filing_url(cik, str(accession), str(primary)),
            }
    if best is None:
        return None
    return {key: value for key, value in best.items() if key != "filed_date"}


def documents_from_ixbrl(
    url: str,
    body: bytes,
    *,
    published: str,
    retrieved: str | None = None,
    accession: str = "",
) -> list[dict]:
    """Parse quarterly inline-XBRL facts. Prose dollars are not claims."""
    retrieved = retrieved or now_iso()
    try:
        html = body.decode("utf-8", errors="replace")
    except Exception:
        return [_empty_document(url, retrieved, "body_not_text")]
    contexts = _contexts(html)
    facts = _ix_facts(html, contexts)
    if not contexts or not facts:
        return [_empty_document(url, retrieved, "no_inline_xbrl_facts")]
    fiscal_year, fiscal_period = _fiscal_focus(html)
    dc_rows = [
        fact
        for fact in facts
        if fact["name"] == "us-gaap:Revenues"
        and fact["usd"] is not None
        and fact["scale"] == 6
        and _is_quarter(fact)
        and _only_member(fact, "ProductOrServiceAxis", "DataCenterMember")
    ]
    total_rows = [
        fact
        for fact in facts
        if fact["name"] == "us-gaap:Revenues"
        and fact["usd"] is not None
        and fact["scale"] == 6
        and _is_quarter(fact)
        and not fact["members"]
    ]
    current, prior = _year_pair(dc_rows)
    total = _match_end(total_rows, (current or {}).get("end"))
    passages: list[dict] = []
    if current:
        passages.append(
            _ix_money_passage(
                current,
                role="dc_current",
                segment="Data Center",
                relation="supports_thesis",
                label=_fiscal_label(fiscal_year, fiscal_period, current=True),
                statement_prefix="Data Center revenue",
            )
        )
    if prior and current:
        passages.append(
            _ix_money_passage(
                prior,
                role="dc_prior",
                segment="Data Center",
                relation="supports_thesis",
                label=_fiscal_label(fiscal_year, fiscal_period, current=False),
                statement_prefix="Data Center revenue",
            )
        )
    if total and current:
        passages.append(
            _ix_money_passage(
                total,
                role="total_current",
                segment="Total",
                relation="context",
                label=_fiscal_label(fiscal_year, fiscal_period, current=True),
                statement_prefix="Total revenue",
            )
        )
    if current:
        passages.extend(_receivable_passages(facts, current["end"]))
    excerpt = [passage["text"] for passage in passages]
    excerpt.append(
        "Quarterly facts are duration contexts of 80 to 100 days. "
        "Longer Data Center rows were not used as the quarter. Their values were not copied."
    )
    event_time = (current or {}).get("end") or "unknown"
    period = passages[0]["applicable_period"] if passages else ""
    return [
        {
            "id": "WEB-001",
            "url": url,
            "path": "",
            "title": f"NVIDIA CORP Form 10-Q inline XBRL for the period ended {event_time}",
            "publisher": "U.S. Securities and Exchange Commission",
            "published": published,
            "retrieved": retrieved,
            "event_time": event_time,
            "applicable_period": period,
            "excerpt": "\n".join(excerpt),
            "locator": "inline-xbrl",
            "availability": "full_text",
            "version": accession or "10-Q",
            "kind": "primary",
            "synthetic": False,
            "issuer": _CIK if _CIK in COMPANY_ISSUERS else "nvidia",
            "stance": "mixed",
            "passages": passages,
        }
    ]


def _filing_url(cik: str, accession: str, primary: str) -> str:
    cik_int = str(int(str(cik).lstrip("0") or "0"))
    accession_compact = accession.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_compact}/{primary}"


def _has_role(docs: list[dict], role: str) -> bool:
    for doc in docs:
        for passage in doc.get("passages") or []:
            if passage.get("role") == role:
                return True
    return False


def _contexts(html: str) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for match in re.finditer(r"<xbrli:context\b([^>]*)>(.*?)</xbrli:context>", html, re.S):
        context_id = _attr(match.group(1), "id")
        if not context_id:
            continue
        body = match.group(2)
        members = re.findall(
            r'<xbrldi:explicitMember dimension="([^"]+)">([^<]+)</xbrldi:explicitMember>',
            body,
        )
        start = re.search(r"<xbrli:startDate>([^<]+)</xbrli:startDate>", body)
        end = re.search(r"<xbrli:endDate>([^<]+)</xbrli:endDate>", body)
        instant = re.search(r"<xbrli:instant>([^<]+)</xbrli:instant>", body)
        found[context_id] = {
            "members": [(dim, mem) for dim, mem in members],
            "start": start.group(1) if start else None,
            "end": end.group(1) if end else None,
            "instant": instant.group(1) if instant else None,
        }
    return found


def _ix_facts(html: str, contexts: dict[str, dict]) -> list[dict]:
    rows: list[dict] = []
    seen: set[tuple] = set()
    pattern = re.compile(r"<ix:nonFraction\b([^>]*)>(.*?)</ix:nonFraction>", re.S)
    for match in pattern.finditer(html):
        attrs = match.group(1)
        name = _attr(attrs, "name")
        context_id = _attr(attrs, "contextRef")
        if not name or not context_id or context_id not in contexts:
            continue
        scale_text = _attr(attrs, "scale")
        if scale_text is None:
            continue
        try:
            scale = int(scale_text)
        except ValueError:
            continue
        raw = _fact_text(match.group(2))
        if not re.fullmatch(r"-?\d+(?:\.\d+)?", raw):
            continue
        key = (name, context_id, raw, scale)
        if key in seen:
            continue
        seen.add(key)
        sign = _attr(attrs, "sign")
        magnitude = D(raw)
        if sign == "-":
            magnitude = -magnitude
        ctx = contexts[context_id]
        usd = None
        percent = None
        if scale == 6 and magnitude >= 0:
            usd = magnitude * Decimal("1000000")
        if scale == -2 and magnitude >= 0:
            percent = q1(magnitude)
        rows.append(
            {
                "name": name,
                "context": context_id,
                "raw": raw,
                "scale": scale,
                "members": ctx["members"],
                "start": ctx["start"],
                "end": ctx["end"],
                "instant": ctx["instant"],
                "usd": usd,
                "percent": percent,
            }
        )
    return rows


def _attr(attrs: str, name: str) -> str | None:
    match = re.search(rf'\b{name}="([^"]*)"', attrs)
    return match.group(1) if match else None


def _fact_text(inner: str) -> str:
    text = re.sub(r"<[^>]+>", "", inner)
    text = unescape(text).replace(",", "").replace("\xa0", "").strip()
    return text


def _fiscal_focus(html: str) -> tuple[int | None, str | None]:
    year_text = _non_numeric(html, "dei:DocumentFiscalYearFocus")
    period_text = _non_numeric(html, "dei:DocumentFiscalPeriodFocus")
    year = None
    if year_text and year_text.isdigit():
        year = int(year_text)
    period = period_text if period_text in {"Q1", "Q2", "Q3", "Q4"} else None
    return year, period


def _non_numeric(html: str, name: str) -> str | None:
    match = re.search(
        rf'<ix:nonNumeric\b[^>]*\bname="{re.escape(name)}"[^>]*>(.*?)</ix:nonNumeric>',
        html,
        re.S,
    )
    if not match:
        return None
    text = re.sub(r"<[^>]+>", "", match.group(1))
    text = unescape(text).replace("\xa0", " ").strip()
    return text or None


def _is_quarter(fact: dict) -> bool:
    start = parse_date(fact.get("start") or "")
    end = parse_date(fact.get("end") or "")
    if start is None or end is None:
        return False
    days = (end - start).days
    return 80 <= days <= 100


def _only_member(fact: dict, axis_suffix: str, member_suffix: str) -> bool:
    members = fact.get("members") or []
    if len(members) != 1:
        return False
    axis, member = members[0]
    return axis.endswith(axis_suffix) and member.endswith(member_suffix)


def _has_member(fact: dict, axis_suffix: str, member_suffix: str) -> bool:
    for axis, member in fact.get("members") or []:
        if axis.endswith(axis_suffix) and member.endswith(member_suffix):
            return True
    return False


def _member_on(fact: dict, axis_suffix: str) -> str:
    for axis, member in fact.get("members") or []:
        if axis.endswith(axis_suffix):
            return member
    return ""


def _year_pair(rows: list[dict]) -> tuple[dict | None, dict | None]:
    current = _unique_latest(rows)
    if not current or not current.get("end"):
        return None, None
    current_end = parse_date(current["end"])
    if current_end is None:
        return current, None
    candidates = []
    for row in rows:
        end = parse_date(row.get("end") or "")
        if end is None or end >= current_end:
            continue
        gap = (current_end - end).days
        if 350 <= gap <= 380:
            candidates.append(row)
    prior = _unique_latest(candidates)
    return current, prior


def _unique_latest(rows: list[dict]) -> dict | None:
    dated = [row for row in rows if row.get("end")]
    if not dated:
        return None
    latest_end = max(str(row["end"]) for row in dated)
    chosen = [row for row in dated if str(row["end"]) == latest_end]
    amounts = {str(row["usd"]) for row in chosen}
    if len(amounts) != 1:
        return None
    return chosen[0]


def _match_end(rows: list[dict], end: str | None) -> dict | None:
    if not end:
        return None
    chosen = [row for row in rows if row.get("end") == end]
    if not chosen:
        return None
    amounts = {str(row["usd"]) for row in chosen}
    if len(amounts) != 1:
        return None
    return chosen[0]


def _fiscal_label(year: int | None, period: str | None, *, current: bool) -> str:
    if year is None or not period:
        return ""
    label_year = year if current else year - 1
    return f"FY{label_year} {period}"


def _ix_money_passage(
    fact: dict,
    *,
    role: str,
    segment: str,
    relation: str,
    label: str,
    statement_prefix: str,
) -> dict:
    millions = q1(D(fact["raw"]))
    amount = format_magnitude(millions, "USD_millions")
    pretty = label or f"ended {fact.get('end')}"
    member = ""
    if fact.get("members"):
        member = fact["members"][0][1]
    text = (
        f"Inline XBRL {fact['name']} context {fact['context']} "
        f"member {member or 'none'} start {fact.get('start')} end {fact.get('end')} "
        f"scale {fact['scale']} displayed {fact['raw']} unit usd, which is {amount}."
    )
    statement = f"{statement_prefix} for {pretty} was {amount}."
    return {
        "locator": f"{fact['name']}:{fact['context']}:{fact.get('end')}",
        "text": text,
        "value": str(millions),
        "unit": "USD_millions",
        "currency": "USD",
        "applicable_period": pretty,
        "period_left": "",
        "period_right": "",
        "segment": segment,
        "metric_class": "revenue",
        "relation": relation,
        "role": role,
        "statement": statement,
        "raw_usd": str(fact["usd"]),
    }


def _receivable_passages(facts: list[dict], end: str) -> list[dict]:
    rows = []
    for fact in facts:
        if fact["name"] != "us-gaap:ConcentrationRiskPercentage1" or fact.get("percent") is None:
            continue
        if fact.get("end") != end or fact.get("scale") != -2:
            continue
        if not _has_member(fact, "ConcentrationRiskByBenchmarkAxis", "AccountsReceivableMember"):
            continue
        if not _has_member(fact, "ConcentrationRiskByTypeAxis", "CustomerConcentrationRiskMember"):
            continue
        customer = _member_on(fact, "MajorCustomersAxis")
        if not customer:
            continue
        if _member_on(fact, "StatementGeographicalAxis") or _member_on(fact, "StatementBusinessSegmentsAxis"):
            continue
        rows.append({**fact, "customer": customer})
    ranked = sorted(rows, key=lambda row: (-row["percent"], row["customer"], row["context"]))
    unique: list[dict] = []
    seen_customers: set[str] = set()
    for row in ranked:
        if row["customer"] in seen_customers:
            continue
        seen_customers.add(row["customer"])
        unique.append(row)
    passages = []
    specs = (
        ("concentration", "The largest tagged direct-customer accounts-receivable share"),
        ("concentration_next", "The next tagged direct-customer accounts-receivable share"),
    )
    for row, (role, prefix) in zip(unique, specs):
        amount = format_magnitude(row["percent"], "percent")
        text = (
            f"Inline XBRL {row['name']} context {row['context']} "
            f"benchmark us-gaap:AccountsReceivableMember customer {row['customer']} "
            f"start {row.get('start')} end {row.get('end')} scale -2 displayed {row['raw']}, "
            f"which is {amount} of accounts receivable."
        )
        statement = f"{prefix} was {amount} as of {end}."
        passages.append(
            {
                "locator": f"{row['name']}:{row['context']}:{end}",
                "text": text,
                "value": str(q1(row["percent"])),
                "unit": "percent",
                "currency": "",
                "applicable_period": f"as of {end}",
                "period_left": "",
                "period_right": "",
                "segment": "consolidated",
                "metric_class": "concentration",
                "relation": "opposes_thesis",
                "role": role,
                "statement": statement,
            }
        )
    return passages
