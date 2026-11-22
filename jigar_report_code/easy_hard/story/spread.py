"""Why the bars of the different-students plot are long. Reruns each student many times and splits the variance.
Writes spread.csv. Same students and plans as the study's run; only the answer streams are fresh."""
import csv, os, sys
os.environ.setdefault('NUMBA_CACHE_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), '.numba_cache'))
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(os.path.dirname(HERE), 'repo', 'experiments', 'difficulty'); sys.path.insert(0, D)
import numpy as np
from multiprocessing import Pool
import hetero as H, make_single2 as M
R = 200
def one(a):
    i, s, m0, name, t, k, n = a
    p = {'o': lambda S: 'H' if S['m'] >= t else 'E', 'f': M.fixed(k), 'a': M.probe(n)}[name]
    return [H.simulate(lambda S: p(S), [s], [m0], 500000 + 1000 * i + r)[0] for r in range(R)]
if __name__ == '__main__':
    rows = []
    with Pool(int(os.environ.get('WORKERS', 8))) as P:
        for hi in (.30, .60, .85):
            tr, trm = M.pop(300, 100, hi); te, tem = M.pop(400, 900, hi)
            thr = np.array([H.oracle_threshold(s) for s in te])
            k = min(range(0, 25), key=lambda k_: H.simulate(M.fixed(k_), tr, trm, 5000).mean())
            n = min(range(1, 8), key=lambda r_: H.simulate(M.probe(r_), tr, trm, 5000).mean())
            for name in 'ofa':
                V = np.array(P.map(one, [(i, te[i], tem[i], name, thr[i], k, n) for i in range(400)], chunksize=8), float)
                within = V.var(1, ddof=1).mean(); between = V.mean(1).var(ddof=1) - within / R
                rows.append(dict(hi=hi, plan=name, chance=within / (within + between), students=between / (within + between)))
    with open(os.path.join(HERE, 'spread.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
    print(rows)
