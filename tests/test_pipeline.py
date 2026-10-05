"""Offline pipeline: clean gate, detectors, repairs, budgets, and the live gate."""

from __future__ import annotations

import json
import unittest
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from research_desk.approval import ApprovalRequired, require_approval
from research_desk.auditor import Auditor
from research_desk.coordinator import Coordinator
from research_desk.editor import _restore_from_passage
from research_desk.live import documents_from_body, fetch_url
from research_desk.mandate import load_mandate
from research_desk.pipeline import run_research
from research_desk.run import main as run_main
from research_desk.scoring import score_verdicts


def _verdict(state, criterion_id, cycle=0):
    for row in state["audits"][cycle]["verdicts"]:
        if row["id"] == criterion_id:
            return row["verdict"]
    raise AssertionError(criterion_id)


class CleanRunTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "clean"
        cls.state = run_research(cls.out, run_id="synthetic-nvda-2026-10-05")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_gate_ready_and_score_recomputes(self):
        final = self.state["audits"][-1]
        self.assertEqual(final["gate"], "READY")
        self.assertEqual(Decimal(final["score"]), Decimal("1"))
        self.assertEqual(self.state["revision_cycles"], 0)
        self.assertFalse(self.state["live_research_executed"])
        self.assertTrue(self.state["synthetic"])
        self.assertEqual(self.state["search_queries_used"], 0)
        self.assertLessEqual(len(self.state["documents_inspected"]), 25)
        mandate = json.loads((self.out / "mandate.json").read_text(encoding="utf-8"))
        scored = score_verdicts(mandate["criteria"], final["verdicts"])
        self.assertEqual(scored["gate"], "READY")

    def test_required_artifacts_exist(self):
        for name in (
            "README.md",
            "mandate.json",
            "rubric.json",
            "sources.jsonl",
            "claims.csv",
            "report.md",
            "countercase.md",
            "audit.json",
            "revision_log.md",
            "manifest.json",
        ):
            self.assertTrue((self.out / name).is_file(), name)
        report = (self.out / "report.md").read_text(encoding="utf-8")
        for heading in (
            "## Thesis",
            "## Supporting evidence",
            "## Opposing evidence",
            "## Alternatives",
            "## Invalidation",
            "## Unknowns",
            "## Monitoring",
        ):
            self.assertIn(heading, report)
        self.assertIn("Judgment: conditionally durable.", report)
        self.assertIn("not a fact", report)
        self.assertIn("not total revenue", report)
        self.assertNotIn("buy ", report.lower())

    def test_post_cutoff_and_undated_sources_are_not_claims(self):
        claims = (self.out / "claims.csv").read_text(encoding="utf-8")
        self.assertNotIn("999.0", claims)
        self.assertNotIn("999", (self.out / "report.md").read_text(encoding="utf-8"))
        used = {}
        for line in (self.out / "sources.jsonl").read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            used[row["id"]] = row
            for field in ("id", "url", "title", "publisher", "published", "retrieved", "excerpt", "availability"):
                self.assertIn(field, row)
        self.assertFalse(used["SRC-008"]["used"])
        self.assertEqual(used["SRC-008"]["exclusion_reason"], "published_after_cutoff")
        self.assertFalse(used["SRC-009"]["used"])
        self.assertEqual(used["SRC-009"]["published"], "unknown")
        self.assertTrue(used["SRC-001"]["used"])
        self.assertLess(used["SRC-001"]["published"], "2026-10-05")

    def test_manifest_says_compliance_not_a_live_result(self):
        manifest = json.loads((self.out / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["gate"], "READY")
        self.assertFalse(manifest["expert_validated"])
        self.assertFalse(manifest["live_research_executed"])
        self.assertGreaterEqual(len(manifest["monitoring"]), 3)


class DetectorLoopTest(unittest.TestCase):
    def test_missing_citation_is_caught_and_the_editor_removes_it(self):
        with TemporaryDirectory() as tmp:
            state = run_research(Path(tmp) / "run", run_id="cite", defect="missing_citation")
        self.assertEqual(_verdict(state, "C14-UNCITED", 0), 1)
        self.assertEqual(state["audits"][0]["gate"], "BLOCKED")
        self.assertEqual(_verdict(state, "C14-UNCITED", -1), 0)
        self.assertEqual(state["audits"][-1]["gate"], "READY")
        self.assertNotIn("Data Center revenue was $40.0 billion.\n", state["report_md"])
        self.assertTrue(any("re-rendered" in action for action in state["revision_log"][0]["editor_actions"]))

    def test_fabrication_is_caught_and_restored_from_the_passage(self):
        with TemporaryDirectory() as tmp:
            state = run_research(Path(tmp) / "run", run_id="fab", defect="fabrication")
        self.assertEqual(_verdict(state, "C15-FABRICATION", 0), 1)
        self.assertEqual(state["audits"][0]["gate"], "BLOCKED")
        self.assertEqual(_verdict(state, "C15-FABRICATION", -1), 0)
        self.assertNotIn("123.4", state["report_md"])
        dc = next(claim for claim in state["claims"] if claim["role"] == "dc_current")
        self.assertEqual(dc["value"], "40.0")
        self.assertTrue(any("restored" in action for action in state["revision_log"][0]["editor_actions"]))

    def test_rubric_mutation_is_caught_and_not_adopted(self):
        with TemporaryDirectory() as tmp:
            state = run_research(Path(tmp) / "run", run_id="mut", defect="rubric_mutation")
        self.assertEqual(_verdict(state, "C16-RUBRIC-MUTATION", 0), 1)
        self.assertNotEqual(state["audits"][0]["working_rubric_sha256"], state["mandate"]["rubric_sha256"])
        self.assertEqual(_verdict(state, "C16-RUBRIC-MUTATION", -1), 0)
        self.assertEqual(state["audits"][-1]["working_rubric_sha256"], state["mandate"]["rubric_sha256"])
        self.assertEqual(state["rubric"][0]["weight"], 5)
        self.assertTrue(any("mutation was not adopted" in action for action in state["revision_log"][0]["editor_actions"]))

    def test_missing_primary_revenue_stays_blocked_without_an_invented_figure(self):
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "run"
            state = run_research(out, run_id="drop", defect="drop_primary_revenue")
            self.assertEqual(state["revision_cycles"], 2)
            self.assertEqual(state["audits"][-1]["gate"], "BLOCKED")
            self.assertIn("C02-PRIMARY-SOURCES", state["audits"][-1]["critical_failures"])
            self.assertNotIn("Judgment: conditionally durable.", state["report_md"])
            self.assertNotIn("Data Center revenue for FY2027 Q2 was $40.0 billion.", state["report_md"])
            self.assertNotIn("123.4", state["report_md"])
            self.assertIn("No figure was filled from memory.", state["report_md"])
            self.assertIn("Unresolved failures kept", (out / "revision_log.md").read_text(encoding="utf-8"))

    def test_editor_does_not_guess_when_the_passage_has_two_amounts(self):
        claim = {
            "value": "1.0",
            "unit": "USD_billions",
            "passage": "One figure was $40.0 billion and another was $32.0 billion.",
            "statement_template": "was {amount}",
            "statement": "was $1.0 billion",
        }
        self.assertFalse(_restore_from_passage(claim))

    def test_document_budget_stops_at_25_and_does_not_read_the_rest(self):
        docs = []
        for index in range(1, 27):
            docs.append(
                {
                    "id": f"SRC-{index:03d}",
                    "url": f"fixture://budget/{index}",
                    "path": "test",
                    "title": f"Budget doc {index}",
                    "publisher": "Synthetic fixture publisher",
                    "published": "2026-08-01",
                    "retrieved": "2026-10-05T09:00:00-05:00",
                    "event_time": "2026-07-26",
                    "applicable_period": "FY2027 Q2",
                    "excerpt": "SYNTHETIC FIXTURE.",
                    "locator": "budget",
                    "availability": "full_text",
                    "version": "t",
                    "kind": "primary",
                    "synthetic": True,
                    "issuer": "synthetic-nvidia",
                    "stance": "supporting",
                    "passages": [],
                }
            )
        docs[-1]["excerpt"] = "Data Center revenue for the second quarter of fiscal 2027 was $77.0 billion."
        docs[-1]["passages"] = [
            {
                "locator": "hidden",
                "text": docs[-1]["excerpt"],
                "value": "77.0",
                "unit": "USD_billions",
                "currency": "USD",
                "applicable_period": "FY2027 Q2",
                "segment": "Data Center",
                "metric_class": "revenue",
                "relation": "supports_thesis",
                "role": "dc_current",
                "statement": "Data Center revenue for FY2027 Q2 was $77.0 billion.",
            }
        ]
        inspected, skipped = Coordinator().select_documents(docs, 25)
        self.assertEqual(len(inspected), 25)
        self.assertEqual(skipped[0]["id"], "SRC-026")
        with TemporaryDirectory() as tmp:
            state = run_research(Path(tmp) / "run", run_id="budget", docs=docs)
        self.assertEqual(len(state["documents_inspected"]), 25)
        self.assertEqual(state["documents_skipped"][0]["id"], "SRC-026")
        self.assertNotIn("77.0", state["report_md"])
        self.assertEqual(state["audits"][-1]["gate"], "BLOCKED")

    def test_scope_breach_and_snippet_verification_block(self):
        with TemporaryDirectory() as tmp:
            state = run_research(Path(tmp) / "run", run_id="cleanish")
        state["report_md"] += "\nPlease buy 10 shares.\n"
        graded = Auditor().grade(state)
        scope = next(row for row in graded["verdicts"] if row["id"] == "C17-SCOPE")
        self.assertEqual(scope["verdict"], 1)
        self.assertEqual(graded["gate"], "BLOCKED")

        state["report_md"] = state["report_md"].replace("\nPlease buy 10 shares.\n", "\n")
        for source in state["sources"]:
            if source["id"] == "SRC-001":
                source["availability"] = "snippet"
        graded = Auditor().grade(state)
        snippet = next(row for row in graded["verdicts"] if row["id"] == "C18-SNIPPET-AS-VERIFICATION")
        self.assertEqual(snippet["verdict"], 1)
        self.assertEqual(graded["gate"], "BLOCKED")


class LiveGateTest(unittest.TestCase):
    def test_live_cli_is_blocked_and_does_not_fetch(self):
        def boom(*_args, **_kwargs):
            raise AssertionError("network fetch was attempted")

        import research_desk.run as run_mod

        original = run_mod.fetch_url
        run_mod.fetch_url = boom
        try:
            with TemporaryDirectory() as tmp:
                code = run_main(["--live", "--root", tmp])
        finally:
            run_mod.fetch_url = original
        self.assertEqual(code, 2)

    def test_require_approval_rejects_a_missing_file(self):
        with TemporaryDirectory() as tmp:
            with self.assertRaises(ApprovalRequired):
                require_approval(Path(tmp) / "missing.json", load_mandate())

    def test_companyfacts_extractor_keeps_segment_and_drops_post_cutoff_rows(self):
        payload = {
            "synthetic": True,
            "entityName": "SYNTHETIC FIXTURE NOT A FILING",
            "facts": {
                "nvda": {
                    "DataCenterRevenue": {
                        "units": {
                            "USD": [
                                {
                                    "end": "2026-07-26",
                                    "val": 40000000000,
                                    "fy": 2027,
                                    "fp": "Q2",
                                    "form": "10-Q",
                                    "filed": "2026-08-26",
                                    "accn": "0001",
                                },
                                {
                                    "end": "2026-10-26",
                                    "val": 999000000000,
                                    "fy": 2027,
                                    "fp": "Q3",
                                    "form": "10-Q",
                                    "filed": "2026-10-06",
                                    "accn": "9999",
                                },
                            ]
                        }
                    }
                },
                "us-gaap": {
                    "RevenueFromContractWithCustomerExcludingAssessedTax": {
                        "units": {
                            "USD": [
                                {
                                    "end": "2026-07-26",
                                    "val": 50000000000,
                                    "fy": 2027,
                                    "fp": "Q2",
                                    "form": "10-Q",
                                    "filed": "2026-08-26",
                                    "accn": "0001",
                                }
                            ]
                        }
                    }
                },
            },
        }
        docs = documents_from_body(
            "https://data.sec.gov/api/xbrl/companyfacts/CIK0001045810.json",
            json.dumps(payload).encode(),
            retrieved="2026-10-05T09:00:00-05:00",
        )
        roles = {passage["role"]: passage for passage in docs[0]["passages"]}
        self.assertEqual(roles["dc_current"]["segment"], "Data Center")
        self.assertEqual(roles["dc_current"]["value"], "40.0")
        self.assertEqual(roles["total_current"]["segment"], "Total")
        self.assertNotIn("999", docs[0]["excerpt"])
        with TemporaryDirectory() as tmp:
            state = run_research(Path(tmp) / "run", run_id="extract", docs=docs, mode="live")
        self.assertTrue(state["live_research_executed"])
        self.assertEqual(state["audits"][-1]["gate"], "BLOCKED")
        self.assertFalse(any(claim.get("value") == "999.0" for claim in state["claims"]))
        total = next(claim for claim in state["claims"] if claim["role"] == "total_current")
        self.assertNotEqual(total["segment"], "Data Center")

    def test_unparsed_html_does_not_become_a_revenue_claim(self):
        docs = documents_from_body(
            "https://www.nvidia.com/ignored",
            b"<html>Data Center revenue was $40.0 billion</html>",
            retrieved="2026-10-05T09:00:00-05:00",
        )
        self.assertEqual(docs[0]["passages"], [])
        self.assertNotIn("$40.0 billion", docs[0]["excerpt"])
        with TemporaryDirectory() as tmp:
            state = run_research(Path(tmp) / "run", run_id="html", docs=docs, mode="live")
        self.assertNotIn("$", state["report_md"])
        self.assertEqual(state["audits"][-1]["gate"], "BLOCKED")

    def test_fetch_allowlist(self):
        with self.assertRaises(ValueError):
            fetch_url("https://evil.example/secret", opener=lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("called")))


if __name__ == "__main__":
    unittest.main()
