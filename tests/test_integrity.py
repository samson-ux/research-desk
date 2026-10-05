"""Detectors for missing citations, fabricated numbers, and rubric mutations."""

from __future__ import annotations

import unittest

from research_desk.fixture_corpus import documents
from research_desk.integrity import (
    find_fabricated_claims,
    find_fabricated_report_magnitudes,
    find_uncited_magnitude_lines,
    rubric_mutated,
    scope_breaches,
)
from research_desk.mandate import load_mandate


def _sourced_claim(value: str = "40.0") -> dict:
    return {
        "claim_id": "CLM-001",
        "value": value,
        "unit": "USD_billions",
        "currency": "USD",
        "passage": "Data Center revenue for the second quarter of fiscal 2027 was $40.0 billion.",
        "formula": "",
        "formula_inputs": [],
        "source_ids": ["SRC-001"],
        "statement": f"Data Center revenue was ${value} billion.",
    }


class IntegrityDetectorTest(unittest.TestCase):
    def test_missing_citation_is_detected_when_the_number_is_real(self):
        claim = _sourced_claim()
        hits = find_uncited_magnitude_lines("Data Center revenue was $40.0 billion.\n", [claim])
        self.assertTrue(hits)
        self.assertEqual(hits[0]["kind"], "missing_citation")
        cited = find_uncited_magnitude_lines("Data Center revenue was $40.0 billion. [SRC-001]\n", [claim])
        self.assertEqual(cited, [])

    def test_citation_that_does_not_own_the_number_is_detected(self):
        claim = _sourced_claim()
        hits = find_uncited_magnitude_lines("Data Center revenue was $40.0 billion. [SRC-999]\n", [claim])
        self.assertTrue(hits)
        self.assertEqual(hits[0]["kind"], "citation_does_not_own_number")

    def test_fabricated_number_is_detected(self):
        bad = _sourced_claim("123.4")
        hits = find_fabricated_claims([bad])
        self.assertTrue(hits)
        self.assertEqual(hits[0]["claim_id"], "CLM-001")
        prose = find_fabricated_report_magnitudes("Upside $123.4 billion [SRC-001]\n", [_sourced_claim()])
        self.assertTrue(prose)
        self.assertEqual(prose[0]["kind"], "fabricated_magnitude")

    def test_sourced_number_is_not_fabricated(self):
        self.assertEqual(find_fabricated_claims([_sourced_claim()]), [])

    def test_rubric_mutation_is_detected(self):
        mandate = load_mandate()
        self.assertFalse(rubric_mutated(mandate["criteria"], mandate["criteria"]))
        mutated = [dict(row) for row in mandate["criteria"]]
        mutated[0]["weight"] = 1
        self.assertTrue(rubric_mutated(mandate["criteria"], mutated))

    def test_scope_detector_catches_orders_and_ignores_research_prose(self):
        self.assertTrue(scope_breaches("Please buy 10 shares of NVDA."))
        self.assertTrue(scope_breaches("The price target is aggressive."))
        self.assertTrue(scope_breaches("Set a position size and place an order."))
        self.assertEqual(scope_breaches("Data Center revenue grew. This is not position advice."), [])
        self.assertEqual(scope_breaches("The desk records no orders."), [])

    def test_fixture_passages_support_their_own_numbers(self):
        docs = documents()
        self.assertEqual(len(docs), 9)
        published = {doc["id"]: doc["published"] for doc in docs}
        self.assertEqual(published["SRC-008"], "2026-10-06")
        self.assertEqual(published["SRC-009"], "unknown")
        self.assertLess(published["SRC-001"], "2026-10-05")


if __name__ == "__main__":
    unittest.main()
