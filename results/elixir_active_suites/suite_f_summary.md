# suite_f Active Ablation Summary

Active ablation rerun using `gpt-5.4` / medium reasoning on `elixir` tasks.

## Condition summary

| Condition | Passed | Total | Pass Rate | 95% CI | Delta vs Baseline |
|---|---:|---:|---:|---:|---:|
| baseline | 162 | 198 | 81.8% | 75.9% to 86.6% | +0.0 |
| explicit_state_threading | 172 | 198 | 86.9% | 81.5% to 90.9% | +5.1 |
| immutable_pipeline | 162 | 198 | 81.8% | 75.9% to 86.6% | +0.0 |
| rebinding_stepwise | 173 | 198 | 87.4% | 82.0% to 91.3% | +5.6 |

## Paired comparison vs baseline

| Condition | Baseline-Only Wins | Condition-Only Wins | McNemar p | Delta 95% CI | Cond. Pass Rate on Baseline-Pass Subset | Cond. Pass Rate on Baseline-Fail Subset |
|---|---:|---:|---:|---:|---:|---:|
| explicit_state_threading | 8 | 18 | 0.075519 | 0.0 to 10.6 | 95.1% | 50.0% |
| immutable_pipeline | 17 | 17 | 1.0 | -5.6 to 6.1 | 89.5% | 47.2% |
| rebinding_stepwise | 9 | 20 | 0.061428 | 0.5 to 11.1 | 94.4% | 55.6% |

## By difficulty

| Condition | Difficulty | Passed | Total | Pass Rate |
|---|---|---:|---:|---:|
| baseline | easy | 12 | 13 | 92.3% |
| baseline | hard | 111 | 139 | 79.9% |
| baseline | medium | 39 | 46 | 84.8% |
| explicit_state_threading | easy | 11 | 13 | 84.6% |
| explicit_state_threading | hard | 119 | 139 | 85.6% |
| explicit_state_threading | medium | 42 | 46 | 91.3% |
| immutable_pipeline | easy | 11 | 13 | 84.6% |
| immutable_pipeline | hard | 113 | 139 | 81.3% |
| immutable_pipeline | medium | 38 | 46 | 82.6% |
| rebinding_stepwise | easy | 12 | 13 | 92.3% |
| rebinding_stepwise | hard | 117 | 139 | 84.2% |
| rebinding_stepwise | medium | 44 | 46 | 95.7% |
