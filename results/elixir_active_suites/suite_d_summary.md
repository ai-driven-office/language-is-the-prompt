# suite_d Active Ablation Summary

Active ablation rerun using `gpt-5.4` / medium reasoning on `elixir` tasks.

## Condition summary

| Condition | Passed | Total | Pass Rate | 95% CI | Delta vs Baseline |
|---|---:|---:|---:|---:|---:|
| baseline | 167 | 198 | 84.3% | 78.6% to 88.7% | +0.0 |
| case_with | 161 | 198 | 81.3% | 75.3% to 86.1% | -3.0 |
| cond_if | 172 | 198 | 86.9% | 81.5% to 90.9% | +2.5 |
| function_heads | 164 | 198 | 82.8% | 77.0% to 87.4% | -1.5 |

## Paired comparison vs baseline

| Condition | Baseline-Only Wins | Condition-Only Wins | McNemar p | Delta 95% CI | Cond. Pass Rate on Baseline-Pass Subset | Cond. Pass Rate on Baseline-Fail Subset |
|---|---:|---:|---:|---:|---:|---:|
| case_with | 15 | 9 | 0.307456 | -8.1 to 2.0 | 91.0% | 29.0% |
| cond_if | 10 | 15 | 0.424356 | -2.5 to 7.6 | 94.0% | 48.4% |
| function_heads | 17 | 14 | 0.7201 | -7.1 to 4.0 | 89.8% | 45.2% |

## By difficulty

| Condition | Difficulty | Passed | Total | Pass Rate |
|---|---|---:|---:|---:|
| baseline | easy | 11 | 13 | 84.6% |
| baseline | hard | 114 | 139 | 82.0% |
| baseline | medium | 42 | 46 | 91.3% |
| case_with | easy | 12 | 13 | 92.3% |
| case_with | hard | 110 | 139 | 79.1% |
| case_with | medium | 39 | 46 | 84.8% |
| cond_if | easy | 12 | 13 | 92.3% |
| cond_if | hard | 119 | 139 | 85.6% |
| cond_if | medium | 41 | 46 | 89.1% |
| function_heads | easy | 11 | 13 | 84.6% |
| function_heads | hard | 116 | 139 | 83.5% |
| function_heads | medium | 37 | 46 | 80.4% |
