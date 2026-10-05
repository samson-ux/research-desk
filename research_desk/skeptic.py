"""Skeptic: mark the forward judgment disputed when contrary claims exist.

The skeptic does not add facts, does not invent a tie, and does not rewrite
sourced numbers.
"""

from __future__ import annotations

from research_desk.researcher import _attach_render


class Skeptic:
    def run(self, state: dict) -> dict:
        opposing = [claim for claim in state["claims"] if claim.get("relation") == "opposes_thesis"]
        for claim in state["claims"]:
            if claim.get("role") != "thesis":
                continue
            if opposing:
                claim["status"] = "disputed"
                claim["dispute_of_note"] = (
                    "Forward durability is disputed from opposing claims already in the table."
                )
        _attach_render(state)
        return state
