"""Parts B and C on the 40-concept graph, on the study's own code path.
B = factor grid at speed 1, start .05, budget 2000. C = speed x start at baseline factors, budget 8000.
One shard per setting; a shard that exists is skipped. Students are the same seeds in every setting, so settings are paired.
The switch threshold is tuned on separate students and reported on the hold-out students."""
import csv
import gzip
import math
import os
import statistics
import sys
import time
from multiprocessing import Pool

import grids as GR
import rules as R

HERE = os.path.dirname(os.path.abspath(__file__))
WORKERS = int(os.environ.get('WORKERS', 12))
FIELDS = 'sid tutor plan thr seed t_end t_closure false declared asked easy right learned'.split()


def rows_for(sid, r, tutor, plan, seeds, budget, speed, m0, thr=None):
    t = '' if thr is None else thr
    out = []
    for s in seeds:
        o = R.run_student(r, tutor, plan, s, budget=budget, speed=speed, m0=m0, thr=thr)
        out.append((sid, tutor, plan, t, s, o['t_end'], o['t_closure'], o['false'], o['declared'], o['asked'],
                    o['easy'], o['right'], o['learned']))
    return out


def tune(sid, r, budget, speed, m0):
    """Lowest median closure on the tuning students; never finished counts as beyond the budget."""
    rows, score = [], {}
    for thr in GR.THRS:
        if thr >= r['c']:
            continue
        x = rows_for(sid, r, 'path', 'switch', GR.TUNE, budget, speed, m0, thr)
        rows += x
        v = [budget + 1 if y[6] is None else y[6] for y in x]
        score[thr] = (statistics.median(v), sum(v) / len(v), thr)
    return min(score, key=score.get), rows


def job(a):
    part, cell = a
    sid = cell['sid']
    budget = 2000 if part == 'graph' else 8000
    speed, m0 = cell.get('speed', 1.), cell.get('m0')
    path = os.path.join(HERE, 'out', part, f's{sid:05d}.csv.gz')
    if os.path.exists(path):
        return sid, 0.
    t0 = time.time()
    r = R.rule(g=cell['g'], J=cell['J'], f=cell['f'], bH=cell['bH'], c=cell['c'])
    best, rows = tune(sid, r, budget, speed, m0)
    rows = [(x[0], x[1], 'tune', *x[3:]) for x in rows]
    for plan in GR.CHAIN_PLANS:
        rows += rows_for(sid, r, 'path', plan, GR.HOLD, budget, speed, m0)
    rows += [(x[0], x[1], 'tuned', *x[3:]) for x in rows_for(sid, r, 'path', 'switch', GR.HOLD, budget, speed, m0, best)]
    for plan in ('random', 'switch'):
        rows += rows_for(sid, r, 'bfs', plan, GR.HOLD, budget, speed, m0)
    rows += rows_for(sid, r, 'ct', 'random', GR.CT1000, budget, speed, m0)
    for plan in (GR.CT_200 if part == 'graph' else GR.CT_200_ARMS):
        rows += rows_for(sid, r, 'ct', plan, GR.HOLD, budget, speed, m0)
    tmp = path + f'.tmp{os.getpid()}'
    with gzip.open(tmp, 'wt', newline='', compresslevel=6) as fh:
        w = csv.writer(fh)
        w.writerow(FIELDS)
        w.writerows(rows)
    os.replace(tmp, path)
    return sid, time.time() - t0


if __name__ == '__main__':
    part = sys.argv[1]
    cells = {'graph': GR.graph, 'arms': GR.arms}[part]()
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    if limit:
        cells = cells[:limit]
    os.makedirs(os.path.join(HERE, 'out', part), exist_ok=True)
    t0 = time.time()
    print(part, 'settings', len(cells), flush=True)
    with Pool(WORKERS) as P:
        for i, (sid, secs) in enumerate(P.imap_unordered(job, [(part, c) for c in cells]), 1):
            print(f'{i}/{len(cells)} sid {sid} took {secs:.0f}s elapsed {time.time() - t0:.0f}s', flush=True)
    print(part, 'done', round(time.time() - t0), 's', flush=True)
