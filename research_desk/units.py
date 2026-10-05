"""Money, percent, and ratio math.

Every ratio the desk reports is produced here. Callers pass sourced inputs.
A quantity the function cannot reconcile is an error, not a guessed number.
"""

from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP

class UnitError(ValueError):
    """Inputs do not share a dimension, or a formula does not apply."""


_MONEY_SCALES = {
    "USD": Decimal("1"),
    "USD_millions": Decimal("1000000"),
    "USD_billions": Decimal("1000000000"),
}

_MAGNITUDE = re.compile(
    r"\$(?P<num>\d+(?:,\d{3})*(?:\.\d+)?)\s*(?P<scale>billion|million)\b"
    r"|(?P<pct>\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:%|percentage points\b|percent\b)",
    re.IGNORECASE,
)


def D(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if value is None or value == "":
        raise UnitError("missing numeric value")
    return Decimal(str(value))


def q1(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def is_money(unit: str) -> bool:
    return unit in _MONEY_SCALES


def to_usd(value: object, unit: str) -> Decimal:
    if unit not in _MONEY_SCALES:
        raise UnitError(f"not a USD unit: {unit}")
    return D(value) * _MONEY_SCALES[unit]


def format_magnitude(value: object, unit: str) -> str:
    quantized = q1(D(value))
    if unit == "USD_billions":
        return f"${quantized} billion"
    if unit == "USD_millions":
        return f"${quantized} million"
    if unit == "USD":
        return f"${quantized}"
    if unit == "percent":
        return f"{quantized}%"
    raise UnitError(f"cannot format unit {unit}")


def parse_magnitudes(text: str) -> list[tuple[str, Decimal]]:
    found: list[tuple[str, Decimal]] = []
    for match in _MAGNITUDE.finditer(text or ""):
        if match.group("pct") is not None:
            number = D(match.group("pct").replace(",", ""))
            found.append(("percent", q1(number)))
            continue
        scale = match.group("scale").lower()
        unit = "USD_billions" if scale == "billion" else "USD_millions"
        number = D(match.group("num").replace(",", ""))
        found.append((unit, q1(number)))
    return found


def same_dollars(left_value: object, left_unit: str, right_value: object, right_unit: str) -> bool:
    return to_usd(left_value, left_unit) == to_usd(right_value, right_unit)


def passage_supports(passage: str, value: object, unit: str) -> bool:
    """True when the passage contains this quantity, after USD scale conversion."""
    if is_money(unit):
        target = to_usd(value, unit)
        for found_unit, found_value in parse_magnitudes(passage):
            if is_money(found_unit) and to_usd(found_value, found_unit) == target:
                return True
        return False
    if unit == "percent":
        target = ("percent", q1(D(value)))
        return target in parse_magnitudes(passage)
    raise UnitError(f"unsupported unit {unit}")


def magnitude_matches_claim(unit: str, value: Decimal, claim: dict) -> bool:
    claim_unit = claim.get("unit") or ""
    claim_value = claim.get("value") or ""
    if claim_value == "":
        return False
    try:
        if unit == claim_unit:
            return q1(D(claim_value)) == q1(value)
        if is_money(unit) and is_money(claim_unit):
            return to_usd(value, unit) == to_usd(claim_value, claim_unit)
    except UnitError:
        return False
    return False


def _money_pair(left: dict, right: dict) -> tuple[Decimal, Decimal]:
    if not is_money(left.get("unit", "")) or not is_money(right.get("unit", "")):
        raise UnitError("both inputs must be USD amounts")
    if left.get("currency") not in (None, "", "USD") or right.get("currency") not in (None, "", "USD"):
        raise UnitError("non-USD currency has no sourced FX rate")
    return to_usd(left["value"], left["unit"]), to_usd(right["value"], right["unit"])


def apply_formula(name: str, inputs: list[dict]) -> tuple[str, str, str]:
    """Return (value, unit, currency) for a named formula. Raises UnitError on mismatch."""
    if name == "yoy_percent":
        new, old = inputs
        new_usd, old_usd = _money_pair(new, old)
        if old_usd == 0:
            raise UnitError("year-over-year base is zero")
        percent = q1((new_usd - old_usd) / old_usd * Decimal("100"))
        return str(percent), "percent", "USD"
    if name == "share_percent":
        part, whole = inputs
        part_usd, whole_usd = _money_pair(part, whole)
        if whole_usd == 0:
            raise UnitError("share denominator is zero")
        percent = q1(part_usd / whole_usd * Decimal("100"))
        return str(percent), "percent", "USD"
    if name == "billion_to_million":
        (src,) = inputs
        if src.get("unit") != "USD_billions" or src.get("currency") not in (None, "", "USD"):
            raise UnitError("billion_to_million requires USD billions")
        millions = q1(D(src["value"]) * Decimal("1000"))
        return str(millions), "USD_millions", "USD"
    if name == "sum_usd":
        left, right = inputs
        _money_pair(left, right)
        if left.get("unit") != right.get("unit"):
            raise UnitError("sum_usd requires a shared display unit; convert first")
        total = q1(D(left["value"]) + D(right["value"]))
        return str(total), left["unit"], "USD"
    if name == "compound_percent":
        unit_change, price_change = inputs
        if unit_change.get("unit") != "percent" or price_change.get("unit") != "percent":
            raise UnitError("compound_percent requires percent inputs")
        units = D(unit_change["value"]) / Decimal("100")
        price = D(price_change["value"]) / Decimal("100")
        percent = q1(((Decimal("1") + units) * (Decimal("1") + price) - Decimal("1")) * Decimal("100"))
        return str(percent), "percent", "USD"
    if name == "usd_to_billions":
        (src,) = inputs
        if src.get("unit") != "USD":
            raise UnitError("usd_to_billions requires raw USD")
        billions = q1(D(src["value"]) / Decimal("1000000000"))
        return str(billions), "USD_billions", "USD"
    raise UnitError(f"unknown formula {name}")


def reconciliation_status(claim: dict, by_id: dict[str, dict]) -> str:
    """reconciled, unreconciled, or not_numeric."""
    if claim.get("value") in (None, ""):
        return "not_numeric"
    unit = claim.get("unit") or ""
    if unit not in _MONEY_SCALES and unit != "percent":
        return "unreconciled"
    if is_money(unit) and claim.get("currency") not in (None, "", "USD"):
        return "unreconciled"
    formula = claim.get("formula") or ""
    if formula:
        try:
            if formula == "usd_to_billions":
                raw = claim.get("raw_usd")
                inputs = [{"value": raw, "unit": "USD", "currency": "USD"}]
            else:
                inputs = [by_id[item] for item in claim.get("formula_inputs") or []]
            value, out_unit, _currency = apply_formula(formula, inputs)
        except (UnitError, KeyError, IndexError):
            return "unreconciled"
        if out_unit == unit and q1(D(value)) == q1(D(claim["value"])):
            return "reconciled"
        return "unreconciled"
    try:
        if passage_supports(claim.get("passage") or "", claim["value"], unit):
            return "reconciled"
    except UnitError:
        return "unreconciled"
    return "unreconciled"
