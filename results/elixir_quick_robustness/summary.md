# Quick Robustness Checks

These analyses reuse existing matched-study outputs. No new model generations are required.

## Explicit-Task Panel

- Comparison: `rich_contract_examples_vs_baseline_compact`
- Overall matched mean delta: `0.104`
- Task-cluster bootstrap 95% CI: `-0.062` to `+0.292`
- Leave-one-task-out delta range: `+0.044` to `+0.156`
- Leave-one-language-out delta range: `+0.031` to `+0.156`

Interpretation: the examples effect remains directionally positive, but the bootstrap interval crosses zero and the leave-one-language-out deltas shrink substantially. This remains a low-power, non-decisive signal.

## Explicit-Task Factorial

| Factor | Overall delta | Task-bootstrap 95% CI | Leave-one-task-out range | Leave-one-language-out range |
| --- | ---: | ---: | ---: | ---: |
| `docs_rich` | `+0.047` | `-0.021` to `+0.120` | `+0.028` to `+0.061` | `+0.039` to `+0.055` |
| `examples` | `+0.203` | `+0.089` to `+0.323` | `+0.172` to `+0.228` | `+0.164` to `+0.250` |
| `contracts_explicit` | `+0.359` | `+0.198` to `+0.531` | `+0.317` to `+0.394` | `+0.305` to `+0.461` |
| `state_guidance` | `-0.026` | `-0.094` to `+0.031` | `-0.033` to `-0.006` | `-0.039` to `-0.016` |

Interpretation: the explicit-contract effect is the most stable same-task result in the current paper. It remains positive under every single-task omission and every single-language omission, and its task-cluster bootstrap interval stays above zero. The examples effect is also consistently positive under these robustness checks, but it still falls short of Holm-corrected significance in the primary paired test.
