PYTHON=python3

.PHONY: figures paper clean

figures:
	$(PYTHON) figures/generate_figures.py

paper: figures
	latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

clean:
	latexmk -C || true
	rm -f figures/*.pdf figures/*.png
