"""Frozen desk constants. The cutoff is an evidence rule, not a clock rewrite."""

CUTOFF_DATE = "2026-10-05"
HORIZON_END = "2027-10-05"
TIMEZONE = "America/Chicago"
ASSET = "NVDA"
READY_THRESHOLD = "0.85"
MAX_REVISION_CYCLES = 2
MAX_SEARCH_QUERIES = 15
MAX_UNIQUE_DOCUMENTS = 25
SCORE_FORMULA = "sum(weight * verdict) / sum(positive weights)"

QUESTION = (
    "How durable is NVIDIA's AI-driven revenue growth over the next 12 months, "
    "and what evidence would invalidate that thesis?"
)

# Company issuers the primary-source rule will accept.
# synthetic-nvidia is the offline fixture. The CIK is NVIDIA's public SEC identifier
# and is used only as a label on documents the live extractor actually parses.
COMPANY_ISSUERS = ("synthetic-nvidia", "nvidia", "0001045810")

PROVENANCE = {
    "framework": "ResearchRubrics",
    "citation": "Sharma, Zhang, Bandi, Wang, et al. ResearchRubrics: A Benchmark of Prompts and Rubrics For Evaluating Deep Research Agents. arXiv:2511.07685.",
    "url": "https://arxiv.org/abs/2511.07685",
    "named_coauthor": "Clinton Wang",
    "what_was_adapted": (
        "Criterion-by-criterion evaluation, negative criteria, and ternary grades "
        "(1 / 0.5 / 0). This desk's criteria were written for the NVDA question. "
        "They are not the expert-written ResearchRubrics benchmark items."
    ),
    "expert_validated": False,
}
