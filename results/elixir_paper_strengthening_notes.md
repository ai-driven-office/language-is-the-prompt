# Elixir Paper Strengthening Notes

## New methodology additions

- Recurring-task fixed-effects sanity check:
  - Script: `scripts/elixir_common_task_fixed_effects.py`
  - Outputs:
    - `results/elixir_common_task_fixed_effects.md`
    - `results/elixir_common_task_clusters.csv`
    - `results/elixir_common_task_language_effects.csv`
    - `results/elixir_common_task_elixir_summary.csv`
- Formal first-failure taxonomy:
  - Script: `scripts/elixir_error_taxonomy.py`
  - Outputs:
    - `results/elixir_error_taxonomy.md`
    - `results/elixir_error_taxonomy_summary.csv`
    - `results/elixir_error_taxonomy_tests.csv`
    - `results/elixir_error_taxonomy_stage_outcomes.csv`
    - `results/elixir_error_taxonomy_runtime_subtypes.csv`

## What these additions strengthen

- The paper is now less dependent on language-level proxy comparisons alone.
- The recurring-task analysis adds a conservative same-title matched subset with task-level demeaning.
- The failure analysis now uses explicit first-failure outcome parsing, Wilson confidence intervals, Fisher exact tests, and Holm correction.

## What the new results actually say

- Recurring-task fixed-effects sanity check:
  - Coverage is limited because ACB-Full does not expose a shared cross-language task id.
  - The conservative exact-title subset yields 28 multi-language clusters, with Elixir appearing in 7.
  - Elixir's mean within-cluster advantage is positive (`0.2143`) but imprecise, with bootstrap CI crossing zero (`-0.4286` to `0.7857`).
  - This supports only a weak sanity check, not a headline causal claim.

- First-failure taxonomy:
  - Elixir still stands out for very low overall failure incidence.
  - But once conditioning on failure, its compile/runtime/wrong-answer mix is not strongly different from the rest after multiple-testing correction.
  - The only surviving corrected difference is lower runtime-failure incidence over all rows, which mostly reflects higher overall pass rate.
  - Therefore the paper should avoid claiming that Elixir has a uniquely special failure-mode composition.

## Claim updates the draft should make

- Keep:
  - Elixir's corrected benchmark lead is real.
  - The artifact-control result is strong.
  - Documentation structure is the strongest causal signal in the active study.

- Soften:
  - Pattern matching as a proved primary driver.
  - Tagged tuples as a proved primary driver.
  - Failure-mode semantics as a major independent explanation.

- Reframe:
  - The safest thesis is explicitness and legibility.
  - Within that thesis, rich task framing is strongly supported.
  - Control flow, result contracts, and explicit state flow remain plausible secondary contributors.
