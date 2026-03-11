# Failure Taxonomy Audit Pack

This pack is designed to strengthen the paper's failure-taxonomy section without rerunning the benchmark.

## Contents

- `audit_samples_blinded.csv`: reviewer-facing sheet with no automatic labels or language names.
- `audit_key.csv`: key containing auto-labels and metadata for adjudication.

## Recommended protocol

1. Give `audit_samples_blinded.csv` to two independent reviewers.
2. Ask each reviewer to fill `review_failure_category` and `review_runtime_subtype` without seeing the automatic labels.
3. Compare the filled sheets to `audit_key.csv` and compute agreement after adjudication.

## Sample composition

- Total rows: `60`
- Elixir failures included exhaustively: `25`
- Non-Elixir comparison failures sampled: `35`
- Category mix: compile `12`, runtime `37`, wrong_answer `11`, other `0`
