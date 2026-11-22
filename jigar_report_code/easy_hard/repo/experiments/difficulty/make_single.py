"""Single-concept results, computed into data/single_*.csv. Version with the proposed rule.
One concept, no prerequisites, no forgetting. Answer model = the simulator's:
  really solving s = m**(1+1.2d), easy d=0.2, hard d=0.8; marked right P = 0.93 s + 0.25 (1-s).
Proposed rule, keyed to REALLY solving:
  easy: m_new = min(max(m, c), m + (g if solved else f) * max(0, 1 - m/c))
  hard: m_new = min(1, m + (J if solved else bH) * (1 - m))
  g = 0.45, J = 0.9, f = 0.10, bH = 0 unless stated; c = 1 means no cap.
Also today's rule (gain on the marked answer, toward 1, any question), the same gains on really solving (plot only),
and the proposed rule keyed to the marked answer (plot only). Goal here: m >= 0.9.
The best plan comes from solve_one.py: backward induction over 2,000,001 levels, next state rounded down and up."""
import csv, os
import numpy as np
import solve_one as SO
K, SLIP, GUESS, DE, DH, GOAL = 1.2, 0.07, 0.25, 0.2, 0.8, 0.9
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
def solve(m, d): return np.power(m, 1 + K * d)
def pright(m, d): s = solve(m, d); return s * (1 - SLIP) + (1 - s) * GUESS
def rule(g=0.45, J=0.9, f=0.10, bH=0.0, c=1.0): return dict(g=g, J=J, f=f, bH=bH, c=c)
CAP = rule(c=0.6)
NOCAP = rule()


def easy_new(m, rate, p):
    return np.minimum(np.maximum(m, p['c']), m + rate * np.maximum(0, 1 - m / p['c']))


def outcomes(m, a, kind, p):
    """Return (prob, new_m) pairs for one question.
    kind: today (marked answer), today_s (same gains, really solving), marked (proposed rule on the marked answer),
    solving (proposed rule on really solving)."""
    d = DE if a == 'E' else DH
    if kind in ('today', 'today_s'):
        pr = pright(m, d) if kind == 'today' else solve(m, d)
        return [(pr, m + 0.45 * (1 - m)), (1 - pr, m + 0.10 * (1 - m))]
    pr = pright(m, d) if kind == 'marked' else solve(m, d)
    if a == 'E':
        return [(pr, easy_new(m, p['g'], p)), (1 - pr, easy_new(m, p['f'], p))]
    return [(pr, np.minimum(1, m + p['J'] * (1 - m))), (1 - pr, m + p['bH'] * (1 - m))]


def egain(m, a, kind, p): return sum(pr * (nm - m) for pr, nm in outcomes(m, a, kind, p))


def write(name, rows):
    with open(os.path.join(OUT, name), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def best_plan(p, goal=GOAL, m0=0.05):
    """Exact bracket for the best plan, and the best single switch on a 0.01 grid (which is what students follow)."""
    a = (p['g'], p['J'], p['f'], p['bH'], p['c'])
    o = SO.solve_cell(*a, goal, 1.0, (m0,))[0]
    t = SO.best_threshold(*a, goal, m0)
    return o, t


def mc(p, policy, n=4000, cap=400, m0=0.05, seed=1, traj=0):
    """Vectorised Monte Carlo. policy(m, q) -> boolean array 'ask hard'. Returns questions to the goal (inf if not by cap)."""
    rng = np.random.default_rng(seed)
    m = np.full(n, m0); t = np.full(n, np.inf); path = []
    for q in range(cap):
        if traj and q <= traj: path.append((m.mean(), m.std()))
        hard = policy(m, q)
        d = np.where(hard, DH, DE)
        s = solve(m, d); solved = rng.random(n) < s
        newE = easy_new(m, np.where(solved, p['g'], p['f']), p)
        newH = np.minimum(1, m + np.where(solved, p['J'], p['bH']) * (1 - m))
        m = np.where(hard, newH, newE)
        hit = (m >= GOAL) & np.isinf(t); t[hit] = q + 1
    return (t, path) if traj else t


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    # 1. one-question expected gain curves. Starts at m = 0, so the start of the easy line is on the plot.
    rows = []
    for m in np.round(np.arange(0.0, 0.951, 0.01), 2):
        for kind, label, p in (('today', 'today, marked answer', CAP), ('today_s', 'today, really solving', CAP),
                               ('marked', 'proposed, marked answer', CAP), ('solving', 'proposed, really solving', CAP),
                               ('solving', 'proposed, really solving, no cap', NOCAP)):
            rows.append(dict(model=label, m=m, gain_easy=round(float(egain(m, 'E', kind, p)), 6),
                             gain_hard=round(float(egain(m, 'H', kind, p)), 6)))
    write('single_gain.csv', rows)
    # 2. one-question crossing vs bH, for the caps
    rows = []
    ms = np.round(np.arange(0.01, 0.95, 0.005), 3)
    for c in (0.6, 0.7, 0.85, 1.0):
        for bH in np.round(np.arange(0, 0.1001, 0.01), 2):
            p = rule(c=c, bH=float(bH))
            hw = [egain(m, 'H', 'solving', p) > egain(m, 'E', 'solving', p) for m in ms]
            if all(hw): sw = 0.0
            elif not any(hw): sw = None
            else: sw = float(ms[hw.index(True)])
            rows.append(dict(c=c, bH=bH, J=0.9, switch_m=sw, hard_always=int(all(hw))))
    write('single_switch.csv', rows)
    # 3. best plan on one concept, identical students, m0 = 0.05, goal 0.9, at most 400 questions
    rows = []; traj_rows = []
    VERSIONS = (('capped at 0.6', CAP), ('no cap', NOCAP),
                ('capped at 0.6, failed hard teaches 0.05', rule(c=0.6, bH=0.05)),
                ('no cap, failed hard teaches 0.05', rule(bH=0.05)),
                ('capped at 0.7', rule(c=0.7)), ('capped at 0.85', rule(c=0.85)))
    for name, p in VERSIONS:
        o, t = best_plan(p)
        thr = t['thr_best']
        res = {}
        res['best switch rule'] = mc(p, lambda m, q: m >= thr)
        fixed = {k: mc(p, (lambda k: lambda m, q: np.full(m.shape, q >= k))(k), n=2000, seed=7) for k in range(0, 31)}
        bk = min(fixed, key=lambda k: np.mean(np.minimum(fixed[k], 400)))
        res['best fixed'] = mc(p, lambda m, q: np.full(m.shape, q >= bk))
        res['easy only'] = mc(p, lambda m, q: np.zeros(m.shape, bool))
        res['hard only'] = mc(p, lambda m, q: np.ones(m.shape, bool))
        for pol, tt in res.items():
            rows.append(dict(version=name, policy=pol, switch_m=thr, best_fixed_k=bk if pol == 'best fixed' else '',
                             exact_best=round(o['best'], 4) if pol == 'best switch rule' else '',
                             exact_width=round(o['best_hi'] - o['best_lo'], 6) if pol == 'best switch rule' else '',
                             exact_easy=(round(o['easy'], 4) if np.isfinite(o['easy']) else 'never') if pol == 'easy only' else '',
                             exact_hard=round(o['hard'], 4) if pol == 'hard only' else '',
                             pattern=o['pattern'] if pol == 'best switch rule' else '',
                             reach400=round(float(np.mean(np.isfinite(tt))), 4),
                             mean_q=round(float(np.mean(tt)), 2) if np.all(np.isfinite(tt)) else '',
                             sd_q=round(float(np.std(tt)), 2) if np.all(np.isfinite(tt)) else '',
                             median_q=float(np.median(tt))))
        if name in ('capped at 0.6', 'no cap'):
            for pol, f in (('easy only', lambda m, q: np.zeros(m.shape, bool)), ('hard only', lambda m, q: np.ones(m.shape, bool)),
                           ('best switch rule', lambda m, q: m >= thr)):
                _, path = mc(p, f, traj=60, seed=11)
                for q, (v, sd) in enumerate(path):
                    traj_rows.append(dict(version=name, policy=pol, q=q, mean_m=round(float(v), 5), sd_m=round(float(sd), 5)))
    write('single_schedule.csv', rows); write('single_traj.csv', traj_rows)
    # 4. share marked right that the learner sees under the best switch rule, and P for easy and hard
    rows = []
    for name, p in (('capped at 0.6', CAP), ('no cap', NOCAP), ('capped at 0.7', rule(c=0.7))):
        _, t = best_plan(p); thr = t['thr_best']
        rng = np.random.default_rng(3); n = 3000
        m = np.full(n, 0.05); alive = np.ones(n, bool); hits = tot = hh = ht = 0.0
        for q in range(400):
            hard = m >= thr
            pr = np.where(hard, pright(m, DH), pright(m, DE))
            hits += pr[alive].sum(); tot += alive.sum(); hh += pr[alive & hard].sum(); ht += (alive & hard).sum()
            s = solve(m, np.where(hard, DH, DE)); solved = rng.random(n) < s
            newE = easy_new(m, np.where(solved, p['g'], p['f']), p)
            newH = np.minimum(1, m + np.where(solved, p['J'], p['bH']) * (1 - m))
            m = np.where(alive, np.where(hard, newH, newE), m)
            alive &= m < GOAL
            if not alive.any(): break
        rows.append(dict(version=name, overall_p_right=round(hits / tot, 4), p_right_on_hard=round(hh / max(ht, 1), 4),
                         share_hard=round(ht / tot, 4)))
    for m in (0.2, 0.4, 0.6, 0.9):
        rows.append(dict(version=f'P at mastery {m}', overall_p_right=round(float(pright(m, DE)), 4),
                         p_right_on_hard=round(float(pright(m, DH)), 4), share_hard=''))
    write('single_success.csv', rows)
