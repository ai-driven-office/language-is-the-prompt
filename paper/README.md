# Elixir arXiv paper - editable source bundle

This bundle gives you editable source files for the paper instead of only the compiled PDFs.

Important note: the exact original figure-generation scripts were **not** present in the saved artifact bundle that remained in this workspace. The surviving files were:

- `main.tex`
- compiled figure PDFs

Because of that, the figure source in this bundle is a **faithful reconstructed source package** built from the paper tables, captions, and figure contents. It is fully editable and reproducible, but it is not guaranteed to be byte-for-byte identical to the lost original plotting scripts.

## What is included

- `main.tex` - the paper source
- `figures/generate_figures.py` - rebuilds all figure PDFs from editable data
- `data/*.csv` - plot data used by the figure script
- `Makefile` - one-command rebuild targets

## Rebuild

```bash
make figures
make paper
```

Or manually:

```bash
python3 figures/generate_figures.py
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

## Outputs

Running the figure script will create these files under `figures/`:

- `figure_1_leaderboard.pdf`
- `figure_2_design_space.pdf`
- `figure_3_difficulty_resilience.pdf`
- `figure_4_suite_a_ablation.pdf`
- `figure_5_factorial_effects.pdf`
- `figure_6_docs_pipeline.pdf`
- `figure_A1_robustness.pdf`

The compiled PDFs are intentionally **not** pre-bundled here so that the package stays source-first.
