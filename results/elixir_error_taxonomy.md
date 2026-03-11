# Error Taxonomy Formalization

## Definitions

- Each failed benchmark row is classified by the first non-passed stage among demo and full tests.
- Categories:
  - `compile`: `COMPILATION_ERROR`, `COMPILE_ERROR`, or `SYNTAX_ERROR`
  - `runtime`: `RUNTIME_ERROR`, `TIME_LIMIT_EXCEEDED`, or `MEMORY_LIMIT_EXCEEDED`
  - `wrong_answer`: `WRONG_ANSWER`
  - `other`: anything else
- Because this sandbox often reports failed assertions as `RUNTIME_ERROR`, runtime errors are further decomposed into assertion-driven test aborts, language exceptions, dependency issues, and timeouts.

## Elixir snapshot

- `compile`: `0` failures, `0.0%` of all rows (95% CI `0.0%` to `1.9%`), `0.0%` of Elixir failures (95% CI `0.0%` to `13.32%`).
- `runtime`: `25` failures, `12.63%` of all rows (95% CI `8.7%` to `17.97%`), `100.0%` of Elixir failures (95% CI `86.68%` to `100.0%`).
- `wrong_answer`: `0` failures, `0.0%` of all rows (95% CI `0.0%` to `1.9%`), `0.0%` of Elixir failures (95% CI `0.0%` to `13.32%`).
- `other`: `0` failures, `0.0%` of all rows (95% CI `0.0%` to `1.9%`), `0.0%` of Elixir failures (95% CI `0.0%` to `13.32%`).

## Elixir runtime subtype mix

- `assertion_test_abort`: `7` rows (`28.0%` of Elixir runtime failures).
- `language_exception`: `2` rows (`8.0%` of Elixir runtime failures).
- `other_runtime`: `16` rows (`64.0%` of Elixir runtime failures).

## Elixir vs rest

- `compile` share among failures: odds ratio `0.8557`, Fisher `p=1.0`, Holm-adjusted `p=1.0`.
- `runtime` share among failures: odds ratio `3.8694`, Fisher `p=0.41209`, Holm-adjusted `p=1.0`.
- `wrong_answer` share among failures: odds ratio `0.3855`, Fisher `p=0.628594`, Holm-adjusted `p=1.0`.
- `other` share among failures: odds ratio `70.8824`, Fisher `p=1.0`, Holm-adjusted `p=1.0`.

## Multiple-testing read

- Significant Elixir-vs-rest failure-mode differences after Holm correction: `1`.
- The surviving signal is the lower runtime-failure incidence across all rows, which mostly reflects Elixir's much higher overall pass rate rather than a uniquely different failure mix once conditioned on failure.
