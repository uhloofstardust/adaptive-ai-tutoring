"""Run the easy/hard x graph grid. Writes data/graph_rows.csv.gz (one row per learner x condition)."""
import csv, itertools, sys, os
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H

# extra rule variants for sweeps
H.RULES.update({
    'slow_bH02':   dict(rhoE=0.3, cE=1.0, beta=2.0, bH=0.02),
    'slow15_bH0':  dict(rhoE=0.15, cE=1.0, beta=2.0, bH=0.0),
    'slow50_bH0':  dict(rhoE=0.5, cE=1.0, beta=2.0, bH=0.0),
    'slow_b15':    dict(rhoE=0.3, cE=1.0, beta=1.5, bH=0.0),
    'slow_b3':     dict(rhoE=0.3, cE=1.0, beta=3.0, bH=0.0),
    'cap60_bH02':  dict(rhoE=1.0, cE=0.6, beta=2.0, bH=0.02),
    'cap60_b3':    dict(rhoE=1.0, cE=0.6, beta=3.0, bH=0.0),
    'cap80_bH0':   dict(rhoE=1.0, cE=0.8, beta=2.0, bH=0.0),
})
N = int(os.environ.get('NLEARN', 100))
SEEDS = [4242 + i for i in range(N)]
ALLPOL = [('path', d) for d in ('random', 'easy', 'hard', 'switch', 'e3h')] + \
         [('bfs', d) for d in ('random', 'easy', 'hard', 'switch', 'e3h')] + \
         [('ct', d) for d in ('random', 'easy', 'hard', 'switch', 'e3h')] + \
         [('ct_hard', d) for d in ('random', 'easy', 'switch', 'e3h')]
MAINRULES = ['current', 'slow_bH0', 'slow_bH05', 'cap60_bH0', 'cap60_bH05', 'cap85_bH0']
SWPOL = [('path', 'easy'), ('path', 'hard'), ('path', 'switch'), ('path', 'random'),
         ('ct', 'random'), ('ct', 'e3h'), ('ct_hard', 'e3h')]

def conditions():
    for r, (c, d) in itertools.product(MAINRULES, ALLPOL):
        yield ('main', r, c, d, 'average', None)
    extra_rules = ['slow_bH02', 'slow15_bH0', 'slow50_bH0', 'slow_b15', 'slow_b3',
                   'cap60_bH02', 'cap60_b3', 'cap80_bH0']
    for r, (c, d) in itertools.product(extra_rules, SWPOL):
        yield ('rules', r, c, d, 'average', None)
    swr = ['current', 'slow_bH0', 'cap60_bH0', 'cap85_bH0', 'slow_bH05']
    for prof in ('slow', 'fast'):
        for r, (c, d) in itertools.product(swr, SWPOL):
            yield ('profile', r, c, d, prof, None)
    for s in (0.0, 0.4, 1.0):
        for r, (c, d) in itertools.product(swr, SWPOL):
            yield ('prereq', r, c, d, 'average', {'prereq_sensitivity': s})
    for im in (0.3,):
        for r, (c, d) in itertools.product(swr, SWPOL):
            yield ('prior', r, c, d, 'average', {'init_mastery': im})

def job(cond):
    grp, r, c, d, prof, ov = cond
    rows = []
    for sd in SEEDS:
        o = H.run(r, c, d, sd, profile=prof, overrides=ov)
        row = dict(group=grp, rule=r, cpol=c, dpol=d, profile=prof,
                   override=('' if not ov else ';'.join(f'{k}={v}' for k, v in ov.items())),
                   seed=sd, t_end=o['t_end'], t_end09=o['t_end09'], t_decl=o['t_decl'],
                   m_end_at_decl=o['m_end_at_decl'], path_mean_at_decl=o['path_mean_at_decl'],
                   idle_at=o['idle_at'])
        for t, cv in o['curve'].items():
            for k, v in cv.items(): row[f'{k}@{t}'] = v
        rows.append(row)
    return rows

if __name__ == '__main__':
    conds = list(conditions())
    print(len(conds), 'conditions x', N, 'learners', flush=True)
    from common import open_out
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'graph_rows.csv.gz')
    with Pool(int(os.environ.get('WORKERS', 12))) as pool, open_out(out) as f:
        w = None
        for i, rows in enumerate(pool.imap(job, conds, chunksize=1)):
            if w is None:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader()
            w.writerows(rows)
            if i % 25 == 0: print(i, flush=True)
    print('done', out)
