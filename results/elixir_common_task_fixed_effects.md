# Common-Task Fixed-Effects Analysis

## Method

- Because ACB-Full does not expose a shared task id across languages, this analysis uses a conservative recurring-task subset.
- A task cluster is included only when multiple languages share the same exact normalized first-line title and each language appears at most once in that cluster.
- This yields `28` high-confidence recurring-task clusters.
- The task-fixed effect estimator is the within-cluster residual: `y_(l,c) - mean_c(y)`.
- For Elixir-specific comparison, we compute `Delta_c = y_(elixir,c) - mean_(others in c)(y)` and bootstrap over clusters.

## Key result

- Elixir appears in `7` recurring-task clusters.
- Mean within-cluster Elixir advantage is `0.2143` with bootstrap CI `-0.4286` to `0.7857`.
- Sign test over non-tied clusters: `p=0.6875`.

## Interpretation

- This is a low-coverage sanity check, not a replacement for a benchmark with explicit shared task ids.
- It is still useful because it removes some of the benchmark-composition ambiguity on the small subset where recurring tasks can be matched exactly by title.
