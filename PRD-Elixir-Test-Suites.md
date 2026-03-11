# PRD: Elixir Hypothesis Test Suites

## Purpose

This document converts the Elixir-overperformance theories into concrete, falsifiable benchmark suites. The goal is not to defend Elixir by rhetoric. The goal is to measure which explanations survive controlled experiments.

This document should be read together with [PRD-Elixir.md](./PRD-Elixir.md).

## Current progress

All suites now have runnable entrypoints in this repo through:

`./scripts/run_elixir_research_suite.sh all`

Current state:

1. `Suites A-G` have implemented baseline analyses plus experiment matrices for future active reruns.
2. `Suite H` has the strongest current evidence and an initial completed run.
3. `Suite I` is implemented as a repo-scale scaffold with task matrix and scorecard, but still needs target-repo execution.

Outputs:

- [suite_a_docs_quality.csv](./results/elixir_suite_a/suite_a_docs_quality.csv)
- [suite_b_corpus_quality.csv](./results/elixir_suite_b/suite_b_corpus_quality.csv)
- [suite_c_stylistic_entropy.csv](./results/elixir_suite_c/suite_c_stylistic_entropy.csv)
- [suite_d_control_flow.csv](./results/elixir_suite_d/suite_d_control_flow.csv)
- [suite_e_result_contracts.csv](./results/elixir_suite_e/suite_e_result_contracts.csv)
- [suite_f_mutability.csv](./results/elixir_suite_f/suite_f_mutability.csv)
- [suite_g_alignment.csv](./results/elixir_suite_g/suite_g_alignment.csv)
- [suite_h_artifact_controls.csv](./results/elixir_suite_h/suite_h_artifact_controls.csv)
- [suite_i_repo_scale_task_matrix.csv](./results/elixir_suite_i/suite_i_repo_scale_task_matrix.csv)

Most useful current reads:

1. [suite_h_artifact_controls.md](./results/elixir_suite_h/suite_h_artifact_controls.md)
2. [suite_d_control_flow.md](./results/elixir_suite_d/suite_d_control_flow.md)
3. [suite_f_mutability.md](./results/elixir_suite_f/suite_f_mutability.md)

Active pilot outputs:

1. [README.md](./results/elixir_active_suites/README.md)
2. [suite_a_summary.md](./results/elixir_active_suites/suite_a_summary.md)
3. [suite_d_summary.md](./results/elixir_active_suites/suite_d_summary.md)
4. [suite_e_summary.md](./results/elixir_active_suites/suite_e_summary.md)
5. [suite_f_summary.md](./results/elixir_active_suites/suite_f_summary.md)

Current active-pilot read:

1. Documentation matters sharply when reduced to signatures only: `100.0% -> 55.6%`.
2. Removing examples and notes while keeping reference structure did not hurt this pilot slice: `100.0% -> 100.0%`.
3. Tagged-tuple helper prompting matched baseline, while sentinel-helper prompting dropped slightly: `100.0% -> 88.9%`.
4. On this pilot slice, control-flow-style and mutability-style prompt constraints did not move pass rate.

## Section 8 follow-through priorities

These are the immediate follow-ons implied by the manuscript's new Limitations and Future Work section:

1. Expand active Suites `D`, `E`, and `F` to `50+` problems each, targeting tasks near the current failure boundary rather than previously-passing rows.
2. Build a `100`-problem human-vetted native isomorphic set across Elixir, Python, TypeScript, Go, Kotlin, and Rust.
3. Execute Suite `I` on Phoenix, Ecto, and GenServer tasks against Rails, Django, and Express analogues.
4. Add a Python `match/case` causal ablation track to test whether explicit pattern matching improves performance outside Elixir.
5. Extend the harness with per-token entropy instrumentation so branch-point uncertainty can be measured directly when provider APIs support it.

## Scientific standard

Each theory must be tested with:

1. A null hypothesis.
2. A measurable intervention.
3. A control group.
4. Predefined metrics.
5. A stopping rule.
6. A falsification condition.

We should assume the thesis is false until the test suite says otherwise.

## Shared benchmark rules

These rules apply to every suite below.

### Models

At minimum:

1. `gpt-5.4` medium
2. `claude-opus-4.6`
3. `claude-sonnet-4.6`
4. one strong Gemini-family or equivalent coding model

### Repetitions

1. Run each condition with at least `n = 5` independent attempts where sampling exists.
2. Fix prompts and environment across conditions except for the variable under test.
3. Use the same scoring harness and language runtime versions.

### Core metrics

1. pass@1
2. compile success rate
3. warning-free success rate
4. first-pass syntax error rate
5. median tokens to first passing solution
6. median wall-clock time to first passing solution
7. repair-iteration count

### Evidence threshold

Treat an effect as meaningful only if:

1. it appears in at least two model families, and
2. the direction is stable across repeated runs, and
3. the effect size is large enough to matter operationally, not just statistically

## Theory catalog

We want to test at least these theories:

1. Elixir libraries tend to have better docs.
2. Elixir libraries tend to have higher code quality.
3. Elixir code has lower stylistic entropy because formatter and conventions are stronger.
4. Elixir exposes control flow more explicitly through pattern matching and guards.
5. Elixir uses more explicit result contracts, especially tagged tuples.
6. Elixir reduces hidden mutable-state reasoning.
7. Elixir ecosystem examples align docs, tests, and implementation better than peer languages.
8. Elixir's win is actually a benchmark artifact, not a language-design effect.
9. Elixir's win is due mostly to corpus cleanliness rather than language semantics.

## Suite A: Documentation quality

### Theory

Elixir performs well because its libraries are documented more consistently, more concretely, and in more model-usable forms than peer languages.

### Null hypothesis

Documentation quality has no meaningful effect on model success once task semantics are fixed.

### Experimental design

Build parallel task sets for the same APIs under four documentation conditions:

1. `No docs`
2. `Minimal signature-only docs`
3. `Reference docs without examples`
4. `Reference docs with examples and doctests`

Use APIs from:

1. Elixir / Phoenix / Ecto
2. Python / FastAPI / SQLAlchemy
3. TypeScript / Effect / Prisma or TypeORM
4. Ruby / Rails / ActiveRecord

### Inputs

For each task:

1. API description
2. target tests
3. code context
4. one documentation condition

### Metrics

1. pass@1 delta by documentation condition
2. compile success delta
3. number of incorrect API calls
4. hallucinated function usage rate
5. fix count caused by misunderstanding docs

### Falsification

If richer docs do not disproportionately help Elixir relative to peers, then "Elixir wins because docs are better" is overstated.

### Deliverable

`suite_a_docs_quality.csv`

## Suite B: Code quality / corpus cleanliness

### Theory

Elixir performs well because public Elixir code is cleaner, more idiomatic, and less noisy than the code corpora available for peer languages.

### Null hypothesis

Corpus cleanliness does not explain Elixir's advantage.

### Experimental design

Construct matched corpora for several languages and score them for:

1. formatter compliance
2. lint violations per KLOC
3. test density
4. docs density
5. type/spec density where applicable
6. project-structure consistency
7. duplication / boilerplate rate

Then create two task sets:

1. `clean corpus context`
2. `degraded corpus context`

The degraded version intentionally injects:

1. inconsistent naming
2. style drift
3. unused code
4. weaker docs
5. irregular folder layout

### Metrics

1. performance delta between clean and degraded contexts
2. delta by language
3. correlation between corpus-quality score and model success

### Falsification

If Elixir does not benefit more from clean corpora, then corpus cleanliness alone is not the main explanation.

### Deliverable

`suite_b_corpus_quality.csv`

## Suite C: Stylistic entropy and formatter strength

### Theory

Elixir wins because the formatter and community conventions collapse many syntactic degrees of freedom, making continuation easier for models.

### Null hypothesis

Reducing stylistic entropy has no material effect on model success.

### Experimental design

Take the same solved tasks and present the surrounding context in:

1. formatter-normalized form
2. human-style-divergent form
3. deliberately noisy form

Apply this to Elixir and to comparison languages with weaker formatting enforcement.

### Metrics

1. pass@1 by style condition
2. syntax error rate
3. wrong-name / wrong-arity errors
4. token efficiency

### Falsification

If normalized Elixir does not outperform noisy Elixir by a meaningful margin, stylistic entropy is probably not a leading explanation.

### Deliverable

`suite_c_stylistic_entropy.csv`

## Suite D: Pattern matching and explicit control flow

### Theory

Elixir wins because pattern matching makes intent legible to LLMs in a way nested imperative branching does not.

### Null hypothesis

Pattern matching and explicit dispatch do not materially improve model correctness.

### Experimental design

Create paired task variants:

1. function-head pattern matching version
2. `case` / `with` version
3. equivalent imperative branching version

Translate the same semantics into multiple languages where possible.

### Metrics

1. pass@1 by control-flow style
2. logical-bug rate
3. missing-branch rate
4. dead-path / impossible-state error rate

### Falsification

If the pattern-matching variants do not outperform imperative variants, this theory weakens substantially.

### Deliverable

`suite_d_control_flow.csv`

## Suite E: Result contracts and tagged tuples

### Theory

Elixir wins because standard result shapes like `{:ok, value}` and `{:error, reason}` reduce ambiguity and improve predictability.

### Null hypothesis

Explicit result contracts do not materially improve model success.

### Experimental design

Create parallel tasks under three contract styles:

1. tagged tuples
2. exception-driven flow
3. ad hoc maps / structs / objects with optional fields

Run this both inside Elixir and in peer languages that can emulate the same contract styles.

### Metrics

1. contract-shape mismatch rate
2. pass@1
3. error-handling branch correctness
4. malformed return rate

### Falsification

If tagged contracts do not outperform ad hoc or exception-heavy variants, then this mechanism is weaker than expected.

### Deliverable

`suite_e_result_contracts.csv`

## Suite F: Hidden state and mutability burden

### Theory

Elixir wins because immutable defaults reduce the amount of hidden state a model must simulate.

### Null hypothesis

Mutability burden does not meaningfully affect success.

### Experimental design

Build matched tasks with:

1. immutable pipeline-style updates
2. mutable shared-state updates
3. mixed style with partial mutation and side effects

Focus on:

1. game state
2. sessions
3. counters and aggregations
4. workflow state machines

### Metrics

1. stale-state bug rate
2. incorrect update-order rate
3. pass@1
4. repair count

### Falsification

If immutable variants do not materially reduce state bugs, then this theory is overstated.

### Deliverable

`suite_f_mutability.csv`

## Suite G: Documentation-test-code alignment

### Theory

Elixir wins because docs, examples, doctests, and tests are unusually aligned, giving models more semantically coherent supervision.

### Null hypothesis

Alignment between docs, examples, and tests does not materially affect success.

### Experimental design

For each task family, build three contexts:

1. aligned docs and tests
2. partial alignment
3. intentionally misaligned examples

Measure how often models follow examples versus tests versus type/shape cues.

### Metrics

1. pass@1
2. example-following error rate
3. test-contradiction error rate
4. hallucinated API behavior rate

### Falsification

If aligned and misaligned contexts perform similarly, this theory is weak.

### Deliverable

`suite_g_alignment.csv`

## Suite H: Benchmark artifact controls

### Theory

Elixir's current lead is mostly an artifact of benchmark composition rather than a real cross-language advantage.

### Null hypothesis

Elixir's advantage survives benchmark normalization.

### Experimental design

Apply all of the following controls:

1. difficulty normalization
2. task-family balancing
3. human-vetted translation parity
4. equal test strictness
5. equal library dependence
6. equal prompt budget and repair budget

### Metrics

1. pass@1 before normalization
2. pass@1 after normalization
3. rank change by language

### Falsification

If Elixir collapses to the pack after normalization, most strong causal claims must be downgraded.

### Deliverable

`suite_h_artifact_controls.csv`

## Suite I: Repo-scale realism

### Theory

Elixir's advantage survives outside snippet benchmarks and extends into practical framework work.

### Null hypothesis

Elixir's advantage disappears on realistic repo tasks.

### Experimental design

Create edit/task suites across:

1. Phoenix routes, controllers, LiveView components
2. Ecto schemas, changesets, queries, migrations
3. GenServer and supervision-tree behavior
4. Plug pipelines
5. Oban or Broadway-style jobs
6. umbrella-app structure tasks

Comparison languages must get similarly realistic framework tasks.

### Metrics

1. task completion rate
2. edit correctness
3. test pass rate
4. regression rate
5. time-to-fix

### Falsification

If Elixir loses its advantage on repo-scale tasks, then the main story is snippet-level ergonomics, not end-to-end engineering advantage.

### Deliverable

`suite_i_repo_scale.csv`

## Instrumentation requirements

We should add or standardize the following measurements in the benchmark harness:

1. compile status
2. warning count
3. repair iteration count
4. exact failure taxonomy
5. prompt tokens
6. output tokens
7. latency
8. docs condition id
9. corpus condition id
10. feature-ablation condition id
11. per-token logprob / entropy traces where provider support exists

## Failure taxonomy

Every suite should classify failures into:

1. syntax error
2. wrong return shape
3. wrong API call
4. wrong control-flow branch
5. stale state / mutation error
6. docs misunderstanding
7. hallucinated library behavior
8. test-time runtime crash
9. timeout / nontermination

## Prioritized execution order

Run in this order:

1. Suite H: benchmark artifact controls
2. Suite D: pattern matching and explicit control flow
3. Suite E: result contracts and tagged tuples
4. Suite A: documentation quality
5. Suite C: stylistic entropy
6. Suite F: hidden state and mutability burden
7. Suite G: doc-test-code alignment
8. Suite B: corpus cleanliness
9. Suite I: repo-scale realism

Reason:

We should first rule out "the benchmark is lying," then identify the strongest language-design explanations, then test ecosystem/documentation explanations, and finally move into expensive repo-scale evals.

## Decision criteria

We can say "Elixir is genuinely model-friendly for reasons X and Y" only if:

1. benchmark artifact controls do not erase the lead
2. at least one language-design suite shows a strong causal effect
3. at least one ecosystem/doc-quality suite also shows a measurable effect
4. the effect survives more than one model family

## Immediate next step

Implement Suite H first.

If we do not clear the artifact question, every stronger Elixir claim remains vulnerable.
