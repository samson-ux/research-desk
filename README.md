# research-desk

Evidence-first research desk for one question: how durable is NVIDIA's AI-driven revenue growth over the twelve months after **2026-10-05** (America/Chicago), and what evidence would invalidate that thesis?

The desk is research only. It does not broker orders, size positions, touch accounts, or invent returns. A gate score measures rubric compliance. It is not a forecast and it is not a return.

Generated criteria are **not expert-validated**. They adapt the criterion-by-criterion method in Sharma, Zhang, Bandi, Wang, et al., [ResearchRubrics](https://arxiv.org/abs/2511.07685) (arXiv:2511.07685), including negative criteria and ternary grades. They are not that paper's expert-written benchmark items.

## Approval gate

Samson approved the frozen rubric on 2026-10-05 (America/Chicago). The approval is `approvals/rubric_approval.json`. `expert_validated` stays false. `approved_by` is Samson.

`python -m research_desk.run --live` is allowed only while that file matches the rubric hash from `python -m research_desk.show_rubric`. The runs under `runs/fixtures/` remain synthetic. Their figures are invented for the pipeline and are not NVIDIA Corporation results.

Historical sources dated before the cutoff stay eligible and keep their own dates. The cutoff does not erase them. A source published after 2026-10-05, or with an unknown publication date, is recorded and unused.

## Commands

From the repository root, with Python 3.11+ (`python` or `python3`):

```bash
python -m unittest discover -s tests -v
python -m research_desk.check_latest
python -m research_desk.show_rubric
python -m research_desk.run --integrity-samples
python -m research_desk.run --fixture
python -m research_desk.run --fixture --defect missing_citation
python -m research_desk.run --fixture --defect fabrication
python -m research_desk.run --fixture --defect rubric_mutation
python -m research_desk.run --fixture --defect drop_primary_revenue
python -m research_desk.paper_journal log \
  --run-id synthetic-nvda-2026-10-05 \
  --asset NVDA \
  --stance conditional \
  --note "Synthetic fixture thesis only. Not an order."
python -m research_desk.paper_journal mark --fixture examples/synthetic_nvda_price.json
python -m research_desk.paper_journal report
python -m research_desk.daily_report --date 2026-10-05
python -m research_desk.run --live
```

`python -m research_desk.run --live` exits 2 until `approvals/rubric_approval.json` matches the printed rubric hash. See `approvals/README.md`. The value `approved_by: agent` is rejected. `expert_validated` must stay false.

When the approval matches, `--live` fetches the SEC submissions index and the latest Form 10-Q filed on or before the cutoff. It reads quarterly inline-XBRL Data Center revenue, consolidated revenue, and direct-customer accounts-receivable shares, and it keeps those revenues in millions. Companyfacts is fetched only if that 10-Q has no quarterly Data Center fact. The run stays inside the 15-search and 25-document budgets.

## What a run contains

Each run writes `runs/<id>/`:

`README.md`, `mandate.json`, `rubric.json`, `sources.jsonl`, `claims.csv`, `report.md`, `countercase.md`, `audit.json`, `revision_log.md`, `manifest.json`.

The report sections are thesis, supporting evidence, opposing evidence, alternatives, invalidation, unknowns, and monitoring.

Fixture runs checked in here:

| Run | What it shows |
| --- | --- |
| `runs/fixtures/synthetic-nvda-2026-10-05` | Full offline loop. Gate READY on the synthetic corpus. Not a live reading. |
| `runs/fixtures/detected-missing-citation` | Cycle 0 blocks an uncited magnitude. The editor re-renders from the claim table. |
| `runs/fixtures/detected-fabrication` | Cycle 0 blocks `$123.4 billion`. The editor restores the passage figure. `123.4` does not survive. |
| `runs/fixtures/detected-rubric-mutation` | Cycle 0 blocks a changed weight. The editor restores the frozen rubric and does not adopt the mutation. |
| `runs/fixtures/blocked-missing-primary` | Primary Data Center revenue is absent. Gate stays BLOCKED after 2 revision cycles. No figure is filled from memory. |
| `runs/fixtures/integrity-samples` | Detector output for a missing citation, a fabricated number, and a rubric mutation. |

The pending rubric for approval is `runs/pending-approval/RUBRIC.txt`.

## Roles and loop

`Coordinator` freezes the mandate and enforces the budgets: 2 revision cycles, 15 web search queries, 25 unique documents.

`Researcher` binds admitted passages to claims. Ratios (year-over-year change, segment share, million/billion conversion, mix sum, price/unit compound) are computed in `research_desk/units.py`.

`Skeptic` disputes the forward judgment when contrary claims exist and does not invent a tie.

`Auditor` grades every frozen criterion `1`, `0.5`, or `0` from the artifacts alone. Negative criteria score the occurrence of the bad behavior. Weights used for the gate always come from the frozen mandate.

`Editor` may restore a number from its cited passage, drop a claim it cannot support, or restore the frozen rubric. It does not guess when a passage contains two amounts, and it does not invent a missing primary figure.

```text
score = sum(weight * verdict) / sum(positive weights)
```

READY requires score ≥ 0.85, every critical positive verdict = 1, every critical negative verdict = 0, and no unknown critical grade. Absolute weights 4 and 5 are critical. A critical failure is BLOCKED. Otherwise a score below 0.85 is PARTIAL. Unknown verdicts contribute 0.

## Paper journal and daily report

`research_desk/paper_journal.py` logs a thesis call linked to a run id. It rejects shares, quantity, and orders. `pnl` and `investment_return` stay `not_computed`. A mark is recorded only from a fixture file or a public quote fetch. If the fetch fails, the mark status is `unavailable` and no price is invented. Two recorded marks can show a `price_observation_ratio`. That ratio is a change between quotes, not position P&L.

`python -m research_desk.daily_report` summarizes that Chicago day's runs, gate counts, journal rows, and monitoring items still ahead of the report date.

The checked-in journal has two rows, both linked to the synthetic run, both with `pnl` and `investment_return` left as `not_computed`:

- `J-001` is marked from `examples/synthetic_nvda_price.json` (`100.00`, `mark_status=fixture`). That number is not a market quote.
- `J-002` is one public quote fetched from the Yahoo chart URL recorded in `mark_source`, with `mark_status=fetched`. It is a quote observation at the row's timestamp, not a target and not a return. A later fetch can differ. No ratio is computed from a single mark.

## Layout

```text
research_desk/
  mandate.py            frozen NVDA rubric
  units.py              USD scale and ratio math
  integrity.py          citation, fabrication, mutation, scope detectors
  coordinator.py        budgets and run open
  researcher.py         claim binding
  skeptic.py
  auditor.py
  editor.py
  pipeline.py           the loop
  live.py               allowlisted fetch; unparsed bodies yield no figures
  check_latest.py
  show_rubric.py
  paper_journal.py
  daily_report.py
  fixture_corpus.py     synthetic documents, including a post-cutoff trap
tests/                  unittest, no network
```

No API key and no paid service is required. Tests run offline.
