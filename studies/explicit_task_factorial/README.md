# Explicit Task Factorial Study

This is a small controlled follow-up to the original explicit-task panel.

## Goal

Estimate the relative contribution of four prompt-side explicitness factors on the
same 16-task, 3-language matched panel:

- documentation richness
- examples
- explicit result contracts
- explicit state-flow guidance

## Design

- 16 tasks
- 3 languages: `elixir`, `python`, `typescript`
- 8 prompt conditions
- total rows: `16 x 3 x 8 = 384`

This is a regular `2^(4-1)` fractional-factorial design with generator:

- `state_guidance = docs_rich XOR examples XOR contracts_explicit`

That keeps the study small enough to run locally while still supporting clean
main-effect estimation.

## Outputs

- prompt records under `studies/explicit_task_factorial/generated/`
- benchmark rows under `data/explicit_task_factorial/`
- scored outputs under `outputs/explicit_task_factorial/`
- analysis under `results/explicit_task_factorial/`

## Main analysis targets

- condition-level pass rates
- matched main effects for each factor overall and by language
- aliased two-factor interaction contrasts
- a concise markdown summary suitable for the paper
