# Elixir Research Suite Program

This file summarizes the first implemented pass across all Elixir hypothesis suites.

## Status

- Suites `A-G` are implemented as baseline analyses over the current benchmark artifacts plus experiment matrices for future reruns.
- Suite `H` is implemented and has the strongest current evidence.
- Suite `I` is implemented as a repo-scale scaffold with task matrix and scorecard.

## Initial read

The current evidence does not support a simple "Elixir only wins because the benchmark was easy" story.

The strongest current signals are:

1. `Suite H`: Elixir remains far above expectation after difficulty and length controls.
2. `Suite D`: Elixir is the strongest language in the current control-flow legibility proxy by a large margin.
3. `Suite F`: Elixir has one of the lowest mutability-burden profiles while still posting the highest pass rate.
4. `Active Suite A`: full docs and reference-without-examples both held at `100.0%`, but signature-only dropped to `55.6%`.
5. `Active Suite E`: tagged-tuple helper prompting held at `100.0%`, while sentinel-helper prompting dropped to `88.9%`.

The weaker or unresolved stories are:

1. `Suite A`: richer prompt-doc structure does not obviously explain Elixir's lead in the current benchmark snapshot.
2. `Suite B`: local cleanliness proxies do not place Elixir at the top.
3. `Suite C`: local style-stability proxies do not obviously explain the gap.
4. `Suite E`: the passive proxy is weak, but the active rerun is more encouraging than the passive read.
5. `Suite G`: local question/code/test alignment is not unusually high for Elixir in this benchmark snapshot.

## Recommended next active reruns

1. `Suite D`: expand to `50+` paired control-flow ablations on harder tasks near the current failure boundary
2. `Suite E`: expand to `50+` explicit tagged-contract vs implicit sentinel reruns on failure-boundary tasks
3. `Suite F`: expand to `50+` immutable-vs-stateful variants with more stateful task families
4. `Suite A`: documentation ablations remain useful as a secondary robustness check once the boundary-focused reruns land

## Section 8 follow-through

1. Build a `100`-problem human-vetted native isomorphic set with Elixir, Python, TypeScript, Go, Kotlin, and Rust.
2. Execute `Suite I` on Phoenix, Ecto, and GenServer tasks against Rails, Django, and Express analogues.
3. Add a Python `match/case` causal ablation track rather than treating pattern matching as an Elixir-only story.
4. Add token-level entropy instrumentation around branch points so uncertainty can be measured directly instead of inferred from proxy metrics.
