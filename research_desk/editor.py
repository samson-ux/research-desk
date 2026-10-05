"""Editor: repair drafts without inventing evidence and without adopting a mutated rubric."""

from __future__ import annotations

import copy

from research_desk.integrity import rubric_mutated
from research_desk.researcher import _attach_render
from research_desk.units import (
    D,
    UnitError,
    apply_formula,
    format_magnitude,
    parse_magnitudes,
    q1,
    reconciliation_status,
)


class Editor:
    def revise(self, state: dict) -> list[str]:
        actions: list[str] = []
        frozen = copy.deepcopy(state["mandate"]["criteria"])
        if rubric_mutated(frozen, state["rubric"]):
            state["rubric"] = frozen
            actions.append("restored the frozen rubric; the mutation was not adopted")

        by_id = {claim["claim_id"]: claim for claim in state["claims"]}
        kept: list[dict] = []
        for claim in state["claims"]:
            if claim.get("value") in (None, "") or claim.get("formula"):
                kept.append(claim)
                continue
            if reconciliation_status(claim, by_id) == "reconciled":
                kept.append(claim)
                continue
            if _restore_from_passage(claim):
                if reconciliation_status(claim, by_id) == "reconciled":
                    actions.append(f"restored {claim['claim_id']} from its cited passage")
                    kept.append(claim)
                    continue
            actions.append(f"dropped {claim['claim_id']}; the passage does not uniquely support a value")

        state["claims"] = _recompute(kept, actions)
        _drop_orphaned_inferences(state, actions)
        _attach_render(state)
        actions.append("re-rendered the report and countercase from the claim table")
        return actions


def _restore_from_passage(claim: dict) -> bool:
    magnitudes = parse_magnitudes(claim.get("passage") or "")
    if len(magnitudes) != 1:
        return False
    unit, value = magnitudes[0]
    if unit != claim.get("unit"):
        return False
    new_value = str(q1(value))
    new_amount = format_magnitude(new_value, unit)
    template = claim.get("statement_template") or ""
    claim["value"] = new_value
    if "{amount}" in template:
        claim["statement"] = template.format(amount=new_amount)
    elif new_amount in template:
        claim["statement"] = template
    else:
        return False
    return True


def _recompute(claims: list[dict], actions: list[str]) -> list[dict]:
    by_id = {claim["claim_id"]: claim for claim in claims if not claim.get("formula")}
    rebuilt: list[dict] = []
    for claim in claims:
        if not claim.get("formula"):
            rebuilt.append(claim)
            by_id[claim["claim_id"]] = claim
            continue
        try:
            if claim["formula"] == "usd_to_billions":
                inputs = [{"value": claim.get("raw_usd"), "unit": "USD", "currency": "USD"}]
            else:
                missing = [item for item in claim.get("formula_inputs") or [] if item not in by_id]
                if missing:
                    raise UnitError("missing input " + ",".join(missing))
                inputs = [by_id[item] for item in claim["formula_inputs"]]
            value, unit, currency = apply_formula(claim["formula"], inputs)
        except (UnitError, KeyError):
            actions.append(f"dropped {claim['claim_id']}; formula inputs no longer reconcile")
            continue
        claim["value"] = str(q1(D(value)))
        claim["unit"] = unit
        claim["currency"] = currency
        template = claim.get("statement_template") or ""
        if "{amount}" in template:
            claim["statement"] = template.format(amount=format_magnitude(claim["value"], unit))
        rebuilt.append(claim)
        by_id[claim["claim_id"]] = claim
    return rebuilt


def _drop_orphaned_inferences(state: dict, actions: list[str]) -> None:
    surviving = {claim["claim_id"] for claim in state["claims"]}
    kept = []
    for claim in state["claims"]:
        if claim.get("claim_type") not in {"inference", "estimate"}:
            kept.append(claim)
            continue
        missing = [item for item in claim.get("supporting_fact_ids") or [] if item not in surviving]
        if missing:
            actions.append(f"dropped {claim['claim_id']}; a supporting fact is gone")
            continue
        kept.append(claim)
    state["claims"] = kept
