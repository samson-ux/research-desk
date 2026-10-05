# Approval gate

`rubric_approval.json` records Samson’s approval of the frozen rubric on 2026-10-05 (America/Chicago).

`expert_validated` stays false. The criteria are generated and are not expert-validated.

Required fields:

- `approved`: true
- `expert_validated`: false
- `approved_by`: a human name (the value `agent` is rejected)
- `rubric_sha256`: the hash printed by `python -m research_desk.show_rubric`
- `mandate_sha256`: the mandate hash printed by the same command
- `cutoff_date`: `2026-10-05`

A changed rubric is a new mandate and needs a new approval.
