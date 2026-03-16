# AI Coding Language Benchmark

## Overview

Benchmark that has **Codex CLI running `gpt-5.4` at `medium` reasoning effort** implement `MiniGit` in multiple languages, comparing generation time, estimated cost, LOC, token usage, and pass rate.

This repo is an adapted fork of the original Claude-focused benchmark. It now includes **Elixir** and writes **Codex JSONL logs**.

## Repository Structure

```text
SPEC-v1.txt          # MiniGit v1 spec (init/add/commit/log)
SPEC-v2.txt          # MiniGit v2 spec (v1 + status/diff/checkout/reset/rm/show)
test-v1.sh           # v1 test suite (11 tests)
test-v2.sh           # v2 test suite (30 tests)
benchmark.rb         # Benchmark runner (Codex CLI)
report.rb            # Report generator (results.json -> report.md)
plot.py              # Graph generator (results.json -> figures/*.png)
requirements.txt     # Python plotting dependencies
Brewfile             # macOS toolchain manifest
results/
  results.json       # Raw result data
  meta.json          # Environment metadata
  report.md          # Generated report
figures/             # Generated graphs
logs/                # Codex JSONL logs
generated/           # Generated source trees
```

## How It Works

1. Run `ruby benchmark.rb`
2. For each language x trial:
   - `v1`: create `generated/minigit-{lang}-{trial}-v1/`, copy spec/tests, invoke `codex exec`
   - `v2`: copy v1 into `minigit-{lang}-{trial}-v2/`, invoke `codex exec` again to extend it
3. Run shell test scripts independently
4. Measure wall-clock time, LOC, token usage, and estimated cost
5. Run `ruby report.rb`
6. Run `python3 plot.py results/results.json`

## Key Commands

```bash
ruby benchmark.rb                                    # All languages x 1 trial (default overwrite)
ruby benchmark.rb --lang python,elixir --trials 1   # Small comparison run
ruby benchmark.rb --trials 1 --start 2 --append     # Append another batch
ruby report.rb                                      # Generate report
python3 plot.py results/results.json                # Generate figures
```

## Supported Languages

`rust`, `go`, `c`, `typescript`, `javascript`, `java`, `perl`, `python`, `python/mypy`, `ruby`, `ruby/steep`, `lua`, `scheme`, `ocaml`, `haskell`, `elixir`

To add a language, update the `LANGUAGES` hash in `benchmark.rb`.

## Important Notes

- The benchmark now defaults to replacing `results/results.json`; use `--append` when combining batches.
- Cost is estimated from published GPT-5.4 token pricing because Codex CLI exposes token usage but not direct cost values.
- Elixir is prompted toward an executable `minigit` script rather than a full Mix project unless Mix is needed.
- `plot.py` forces the `Agg` backend so it can render in headless macOS shells.
