# Elixir arXiv paper - editable source bundle

This directory contains the editable manuscript source and the generated figure assets used for submission packaging.

Important note: the exact original plotting scripts were not preserved in the older saved artifact bundle. The current figure script is a reconstructed, editable source package built from the paper tables, captions, and rendered figure contents. It is reproducible for this repository state, but it is not guaranteed to be byte-for-byte identical to any earlier private plotting code.

## What is included

- `main.tex` - the manuscript source
- `build.sh` - build/package entrypoint
- `figures/generate_figures.py` - regenerates the figure PDFs and PNGs used by the paper
- `figures/*.pdf` - compiled figure assets referenced by `main.tex`
- `00README.XXX` - arXiv submission note included in the arXiv source zip

## Build

Preferred local build:

```bash
./build.sh compile
```

Full rebuild:

```bash
./build.sh
```

That runs figure generation, compiles the manuscript, creates `paper_overleaf.zip`, and creates `arxiv_source.zip`.

To generate only the arXiv-ready source bundle:

```bash
./build.sh arxiv
```

## Outputs

- `main.pdf` - compiled manuscript
- `paper_overleaf.zip` - editable upload bundle for Overleaf
- `arxiv_source.zip` - minimal arXiv upload bundle with `main.tex`, `00README.XXX`, and the referenced figure PDFs

For arXiv, upload `arxiv_source.zip`, not the repository root.
