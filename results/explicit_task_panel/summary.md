# Explicit Task Panel Results

## Language By Condition

- `elixir / baseline_compact`: `9/16 = 56.2%` (95% Wilson CI `33.2%` to `76.9%`).
- `elixir / rich_contract`: `9/16 = 56.2%` (95% Wilson CI `33.2%` to `76.9%`).
- `elixir / rich_contract_examples`: `13/16 = 81.2%` (95% Wilson CI `57.0%` to `93.4%`).
- `python / baseline_compact`: `13/16 = 81.2%` (95% Wilson CI `57.0%` to `93.4%`).
- `python / rich_contract`: `13/16 = 81.2%` (95% Wilson CI `57.0%` to `93.4%`).
- `python / rich_contract_examples`: `13/16 = 81.2%` (95% Wilson CI `57.0%` to `93.4%`).
- `typescript / baseline_compact`: `13/16 = 81.2%` (95% Wilson CI `57.0%` to `93.4%`).
- `typescript / rich_contract`: `13/16 = 81.2%` (95% Wilson CI `57.0%` to `93.4%`).
- `typescript / rich_contract_examples`: `14/16 = 87.5%` (95% Wilson CI `64.0%` to `96.5%`).

## Aggregate Condition Totals

- `baseline_compact`: `35/48 = 72.9%` (95% Wilson CI `59.0%` to `83.4%`).
- `rich_contract`: `35/48 = 72.9%` (95% Wilson CI `59.0%` to `83.4%`).
- `rich_contract_examples`: `40/48 = 83.3%` (95% Wilson CI `70.4%` to `91.3%`).

## Paired Cross-Language Comparisons

- `rich_contract_vs_baseline_compact`: mean paired delta `0.0`, wins `0` vs losses `0`, discordant pairs `0`, exact sign p `1.0`.
- `rich_contract_examples_vs_baseline_compact`: mean paired delta `0.104`, wins `7` vs losses `2`, discordant pairs `9`, exact sign p `0.179688`.
- `rich_contract_examples_vs_rich_contract`: mean paired delta `0.104`, wins `7` vs losses `2`, discordant pairs `9`, exact sign p `0.179688`.

## Per-Language Paired Comparisons

- `elixir / rich_contract_vs_baseline_compact`: mean task delta `0.0`, wins `0` vs losses `0`, tied pass `9`, tied fail `7`, exact sign p `1.0`.
- `elixir / rich_contract_examples_vs_baseline_compact`: mean task delta `0.25`, wins `4` vs losses `0`, tied pass `9`, tied fail `3`, exact sign p `0.125`.
- `elixir / rich_contract_examples_vs_rich_contract`: mean task delta `0.25`, wins `4` vs losses `0`, tied pass `9`, tied fail `3`, exact sign p `0.125`.
- `python / rich_contract_vs_baseline_compact`: mean task delta `0.0`, wins `0` vs losses `0`, tied pass `13`, tied fail `3`, exact sign p `1.0`.
- `python / rich_contract_examples_vs_baseline_compact`: mean task delta `0.0`, wins `1` vs losses `1`, tied pass `12`, tied fail `2`, exact sign p `1.0`.
- `python / rich_contract_examples_vs_rich_contract`: mean task delta `0.0`, wins `1` vs losses `1`, tied pass `12`, tied fail `2`, exact sign p `1.0`.
- `typescript / rich_contract_vs_baseline_compact`: mean task delta `0.0`, wins `0` vs losses `0`, tied pass `13`, tied fail `3`, exact sign p `1.0`.
- `typescript / rich_contract_examples_vs_baseline_compact`: mean task delta `0.062`, wins `2` vs losses `1`, tied pass `12`, tied fail `1`, exact sign p `1.0`.
- `typescript / rich_contract_examples_vs_rich_contract`: mean task delta `0.062`, wins `2` vs losses `1`, tied pass `12`, tied fail `1`, exact sign p `1.0`.

## Tasks Rescued By Examples

- `Dense Rankings` (`dense_rankings`): rescued for `elixir`.
- `Rule Based Discount` (`rule_based_discount`): rescued for `elixir, typescript`.
- `Session Durations` (`session_durations`): rescued for `elixir, python, typescript`.
- `Stable Group Runs` (`stable_group_runs`): rescued for `elixir`.
