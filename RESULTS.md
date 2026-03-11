# AutoCodeBenchmark Extension Results

This branch packages a local benchmarking extension of AutoCodeBenchmark with:

- corrected host-native scoring for languages that were broken in the stock local flow
- extension translation templates for `gleam`, `lean4`, and `typescript_effect`
- extension benchmarking scripts for translated benchmark slices
- compact result summaries for a single OpenAI run configuration

## Run configuration

- Model: `gpt-5.4`
- Reasoning: `medium`
- Solve verbosity: `low`
- Main benchmark: `ACB-Full` (`3920` problems, `20` original languages)
- Extension slices: Python-source translated subsets (`196` source rows each)

## Main benchmark

These are the corrected local results for the original `20`-language benchmark after fixing the broken `elixir` and `racket` local runtime paths.

- Overall: `2088 / 3920 = 53.3%`

| Language | Passed | Total | Pass Rate |
|---|---:|---:|---:|
| cpp | 93 | 186 | 50.0% |
| csharp | 144 | 199 | 72.4% |
| dart | 113 | 200 | 56.5% |
| elixir | 173 | 198 | 87.4% |
| go | 82 | 191 | 42.9% |
| java | 96 | 188 | 51.1% |
| javascript | 79 | 184 | 42.9% |
| julia | 114 | 200 | 57.0% |
| kotlin | 153 | 200 | 76.5% |
| perl | 89 | 200 | 44.5% |
| php | 71 | 199 | 35.7% |
| python | 86 | 196 | 43.9% |
| r | 108 | 198 | 54.5% |
| racket | 100 | 196 | 51.0% |
| ruby | 126 | 200 | 63.0% |
| rust | 80 | 199 | 40.2% |
| scala | 101 | 199 | 50.8% |
| shell | 95 | 188 | 50.5% |
| swift | 87 | 200 | 43.5% |
| typescript | 98 | 199 | 49.2% |

## Extension slices

These are not part of the original `ACB-Full` leaderboard. They are forked extension slices built from the Python-source portion of the benchmark.

### Validated extension slices

For `gleam` and `lean4`, the raw translated benchmark rows were noisy enough that reporting naive end-to-end scores would have been misleading. Those two languages were rerun with:

- stricter translation templates
- canonical validation of translated benchmark rows before solving
- solve scoring only on the validated subset

| Language | Source Rows | Validated Rows | Validated Coverage | Passed | Pass Rate on Validated Rows | Pass Rate over 196 |
|---|---:|---:|---:|---:|---:|---:|
| gleam | 196 | 122 | 62.2% | 25 | 20.5% | 12.8% |
| lean4 | 196 | 125 | 63.8% | 36 | 28.8% | 18.4% |

### Preliminary extension slice

`typescript_effect` was run before the canonical-validation gate was added to the extension pipeline. The score below is still useful, but it is less rigorously normalized than the `gleam` and `lean4` reruns.

| Language | Source Rows | Passed | Pass Rate | Notes |
|---|---:|---:|---:|---|
| typescript_effect | 196 | 105 | 53.6% | Legacy extension run without canonical-validation filter |

## Files

Compact summaries:

- [results/acb_full_openai_gpt_5_4_medium.csv](/Users/a12907/Documents/GitHub/AutoCodeBenchmark/results/acb_full_openai_gpt_5_4_medium.csv)
- [results/extension_slices_openai_gpt_5_4_medium.csv](/Users/a12907/Documents/GitHub/AutoCodeBenchmark/results/extension_slices_openai_gpt_5_4_medium.csv)
- [results/summary.json](/Users/a12907/Documents/GitHub/AutoCodeBenchmark/results/summary.json)

Primary raw result artifacts used for the summaries:

- [outputs/openai-5-4-medium-adaptive.native-fixed.exec.jsonl](/Users/a12907/Documents/GitHub/AutoCodeBenchmark/outputs/openai-5-4-medium-adaptive.native-fixed.exec.jsonl)
- [outputs/extensions/gleam-from-python-v2.benchmark.valid.jsonl](/Users/a12907/Documents/GitHub/AutoCodeBenchmark/outputs/extensions/gleam-from-python-v2.benchmark.valid.jsonl)
- [outputs/extensions/gleam-from-python-v2.solutions.exec.jsonl](/Users/a12907/Documents/GitHub/AutoCodeBenchmark/outputs/extensions/gleam-from-python-v2.solutions.exec.jsonl)
- [outputs/extensions/lean4-from-python-v2.benchmark.valid.jsonl](/Users/a12907/Documents/GitHub/AutoCodeBenchmark/outputs/extensions/lean4-from-python-v2.benchmark.valid.jsonl)
- [outputs/extensions/lean4-from-python-v2.solutions.exec.jsonl](/Users/a12907/Documents/GitHub/AutoCodeBenchmark/outputs/extensions/lean4-from-python-v2.solutions.exec.jsonl)
- [outputs/extensions/typescript-effect-from-python.solutions.exec.jsonl](/Users/a12907/Documents/GitHub/AutoCodeBenchmark/outputs/extensions/typescript-effect-from-python.solutions.exec.jsonl)

## Notes

- The earlier `gleam` and `lean4` scores (`0.5%` and `1.0%`) should be treated as invalid. They were dominated by broken translated benchmark rows.
- The corrected `elixir` and `racket` main-benchmark results replaced a broken local runtime path, not a model regression.
- Large raw outputs and logs remain ignored by git in this branch to keep the repo reviewable.
