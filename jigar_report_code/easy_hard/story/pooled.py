"""The different-students plot from many runs per student, so that one unusual run cannot move it.
Same 400 students and plans as the study's run; 200 fresh answer streams per student, shared across plans. Writes pooled.csv."""
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
    rows = []; per = []; rng = np.random.default_rng(20261107)
    with Pool(int(os.environ.get('WORKERS', 6))) as P:
        for hi in (.30, .60, .85):
            tr, trm = M.pop(300, 100, hi); te, tem = M.pop(400, 900, hi)
            thr = np.array([H.oracle_threshold(s) for s in te])
            k = min(range(0, 25), key=lambda k_: H.simulate(M.fixed(k_), tr, trm, 5000).mean())
            n = min(range(1, 8), key=lambda r_: H.simulate(M.probe(r_), tr, trm, 5000).mean())
            V = {name: np.array(P.map(one, [(i, te[i], tem[i], name, thr[i], k, n) for i in range(400)], chunksize=8), float) for name in 'ofa'}
            row = dict(hi=hi, k=k, n_row=n)
            for name, v in V.items():
                q = np.percentile(v.ravel(), [25, 50, 75, 95])
                row.update({f'{name}_q1': q[0], f'{name}_med': q[1], f'{name}_q3': q[2], f'{name}_p95': q[3], f'{name}_mean': v.mean(), f'{name}_sd': v.ravel().std(), f'{name}_min': v.min(), f'{name}_chance': v.var(1, ddof=1).mean() / v.ravel().var()})
            for a, b, tag in (('f', 'o', 'fo'), ('a', 'f', 'af')):
                d = V[a].mean(1) - V[b].mean(1); bs = [d[rng.integers(0, 400, 400)].mean() for _ in range(4000)]
                row.update({f'{tag}_d': d.mean(), f'{tag}_lo': np.percentile(bs, 2.5), f'{tag}_hi': np.percentile(bs, 97.5), f'{tag}_slower': float((d > 0).mean()), f'{tag}_max': d.max()})
            rows.append(row); print(row, flush=True)
            for i in range(400):
                per.append(dict(hi=hi, i=i, c=te[i][0], J=te[i][1], l=te[i][2], m0=tem[i], o=V['o'][i].mean(), f=V['f'][i].mean(), a=V['a'][i].mean()))
    with open(os.path.join(HERE, 'pooled.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
    with open(os.path.join(HERE, 'pooled_students.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, list(per[0])); w.writeheader(); w.writerows(per)
