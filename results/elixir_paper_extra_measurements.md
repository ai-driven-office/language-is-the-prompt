# Extra Measurements For The Elixir Paper

## High-signal additions

- The strongest active effect in the completed study is still documentation structure removal: `signature_only` in `suite_a` moves pass rate by `-41.4` points.
- The strongest positive active effect is `rebinding_stepwise` in `suite_f` at `5.6` points, but those gains are much smaller than the docs losses.
- On hard Elixir tasks, `signature_only` drops to `38.8%` from `84.2%` full-docs baseline, with McNemar `p=0.0`.
- On hard Elixir tasks, `minimal_docs` drops to `39.6%` from `84.2%`, with McNemar `p=0.0`.

## Cross-language proxy read

- Cross-language documentation proxy is only a weak-to-moderate correlate of pass rate: Spearman `0.396`, Pearson `0.228`.
- Control-flow proxy is directionally strongest in Pearson space: Spearman `0.197`, Pearson `0.564`.
- Mutability burden is only moderately negative: Spearman `-0.24`, Pearson `-0.207`.
- The three-part explicitness composite correlates with pass rate across all 20 languages at Pearson `0.391`, but collapses without Elixir to Pearson `-0.034`.
- Leaving Elixir out moves control-flow Pearson from `0.564` to `0.074`, showing how much the current cross-language control-flow result depends on the Elixir outlier.
- Leaving Elixir out moves documentation Pearson from `0.228` to `0.398`, which is much less dramatic.

## Multiple-testing control

- After Holm correction across all active interventions, `2` contrasts remain significant at 0.05.
- The surviving signals are the large documentation-structure degradations, not the smaller control-flow or contract perturbations.

## What the draft should tighten

- Do not keep the old claim that documentation is not explanatory in any important sense. The full paper-scale Suite A now shows that rich task framing is a major within-language driver.
- Keep the narrower claim instead: cross-language docs-quality proxies do not explain why Elixir beats every other language, because Elixir is not top-ranked on those proxies.
- Soften the causal claims for pattern matching and tagged tuples. The full active reruns are much weaker there than the earlier pilot suggested.
- Reframe the state-style claim from 'immutability is the direct cause' to 'explicit state transitions matter more than hidden mutable state.'

## Recommended thesis update

Elixir's advantage is best framed as an explicitness-and-legibility effect with two tiers:

1. Strong evidence: rich documentation structure and explicit task framing make correct continuations much easier to predict.
2. Directional but weaker evidence: control-flow explicitness, result-shape conventions, and explicit state flow likely help, but the full active ablations do not justify treating them as equally established causal drivers yet.

