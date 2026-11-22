#!/bin/sh
# Regenerate every result, figure and number under the proposed rule. This is the version behind the report.
set -e
cd "$(dirname "$0")"
python3 -B make_single.py      # one concept: data/single_gain, single_switch, single_schedule, single_traj, single_success
python3 -B make_single2.py     # one concept: data/single_hetero, single_adapt, single_cusum
python3 -B run_grid.py         # 40-concept graph, first grid: data/graph_rows.csv.gz (100 students)
python3 -B run_ef.py           # easy-first vs random: data/ef_rows.csv.gz (200 students)
python3 -B make_extra.py       # extra graph runs: data/extra_rows.csv.gz (200 students)
python3 -B make_figs.py        # figs/*.pdf
python3 -B make_numbers.py     # gen/numbers.tex, gen/t_graph.tex, gen/t_easyfirst.tex
