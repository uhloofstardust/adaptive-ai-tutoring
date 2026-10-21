"""Single concept, part 2 -> data/single_hetero.csv, data/single_adapt.csv, data/single_cusum.csv.
Uses hetero.py: capped reading, bH = 0, per-student (cE, beta, lr). Target 0.9, cap 200.
Students: cE ~ U(0.4, 0.8), beta ~ U(1.5, 3), lr ~ lognormal(0, 0.3), prior m0 ~ U(0.02, hi).
Settings are tuned on 300 'training' students and reported on 400 fresh ones."""
import csv, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hetero import step, oracle_threshold, simulate
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
def write(name, rows):
    with open(os.path.join(OUT, name), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def pop(n, seed, hi):
    r = np.random.default_rng(seed)
    st = list(zip(r.uniform(0.4, 0.8, n), r.uniform(1.5, 3.0, n), np.exp(r.normal(0, 0.3, n))))
    return st, r.uniform(0.02, hi, n)
def fixed(k): return lambda S: 'E' if S['q'] < k else 'H'
def probe(r):
    """Uses answers only: try hard; a hard miss sends the student to easy until r easy answers right in a row."""
    def pol(S):
        mode, ok = 'H', 0
        for a, c in S['hist']:
            if mode == 'H':
                if not c: mode, ok = 'E', 0
            else:
                ok = ok + 1 if c else 0
                if ok >= r: mode = 'H'
        return mode
    return pol
if __name__ == '__main__':
    rows_sw, rows_ad = [], []
    for hi in (0.30, 0.60, 0.85):
        tr, trm = pop(300, 100, hi); te, tem = pop(400, 900, hi)
        thr = np.array([oracle_threshold(s) for s in te])
        if hi == 0.30:
            rows_sw = [dict(student=i, cE=round(s[0], 4), beta=round(s[1], 4), lr=round(s[2], 4), best_switch=round(float(x), 4))
                       for i, (s, x) in enumerate(zip(te, thr))]
        o = simulate(lambda S: 'H' if S['m'] >= thr[S['student']] else 'E', te, tem, 7000)
        bk = min(range(0, 25), key=lambda k: simulate(fixed(k), tr, trm, 5000).mean())
        br = min(range(1, 8), key=lambda r: simulate(probe(r), tr, trm, 5000).mean())
        f = simulate(fixed(bk), te, tem, 7000); a = simulate(probe(br), te, tem, 7000)
        rows_ad.append(dict(prior_hi=hi, oracle_mean=round(float(o.mean()), 3), best_fixed_mean=round(float(f.mean()), 3), best_fixed_k=bk,
                            answer_rule_mean=round(float(a.mean()), 3), answer_rule_r=br,
                            gap_fixed_minus_oracle=round(float(f.mean() - o.mean()), 3),
                            fixed_minus_rule=round(float((f - a).mean()), 3)))
    write('single_hetero.csv', rows_sw); write('single_adapt.csv', rows_ad)
    # The mastery test fooled by easy questions (CurriculumTutor's CUSUM: h = ln(1/0.0004), guess .25, slip .10)
    H = np.log(1 / 0.0004)
    def declares(ans, guess, slip):
        up, dn = np.log((1 - slip) / guess), np.log(slip / (1 - guess)); U = 0.0
        for t, c in enumerate(ans):
            U = max(0.0, U + (up if c else dn))
            if U > H: return t + 1
        return None
    rows = []
    for cE in (0.4, 0.6, 0.7):
        blind, aware = [], []
        for i in range(1000):
            rng = np.random.default_rng(10_000 + i); m, ans = 0.05, []
            for q in range(200):
                m, c = step(m, 'E', (cE, 2.0, 1.0), rng); ans.append(c)
            blind.append(declares(ans, 0.25, 0.10)); aware.append(declares(ans, 0.65, 0.10))
        bd = [x for x in blind if x is not None]
        rows.append(dict(ceiling=cE, blind_false_rate=np.mean([x is not None for x in blind]),
                         blind_median_q=float(np.median(bd)) if bd else '',
                         aware_false_rate=np.mean([x is not None for x in aware]), n=1000))
    write('single_cusum.csv', rows)
