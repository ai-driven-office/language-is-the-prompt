# Paper Limitations Upgrade

This note records the strongest follow-up work that can be done without rerunning the full ACB-Full benchmark.

## What is improved immediately

### 1. Failure-taxonomy reliability

Added a manual audit workflow:

- [README.md](/Users/a12907/Documents/GitHub/AutoCodeBenchmark/results/elixir_failure_audit/README.md)
- [audit_samples_blinded.csv](/Users/a12907/Documents/GitHub/AutoCodeBenchmark/results/elixir_failure_audit/audit_samples_blinded.csv)
- [audit_key.csv](/Users/a12907/Documents/GitHub/AutoCodeBenchmark/results/elixir_failure_audit/audit_key.csv)

This directly strengthens the taxonomy section by enabling independent human review and later agreement reporting, without changing any benchmark outputs.

### 2. Follow-up study sizing

Added a sample-size planning artifact:

- [README.md](/Users/a12907/Documents/GitHub/AutoCodeBenchmark/results/elixir_power_plan/README.md)
- [power_plan.csv](/Users/a12907/Documents/GitHub/AutoCodeBenchmark/results/elixir_power_plan/power_plan.csv)

Current read:

- Suite A docs effects are already powered.
- Suite F state-flow effects become realistic follow-up targets at about `N=480`.
- Suite D and Suite E directional effects likely need around `N=1200-1600` matched tasks at the observed effect sizes.

This turns the paper's "future work" section into a concrete experimental budget instead of a vague suggestion list.

## What requires new tasks, but not ACB-Full reruns

### 3. Shared task IDs across languages

Added a new same-task study scaffold:

- [README.md](/Users/a12907/Documents/GitHub/AutoCodeBenchmark/studies/explicit_task_panel/README.md)
- [study.json](/Users/a12907/Documents/GitHub/AutoCodeBenchmark/studies/explicit_task_panel/study.json)
- [tasks.json](/Users/a12907/Documents/GitHub/AutoCodeBenchmark/studies/explicit_task_panel/tasks.json)
- [conditions.json](/Users/a12907/Documents/GitHub/AutoCodeBenchmark/studies/explicit_task_panel/conditions.json)
- [panel_summary.json](/Users/a12907/Documents/GitHub/AutoCodeBenchmark/studies/explicit_task_panel/generated/panel_summary.json)
- [prompt_records.jsonl](/Users/a12907/Documents/GitHub/AutoCodeBenchmark/studies/explicit_task_panel/generated/prompt_records.jsonl)

This creates:

- `8` explicit task IDs
- `3` target languages: Elixir, Python, TypeScript
- `3` prompt conditions
- `72` generated prompt rows

This is the cleanest way to reduce the "no shared task id" limitation and to test whether richer task framing transfers to weaker languages.

## What remains unresolved

- Single-model causality still remains until another model family is run.
- Repo-scale validation still remains until Suite I is executed.
- The original ACB-Full benchmark itself still has no official shared task IDs, so that limitation can only be reduced, not fully removed, by auxiliary studies.

## Best next run

If we want the biggest scientific gain without repeating ACB-Full, the next run should be:

1. convert the explicit task panel into executable language-specific rows
2. run GPT-5.4 medium on those rows
3. analyze task-fixed effects and cross-language intervention lift

That would strengthen three limitations at once:

- shared task identity
- task framing versus ecosystem entanglement
- cross-language causal transfer
