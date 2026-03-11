# Elixir Active Ablation Pilot

This report summarizes the first active rerun pass for the scientific Elixir suites.

Pilot shape:

- `9` Elixir benchmark rows
- `3` easy, `3` medium, `3` hard
- source rows selected from tasks that already passed in the corrected main benchmark run
- model: `gpt-5.4` with medium reasoning

## Key findings

- `suite_a`: baseline `full_docs` = `100.0%`; best condition `full_docs` = `100.0%`; worst condition `signature_only` = `55.6%`.
- `suite_d`: baseline `baseline` = `100.0%`; best condition `baseline` = `100.0%`; worst condition `baseline` = `100.0%`.
- `suite_e`: baseline `baseline` = `100.0%`; best condition `baseline` = `100.0%`; worst condition `sentinel_helpers` = `88.9%`.
- `suite_f`: baseline `baseline` = `100.0%`; best condition `baseline` = `100.0%`; worst condition `baseline` = `100.0%`.

Interpretation:

- Documentation compression clearly hurts once the prompt is reduced to signatures only.
- Tagged-tuple helper prompting is at least competitive with the unconstrained baseline on this slice.
- Control-flow style and mutability-style prompt constraints did not move pass rate on this first pilot slice, which means those hypotheses need a larger or harder intervention set before drawing strong conclusions.
