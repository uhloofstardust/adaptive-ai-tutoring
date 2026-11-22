#!/bin/zsh
# Full sweep. Resumable: finished shards are skipped.
cd "${0:A:h}"
export WORKERS=12
python3 -B run_one.py > logs/one.log 2>&1 && \
python3 -B run_graph.py arms > logs/arms.log 2>&1 && \
python3 -B run_graph.py graph > logs/graph.log 2>&1
echo "run_all exit $?"
