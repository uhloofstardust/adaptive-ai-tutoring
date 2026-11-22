"""Part A, one concept. One shard per factor setting: goals .9 and .8, speeds 1, .5, .25, starts .05, .3, .65.
Resumable: a shard that exists is skipped."""
import csv
import math
import os
import sys
import time
from multiprocessing import Pool

import grids as GR
import solve_one as SO

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'one')
WORKERS = int(os.environ.get('WORKERS', 12))
FIELDS = ('sid arm g J f bH c goal speed start best_hi best_lo best easy hard hard_start hard_start_lo first_hard '
          'n_changes pattern ever_hard q_easy q_hard right thr_best thr_value best_K2e5').split()


def job(cell):
    path = os.path.join(OUT, f"s{cell['sid']:05d}.csv")
    if os.path.exists(path):
        return cell['sid'], 0.
    t0 = time.time()
    a = (cell['g'], cell['J'], cell['f'], cell['bH'], cell['c'])
    rows = []
    for goal in (.9, .8):
        for speed in (1., .5, .25):
            for r in SO.solve_cell(*a, goal, speed, (.05, .3, .65)):
                r.update(sid=cell['sid'], arm=cell['arm'])
                if speed == 1. and r['start'] == .05:
                    r.update(SO.best_threshold(*a, goal))
                rows.append(r)
    tmp = path + f'.tmp{os.getpid()}'
    with open(tmp, 'w', newline='') as fh:
        w = csv.DictWriter(fh, FIELDS, restval='')
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, path)
    return cell['sid'], time.time() - t0


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    cells = GR.one_concept()
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    if limit:
        cells = cells[:limit]
    SO.solve_cell(.45, .9, .10, 0., .6, .9, 1., (.05,), K=2000)     # compile once before the workers start
    SO.best_threshold(.45, .9, .10, 0., .6, .9, K=2000)
    t0 = time.time()
    print('cells', len(cells), flush=True)
    with Pool(WORKERS) as P:
        for i, (sid, secs) in enumerate(P.imap_unordered(job, cells), 1):
            if i % 50 == 0 or i == len(cells):
                print(f'{i}/{len(cells)} last {secs:.1f}s elapsed {time.time() - t0:.0f}s', flush=True)
    print('one concept done', round(time.time() - t0), 's', flush=True)
