#!/usr/bin/env bash
set -euo pipefail

# ── The Language Is the Prompt — Build Script ────────────────────────────
# Usage:
#   ./build.sh              # full build: figures → compile → overleaf zip → arXiv zip
#   ./build.sh figures      # regenerate figures only
#   ./build.sh compile      # compile PDF only (skip figures)
#   ./build.sh overleaf     # package Overleaf zip only (skip compile)
#   ./build.sh arxiv        # compile with pdfLaTeX-compatible path + package arXiv zip
#   ./build.sh clean        # remove all generated artifacts

PAPER_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PAPER_DIR"

# ── Colors for output ───────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

log()  { echo -e "${BLUE}▸${NC} $*"; }
ok()   { echo -e "${GREEN}✓${NC} $*"; }
fail() { echo -e "${RED}✗${NC} $*" >&2; exit 1; }

# ── Detect tools ────────────────────────────────────────────────────────
find_latex_engine() {
    if command -v latexmk &>/dev/null; then
        echo "latexmk"
    elif command -v pdflatex &>/dev/null; then
        echo "pdflatex"
    elif command -v tectonic &>/dev/null; then
        echo "tectonic"
    else
        fail "No LaTeX engine found. Install tectonic, latexmk, or pdflatex."
    fi
}

find_python() {
    if command -v python3 &>/dev/null; then
        echo "python3"
    elif command -v python &>/dev/null; then
        echo "python"
    else
        fail "Python not found. Install Python 3 to generate figures."
    fi
}

# ── Step 1: Generate figures ────────────────────────────────────────────
build_figures() {
    log "Generating figures..."
    local py
    py="$(find_python)"

    # Check matplotlib is available
    if ! "$py" -c "import matplotlib" 2>/dev/null; then
        fail "matplotlib not found. Install: pip install matplotlib numpy"
    fi

    "$py" figures/generate_figures.py

    local count
    count=$(ls figures/*.pdf 2>/dev/null | wc -l | tr -d ' ')
    ok "Generated ${count} figure PDFs + PNGs"
}

# ── Step 2: Compile PDF ─────────────────────────────────────────────────
build_pdf() {
    log "Compiling main.tex..."
    local engine
    engine="$(find_latex_engine)"

    case "$engine" in
        latexmk)
            log "Using latexmk (pdfLaTeX-compatible / arXiv-safe path)"
            latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
            ;;
        pdflatex)
            log "Using pdflatex (3 passes for references)"
            pdflatex -interaction=nonstopmode main.tex
            pdflatex -interaction=nonstopmode main.tex
            pdflatex -interaction=nonstopmode main.tex
            ;;
        tectonic)
            log "Using tectonic fallback"
            tectonic main.tex 2>&1 | tail -5
            ;;
    esac

    if [[ -f main.pdf ]]; then
        local size
        size=$(du -h main.pdf | cut -f1 | tr -d ' ')
        local pages
        pages=$( (pdfinfo main.pdf 2>/dev/null || echo "Pages: ?") | grep Pages | awk '{print $2}')
        ok "main.pdf — ${pages} pages, ${size}"
    else
        fail "Compilation failed — no main.pdf produced"
    fi
}

# ── Step 3: Package for Overleaf ────────────────────────────────────────
build_overleaf() {
    log "Packaging Overleaf zip..."

    local zipfile="${PAPER_DIR}/paper_overleaf.zip"
    rm -f "$zipfile"

    # Collect files into a temp staging dir for clean zip structure
    local staging
    staging=$(mktemp -d)
    trap "rm -rf '$staging'" EXIT

    # main.tex
    cp main.tex "$staging/"

    # Cover/logo assets
    if [[ -d assets ]]; then
        cp -R assets "$staging/"
    fi

    # Figure PDFs
    mkdir -p "$staging/figures"
    for f in figures/*.pdf; do
        [[ -f "$f" ]] && cp "$f" "$staging/figures/"
    done

    # Data CSVs
    mkdir -p "$staging/data"
    for f in data/*.csv; do
        [[ -f "$f" ]] && cp "$f" "$staging/data/"
    done

    # Figure generation script (for reproducibility)
    cp figures/generate_figures.py "$staging/figures/"

    # Create zip
    (cd "$staging" && zip -r "$zipfile" . -x ".*") >/dev/null

    local size
    size=$(du -h "$zipfile" | cut -f1 | tr -d ' ')
    local count
    count=$(unzip -l "$zipfile" 2>/dev/null | tail -1 | awk '{print $2}')
    ok "paper_overleaf.zip — ${size}, ${count} files"
    echo ""
    echo -e "  ${BOLD}Overleaf upload instructions:${NC}"
    echo "  1. Go to overleaf.com → New Project → Upload Project"
    echo "  2. Upload paper_overleaf.zip"
    echo "  3. Set compiler to pdfLaTeX (Menu → Compiler)"
    echo "  4. Click Recompile"
    echo ""
}

# ── Step 4: Package for arXiv ────────────────────────────────────────────
build_arxiv() {
    log "Packaging arXiv source zip..."

    local zipfile="${PAPER_DIR}/arxiv_source.zip"
    rm -f "$zipfile"

    local staging
    staging=$(mktemp -d)
    trap "rm -rf '$staging'" EXIT

    cp main.tex "$staging/"

    # Cover/logo assets
    if [[ -d assets ]]; then
        cp -R assets "$staging/"
    fi

    if [[ -f 00README.XXX ]]; then
        cp 00README.XXX "$staging/"
    fi

    mkdir -p "$staging/figures"
    for f in figures/*.pdf; do
        [[ -f "$f" ]] && cp "$f" "$staging/figures/"
    done

    (cd "$staging" && zip -r "$zipfile" . -x ".*") >/dev/null

    local size
    size=$(du -h "$zipfile" | cut -f1 | tr -d ' ')
    local count
    count=$(unzip -l "$zipfile" 2>/dev/null | tail -1 | awk '{print $2}')
    ok "arxiv_source.zip — ${size}, ${count} files"
    echo ""
    echo -e "  ${BOLD}arXiv upload instructions:${NC}"
    echo "  1. Upload arxiv_source.zip (not the repository root)"
    echo "  2. Keep main.tex at the archive root"
    echo "  3. Compile with pdfLaTeX on arXiv unless you have a reason not to"
    echo ""
}

# ── Clean ───────────────────────────────────────────────────────────────
clean() {
    log "Cleaning build artifacts..."
    rm -f main.pdf main.aux main.log main.out main.bbl main.blg main.fls main.fdb_latexmk main.synctex.gz
    rm -f figures/*.pdf figures/*.png
    rm -f paper_overleaf.zip
    rm -f arxiv_source.zip
    ok "Cleaned"
}

# ── Main ────────────────────────────────────────────────────────────────
main() {
    echo -e "${BOLD}═══ The Language Is the Prompt — Paper Build ═══${NC}"
    echo ""

    local cmd="${1:-all}"

    case "$cmd" in
        figures)
            build_figures
            ;;
        compile|pdf)
            build_pdf
            ;;
        overleaf|zip)
            build_overleaf
            ;;
        arxiv)
            build_pdf
            echo ""
            build_arxiv
            ;;
        clean)
            clean
            ;;
        all|"")
            build_figures
            echo ""
            build_pdf
            echo ""
            build_overleaf
            echo ""
            build_arxiv
            ;;
        *)
            echo "Usage: ./build.sh [figures|compile|overleaf|arxiv|clean|all]"
            exit 1
            ;;
    esac
}

main "$@"
