"""Single-concept results for the report, computed into data/single_*.csv.
One concept, no prerequisites, no forgetting. Answer model = the simulator's:
  genuine solve s = m**(1+1.2d), easy d=0.2, hard d=0.8; P(right) = s(1-0.07) + (1-s)0.25.
Learning rule (the professor's idea), keyed to GENUINE solving:
  EASY: m += lr*rhoE*(0.45 if solved else 0.10)*max(0, cE - m)
  HARD: m += lr*(min(1, beta*0.45)*(1-m) if solved else bH*(1-m)), capped at 1
Also 'today' (gain on the OBSERVED answer, toward 1, any question) and 'observed' (the idea but gain on the
observed answer, so lucky guesses on hard questions pay). Target for 'learned' here: m >= 0.9 (as in the
earlier single-concept notes)."""
import csv, os
import numpy as np
K, SLIP, GUESS, DE, DH, T = 1.2, 0.07, 0.25, 0.2, 0.8, 0.9
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
def solve(m, d): return np.power(m, 1 + K * d)
def pright(m, d): s = solve(m, d); return s * (1 - SLIP) + (1 - s) * GUESS
CAP = dict(rhoE=1.0, cE=0.6, beta=2.0, bH=0.0)
SLOW = dict(rhoE=0.3, cE=1.0, beta=2.0, bH=0.0)

def outcomes(m, a, kind, p):
    """Return (prob, new_m) pairs for one question. kind in today / observed / genuine."""
    if kind == 'today':
        pr = pright(m, DE if a == 'E' else DH)
        return [(pr, m + 0.45 * (1 - m)), (1 - pr, m + 0.10 * (1 - m))]
    if kind == 'observed':
        if a == 'E':
            pr = pright(m, DE); room = np.maximum(0, p['cE'] - m)
            return [(pr, m + p['rhoE'] * 0.45 * room), (1 - pr, m + p['rhoE'] * 0.10 * room)]
        pr = pright(m, DH)
        return [(pr, np.minimum(1, m + min(1, p['beta'] * 0.45) * (1 - m))), (1 - pr, m + p['bH'] * (1 - m))]
    if a == 'E':
        s = solve(m, DE); room = np.maximum(0, p['cE'] - m)
        return [(s, m + p['rhoE'] * 0.45 * room), (1 - s, m + p['rhoE'] * 0.10 * room)]
    s = solve(m, DH)
    return [(s, np.minimum(1, m + min(1, p['beta'] * 0.45) * (1 - m))), (1 - s, m + p['bH'] * (1 - m))]

def egain(m, a, kind, p): return sum(pr * (nm - m) for pr, nm in outcomes(m, a, kind, p))

def write(name, rows):
    with open(os.path.join(OUT, name), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

GRID = np.linspace(0, 1, 2001)
def ssp(p):
    """Min expected questions to reach m >= 0.9 from each m (value iteration; genuine rule)."""
    sE, sH = solve(GRID, DE), solve(GRID, DH)
    room = np.maximum(0, p['cE'] - GRID)
    eok, eno = GRID + p['rhoE'] * 0.45 * room, GRID + p['rhoE'] * 0.10 * room
    hok = np.minimum(1, GRID + min(1, p['beta'] * 0.45) * (1 - GRID)); hno = GRID + p['bH'] * (1 - GRID)
    done = GRID >= T
    V = np.where(done, 0.0, 200.0)
    for _ in range(20000):
        qE = 1 + sE * np.interp(eok, GRID, V) + (1 - sE) * np.interp(eno, GRID, V)
        if p['bH'] == 0:
            with np.errstate(divide='ignore', invalid='ignore'):
                qH = np.where(sH > 1e-12, (1 + sH * np.interp(hok, GRID, V)) / sH, 1e12)
        else:
            qH = 1 + sH * np.interp(hok, GRID, V) + (1 - sH) * np.interp(hno, GRID, V)
        nV = np.where(done, 0.0, np.minimum(np.minimum(qE, qH), 1e9))
        if np.max(np.abs(nV - V)) < 1e-9: V = nV; break
        V = nV
    hard = (qH < qE) & ~done
    idx = np.where(hard & (GRID >= 0.02))[0]
    return V, (GRID[idx[0]] if len(idx) else None)

def mc(p, policy, n=4000, cap=400, m0=0.05, seed=1, kind='genuine', traj=0):
    """Vectorised Monte Carlo. policy(m, q) -> boolean array 'ask hard'. Returns questions-to-0.9 (inf if not by cap)."""
    rng = np.random.default_rng(seed)
    m = np.full(n, m0); t = np.full(n, np.inf); path = []
    for q in range(cap):
        if traj and q <= traj: path.append(m.mean())
        hard = policy(m, q)
        d = np.where(hard, DH, DE)
        s = solve(m, d); solved = rng.random(n) < s
        roomE = np.maximum(0, p['cE'] - m)
        if kind == 'genuine':
            newE = m + p['rhoE'] * np.where(solved, 0.45, 0.10) * roomE
            newH = np.where(solved, np.minimum(1, m + min(1, p['beta'] * 0.45) * (1 - m)), m + p['bH'] * (1 - m))
        else:
            raise ValueError
        m = np.minimum(1, np.where(hard, newH, newE))
        hit = (m >= T) & np.isinf(t); t[hit] = q + 1
    return (t, path) if traj else t

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    # 1. one-step expected gain curves
    rows = []
    for m in np.round(np.arange(0.02, 0.951, 0.01), 2):
        for kind, label in (('today', 'today'), ('observed', 'idea, learn from marked answer'), ('genuine', 'idea, learn from solving')):
            rows.append(dict(model=label, m=m, gain_easy=round(float(egain(m, 'E', kind, CAP)), 6),
                             gain_hard=round(float(egain(m, 'H', kind, CAP)), 6)))
    write('single_gain.csv', rows)
    # 2. one-step switch point vs bH, for three easy ceilings
    rows = []
    ms = np.round(np.arange(0.01, 0.95, 0.005), 3)
    for cE in (0.4, 0.6, 0.8):
        for bH in np.round(np.arange(0, 0.1001, 0.01), 2):
            p = dict(rhoE=1.0, cE=cE, beta=2.0, bH=bH)
            hw = [egain(m, 'H', 'genuine', p) > egain(m, 'E', 'genuine', p) for m in ms]
            if all(hw): sw = 0.0
            elif not any(hw): sw = None
            else: sw = float(ms[hw.index(True)])
            rows.append(dict(cE=cE, bH=bH, beta=2.0, switch_m=sw, hard_always=int(all(hw))))
    write('single_switch.csv', rows)
    # 3. best schedule for one concept, identical students, m0 = 0.05, target 0.9, cap 400
    rows = []; traj_rows = []
    for name, p in (('capped at 0.6', CAP), ('slow (30% speed)', SLOW),
                    ('capped at 0.6, failed hard teaches 0.05', dict(CAP, bH=0.05)),
                    ('slow, failed hard teaches 0.05', dict(SLOW, bH=0.05))):
        V, ms_ = ssp(p)
        i0 = int(round(0.05 * 2000))
        thr = ms_ if ms_ is not None else 2.0
        res = {}
        res['best switch rule'] = mc(p, lambda m, q: m >= thr)
        fixed = {k: mc(p, (lambda k: lambda m, q: np.full(m.shape, q >= k))(k), n=2000, seed=7) for k in range(0, 31)}
        bk = min(fixed, key=lambda k: np.mean(np.minimum(fixed[k], 400)))
        res[f'best fixed'] = mc(p, lambda m, q: np.full(m.shape, q >= bk))
        res['easy only'] = mc(p, lambda m, q: np.zeros(m.shape, bool))
        res['hard only'] = mc(p, lambda m, q: np.ones(m.shape, bool))
        for pol, t in res.items():
            rows.append(dict(version=name, policy=pol, switch_m=ms_, best_fixed_k=bk if pol == 'best fixed' else '',
                             ssp_expected=round(float(V[i0]), 2) if pol == 'best switch rule' else '',
                             reach400=round(float(np.mean(np.isfinite(t))), 4),
                             mean_q=round(float(np.mean(t)), 2) if np.all(np.isfinite(t)) else '',
                             median_q=float(np.median(t))))
        if name in ('capped at 0.6', 'slow (30% speed)'):
            for pol, f in (('easy only', lambda m, q: np.zeros(m.shape, bool)), ('hard only', lambda m, q: np.ones(m.shape, bool)),
                           ('best switch rule', lambda m, q: m >= thr)):
                _, path = mc(p, f, traj=60, seed=11)
                for q, v in enumerate(path): traj_rows.append(dict(version=name, policy=pol, q=q, mean_m=round(float(v), 5)))
    write('single_schedule.csv', rows); write('single_traj.csv', traj_rows)
    # 4. success rate the learner sees under the best switch rule, and P(right) for easy/hard
    rows = []
    for name, p in (('capped at 0.6', CAP), ('slow (30% speed)', SLOW)):
        _, ms_ = ssp(p)
        rng = np.random.default_rng(3); n = 3000
        m = np.full(n, 0.05); alive = np.ones(n, bool); hits = tot = hh = ht = 0.0
        for q in range(400):
            hard = m >= ms_
            pr = np.where(hard, pright(m, DH), pright(m, DE))
            hits += pr[alive].sum(); tot += alive.sum(); hh += pr[alive & hard].sum(); ht += (alive & hard).sum()
            s = solve(m, np.where(hard, DH, DE)); solved = rng.random(n) < s
            roomE = np.maximum(0, p['cE'] - m)
            newE = m + p['rhoE'] * np.where(solved, 0.45, 0.10) * roomE
            newH = np.where(solved, np.minimum(1, m + min(1, p['beta'] * 0.45) * (1 - m)), m + p['bH'] * (1 - m))
            m = np.where(alive, np.minimum(1, np.where(hard, newH, newE)), m)
            alive &= m < T
            if not alive.any(): break
        rows.append(dict(version=name, overall_p_right=round(hits / tot, 4), p_right_on_hard=round(hh / max(ht, 1), 4),
                         share_hard=round(ht / tot, 4)))
    for m in (0.2, 0.4, 0.6, 0.9):
        rows.append(dict(version=f'P(right) at mastery {m}', overall_p_right=round(float(pright(m, DE)), 4),
                         p_right_on_hard=round(float(pright(m, DH)), 4), share_hard=''))
    write('single_success.csv', rows)
