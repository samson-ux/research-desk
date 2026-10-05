# Approval gate

Live web research is blocked until a human adds `approvals/rubric_approval.json`.

This directory does not contain that approval. The generated rubric is not expert-validated.

Required fields:

- `approved`: true
- `expert_validated`: false
- `approved_by`: a human name (the value `agent` is rejected)
- `rubric_sha256`: the hash printed by `python -m research_desk.show_rubric`
- `mandate_sha256`: the mandate hash printed by the same command
- `cutoff_date`: `2026-10-05`

A changed rubric is a new mandate and needs a new approval.
