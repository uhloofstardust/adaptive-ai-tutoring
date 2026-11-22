#!/bin/zsh
# Figures, BKT numbers, then the PDF. The simulation numbers are read from ../story/gen.tex and ../shared/sweep_gen.tex.
cd "${0:A:h}"
python3 make_figs.py > figs.log 2>&1 || { tail -5 figs.log; exit 1; }
python3 bkt_numbers.py > bkt_numbers.log 2>&1 || { tail -5 bkt_numbers.log; exit 1; }
python3 bkt_intervals.py > bkt_intervals.log 2>&1 || { tail -5 bkt_intervals.log; exit 1; }
python3 sep_numbers.py > sep_numbers.log 2>&1 || { tail -5 sep_numbers.log; exit 1; }
python3 format_keys.py > format_keys.log 2>&1 || { tail -5 format_keys.log; exit 1; }
for i in 1 2 3; do pdflatex -interaction=nonstopmode -halt-on-error main.tex > build.log 2>&1 || { grep -n '^!' -A4 build.log | head -20; exit 1; }; done
grep -c 'Overfull' build.log; pdfinfo main.pdf | grep Pages
