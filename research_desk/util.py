"""Shared helpers: time, hashing, and markdown sections."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from zoneinfo import ZoneInfo

from research_desk.constants import TIMEZONE

CHICAGO = ZoneInfo(TIMEZONE)


def now_chicago() -> datetime:
    return datetime.now(CHICAGO)


def now_iso() -> str:
    return now_chicago().isoformat(timespec="seconds")


def chicago_date(stamp: str) -> date:
    parsed = datetime.fromisoformat(stamp)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=CHICAGO)
    return parsed.astimezone(CHICAGO).date()


def parse_date(value: str) -> date | None:
    if value is None or value == "" or value == "unknown":
        return None
    return date.fromisoformat(value[:10])


def canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(obj: object) -> str:
    return hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def section_body(markdown: str, heading: str) -> str:
    """Return the body under a level-2 heading, without the heading line."""
    needle = f"## {heading}"
    lines = markdown.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == needle:
            start = index + 1
            break
    if start is None:
        return ""
    collected: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        collected.append(line)
    return "\n".join(collected).strip()


def render_sections(title: str, preamble: list[str], sections: list[tuple[str, list[str]]]) -> str:
    parts: list[str] = [f"# {title}", ""]
    parts.extend(preamble)
    if preamble:
        parts.append("")
    for heading, lines in sections:
        parts.append(f"## {heading}")
        parts.append("")
        parts.extend(lines if lines else ["None recorded."])
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"
