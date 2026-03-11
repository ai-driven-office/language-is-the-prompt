# suite_e Active Ablation Summary

Active ablation rerun using `gpt-5.4` / medium reasoning on `elixir` tasks.

## Condition summary

| Condition | Passed | Total | Pass Rate | 95% CI | Delta vs Baseline |
|---|---:|---:|---:|---:|---:|
| baseline | 166 | 198 | 83.8% | 78.1% to 88.3% | +0.0 |
| sentinel_helpers | 166 | 198 | 83.8% | 78.1% to 88.3% | +0.0 |
| tagged_tuple_helpers | 172 | 198 | 86.9% | 81.5% to 90.9% | +3.0 |

## Paired comparison vs baseline

| Condition | Baseline-Only Wins | Condition-Only Wins | McNemar p | Delta 95% CI | Cond. Pass Rate on Baseline-Pass Subset | Cond. Pass Rate on Baseline-Fail Subset |
|---|---:|---:|---:|---:|---:|---:|
| sentinel_helpers | 12 | 12 | 1.0 | -5.1 to 5.1 | 92.8% | 37.5% |
| tagged_tuple_helpers | 9 | 15 | 0.307456 | -2.0 to 8.1 | 94.6% | 46.9% |

## By difficulty

| Condition | Difficulty | Passed | Total | Pass Rate |
|---|---|---:|---:|---:|
| baseline | easy | 12 | 13 | 92.3% |
| baseline | hard | 119 | 139 | 85.6% |
| baseline | medium | 35 | 46 | 76.1% |
| sentinel_helpers | easy | 11 | 13 | 84.6% |
| sentinel_helpers | hard | 116 | 139 | 83.5% |
| sentinel_helpers | medium | 39 | 46 | 84.8% |
| tagged_tuple_helpers | easy | 12 | 13 | 92.3% |
| tagged_tuple_helpers | hard | 119 | 139 | 85.6% |
| tagged_tuple_helpers | medium | 41 | 46 | 89.1% |
