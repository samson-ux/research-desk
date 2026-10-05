"""Mandate shape, score math, and unit reconciliation."""

from __future__ import annotations

import unittest
from decimal import Decimal

from research_desk.mandate import load_mandate, positive_weight_sum, rubric_hash, validate_mandate
from research_desk.scoring import score_verdicts
from research_desk.units import (
    UnitError,
    apply_formula,
    format_magnitude,
    parse_magnitudes,
    passage_supports,
    reconciliation_status,
    same_dollars,
    to_usd,
)


class MandateContractTest(unittest.TestCase):
    def test_criteria_are_atomic_and_not_expert_validated(self):
        mandate = load_mandate()
        rows = mandate["criteria"]
        self.assertGreaterEqual(len(rows), 12)
        self.assertLessEqual(len(rows), 20)
        self.assertFalse(mandate["expert_validated"])
        self.assertFalse(mandate["provenance"]["expert_validated"])
        self.assertEqual(mandate["asset"], "NVDA")
        self.assertIn("invalidate", mandate["question"])
        self.assertEqual(mandate["cutoff_date"], "2026-10-05")
        self.assertEqual(mandate["timezone"], "America/Chicago")
        self.assertEqual(mandate["budgets"]["max_revision_cycles"], 2)
        self.assertEqual(mandate["budgets"]["max_search_queries"], 15)
        self.assertEqual(mandate["budgets"]["max_unique_documents"], 25)
        ids = [row["id"] for row in rows]
        self.assertEqual(len(ids), len(set(ids)))
        for row in rows:
            self.assertNotEqual(row["weight"], 0)
            self.assertGreaterEqual(row["weight"], -5)
            self.assertLessEqual(row["weight"], 5)
            self.assertEqual(row["critical"], abs(row["weight"]) >= 4)
            self.assertTrue(row["test"].strip())
        validate_mandate(mandate)
        self.assertEqual(positive_weight_sum(rows), 50)
        self.assertEqual(rubric_hash(), mandate["rubric_sha256"])
        again = load_mandate()
        self.assertEqual(again["mandate_sha256"], mandate["mandate_sha256"])

    def test_hash_changes_when_a_weight_changes(self):
        mandate = load_mandate()
        mutated = [dict(row) for row in mandate["criteria"]]
        mutated[0]["weight"] = 1
        self.assertNotEqual(rubric_hash(mandate["criteria"]), rubric_hash(mutated))


class ScoringTest(unittest.TestCase):
    def setUp(self):
        self.criteria = load_mandate()["criteria"]

    def _verdicts(self, **overrides):
        rows = []
        for criterion in self.criteria:
            value = overrides.get(criterion["id"], 0 if criterion["weight"] < 0 else 1)
            unknown = value == "unknown"
            rows.append(
                {
                    "id": criterion["id"],
                    "verdict": None if unknown else value,
                    "unknown": unknown,
                }
            )
        return rows

    def test_perfect_score_is_ready(self):
        scored = score_verdicts(self.criteria, self._verdicts())
        self.assertEqual(Decimal(scored["score"]), Decimal("1"))
        self.assertEqual(scored["gate"], "READY")
        self.assertEqual(scored["positive_weight_sum"], 50)

    def test_noncritical_miss_can_stay_ready(self):
        scored = score_verdicts(self.criteria, self._verdicts(**{"C13-LOCATORS": 0}))
        self.assertEqual(Decimal(scored["score"]), Decimal("48") / Decimal("50"))
        self.assertEqual(scored["gate"], "READY")

    def test_three_optional_misses_are_partial(self):
        scored = score_verdicts(
            self.criteria,
            self._verdicts(**{"C07-ALTERNATIVES": 0, "C10-TIMESTAMPS": 0, "C11-MONITORING": 0}),
        )
        self.assertEqual(Decimal(scored["score"]), Decimal("41") / Decimal("50"))
        self.assertEqual(scored["gate"], "PARTIAL")
        self.assertEqual(scored["critical_failures"], [])

    def test_critical_partial_credit_blocks(self):
        scored = score_verdicts(self.criteria, self._verdicts(**{"C05-INVALIDATION": 0.5}))
        self.assertEqual(scored["gate"], "BLOCKED")
        self.assertIn("C05-INVALIDATION", scored["critical_failures"])
        self.assertGreaterEqual(Decimal(scored["score"]), Decimal("0.85"))

    def test_critical_negative_hit_blocks(self):
        scored = score_verdicts(self.criteria, self._verdicts(**{"C15-FABRICATION": 1}))
        self.assertEqual(scored["gate"], "BLOCKED")
        self.assertEqual(Decimal(scored["score"]), Decimal("45") / Decimal("50"))

    def test_unknown_critical_blocks_and_adds_nothing(self):
        scored = score_verdicts(self.criteria, self._verdicts(**{"C01-THESIS": "unknown"}))
        self.assertEqual(scored["gate"], "BLOCKED")
        self.assertIn("C01-THESIS", scored["critical_failures"])
        self.assertEqual(Decimal(scored["weighted_sum"]), Decimal("45"))


class UnitsTest(unittest.TestCase):
    def test_billions_and_millions_are_the_same_dollars(self):
        self.assertTrue(same_dollars("40.0", "USD_billions", "40000.0", "USD_millions"))
        self.assertEqual(to_usd("40.0", "USD_billions"), to_usd("40000", "USD_millions"))
        self.assertTrue(passage_supports("Revenue was $40.0 billion.", "40000.0", "USD_millions"))

    def test_parse_magnitudes_ignores_iso_dates(self):
        found = parse_magnitudes("Cutoff 2026-10-05 and growth 25.0% on $40.0 billion.")
        self.assertEqual(found, [("percent", Decimal("25.0")), ("USD_billions", Decimal("40.0"))])

    def test_yoy_share_and_compound(self):
        new = {"value": "40.0", "unit": "USD_billions", "currency": "USD"}
        old = {"value": "32.0", "unit": "USD_billions", "currency": "USD"}
        self.assertEqual(apply_formula("yoy_percent", [new, old])[0], "25.0")
        whole = {"value": "50.0", "unit": "USD_billions", "currency": "USD"}
        self.assertEqual(apply_formula("share_percent", [new, whole])[0], "80.0")
        units = {"value": "0.0", "unit": "percent", "currency": ""}
        price = {"value": "25.0", "unit": "percent", "currency": ""}
        self.assertEqual(apply_formula("compound_percent", [units, price])[0], "25.0")
        self.assertEqual(format_magnitude("40.0", "USD_billions"), "$40.0 billion")

    def test_percent_cannot_be_added_to_dollars(self):
        with self.assertRaises(UnitError):
            apply_formula(
                "sum_usd",
                [
                    {"value": "40.0", "unit": "USD_billions", "currency": "USD"},
                    {"value": "25.0", "unit": "percent", "currency": ""},
                ],
            )

    def test_foreign_currency_is_unreconciled(self):
        claim = {
            "claim_id": "CLM-X",
            "value": "40.0",
            "unit": "USD_billions",
            "currency": "EUR",
            "formula": "",
            "formula_inputs": [],
            "passage": "Revenue was $40.0 billion.",
        }
        self.assertEqual(reconciliation_status(claim, {"CLM-X": claim}), "unreconciled")


if __name__ == "__main__":
    unittest.main()
