"""Synthetic NVDA corpus for the offline desk.

Every figure in this module is invented for tests. None of it is an NVIDIA
Corporation filing, a market print, or a live research result.
"""

from __future__ import annotations

from research_desk.units import D, format_magnitude, passage_supports, q1

RETRIEVED = "2026-10-05T09:00:00-05:00"
BANNER = (
    "SYNTHETIC FIXTURE. This text is not an NVIDIA Corporation filing, "
    "not a regulator's notice, and not a market quote."
)


def _money(value: str) -> str:
    return format_magnitude(value, "USD_billions")


def _percent(value: str) -> str:
    return format_magnitude(value, "percent")


def _passage(
    locator: str,
    text: str,
    *,
    value: str = "",
    unit: str = "",
    currency: str = "",
    applicable_period: str = "",
    period_left: str = "",
    period_right: str = "",
    segment: str = "",
    metric_class: str = "",
    relation: str = "context",
    role: str = "",
    statement: str = "",
) -> dict:
    return {
        "locator": locator,
        "text": text,
        "value": value,
        "unit": unit,
        "currency": currency,
        "applicable_period": applicable_period,
        "period_left": period_left,
        "period_right": period_right,
        "segment": segment,
        "metric_class": metric_class,
        "relation": relation,
        "role": role,
        "statement": statement,
    }


def _document(
    *,
    doc_id: str,
    url: str,
    title: str,
    publisher: str,
    published: str,
    event_time: str,
    applicable_period: str,
    kind: str,
    issuer: str,
    stance: str,
    passages: list[dict],
) -> dict:
    text = BANNER + "\n" + "\n".join(passage["text"] for passage in passages)
    return {
        "id": doc_id,
        "url": url,
        "path": "research_desk/fixture_corpus.py",
        "title": title,
        "publisher": publisher,
        "published": published,
        "retrieved": RETRIEVED,
        "event_time": event_time,
        "applicable_period": applicable_period,
        "excerpt": text,
        "locator": "fixture-corpus",
        "availability": "full_text",
        "version": "fixture-v1",
        "kind": kind,
        "synthetic": True,
        "issuer": issuer,
        "stance": stance,
        "passages": passages,
    }


def documents() -> list[dict]:
    """Nine short documents, including one post-cutoff trap and one undated note."""
    dc_current = _money("40.0")
    dc_prior = _money("32.0")
    total = _money("50.0")
    margin = _percent("70.0")
    concentration = _percent("20.0")
    inventory = _money("10.0")
    inventory_prior = _money("8.0")
    commitments = _money("15.0")
    exposure = _percent("10.0")
    networking = _money("8.0")
    compute = _money("32.0")
    units = _percent("0.0")
    asp = _percent("25.0")

    docs = [
        _document(
            doc_id="SRC-001",
            url="fixture://synthetic/nvda/fy2027q2-earnings-release",
            title="SYNTHETIC fixture — Q2 FY2027 earnings release (not an NVIDIA filing)",
            publisher="Synthetic fixture publisher (not NVIDIA Corporation)",
            published="2026-08-26",
            event_time="2026-07-26",
            applicable_period="FY2027 Q2",
            kind="primary",
            issuer="synthetic-nvidia",
            stance="supporting",
            passages=[
                _passage(
                    "dc-fy2027-q2",
                    f"Data Center revenue for the second quarter of fiscal 2027, ended 2026-07-26, was {dc_current}.",
                    value="40.0",
                    unit="USD_billions",
                    currency="USD",
                    applicable_period="FY2027 Q2",
                    segment="Data Center",
                    metric_class="revenue",
                    relation="supports_thesis",
                    role="dc_current",
                    statement=f"Data Center revenue for FY2027 Q2 was {dc_current}.",
                ),
                _passage(
                    "dc-fy2026-q2",
                    f"Data Center revenue for the second quarter of fiscal 2026 was {dc_prior}.",
                    value="32.0",
                    unit="USD_billions",
                    currency="USD",
                    applicable_period="FY2026 Q2",
                    segment="Data Center",
                    metric_class="revenue",
                    relation="supports_thesis",
                    role="dc_prior",
                    statement=f"Data Center revenue for FY2026 Q2 was {dc_prior}.",
                ),
                _passage(
                    "total-fy2027-q2",
                    f"Total revenue for the second quarter of fiscal 2027 was {total}.",
                    value="50.0",
                    unit="USD_billions",
                    currency="USD",
                    applicable_period="FY2027 Q2",
                    segment="Total",
                    metric_class="revenue",
                    relation="context",
                    role="total_current",
                    statement=f"Total revenue for FY2027 Q2 was {total}.",
                ),
                _passage(
                    "margin-fy2027-q2",
                    f"GAAP gross margin for the second quarter of fiscal 2027 was {margin}.",
                    value="70.0",
                    unit="percent",
                    currency="",
                    applicable_period="FY2027 Q2",
                    segment="consolidated",
                    metric_class="margin",
                    relation="context",
                    role="gross_margin",
                    statement=f"GAAP gross margin for FY2027 Q2 was {margin}.",
                ),
            ],
        ),
        _document(
            doc_id="SRC-002",
            url="fixture://synthetic/nvda/fy2027q2-10q",
            title="SYNTHETIC fixture — Q2 FY2027 Form 10-Q excerpt (not an NVIDIA filing)",
            publisher="Synthetic fixture publisher (not NVIDIA Corporation)",
            published="2026-08-28",
            event_time="2026-07-26",
            applicable_period="FY2027 Q2",
            kind="primary",
            issuer="synthetic-nvidia",
            stance="opposing",
            passages=[
                _passage(
                    "customer-concentration",
                    f"During the second quarter of fiscal 2027, one customer accounted for {concentration} of revenue.",
                    value="20.0",
                    unit="percent",
                    currency="",
                    applicable_period="FY2027 Q2",
                    segment="consolidated",
                    metric_class="concentration",
                    relation="opposes_thesis",
                    role="concentration",
                    statement=f"One customer accounted for {concentration} of revenue in FY2027 Q2.",
                ),
                _passage(
                    "inventory-fy2027-q2",
                    f"Inventory at the end of the second quarter of fiscal 2027 was {inventory}.",
                    value="10.0",
                    unit="USD_billions",
                    currency="USD",
                    applicable_period="FY2027 Q2",
                    segment="consolidated",
                    metric_class="inventory",
                    relation="context",
                    role="inventory",
                    statement=f"Inventory at the end of FY2027 Q2 was {inventory}.",
                ),
                _passage(
                    "inventory-fy2027-q1",
                    f"Inventory at the end of the first quarter of fiscal 2027 was {inventory_prior}.",
                    value="8.0",
                    unit="USD_billions",
                    currency="USD",
                    applicable_period="FY2027 Q1",
                    segment="consolidated",
                    metric_class="inventory",
                    relation="context",
                    role="inventory_prior",
                    statement=f"Inventory at the end of FY2027 Q1 was {inventory_prior}.",
                ),
                _passage(
                    "commitments",
                    f"Purchase commitments at the end of the second quarter of fiscal 2027 were {commitments}.",
                    value="15.0",
                    unit="USD_billions",
                    currency="USD",
                    applicable_period="FY2027 Q2",
                    segment="consolidated",
                    metric_class="commitments",
                    relation="context",
                    role="commitments",
                    statement=f"Purchase commitments at the end of FY2027 Q2 were {commitments}.",
                ),
            ],
        ),
        _document(
            doc_id="SRC-003",
            url="fixture://synthetic/nvda/spending-pause-note",
            title="SYNTHETIC fixture — customer spending-pause note (not an industry publication)",
            publisher="Synthetic fixture publisher (not a news organization)",
            published="2026-09-15",
            event_time="2026-09-15",
            applicable_period="next two quarters after 2026-09-15",
            kind="secondary",
            issuer="synthetic-note",
            stance="opposing",
            passages=[
                _passage(
                    "spending-pause",
                    "Two large cloud customers described a spending pause on incremental accelerator orders for the next two quarters.",
                    applicable_period="next two quarters after 2026-09-15",
                    segment="customers",
                    metric_class="qualitative",
                    relation="opposes_thesis",
                    role="pause",
                    statement=(
                        "Two large cloud customers described a spending pause on incremental "
                        "accelerator orders for the next two quarters."
                    ),
                ),
            ],
        ),
        _document(
            doc_id="SRC-004",
            url="fixture://synthetic/nvda/export-license-note",
            title="SYNTHETIC fixture — export-license exposure note (not a government document)",
            publisher="Synthetic fixture publisher (not a regulator)",
            published="2026-09-20",
            event_time="2026-09-20",
            applicable_period="trailing period described in the note",
            kind="official",
            issuer="synthetic-regulator",
            stance="opposing",
            passages=[
                _passage(
                    "export-exposure",
                    f"License requirements described here would have covered {exposure} of trailing Data Center revenue.",
                    value="10.0",
                    unit="percent",
                    currency="",
                    applicable_period="trailing period described in the note",
                    segment="Data Center",
                    metric_class="exposure",
                    relation="opposes_thesis",
                    role="exposure",
                    statement=f"Export-license exposure covered {exposure} of trailing Data Center revenue.",
                ),
            ],
        ),
        _document(
            doc_id="SRC-005",
            url="fixture://synthetic/nvda/datacenter-mix",
            title="SYNTHETIC fixture — Data Center mix supplement (not an NVIDIA filing)",
            publisher="Synthetic fixture publisher (not NVIDIA Corporation)",
            published="2026-08-26",
            event_time="2026-07-26",
            applicable_period="FY2027 Q2",
            kind="primary",
            issuer="synthetic-nvidia",
            stance="alternative",
            passages=[
                _passage(
                    "networking",
                    f"Within Data Center for the second quarter of fiscal 2027, networking revenue was {networking}.",
                    value="8.0",
                    unit="USD_billions",
                    currency="USD",
                    applicable_period="FY2027 Q2",
                    segment="Networking",
                    metric_class="revenue",
                    relation="alternative",
                    role="networking",
                    statement=f"Networking revenue inside Data Center for FY2027 Q2 was {networking}.",
                ),
                _passage(
                    "compute",
                    f"Within Data Center for the second quarter of fiscal 2027, compute revenue was {compute}.",
                    value="32.0",
                    unit="USD_billions",
                    currency="USD",
                    applicable_period="FY2027 Q2",
                    segment="Compute",
                    metric_class="revenue",
                    relation="alternative",
                    role="compute",
                    statement=f"Compute revenue inside Data Center for FY2027 Q2 was {compute}.",
                ),
            ],
        ),
        _document(
            doc_id="SRC-006",
            url="fixture://synthetic/nvda/price-versus-units",
            title="SYNTHETIC fixture — price versus units supplement (not an NVIDIA filing)",
            publisher="Synthetic fixture publisher (not NVIDIA Corporation)",
            published="2026-08-26",
            event_time="2026-07-26",
            applicable_period="FY2027 Q2",
            kind="primary",
            issuer="synthetic-nvidia",
            stance="alternative",
            passages=[
                _passage(
                    "unit-shipments",
                    f"Data Center unit shipments changed {units} year over year in the second quarter of fiscal 2027.",
                    value="0.0",
                    unit="percent",
                    currency="",
                    applicable_period="FY2027 Q2 vs FY2026 Q2",
                    period_left="FY2027 Q2",
                    period_right="FY2026 Q2",
                    segment="Data Center",
                    metric_class="volume",
                    relation="alternative",
                    role="units",
                    statement=f"Data Center unit shipments changed {units} from FY2026 Q2 to FY2027 Q2.",
                ),
                _passage(
                    "asp",
                    f"Data Center average selling price changed {asp} year over year in the second quarter of fiscal 2027.",
                    value="25.0",
                    unit="percent",
                    currency="",
                    applicable_period="FY2027 Q2 vs FY2026 Q2",
                    period_left="FY2027 Q2",
                    period_right="FY2026 Q2",
                    segment="Data Center",
                    metric_class="price",
                    relation="alternative",
                    role="asp",
                    statement=f"Data Center average selling price changed {asp} from FY2026 Q2 to FY2027 Q2.",
                ),
            ],
        ),
        _document(
            doc_id="SRC-007",
            url="fixture://synthetic/nvda/ir-calendar",
            title="SYNTHETIC fixture — IR calendar (not an NVIDIA calendar)",
            publisher="Synthetic fixture publisher (not NVIDIA Corporation)",
            published="2026-09-30",
            event_time="2026-09-30",
            applicable_period="calendar after 2026-10-05",
            kind="calendar",
            issuer="synthetic-nvidia",
            stance="monitoring",
            passages=[
                _passage(
                    "earnings-date",
                    "The next earnings release is scheduled for 2026-11-18.",
                    applicable_period="2026-11-18",
                    segment="",
                    metric_class="schedule",
                    relation="monitoring",
                    role="monitor_earnings",
                    statement="The next earnings release is scheduled for 2026-11-18.",
                ),
                _passage(
                    "tenq-window",
                    "The quarterly report on Form 10-Q filing window opens on 2026-12-07.",
                    applicable_period="2026-12-07",
                    segment="",
                    metric_class="schedule",
                    relation="monitoring",
                    role="monitor_10q",
                    statement="The Form 10-Q filing window opens on 2026-12-07.",
                ),
                _passage(
                    "tenk-window",
                    "The annual report on Form 10-K filing window opens on 2027-02-17.",
                    applicable_period="2027-02-17",
                    segment="",
                    metric_class="schedule",
                    relation="monitoring",
                    role="monitor_10k",
                    statement="The Form 10-K filing window opens on 2027-02-17.",
                ),
            ],
        ),
        _document(
            doc_id="SRC-008",
            url="fixture://synthetic/nvda/post-cutoff-trap",
            title="SYNTHETIC fixture — published after the cutoff and ineligible",
            publisher="Synthetic fixture publisher (not NVIDIA Corporation)",
            published="2026-10-06",
            event_time="2026-10-06",
            applicable_period="after cutoff",
            kind="primary",
            issuer="synthetic-nvidia",
            stance="trap",
            passages=[
                _passage(
                    "post-cutoff-revenue",
                    f"Data Center revenue in this post-cutoff trap was {_money('999.0')}.",
                    value="999.0",
                    unit="USD_billions",
                    currency="USD",
                    applicable_period="after cutoff",
                    segment="Data Center",
                    metric_class="revenue",
                    relation="excluded",
                    role="post_cutoff_trap",
                    statement="Ineligible post-cutoff figure.",
                ),
            ],
        ),
        _document(
            doc_id="SRC-009",
            url="fixture://synthetic/nvda/undated-channel-note",
            title="SYNTHETIC fixture — publication date unknown and ineligible",
            publisher="Synthetic fixture publisher (not a news organization)",
            published="unknown",
            event_time="unknown",
            applicable_period="unknown",
            kind="secondary",
            issuer="synthetic-note",
            stance="unknown",
            passages=[
                _passage(
                    "undated-note",
                    "Channel commentary said demand changed, with no dated figure in this note.",
                    applicable_period="unknown",
                    segment="",
                    metric_class="qualitative",
                    relation="excluded",
                    role="undated",
                    statement="Undated channel commentary is not a verified fact.",
                ),
            ],
        ),
    ]
    validate_corpus(docs)
    return docs


def validate_corpus(docs: list[dict]) -> None:
    ids = [doc["id"] for doc in docs]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate source ids in the fixture corpus")
    for doc in docs:
        for passage in doc["passages"]:
            if passage["text"] not in doc["excerpt"]:
                raise ValueError(f"{doc['id']} {passage['locator']} is missing from the excerpt")
            if passage["value"]:
                if not passage_supports(passage["text"], passage["value"], passage["unit"]):
                    raise ValueError(
                        f"{doc['id']} {passage['locator']} passage does not support "
                        f"{passage['value']} {passage['unit']}"
                    )
                if str(q1(D(passage["value"]))) != passage["value"]:
                    raise ValueError(f"{passage['locator']} value is not one-decimal quantized")


def drop_roles(docs: list[dict], roles: set[str]) -> list[dict]:
    """Return a deep copy of the corpus without selected fact roles."""
    import copy

    copied = copy.deepcopy(docs)
    for doc in copied:
        doc["passages"] = [passage for passage in doc["passages"] if passage.get("role") not in roles]
        doc["excerpt"] = BANNER + "\n" + "\n".join(passage["text"] for passage in doc["passages"])
    return copied
