# Active-Suite Power Plan

This report estimates how much sample size is needed to turn directional active-suite results into higher-power follow-up studies without rerunning the full benchmark.

## Method

- Use observed discordant-pair rates from the completed paper-grade suites.
- Simulate paired Bernoulli outcomes at larger `N` while keeping the same discordance structure.
- Use exact McNemar p-values and estimate power as the share of simulations with `p < 0.05`.

## Summary

- `suite_a / minimal_docs`: observed delta `-38.38` points, discordance `47.47%`, current estimated power `1.00`, N for 80% power `198`.
- `suite_a / reference_no_examples`: observed delta `0.0` points, discordance `10.1%`, current estimated power `0.03`, N for 80% power `>2000`.
- `suite_a / signature_only`: observed delta `-41.41` points, discordance `48.48%`, current estimated power `1.00`, N for 80% power `198`.
- `suite_d / case_with`: observed delta `-3.03` points, discordance `12.12%`, current estimated power `0.17`, N for 80% power `1200`.
- `suite_d / cond_if`: observed delta `2.53` points, discordance `12.63%`, current estimated power `0.11`, N for 80% power `1600`.
- `suite_d / function_heads`: observed delta `-1.52` points, discordance `15.66%`, current estimated power `0.06`, N for 80% power `>2000`.
- `suite_e / sentinel_helpers`: observed delta `0.0` points, discordance `12.12%`, current estimated power `0.04`, N for 80% power `>2000`.
- `suite_e / tagged_tuple_helpers`: observed delta `3.03` points, discordance `12.12%`, current estimated power `0.17`, N for 80% power `1200`.
- `suite_f / explicit_state_threading`: observed delta `5.05` points, discordance `13.13%`, current estimated power `0.43`, N for 80% power `480`.
- `suite_f / immutable_pipeline`: observed delta `0.0` points, discordance `17.17%`, current estimated power `0.04`, N for 80% power `>2000`.
- `suite_f / rebinding_stepwise`: observed delta `5.56` points, discordance `14.65%`, current estimated power `0.46`, N for 80% power `480`.
