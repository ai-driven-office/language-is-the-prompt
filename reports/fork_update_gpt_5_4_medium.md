# Fork Update Report: GPT-5.4 Medium and Extension Languages

Date: March 11, 2026

## Scope

This fork extends the upstream AutoCodeBenchmark repository with:

- a locally reproduced `ACB-Full` evaluation for `gpt-5.4` with `medium` reasoning
- corrected host-native local scoring for runtime paths that produced invalid zeros in the stock local setup
- translated extension benchmark slices for `gleam`, `lean4`, and `typescript_effect`
- canonical-validation of translated benchmark rows before solving for `gleam` and `lean4`

## Benchmark assets

The main benchmark result in this fork uses the latest benchmark assets available in this repository snapshot on March 11, 2026:

- `ACB-Full`: `3920` rows across `20` original languages

The extension language results are fork-specific translated slices built from the Python-source subset:

- `gleam`: `196` source rows
- `lean4`: `196` source rows
- `typescript_effect`: `196` source rows

## Main benchmark result

- Model: `gpt-5.4`
- Reasoning: `medium`
- Overall: `2088 / 3920 = 53.3%`

Top-performing languages in this run:

| Language | Passed | Total | Pass Rate |
|---|---:|---:|---:|
| elixir | 173 | 198 | 87.4% |
| kotlin | 153 | 200 | 76.5% |
| csharp | 144 | 199 | 72.4% |
| ruby | 126 | 200 | 63.0% |
| julia | 114 | 200 | 57.0% |

## Fork-only extension languages

### Validated translated slices

These are the meaningful corrected results for the new extension languages. The earlier near-zero Gleam and Lean4 numbers were invalid because the translated benchmark rows themselves were broken.

| Language | Validated Rows | Passed | Pass Rate on Validated Rows | Coverage of 196 Source Rows |
|---|---:|---:|---:|---:|
| gleam | 122 | 25 | 20.5% | 62.2% |
| lean4 | 125 | 36 | 28.8% | 63.8% |

### Preliminary extension slice

| Language | Source Rows | Passed | Pass Rate | Note |
|---|---:|---:|---:|---|
| typescript_effect | 196 | 105 | 53.6% | Legacy extension run prior to canonical-validation gating |

## What changed in the fork

### Evaluation/runtime fixes

- Added host-native scoring paths in `call_sandbox.py` for:
  - `elixir`
  - `racket`
  - `gleam`
  - `lean4`
  - `typescript_effect`

### Extension-language support

- Added translation templates for:
  - `gleam`
  - `lean4`
  - `typescript_effect`
- Added extension benchmarking scripts:
  - translated benchmark generation
  - translated benchmark extraction
  - repair prompts for invalid translated rows
  - benchmark row merging
  - validated-subset filtering

### Reporting artifacts

- Added compact CSV and JSON summaries under `results/`
- Added fork-specific SVG figures under `figures/`
- Added README updates summarizing the new run and extension slices

## Interpretation notes

- The corrected `elixir` and `racket` main-benchmark values fix a local runtime problem. They should replace the earlier broken local zeros.
- `gleam` and `lean4` are reported on validated translated subsets, because naive reporting over broken translated rows would understate model performance and misrepresent the benchmark.
- `typescript_effect` should be treated as a useful but earlier-stage extension result until it is rerun under the same canonical-validation gate.
