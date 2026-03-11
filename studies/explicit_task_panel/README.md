# Explicit Task Panel

This study is a direct response to the strongest remaining limitations in the Elixir paper:

- ACB-Full does not provide explicit shared task IDs across languages.
- The benchmark-level docs effect and ecosystem effect are still partially entangled.
- The current causal story is strongest within Elixir, but weaker for cross-language interventions.

## Purpose

The panel defines a new small benchmark with:

- explicit `task_id` values
- the same task semantics across languages
- prompt conditions that isolate task framing, contract richness, and examples
- target languages fixed to `elixir`, `python`, and `typescript`

## Intended use

1. Build language-specific executable rows from `tasks.json`.
2. Generate model outputs under each condition from `conditions.json`.
3. Score them with the existing local benchmark runner.
4. Analyze:
   - fixed task effects
   - lift from richer task framing in weaker languages
   - whether Elixir still leads when task identity is fully controlled

## Why this helps the paper

- It materially reduces the "no shared task id" limitation.
- It tests whether Elixir-like explicitness transfers to other languages.
- It can be run without rerunning ACB-Full.

## Current status

- Task specifications are defined.
- Prompt conditions are defined.
- `scripts/build_explicit_task_panel.py` generates prompt records for all task/language/condition combinations.
- Canonical solutions and language-specific test harnesses are intentionally left for the next step.
