# suite_a Active Ablation Summary

Active ablation rerun using `gpt-5.4` / medium reasoning on `elixir` tasks.

## Condition summary

| Condition | Passed | Total | Pass Rate | 95% CI | Delta vs Baseline |
|---|---:|---:|---:|---:|---:|
| full_docs | 167 | 198 | 84.3% | 78.6% to 88.7% | +0.0 |
| minimal_docs | 91 | 198 | 46.0% | 39.2% to 52.9% | -38.4 |
| reference_no_examples | 167 | 198 | 84.3% | 78.6% to 88.7% | +0.0 |
| signature_only | 85 | 198 | 42.9% | 36.2% to 49.9% | -41.4 |

## Paired comparison vs baseline

| Condition | Baseline-Only Wins | Condition-Only Wins | McNemar p | Delta 95% CI | Cond. Pass Rate on Baseline-Pass Subset | Cond. Pass Rate on Baseline-Fail Subset |
|---|---:|---:|---:|---:|---:|---:|
| minimal_docs | 85 | 9 | 0.0 | -46.0 to -30.3 | 49.1% | 29.0% |
| reference_no_examples | 10 | 10 | 1.0 | -4.5 to 4.5 | 94.0% | 32.3% |
| signature_only | 89 | 7 | 0.0 | -49.0 to -33.8 | 46.7% | 22.6% |

## By difficulty

| Condition | Difficulty | Passed | Total | Pass Rate |
|---|---|---:|---:|---:|
| full_docs | easy | 12 | 13 | 92.3% |
| full_docs | hard | 117 | 139 | 84.2% |
| full_docs | medium | 38 | 46 | 82.6% |
| minimal_docs | easy | 9 | 13 | 69.2% |
| minimal_docs | hard | 55 | 139 | 39.6% |
| minimal_docs | medium | 27 | 46 | 58.7% |
| reference_no_examples | easy | 13 | 13 | 100.0% |
| reference_no_examples | hard | 113 | 139 | 81.3% |
| reference_no_examples | medium | 41 | 46 | 89.1% |
| signature_only | easy | 6 | 13 | 46.2% |
| signature_only | hard | 54 | 139 | 38.8% |
| signature_only | medium | 25 | 46 | 54.3% |
