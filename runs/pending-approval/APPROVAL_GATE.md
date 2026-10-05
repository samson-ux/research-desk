# Approval gate

Live web research is blocked until a human writes `approvals/rubric_approval.json`
with the rubric hash below. This file is not that approval.

- Rubric SHA256: `4a71f17ba76d41fad68845f21b826582ba204890115e5dcf6744c1c88a5fbbff`
- Mandate SHA256: `e81d4d720dc5e28ef94ba7f9d19fdb011479db3f97c36f03cb1f375af4e5c64e`
- Cutoff: `2026-10-05` (America/Chicago)
- `expert_validated` must stay `false`.
- `approved_by` must be a human name. The desk rejects `agent`.

A changed rubric is a new mandate and needs a new approval. Historical
evidence from before the cutoff remains usable; the cutoff does not erase it.

This build has not executed live NVDA research.
