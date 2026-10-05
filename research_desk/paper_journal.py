"""Paper journal of research thesis calls.

This is not a broker. Rows do not size a position, send an order, or invent
P&L. A mark is recorded only when a price is fetched or supplied by a file.
`pnl` and `investment_return` stay `not_computed`.
"""

from __future__ import annotations

import argparse
import csv
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.request import Request, urlopen

from research_desk.util import canonical, now_iso

STANCES = ("conditional", "durable", "weakening", "invalidated", "unresolved")
FIELDS = [
    "record_id",
    "timestamp",
    "run_id",
    "asset",
    "thesis_link",
    "stance",
    "entry_note",
    "mark_status",
    "mark_price",
    "mark_currency",
    "mark_timestamp",
    "mark_source",
    "price_observation_ratio",
    "pnl",
    "investment_return",
]
NOT_COMPUTED = "not_computed"
YAHOO_HOST = "query1.finance.yahoo.com"


def journal_csv(root: Path) -> Path:
    return root / "journal" / "paper_trades.csv"


def journal_jsonl(root: Path) -> Path:
    return root / "journal" / "paper_trades.jsonl"


def marks_jsonl(root: Path) -> Path:
    return root / "journal" / "marks.jsonl"


def find_run(root: Path, run_id: str) -> Path:
    runs = root / "runs"
    if runs.is_dir():
        for manifest_path in runs.glob("**/manifest.json"):
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("run_id") == run_id:
                return manifest_path.parent
    raise FileNotFoundError(f"no research run with id {run_id}")


def log_call(
    root: Path,
    *,
    run_id: str,
    asset: str,
    stance: str,
    note: str,
) -> dict:
    if stance not in STANCES:
        raise ValueError(f"stance must be one of {', '.join(STANCES)}")
    run_dir = find_run(root, run_id)
    report = run_dir / "report.md"
    if not report.is_file():
        raise FileNotFoundError(f"{report} is missing")
    thesis_link = str(report.relative_to(root)) + "#thesis"
    rows = _read_rows(journal_csv(root))
    record = {
        "record_id": f"J-{len(rows) + 1:03d}",
        "timestamp": now_iso(),
        "run_id": run_id,
        "asset": asset.upper(),
        "thesis_link": thesis_link,
        "stance": stance,
        "entry_note": note,
        "mark_status": "unmarked",
        "mark_price": "",
        "mark_currency": "",
        "mark_timestamp": "",
        "mark_source": "",
        "price_observation_ratio": "unavailable",
        "pnl": NOT_COMPUTED,
        "investment_return": NOT_COMPUTED,
    }
    rows.append(record)
    _write_rows(root, rows)
    return record


def mark(
    root: Path,
    *,
    record_id: str | None = None,
    fixture: Path | None = None,
    fetch: bool = False,
    opener=urlopen,
) -> list[dict]:
    rows = _read_rows(journal_csv(root))
    if not rows:
        raise ValueError("journal is empty")
    targets = rows if record_id is None else [row for row in rows if row["record_id"] == record_id]
    if record_id and not targets:
        raise ValueError(f"unknown record {record_id}")
    updated = []
    for row in targets:
        observation = _observation(row["asset"], fixture=fixture, fetch=fetch, opener=opener)
        _append_mark(root, {**observation, "record_id": row["record_id"]})
        _apply_latest(root, row, observation)
        updated.append(row)
    _write_rows(root, rows)
    return updated


def report(root: Path) -> str:
    rows = _read_rows(journal_csv(root)) if journal_csv(root).is_file() else []
    lines = [
        "# Paper journal",
        "",
        "Thesis calls linked to research runs. Not a broker. No position size is stored.",
        "pnl and investment_return are not_computed. A price observation ratio is a change",
        "between two recorded marks, not position P&L and not an investment return.",
        "",
    ]
    if not rows:
        lines.append("No thesis calls are logged.")
        return "\n".join(lines) + "\n"
    for row in rows:
        if row.get("pnl") != NOT_COMPUTED or row.get("investment_return") != NOT_COMPUTED:
            raise ValueError("journal row invented pnl or an investment return")
        lines.append(f"## {row['record_id']} {row['asset']} {row['stance']}")
        lines.append("")
        lines.append(f"- timestamp: {row['timestamp']}")
        lines.append(f"- run_id: {row['run_id']}")
        lines.append(f"- thesis_link: {row['thesis_link']}")
        lines.append(f"- entry_note: {row['entry_note']}")
        lines.append(f"- mark_status: {row['mark_status']}")
        lines.append(f"- mark_price: {row['mark_price'] or 'unavailable'}")
        lines.append(f"- mark_currency: {row['mark_currency'] or 'unavailable'}")
        lines.append(f"- mark_timestamp: {row['mark_timestamp'] or 'unavailable'}")
        lines.append(f"- mark_source: {row['mark_source'] or 'unavailable'}")
        lines.append(f"- price_observation_ratio: {row['price_observation_ratio']}")
        lines.append(f"- pnl: {row['pnl']}")
        lines.append(f"- investment_return: {row['investment_return']}")
        lines.append("")
    return "\n".join(lines) + "\n"


def _observation(asset: str, *, fixture: Path | None, fetch: bool, opener) -> dict:
    if fixture is not None:
        payload = json.loads(Path(fixture).read_text(encoding="utf-8"))
        if payload.get("asset", asset).upper() != asset.upper():
            raise ValueError("fixture asset does not match the journal row")
        return {
            "mark_status": "fixture" if payload.get("synthetic") else "supplied",
            "mark_price": str(Decimal(str(payload["price"])).quantize(Decimal("0.01"))),
            "mark_currency": payload.get("currency") or "USD",
            "mark_timestamp": payload.get("as_of") or now_iso(),
            "mark_source": payload.get("source") or str(fixture),
            "asset": asset.upper(),
        }
    if not fetch:
        return {
            "mark_status": "unavailable",
            "mark_price": "",
            "mark_currency": "",
            "mark_timestamp": now_iso(),
            "mark_source": "",
            "asset": asset.upper(),
        }
    try:
        price, source = fetch_public_price(asset, opener=opener)
    except Exception as exc:  # noqa: BLE001 — fail closed, do not invent a price
        return {
            "mark_status": "unavailable",
            "mark_price": "",
            "mark_currency": "",
            "mark_timestamp": now_iso(),
            "mark_source": f"fetch_failed:{exc.__class__.__name__}",
            "asset": asset.upper(),
        }
    return {
        "mark_status": "fetched",
        "mark_price": price,
        "mark_currency": "USD",
        "mark_timestamp": now_iso(),
        "mark_source": source,
        "asset": asset.upper(),
    }


def fetch_public_price(asset: str, opener=urlopen, timeout: int = 15) -> tuple[str, str]:
    """Read a last price from a public quote endpoint. Raise if it cannot be parsed."""
    symbol = asset.upper()
    url = f"https://{YAHOO_HOST}/v8/finance/chart/{symbol}?interval=1d&range=1d"
    request = Request(url, headers={"User-Agent": "research-desk/0.1", "Accept": "application/json"})
    with opener(request, timeout=timeout) as response:
        body = response.read()
    price = parse_yahoo_chart(body)
    return price, url


def parse_yahoo_chart(body: bytes) -> str:
    payload = json.loads(body.decode("utf-8"))
    meta = payload["chart"]["result"][0]["meta"]
    raw = meta.get("regularMarketPrice")
    if raw is None:
        raise ValueError("regularMarketPrice missing")
    return str(Decimal(str(raw)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _apply_latest(root: Path, row: dict, observation: dict) -> None:
    row["mark_status"] = observation["mark_status"]
    row["mark_price"] = observation["mark_price"]
    row["mark_currency"] = observation["mark_currency"]
    row["mark_timestamp"] = observation["mark_timestamp"]
    row["mark_source"] = observation["mark_source"]
    row["pnl"] = NOT_COMPUTED
    row["investment_return"] = NOT_COMPUTED
    row["price_observation_ratio"] = _ratio(root, row["record_id"])


def _ratio(root: Path, record_id: str) -> str:
    path = marks_jsonl(root)
    if not path.is_file():
        return "unavailable"
    marks = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if item.get("record_id") == record_id and item.get("mark_status") in {"fixture", "fetched", "supplied"} and item.get("mark_price"):
            marks.append(item)
    if len(marks) < 2:
        return "unavailable"
    first = Decimal(marks[0]["mark_price"])
    latest = Decimal(marks[-1]["mark_price"])
    if first == 0:
        return "unavailable"
    ratio = (latest - first) / first
    return format(ratio.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP), "f")


def _append_mark(root: Path, observation: dict) -> None:
    path = marks_jsonl(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(canonical(observation) + "\n")


def _read_rows(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_rows(root: Path, rows: list[dict]) -> None:
    csv_path = journal_csv(root)
    jsonl_path = journal_jsonl(root)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(canonical({field: row.get(field, "") for field in FIELDS}) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Log a research thesis call. Not a broker.")
    parser.add_argument("--root", default=".")
    sub = parser.add_subparsers(dest="command", required=True)

    log_parser = sub.add_parser("log", help="Link a thesis call to a research run.")
    log_parser.add_argument("--run-id", required=True)
    log_parser.add_argument("--asset", default="NVDA")
    log_parser.add_argument("--stance", required=True, choices=STANCES)
    log_parser.add_argument("--note", required=True)
    log_parser.add_argument("--shares", type=str, default=None)
    log_parser.add_argument("--quantity", type=str, default=None)
    log_parser.add_argument("--order", type=str, default=None)

    mark_parser = sub.add_parser("mark", help="Record a price mark or an explicit unavailable mark.")
    mark_parser.add_argument("--record-id", default=None)
    mark_parser.add_argument("--fixture", default=None, help="JSON file with price, currency, source, synthetic.")
    mark_parser.add_argument("--fetch", action="store_true", help="Fetch a public quote. On failure the mark is unavailable.")
    mark_parser.add_argument("--shares", type=str, default=None)

    sub.add_parser("report", help="Print the journal. P&L stays not_computed.")
    args = parser.parse_args(argv)
    if getattr(args, "shares", None) or getattr(args, "quantity", None) or getattr(args, "order", None):
        print("Rejected. The paper journal does not accept shares, quantity, or orders.")
        return 2
    root = Path(args.root)
    if args.command == "log":
        record = log_call(root, run_id=args.run_id, asset=args.asset, stance=args.stance, note=args.note)
        print(f"logged {record['record_id']} stance {record['stance']} run {record['run_id']}")
        print(f"thesis_link: {record['thesis_link']}")
        print("pnl: not_computed")
        return 0
    if args.command == "mark":
        fixture = Path(args.fixture) if args.fixture else None
        updated = mark(root, record_id=args.record_id, fixture=fixture, fetch=args.fetch)
        for row in updated:
            print(
                f"{row['record_id']} mark_status {row['mark_status']} "
                f"mark_price {row['mark_price'] or 'unavailable'} "
                f"price_observation_ratio {row['price_observation_ratio']} "
                f"pnl {row['pnl']} investment_return {row['investment_return']}"
            )
        return 0
    print(report(root), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
