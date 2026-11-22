"""Independent replay of the BKT comparisons, plus student-level bootstrap intervals. My own trace code, not the projects'. It replays
the saved fitted numbers and does not refit them. Every value of the report's Table 2 must match the saved console logs to 4 decimals,
so this also checks those logs. Bootstrap: resample students, keep each student's rows together, keep fitted numbers fixed. Writes gen_ci.tex."""
import math, os, sys
sys.dont_write_bytecode = True
import numpy as np, pandas as pd
H = os.path.expanduser('~'); HERE = os.path.dirname(os.path.abspath(__file__))
V = {}
def put(k, v): V['bk.ci.' + k] = str(v)
def hu(x, d=4):
    f = 10 ** d; r = math.floor(x * f + .5 + 1e-9) / f
    return f'{r:.{d}f}'
def signed(x, d=4): return ('+' if x >= 0 else '-') + hu(abs(x), d)
def trace(seq, init, learn, slip, guess, forget=0., score_from=0):
    k, out = init, []
    for i, a in enumerate(seq):
        if i >= score_from: out.append(k * (1 - slip) + (1 - k) * guess)
        n = k * (1 - slip) if a else k * slip
        o = (1 - k) * guess if a else (1 - k) * (1 - guess)
        k = n / (n + o); k = k * (1 - forget) + (1 - k) * learn
    return out
d = pd.read_csv(os.path.join(H, 'bkt-project', 'data', 'cleaned.csv')).sort_values(['user_id', 'order_id'], kind='mergesort').reset_index(drop=True)
def auc_w(gid, G, y, w):
    pos = np.bincount(gid, weights=w * y, minlength=G); neg = np.bincount(gid, weights=w * (1 - y), minlength=G)
    return float((pos * (np.cumsum(neg) - neg + .5 * neg)).sum() / (pos.sum() * neg.sum()))
def grp(p):
    u, inv = np.unique(p, return_inverse=True); return inv, len(u)
class Block:
    """Row-level predictions of several predictors on the same scored rows."""
    def __init__(s, frame, preds):
        s.y = frame.y.values.astype(float); s.su = pd.factorize(frame.u)[0]; s.n = s.su.max() + 1; s.c = pd.factorize(frame.c)[0]; s.nc = s.c.max() + 1
        s.p = {k: frame[k].values for k in preds}; s.g = {k: grp(v) for k, v in s.p.items()}
        s.idx = [np.where(s.c == i)[0] for i in range(s.nc)]; s.gc = {k: [grp(v[ix]) for ix in s.idx] for k, v in s.p.items()}
    def overall(s, k, w=None):
        w = np.ones(len(s.y)) if w is None else w
        return auc_w(*s.g[k][:1], s.g[k][1], s.y, w)
    def macro(s, k, w=None, keep=None):
        w = np.ones(len(s.y)) if w is None else w
        out = []
        for i, ix in enumerate(s.idx):
            if keep is not None and i not in keep: continue
            yy, ww = s.y[ix], w[ix]
            if (yy * ww).sum() == 0 or ((1 - yy) * ww).sum() == 0: continue
            out.append(auc_w(s.gc[k][i][0], s.gc[k][i][1], yy, ww))
        return float(np.mean(out))
    def boot(s, fn, B=2000, seed=11):
        rng = np.random.default_rng(seed); out = []
        for _ in range(B):
            cnt = np.bincount(rng.integers(0, s.n, s.n), minlength=s.n); out.append(fn(cnt[s.su].astype(float)))
        return np.percentile(out, [2.5, 97.5])
    def cross_share(s):
        pos, neg = s.y.sum(), (1 - s.y).sum(); inside = sum(s.y[ix].sum() * (1 - s.y[ix]).sum() for ix in s.idx)
        return 1 - inside / (pos * neg)
def show(tag, point, lo, hi):
    put(f'{tag}.d', signed(point)); put(f'{tag}.lo', signed(lo)); put(f'{tag}.hi', signed(hi)); print(tag, signed(point), signed(lo), signed(hi))
def check(val, want, what):
    assert hu(val) == want, (what, val, want)
# ---- by-student split, same held-out students as the projects
rng = np.random.default_rng(42); st = np.sort(d.user_id.unique()); test = set(rng.choice(st, size=int(len(st) * .2), replace=False).tolist()); assert len(test) == 832
P0 = pd.read_csv(os.path.join(H, 'bkt-project', 'results', 'params.csv')).set_index('skill_id')
PF = pd.read_csv(os.path.join(H, 'fbkt-project', 'results', 'params_forget.csv')).set_index('skill_id')
trainmean = d[~d.user_id.isin(test)].groupby('skill_id').correct.mean()
rows = []
for (u, c), g in d[d.user_id.isin(test)].groupby(['user_id', 'skill_id'], sort=False):
    if c not in P0.index: continue
    y = g.correct.tolist(); a = P0.loc[c]; b = PF.loc[c]
    pa = trace(y, a.pL0, a.pT, a.pS, a.pG); pb = trace(y, b.pL0, b.pT, b.pS, b.pG, b.pF)
    rows += [(u, c, yy, x1, x2, trainmean[c]) for yy, x1, x2 in zip(y, pa, pb)]
S = pd.DataFrame(rows, columns=['u', 'c', 'y', 'basic', 'forget', 'mean']); assert len(S) == 58138
BS = Block(S, ['basic', 'forget', 'mean'])
check(BS.overall('mean'), '0.6180', 'mean s'); check(BS.overall('basic'), '0.7257', 'basic s'); check(BS.overall('forget'), '0.7319', 'forget s')
check(BS.macro('basic'), '0.6468', 'basic m'); check(BS.macro('forget'), '0.6569', 'forget m')
lo, hi = BS.boot(lambda w: BS.overall('forget', w) - BS.overall('basic', w)); show('f', BS.overall('forget') - BS.overall('basic'), lo, hi)
lo, hi = BS.boot(lambda w: BS.macro('forget', w) - BS.macro('basic', w), B=500); show('f.m', BS.macro('forget') - BS.macro('basic'), lo, hi)
# ---- by-time split
n = d.groupby('user_id').user_id.transform('size'); pos = d.groupby('user_id').cumcount(); d['fut'] = pos >= np.maximum(1, np.floor(n * .7)).astype(int)
PT = pd.read_csv(os.path.join(H, 'ibkt-project', 'results', 'params_temporal.csv')).set_index('skill_id')
MU = pd.read_csv(os.path.join(H, 'ibkt-project', 'results', 'student_multipliers.csv')).set_index('user_id')
PS = pd.read_csv(os.path.join(H, 'sbkt-project', 'results', 'params_students.csv')).set_index('user_id')
pastc = d[~d.fut].groupby('skill_id').correct.mean(); pastu = d[~d.fut].groupby('user_id').correct.mean()
rI, rS = [], []
for (u, c), g in d.groupby(['user_id', 'skill_id'], sort=False):
    if c not in PT.index or not g.fut.any(): continue
    y = g.correct.tolist(); k = int((~g.fut).sum()); yf = y[k:]; t = PT.loc[c]
    pa = trace(y, t.pL0, t.pT, t.pS, t.pG, score_from=k)
    mL, mT = (MU.loc[u, 'mL0'], MU.loc[u, 'mT']) if u in MU.index else (1., 1.)
    pi = trace(y, float(np.clip(mL * t.pL0, .01, .99)), float(np.clip(mT * t.pT, .005, .95)), t.pS, t.pG, score_from=k)
    rI += [(u, c, yy, x1, x2, pastc[c]) for yy, x1, x2 in zip(yf, pa, pi)]
    if u in PS.index:
        s = PS.loc[u]; ps = trace(y, s.pL0, s.pT, s.pS, s.pG, score_from=k)
        rS += [(u, c, yy, x1, x2, pastc[c], pastu[u], (x1 + x2) / 2) for yy, x1, x2 in zip(yf, pa, ps)]
I = pd.DataFrame(rI, columns=['u', 'c', 'y', 'basic', 'indiv', 'mean']); assert len(I) == 93927
BI = Block(I, ['basic', 'indiv', 'mean'])
check(BI.overall('mean'), '0.6243', 'mean t'); check(BI.overall('basic'), '0.7259', 'basic t'); check(BI.overall('indiv'), '0.7322', 'indiv t')
check(BI.macro('basic'), '0.6487', 'basic tm'); check(BI.macro('indiv'), '0.6701', 'indiv tm')
lo, hi = BI.boot(lambda w: BI.overall('indiv', w) - BI.overall('basic', w)); show('i', BI.overall('indiv') - BI.overall('basic'), lo, hi)
lo, hi = BI.boot(lambda w: BI.macro('indiv', w) - BI.macro('basic', w), B=500); show('i.m', BI.macro('indiv') - BI.macro('basic'), lo, hi)
# ---- by-time split, answers where both Basic BKT and Student-based BKT exist
C = pd.DataFrame(rS, columns=['u', 'c', 'y', 'basic', 'stud', 'mc', 'ms', 'avg']); assert len(C) == 84850
BC = Block(C, ['basic', 'stud', 'mc', 'ms', 'avg'])
keep = {i for i, ix in enumerate(BC.idx) if len(ix) >= 30 and 0 < BC.y[ix].sum() < len(ix)}; assert len(keep) == 92
check(BC.overall('mc'), '0.6253', 'mean c'); check(BC.overall('ms'), '0.6619', 'mean st'); check(BC.overall('basic'), '0.7219', 'basic c'); check(BC.overall('stud'), '0.6961', 'stud c')
check(BC.macro('ms', keep=keep), '0.6533', 'ms m'); check(BC.macro('basic', keep=keep), '0.6486', 'basic cm'); check(BC.macro('stud', keep=keep), '0.6718', 'stud cm')
lo, hi = BC.boot(lambda w: BC.overall('basic', w) - BC.overall('stud', w)); show('s', BC.overall('basic') - BC.overall('stud'), lo, hi)
lo, hi = BC.boot(lambda w: BC.macro('stud', w, keep) - BC.macro('basic', w, keep), B=500); show('s.m', BC.macro('stud', keep=keep) - BC.macro('basic', keep=keep), lo, hi)
lo, hi = BC.boot(lambda w: BC.overall('ms', w) - BC.overall('mc', w)); show('ms', BC.overall('ms') - BC.overall('mc'), lo, hi)
tr = lambda w=None: (BC.overall('basic', w) - BC.overall('mc', w)) - (BC.overall('stud', w) - BC.overall('ms', w))
lo, hi = BC.boot(tr); show('track', tr(), lo, hi)
lo, hi = BC.boot(lambda w: BC.overall('avg', w) - BC.overall('basic', w)); show('avg', BC.overall('avg') - BC.overall('basic'), lo, hi); put('avg.auc', hu(BC.overall('avg')))
# ---- how much of the overall AUC compares answers from different concepts
xs = [BS.cross_share(), BI.cross_share(), BC.cross_share()]; print('cross-concept pairs', xs); assert all(hu(100 * x, 0) == '98' for x in xs); put('cross', '98')
with open(os.path.join(HERE, 'gen_ci.tex'), 'w') as fh:
    for k, v in sorted(V.items()): fh.write(f'\\expandafter\\def\\csname v@{k}\\endcsname{{{v}}}\n')
print(len(V), 'keys; every Table 2 value matched')
