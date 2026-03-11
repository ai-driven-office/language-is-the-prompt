# Suite H: Benchmark Artifact Controls

- Overall pass rate in this scored run: `53.3%` across `3920` rows and `20` languages.
- Elixir observed pass rate: `87.4%`.
- Elixir delta vs difficulty-only expectation: `+40.4` points.
- Elixir delta vs difficulty+question-length expectation: `+42.7` points.
- Elixir delta vs difficulty+full-test-length expectation: `+36.8` points.

## Initial read

Elixir does not look like an obvious easy-slice artifact in the current run. It remains strongly above its leave-one-language-out expected rate even after controlling for difficulty and a crude brevity proxy.

## Top observed languages

| Language | Observed | Delta vs Difficulty | Delta vs Difficulty+Question | Delta vs Difficulty+Full Test | Hard % | Median Question | Runtime Errors |
|---|---:|---:|---:|---:|---:|---:|---:|
| elixir | 87.4% | +40.4 | +42.7 | +36.8 | 70.2% | 1432 | 25 |
| kotlin | 76.5% | +16.0 | +15.8 | +17.5 | 43.5% | 2356 | 47 |
| csharp | 72.4% | +12.5 | +10.8 | +17.3 | 46.2% | 3058 | 45 |
| ruby | 63.0% | +6.4 | +7.3 | +5.8 | 54.0% | 1797 | 70 |
| julia | 57.0% | +4.4 | +6.2 | +0.5 | 62.5% | 1581 | 85 |
| dart | 56.5% | +6.4 | +5.6 | +7.0 | 68.0% | 2565 | 87 |
| r | 54.5% | +2.5 | +3.9 | +1.2 | 64.1% | 1646 | 90 |
| java | 51.1% | -5.0 | -10.1 | -1.6 | 56.4% | 3831 | 73 |

## Top adjusted by difficulty + question length

| Language | Observed | Expected | Delta |
|---|---:|---:|---:|
| elixir | 87.4% | 44.6% | +42.7 |
| kotlin | 76.5% | 60.7% | +15.8 |
| csharp | 72.4% | 61.5% | +10.8 |
| ruby | 63.0% | 55.7% | +7.3 |
| julia | 57.0% | 50.8% | +6.2 |
| dart | 56.5% | 50.9% | +5.6 |
| r | 54.5% | 50.7% | +3.9 |
| typescript | 49.2% | 46.8% | +2.5 |

## Hard-bucket leaders

| Language | Passed | Total | Pass Rate |
|---|---:|---:|---:|
| elixir | 120 | 139 | 86.3% |
| csharp | 50 | 92 | 54.3% |
| kotlin | 44 | 87 | 50.6% |
| dart | 64 | 136 | 47.1% |
| ruby | 49 | 108 | 45.4% |
| racket | 46 | 111 | 41.4% |
| r | 50 | 127 | 39.4% |
| julia | 48 | 125 | 38.4% |

## Caveat

Elixir rows appear shorter than many peer languages by median question and test length. That remains a live confound. The artifact-control result is therefore directional, not final proof.

## Files

- `suite_h_artifact_controls.csv`: per-language artifact-control summary
- `suite_h_artifact_controls_by_difficulty.csv`: per-language difficulty breakdown
- `suite_h_artifact_controls.json`: machine-readable output
