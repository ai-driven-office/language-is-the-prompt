# Elixir Paper-Grade Active Study

## Executive summary

- We replicated Elixir's strong benchmark result in the corrected local run: `87.4%` pass@1.
- That lead survives benchmark-artifact controls: `+40.4` points vs the difficulty-only expectation and `+42.7` points vs the difficulty+question-length expectation.
- The strongest current causal evidence points to documentation richness and explicit public contracts.
- Pattern matching and low hidden-state burden remain plausible secondary contributors, not yet the primary proved causes.

## Method

- Model: `gpt-5.4` with medium reasoning
- Language under study: `elixir`
- Active documentation task count: `198` source tasks
- Active contract task count: `198` source tasks
- Scoring: native Elixir execution through the corrected local scorer
- Analysis: paired condition comparisons against the same task set

## Benchmark replication evidence

- Corrected Elixir pass rate: `87.4%`
- Expected pass rate under difficulty-only control: `47.0%`
- Expected pass rate under difficulty+question-length control: `44.6%`
- Delta vs difficulty-only expectation: `40.4` points
- Delta vs difficulty+question-length expectation: `42.7` points
- Delta vs difficulty+full-test-length expectation: `36.8` points

## Documentation Quality

| Condition | Pass Rate | 95% CI | Delta vs Baseline | Baseline-Only Wins | Condition-Only Wins | McNemar p | Delta 95% CI | Cond. Pass Rate on Baseline-Pass Subset |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| full_docs | 84.3% | 78.6% to 88.7% | +0.0 | 0 | 0 | 1.0 | 0.0 to 0.0 | 100.0% |
| minimal_docs | 46.0% | 39.2% to 52.9% | -38.4 | 85 | 9 | 0.0 | -46.0 to -30.3 | 49.1% |
| reference_no_examples | 84.3% | 78.6% to 88.7% | 0.0 | 10 | 10 | 1.0 | -4.5 to 4.5 | 94.0% |
| signature_only | 42.9% | 36.2% to 49.9% | -41.4 | 89 | 7 | 0.0 | -49.0 to -33.8 | 46.7% |

Read:

- This suite directly tests whether documentation richness is carrying Elixir.
- The strongest negative intervention is the one that collapses the prompt down to signatures only.

## Pattern Matching and Control Flow

| Condition | Pass Rate | 95% CI | Delta vs Baseline | Baseline-Only Wins | Condition-Only Wins | McNemar p | Delta 95% CI | Cond. Pass Rate on Baseline-Pass Subset |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 84.3% | 78.6% to 88.7% | +0.0 | 0 | 0 | 1.0 | 0.0 to 0.0 | 100.0% |
| case_with | 81.3% | 75.3% to 86.1% | -3.0 | 15 | 9 | 0.307456 | -8.1 to 2.0 | 91.0% |
| cond_if | 86.9% | 81.5% to 90.9% | 2.5 | 10 | 15 | 0.424356 | -2.5 to 7.6 | 94.0% |
| function_heads | 82.8% | 77.0% to 87.4% | -1.5 | 17 | 14 | 0.7201 | -7.1 to 4.0 | 89.8% |

Read:

- This suite tests whether forcing alternative control-flow surface forms changes outcomes materially.
- A flat result here argues against a simple 'pattern matching alone explains everything' story.

## Result Contracts

| Condition | Pass Rate | 95% CI | Delta vs Baseline | Baseline-Only Wins | Condition-Only Wins | McNemar p | Delta 95% CI | Cond. Pass Rate on Baseline-Pass Subset |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 83.8% | 78.1% to 88.3% | +0.0 | 0 | 0 | 1.0 | 0.0 to 0.0 | 100.0% |
| sentinel_helpers | 83.8% | 78.1% to 88.3% | 0.0 | 12 | 12 | 1.0 | -5.1 to 5.1 | 92.8% |
| tagged_tuple_helpers | 86.9% | 81.5% to 90.9% | 3.0 | 9 | 15 | 0.307456 | -2.0 to 8.1 | 94.6% |

Read:

- This suite tests whether explicit tagged-contract prompting helps relative to weaker implicit sentinel contracts.
- If tagged-tuple prompting stays competitive while sentinel prompting degrades, that strengthens the explicit-contract hypothesis.

## Mutability and State Style

| Condition | Pass Rate | 95% CI | Delta vs Baseline | Baseline-Only Wins | Condition-Only Wins | McNemar p | Delta 95% CI | Cond. Pass Rate on Baseline-Pass Subset |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 81.8% | 75.9% to 86.6% | +0.0 | 0 | 0 | 1.0 | 0.0 to 0.0 | 100.0% |
| explicit_state_threading | 86.9% | 81.5% to 90.9% | 5.1 | 8 | 18 | 0.075519 | 0.0 to 10.6 | 95.1% |
| immutable_pipeline | 81.8% | 75.9% to 86.6% | 0.0 | 17 | 17 | 1.0 | -5.6 to 6.1 | 89.5% |
| rebinding_stepwise | 87.4% | 82.0% to 91.3% | 5.6 | 9 | 20 | 0.061428 | 0.5 to 11.1 | 94.4% |

Read:

- This suite tests whether forcing more explicit or more stepwise state style moves the needle materially.
- A flat result argues that low mutability burden may matter more as a language property than as a prompt-level style intervention.

## Claim boundary

- These active suites can show which interventions materially change outcomes on matched Elixir tasks.
- They cannot by themselves prove what the entire public Elixir corpus taught the model during pretraining.
- The strongest defensible statement today is that explicit docs and explicit contracts are the best-supported explanations for Elixir's benchmark advantage in this setup.

## What other language designers should copy

- Normalize result-shape conventions instead of encouraging ad hoc sentinel returns.
- Make reference docs concrete enough that the API contract remains legible under compression.
- Keep docs, tests, and public behavior tightly aligned.
- Reduce opportunities for hidden mutable state and ambiguous control flow.
