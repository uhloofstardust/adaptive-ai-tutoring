#!/bin/sh
# Rebuilds the story's figures, numbers and PDF. spread.py is separate, since it takes minutes.
set -e
cd "$(dirname "$0")"
python3 -B make_figs.py >/dev/null 2>&1
python3 -B story_numbers.py >/dev/null 2>&1
pdflatex -interaction=nonstopmode -halt-on-error main.tex > build.log 2>&1 || { tail -30 build.log; exit 1; }
pdflatex -interaction=nonstopmode -halt-on-error main.tex > build.log 2>&1
pdflatex -interaction=nonstopmode -halt-on-error main.tex > build.log 2>&1
grep -E "^!|undefined number|multiply defined|Overfull" main.log || true
pdfinfo main.pdf | grep Pages
