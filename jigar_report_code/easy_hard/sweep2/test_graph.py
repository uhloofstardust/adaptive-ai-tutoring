"""Control for the graph runs. The new loop must reproduce every saved row of the study's variants, per student.
V0 = the study unchanged; VBC = (1 - m/c) with the upper limit, no rho. Both were produced by the study's own scripts."""
import csv
import gzip
import os
import sys
from collections import Counter
from multiprocessing import Pool

import rules as R

T = os.environ['TRACE']
LAM = os.environ['LAM']
WORKERS = int(os.environ.get('WORKERS', 12))


def rows(v, n):
    return list(csv.DictReader(gzip.open(f'{T}/{v}/data/{n}.csv.gz', 'rt', newline='')))


def num(x):
    return None if x in ('', 'None') else int(float(x))


NEW = {'slow_bH0': R.rule(), 'slow_bH02': R.rule(bH=.02), 'slow_bH05': R.rule(bH=.05), 'slow_bH005': R.rule(bH=.005),
       'slow_bH01': R.rule(bH=.01), 'cap60_bH0': R.rule(c=.6), 'cap85_bH0': R.rule(c=.85),
       'slow_b1': R.rule(J=.45), 'cap60_b1': R.rule(J=.45, c=.6)}
OLD = {'slow_bH0': R.rule(g=.135, f=.03), 'slow_bH02': R.rule(g=.135, f=.03, bH=.02),
       'slow_bH05': R.rule(g=.135, f=.03, bH=.05), 'slow_b1': R.rule(g=.135, f=.03, J=.45)}


def check(job):
    kind, r, x = job
    if kind == 'ef':
        o = R.run_student(r, x['cpol'], x['dpol'], int(x['seed']), budget=2000)
        ok = (o['t_end'] == num(x['t_end']) and o['t_closure'] == num(x['t_closure'])
              and o['false'] == int(x['false_decl@2000']) and o['declared'] == int(x['declared@2000'])
              and o['learned'] == int(x['learned@2000'])
              and abs(o['easy'] / max(o['asked'], 1) - float(x['easy_share'])) < 6e-5)
    elif kind == 'xt':
        o = R.run_student(r, x['cpol'], x['dpol'], int(x['seed']), budget=2000)
        ok = o['t_end'] == num(x['t_end']) and o['t_closure'] == num(x['t_closure']) and o['false'] == int(x['false_decl'])
    else:
        o = R.run_student(r, 'ct', 'random', int(x['seed']), budget=8000, speed=float(x['lam']))
        ok = (o['t_closure'] == num(x['tc']) and o['false'] == int(x['false']) and o['declared'] == int(x['decl'])
              and o['asked'] == int(x['asked']))
    return (kind, ok, None if ok else (x, o))


def main():
    jobs = []
    for x in rows('VBC', 'ef_rows'):
        if x['rule'] in NEW:
            jobs.append(('ef', NEW[x['rule']], x))
    for x in rows('V0', 'ef_rows'):
        if x['rule'] in OLD:
            jobs.append(('ef', OLD[x['rule']], x))
    for x in rows('VBC', 'extra_rows'):
        if x['group'] == 'newpol' and x['dpol'] == 'e3h' and x['rule'] in NEW:
            jobs.append(('xt', NEW[x['rule']], x))
        if x['group'] == 'bh_sweep' and x['rule'] in NEW:
            jobs.append(('xt', NEW[x['rule']], x))
    for x in csv.DictReader(open(LAM)):
        jobs.append(('sp', R.rule(c=float(x['c'])), x))
    print('jobs', len(jobs), flush=True)
    done, bad = Counter(), Counter()
    with Pool(WORKERS) as P:
        for kind, ok, info in P.imap_unordered(check, jobs, chunksize=40):
            done[kind] += 1
            if not ok:
                bad[kind] += 1
                if sum(bad.values()) <= 10:
                    print('MISMATCH', kind, info, flush=True)
    print('compared', dict(done), 'mismatches', dict(bad), flush=True)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
