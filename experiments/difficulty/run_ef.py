import csv, itertools, os, sys
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness2 as H2
N = 200
SEEDS = [4242 + i for i in range(N)]
RULES = ['current', 'slow_bH0', 'slow_bH02', 'slow_bH05', 'cap60_bH0', 'cap85_bH0', 'slow_b1', 'cap60_b1']
CPOL = ['path', 'bfs', 'ct']
DPOL = ['random', 'easyfirst', 'k2', 'k4', 'k8', 'k12', 'k16', 'switch']
def job(cond):
    r, c, d = cond
    rows = []
    for sd in SEEDS:
        o = H2.run2(r, c, d, sd)
        row = dict(rule=r, cpol=c, dpol=d, seed=sd, t_end=o['t_end'], t_closure=o['t_closure'], t_decl=o['t_decl'],
                   m_end_at_decl=o['m_end_at_decl'], closure_ok_at_decl=o['closure_ok_at_decl'],
                   easy_share=round(o['easy_share'], 4),
                   q_chain=';'.join('' if x is None else str(x) for x in o['q_chain']))
        for t, cv in o['cp'].items():
            for k, v in cv.items(): row[f'{k}@{t}'] = v
        rows.append(row)
    return rows
if __name__ == '__main__':
    conds = list(itertools.product(RULES, CPOL, DPOL))
    print(len(conds), 'conditions x', N, flush=True)
    from common import open_out
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'ef_rows.csv.gz')
    with Pool(int(os.environ.get('WORKERS', 12))) as pool, open_out(out) as f:
        w = None
        for rows in pool.imap(job, conds):
            if w is None: w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader()
            w.writerows(rows)
    print('done', out)
