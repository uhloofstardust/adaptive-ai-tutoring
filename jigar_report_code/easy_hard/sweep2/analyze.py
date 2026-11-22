"""Analysis of the full sweep. Reads only out/one, out/arms, out/graph. Writes out/analysis/:
sweep_gen.tex (number keys sw.*), per-setting CSVs, and figs. Printed values are never typed by hand elsewhere.
Everything is under the proposed rule. Grids: see grids.py. Shares always name their grid."""
import glob
import os
import sys

import matplotlib
matplotlib.use('pdf')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import grids as GR

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'analysis')
os.makedirs(OUT, exist_ok=True)
INF = np.inf
V = {}


def put(k, v):
    k = 'sw.' + k
    assert k not in V, k
    V[k] = v


def i_(x): return f'{int(x):,}'
def rhu(x): return int(np.floor(float(x) + .5 + 1e-9))      # round half up, so 82.5 prints as 83 (0.825 is 825 of 1,000)
def f1(x): return '$\\infty$' if x == INF else f'{x:,.1f}'
def f2(x): return f'{x:.2f}'
def f3(x): return f'{x:.3f}'
def med(x):
    if x != x: return 'nan'     # only on a partial run; the final run asserts that none is left
    return 'never' if x == INF else (f'{x:,.0f}' if abs(x - round(x)) < 1e-9 else f'{x:,.1f}')
def pct(a, b): return f'{100 * a / b:.0f}'


# ------------------------------------------------------------------ part A: one concept
A = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(HERE, 'out', 'one', '*.csv')))], ignore_index=True)
A['easy'] = A.easy.replace('inf', INF).astype(float)
A.to_csv(os.path.join(OUT, 'one_concept.csv.gz'), index=False)
assert A.sid.nunique() == len(GR.one_concept())
put('a.width.max', f2((A.best_hi - A.best_lo).max()))
put('a.width.rel', f2(100 * ((A.best_hi - A.best_lo) / A.best).max()))
P = A[A.arm == 'proposed']
B0 = P[(P.speed == 1) & (P.start == .05)]
N = int(len(B0[B0.goal == .9]))
assert N == 912
put('a.n', i_(N)); put('a.ncap', i_(N // 4))


def classify(p):
    if p == 'H': return 'hard only'
    if p == 'E': return 'easy only'
    if p == 'EH': return 'one switch'
    if p.startswith('E'): return 'more changes'
    return 'starts hard, then easy'


for goal, tag in ((.9, 'g9'), (.8, 'g8')):
    g = B0[B0.goal == goal]
    k = g.pattern.map(classify)
    for name, kk in (('one switch', 'eh'), ('more changes', 'multi'), ('hard only', 'h'), ('easy only', 'e'), ('starts hard, then easy', 'he')):
        put(f'a.{tag}.{kk}', i_((k == name).sum()))
    put(f'a.{tag}.starthard', i_(g.hard_start.sum()))
    put(f'a.{tag}.easy10', i_((g.easy <= 1.10 * g.best).sum()))
    put(f'a.{tag}.easy25', i_((g.easy > 1.25 * g.best).sum()))
    put(f'a.{tag}.easynever', i_((g.easy == INF).sum()))
    put(f'a.{tag}.hard10', i_((g.hard <= 1.10 * g.best).sum()))
    put(f'a.{tag}.hard2x', i_((g.hard > 2 * g.best).sum()))
    gap = (g.thr_value - g.best_K2e5) / g.best_K2e5
    put(f'a.{tag}.thr1', i_((gap <= .01).sum()))
    put(f'a.{tag}.thrmax', f1(100 * gap.max()))
    put(f'a.{tag}.best.lo', f1(g.best.min())); put(f'a.{tag}.best.hi', f1(g.best.max()))
    put(f'a.{tag}.right.lo', i_(rhu(100 * g.right.min()))); put(f'a.{tag}.right.hi', i_(rhu(100 * g.right.max())))
    lt, eq = g[g.bH < g.f], g[g.bH == g.f]
    put(f'a.{tag}.lt.n', i_(len(lt))); put(f'a.{tag}.eq.n', i_(len(eq)))
    put(f'a.{tag}.lt.startE', i_((lt.hard_start == 0).sum())); put(f'a.{tag}.eq.startE', i_((eq.hard_start == 0).sum()))
    put(f'a.{tag}.lt.easyopt', i_((lt.pattern == 'E').sum()))
    put(f'a.{tag}.lt.hard10', i_((lt.hard <= 1.10 * lt.best).sum()))
    put(f'a.{tag}.lt.starthard', i_(lt.hard_start.sum())); put(f'a.{tag}.eq.starthard', i_(eq.hard_start.sum()))
    for c, g2 in g.groupby('c'):
        t = f'{tag}.c{int(round(c * 100))}'
        put(f'a.{t}.n', i_(len(g2)))
        put(f'a.{t}.best', f1(g2.best.median()))
        put(f'a.{t}.thr', f2(g2.thr_best.median()))
        put(f'a.{t}.thrlo', f2(g2.thr_best.min())); put(f'a.{t}.thrhi', f2(g2.thr_best.max()))
        put(f'a.{t}.startE', i_((g2.hard_start == 0).sum()))
        put(f'a.{t}.easy10', i_((g2.easy <= 1.10 * g2.best).sum()))
        put(f'a.{t}.easy25', i_((g2.easy > 1.25 * g2.best).sum()))
        put(f'a.{t}.easyfin', i_((g2.easy < INF).sum()))
        put(f'a.{t}.hard10', i_((g2.hard <= 1.10 * g2.best).sum()))
        put(f'a.{t}.eh', i_((g2.pattern == 'EH').sum()))
        put(f'a.{t}.thr1', i_((((g2.thr_value - g2.best_K2e5) / g2.best_K2e5) <= .01).sum()))
    # by factor
    for b, g2 in lt.groupby('bH'):
        put(f'a.{tag}.bh{int(round(b * 100)):02d}.hard10', i_((g2.hard <= 1.10 * g2.best).sum()))
        put(f'a.{tag}.bh{int(round(b * 100)):02d}.n', i_(len(g2)))
        put(f'a.{tag}.bh{int(round(b * 100)):02d}.thr', f2(g2.thr_best.median()))
    put(f'a.{tag}.eq.hard10', i_((eq.hard <= 1.10 * eq.best).sum()))
    put(f'a.{tag}.eq.thr', f2(eq.thr_best.median()))
    # does the no-cap easy gap depend on g?
    nc = g[(g.c == 1) & (g.bH < g.f)]
    for gg, g2 in nc.groupby('g'):
        put(f'a.{tag}.nc.g{int(round(gg * 100))}.easy25', i_((g2.easy > 1.25 * g2.best).sum()))
        put(f'a.{tag}.nc.g{int(round(gg * 100))}.easy10', i_((g2.easy <= 1.10 * g2.best).sum()))
        put(f'a.{tag}.nc.g{int(round(gg * 100))}.n', i_(len(g2)))
ab = A[(A.arm == 'bH_above_f') & (A.speed == 1) & (A.start == .05)]
for goal, tag in ((.9, 'g9'), (.8, 'g8')):
    g = ab[ab.goal == goal]
    put(f'a.{tag}.gt.n', i_(len(g))); put(f'a.{tag}.gt.startH', i_(g.hard_start.sum()))
    put(f'a.{tag}.gt.hard10', i_((g.hard <= 1.10 * g.best).sum()))
# start and speed, start-easy counts per cap
for goal, tag in ((.9, 'g9'), (.8, 'g8')):
    for sp, tsp in ((1., 's100'), (.5, 's50'), (.25, 's25')):
        for st, tst in ((.05, 'm05'), (.3, 'm30'), (.65, 'm65')):
            for c in GR.CAPS:
                g = P[(P.goal == goal) & (P.speed == sp) & (P.start == st) & (P.c == c)]
                t = f'{tag}.{tsp}.{tst}.c{int(round(c * 100))}'
                put(f'a.{t}.startE', i_((g.hard_start == 0).sum()))
                g3 = g[g.bH < g.f]
                put(f'a.{t}.lt.startE', i_((g3.hard_start == 0).sum()))
for sp, tsp in ((1., 's100'), (.5, 's50'), (.25, 's25')):
    for c in GR.CAPS:
        g = P[(P.goal == .9) & (P.speed == sp) & (P.start == .05) & (P.c == c)]
        put(f'a.{tsp}.c{int(round(c * 100))}.best', f1(g.best.median()))
# hard only within 10% with bH < f, and settings at or above the published 62%, at each start and speed, goal .9
PUB = .62
for sp, tsp in ((1., 's100'), (.5, 's50'), (.25, 's25')):
    for st, tst in ((.05, 'm05'), (.3, 'm30'), (.65, 'm65')):
        g = P[(P.goal == .9) & (P.speed == sp) & (P.start == st)]
        lt = g[g.bH < g.f]
        put(f'a.g9.lt.hard10.{tst}.{tsp}', i_((lt.hard <= 1.10 * lt.best).sum()))
        put(f'a.g9.right62.{tst}.{tsp}', i_((g.right >= PUB).sum()))
        put(f'a.g9.right.lo.{tst}.{tsp}', i_(rhu(100 * g.right.min()))); put(f'a.g9.right.hi.{tst}.{tsp}', i_(rhu(100 * g.right.max())))
g = P[(P.goal == .9) & (P.start == .05)]
assert (g.right < PUB).all() and (g[g.bH < g.f].hard > 1.10 * g[g.bH < g.f].best).all()
put('a.g9.right.hi.m05.any', i_(rhu(100 * g.right.max())))
# no cap, bH < f, goal .9: easy only within 10% by g and J (15 settings per cell)
nc = B0[(B0.goal == .9) & (B0.c == 1) & (B0.bH < B0.f)]
for (gg, jj), g2 in nc.groupby(['g', 'J']):
    put(f'a.g9.nc.g{int(round(gg * 100))}.J{int(round(jj * 100))}.easy10', i_((g2.easy <= 1.10 * g2.best).sum()))
    put(f'a.g9.nc.g{int(round(gg * 100))}.J{int(round(jj * 100))}.n', i_(len(g2)))
# with bH = f, settings starting hard per cap, goal .9
for c, g2 in B0[(B0.goal == .9) & (B0.bH == B0.f)].groupby('c'):
    put(f'a.g9.eq.c{int(round(c * 100))}.starthard', i_(g2.hard_start.sum()))
    put(f'a.g9.eq.c{int(round(c * 100))}.n', i_(len(g2)))
# on the grid, bH < f always means bH at most f/2
assert abs((B0[B0.bH < B0.f].bH / B0[B0.bH < B0.f].f).max() - .5) < 1e-12
# labeled rows at goal .9, start .05, speed 1
lab = A[(A.goal == .9) & (A.speed == 1) & (A.start == .05)]
for _, r in lab[lab.arm == 'slow_row'].iterrows():
    t = f"slow.b{int(round(r.bH * 100)):02d}.c{int(round(r.c * 100))}"
    put(f'a.{t}.best', f1(r.best)); put(f'a.{t}.easy', 'never' if r.easy == INF else f1(r.easy)); put(f'a.{t}.hard', f1(r.hard)); put(f'a.{t}.thr', f2(r.thr_best))
    put(f'a.{t}.pat', r.pattern)
for _, r in lab[lab.arm == 'cap_table'].iterrows():
    t = f"cap.c{int(round(r.c * 100))}"
    put(f'a.{t}.best', f1(r.best)); put(f'a.{t}.thr', f2(r.thr_best)); put(f'a.{t}.right', i_(rhu(100 * r.right)))
for _, r in lab[lab.arm == 'J1'].iterrows():
    t = f"J1.b{int(round(r.bH * 100)):02d}.c{int(round(r.c * 100))}"
    put(f'a.{t}.best', f1(r.best)); put(f'a.{t}.thr', f2(r.thr_best))
    put(f'a.{t}.easy', 'never' if r.easy == INF else f1(r.easy)); put(f'a.{t}.hard', f1(r.hard))
base = lab[(lab.arm == 'proposed') & (lab.g == .45) & (lab.J == .9) & (lab.f == .1) & (lab.bH == 0)]
for _, r in base.iterrows():
    t = f"base.c{int(round(r.c * 100))}"
    put(f'a.{t}.best', f1(r.best)); put(f'a.{t}.thr', f2(r.thr_best)); put(f'a.{t}.right', i_(rhu(100 * r.right)))
    put(f'a.{t}.easy', 'never' if r.easy == INF else f1(r.easy)); put(f'a.{t}.hard', f1(r.hard))


# the two labeled rows of the table with bH at or above f, g .45, J .9, no cap
for tag, arm, f_, b_ in (('eq', 'proposed', .10, .10), ('gt', 'bH_above_f', .05, .10)):
    r = lab[(lab.arm == arm) & (lab.g == .45) & (lab.J == .9) & (lab.f == f_) & (lab.bH == b_) & (lab.c == 1)]
    assert len(r) == 1
    r = r.iloc[0]
    t = f'{tag}.f{int(round(f_ * 100)):02d}.b{int(round(b_ * 100)):02d}.c100'
    put(f'a.{t}.best', f1(r.best)); put(f'a.{t}.easy', 'never' if r.easy == INF else f1(r.easy)); put(f'a.{t}.hard', f1(r.hard))


# one question, no simulation: settings where hard gains more than easy at every level, the count Figure 2's part prints on this grid
LV = np.round(np.arange(.01, .95, .005), 3)
def _hard_every_level(r):
    sE, sH = LV ** 1.24, LV ** 1.96
    up = lambda x: np.minimum(np.maximum(LV, r.c), LV + x * np.maximum(0, 1 - LV / r.c)) - LV
    return ((sH * r.J + (1 - sH) * r.bH) * (1 - LV) > sE * up(r.g) + (1 - sE) * up(r.f)).all()
_hits = [r for r in B0[B0.goal == .9].itertuples() if _hard_every_level(r)]
assert all(r.bH == r.f for r in _hits)
put('a.always.hits', i_(len(_hits)))


# ------------------------------------------------------------------ graph shards
def load_part(part, cells):
    fs = sorted(glob.glob(os.path.join(HERE, 'out', part, '*.csv.gz')))
    d = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
    C = pd.DataFrame(cells).set_index('sid')
    for k in C.columns:
        d[k] = d.sid.map(C[k])
    d['tc'] = d.t_closure.fillna(INF)
    d['te'] = d.t_end.fillna(INF)
    return d, len(fs)


def summarize(d):
    rows = []
    for (sid, tutor, plan), g in d.groupby(['sid', 'tutor', 'plan'], sort=False):
        x = g.iloc[0]
        q = np.sort(g.tc.values)
        n = len(q)
        rows.append(dict(sid=sid, tutor=tutor, plan=plan, arm=x.arm, g=x.g, J=x.J, f=x.f, bH=x.bH, c=x.c, speed=x.get('speed', 1.), m0=x.get('m0', .05),
                         thr=x.thr, n=n, med=np.median(q), q1=np.percentile(q, 25, method='lower'), q3=np.percentile(q, 75, method='higher'), reach=np.mean(q < INF), false_mean=g.false.mean(),
                         false_sd=g.false.std(ddof=0), false_any=(g.false > 0).mean(), never=np.mean(q == INF), asked=np.median(g.asked), easy_share=g.easy.sum() / max(g.asked.sum(), 1),
                         right_share=g.right.sum() / max(g.asked.sum(), 1)))
    return pd.DataFrame(rows)


cells_g = GR.graph()
D, nshards = load_part('graph', cells_g)
print('graph shards', nshards, 'of', len(cells_g), flush=True)
SG = summarize(D)
SG.to_csv(os.path.join(OUT, 'graph_summary.csv.gz'), index=False)
put('g.nshards', i_(nshards))
J_ = SG[SG.arm == 'joint']
Ns = J_.sid.nunique()
put('g.n', i_(Ns))


def pivot(tutor, value='med', sg=J_):
    return sg[sg.tutor == tutor].pivot(index='sid', columns='plan', values=value)


PT = pivot('path')
meta = J_.drop_duplicates('sid').set_index('sid')[['g', 'J', 'f', 'bH', 'c']]
PT = PT.join(meta)
ANS = ['random', 'easyfirst', 'e3h', 'k2', 'k4', 'k8', 'k12', 'k16']   # plans that use only answers
ALL = ANS + ['easy', 'hard', 'switch', 'tuned']


def paired_counts(d, plan_a, plan_b, tutor='path'):
    """per setting, students faster and slower under plan_a than plan_b, same seeds, closure measure."""
    a = d[(d.tutor == tutor) & (d.plan == plan_a)].set_index(['sid', 'seed']).tc
    b = d[(d.tutor == tutor) & (d.plan == plan_b)].set_index(['sid', 'seed']).tc
    j = pd.concat([a.rename('a'), b.rename('b')], axis=1, join='inner')
    return pd.DataFrame({'w': (j.a < j.b).groupby('sid').sum(), 'l': (j.a > j.b).groupby('sid').sum()})


JJ = D[D.arm == 'joint']
# who is fastest among all plans
best = PT[ALL].min(axis=1)
for pl in ALL:
    put(f'g.best.{pl}', i_((PT[pl] <= best).sum()))
bestA = PT[ANS].min(axis=1)
for pl in ANS:
    put(f'g.bestA.{pl}', i_((PT[pl] <= bestA).sum()))
for pl in ALL:
    put(f'g.med.{pl}', med(PT[pl].median()))
    put(f'g.never.{pl}', i_((PT[pl] == INF).sum()))
# easy first vs random etc, overall and by factor
for pa, tag in (('easyfirst', 'ef'), ('e3h', 'e3'), ('k2', 'k2'), ('k4', 'k4'), ('k8', 'k8'), ('k12', 'k12'), ('k16', 'k16')):
    pc = paired_counts(JJ, pa, 'random').join(meta)
    wins = pc.w > pc.l
    put(f'g.{tag}.wins', i_(wins.sum()))
    put(f'g.{tag}.medwins', i_((PT[pa] < PT['random']).sum()))
    for b in (0., .02, .05):
        put(f'g.{tag}.b{int(b * 100):02d}.wins', i_(wins[pc.bH == b].sum()))
    for c in GR.CAPS:
        put(f'g.{tag}.c{int(round(c * 100))}.wins', i_(wins[pc.c == c].sum()))
    for g_ in GR.GS:
        put(f'g.{tag}.g{int(round(g_ * 100))}.wins', i_(wins[pc.g == g_].sum()))
    for f_ in (.05, .10, .20):
        put(f'g.{tag}.f{int(round(f_ * 100)):02d}.wins', i_(wins[pc.f == f_].sum()))
# hard only
for b in (0., .02, .05):
    x = PT[PT.bH == b]
    put(f'g.hard.b{int(b * 100):02d}.n', i_(len(x)))
    put(f'g.hard.b{int(b * 100):02d}.never', i_((x.hard == INF).sum()))
    put(f'g.hard.b{int(b * 100):02d}.tuned10', i_((x.hard <= 1.1 * x.tuned).sum()))
    put(f'g.hard.b{int(b * 100):02d}.beats', i_((x.hard < x.tuned).sum()))
    if b != 0:
        assert (x[x.hard < x.tuned].bH == x[x.hard < x.tuned].f).all()      # hard only beats the tuned switch only at bH = f
    put(f'g.hard.b{int(b * 100):02d}.med', med(x.hard.median()))
    put(f'g.tuned.b{int(b * 100):02d}.med', med(x.tuned.median()))
    put(f'g.random.b{int(b * 100):02d}.med', med(x.random.median()))
    put(f'g.easyfirst.b{int(b * 100):02d}.med', med(x.easyfirst.median()))
# easy only
for c in GR.CAPS:
    x = PT[PT.c == c]
    t = f'c{int(round(c * 100))}'
    put(f'g.easy.{t}.n', i_(len(x)))
    put(f'g.easy.{t}.never', i_((x.easy == INF).sum()))
    put(f'g.easy.{t}.25', i_((x.easy > 1.25 * x.tuned).sum()))
    put(f'g.easy.{t}.10', i_((x.easy <= 1.10 * x.tuned).sum()))
    for pl in ('random', 'switch', 'tuned', 'easyfirst', 'e3h', 'k4', 'k8', 'k16', 'hard', 'easy'):
        put(f'g.{pl}.{t}.med', med(x[pl].median()))
# tuned against fixed
gap = PT.switch - PT.tuned
rel = gap / PT.tuned
put('g.fix.gapmed', med(gap[np.isfinite(gap)].median()))
put('g.fix.gapmax', med(gap[np.isfinite(gap)].max()))
put('g.fix.rel10', i_((rel > .10).sum()))
put('g.fix.rel25', i_((rel > .25).sum()))
put('g.fix.relmax', i_(rhu(100 * rel[np.isfinite(rel)].max())))
put('g.fix.worse', i_((gap < 0).sum()))
pc_ = paired_counts(JJ, 'easyfirst', 'random').join(meta)
loss = pc_[pc_.w < pc_.l]
assert (loss.f == .05).all()
put('g.ef.f05.n', i_((pc_.f == .05).sum()))
put('g.ef.loss', i_(len(loss))); put('g.ef.loss.f05', i_((loss.f == .05).sum()))
put('g.ef.loss.b00', i_((loss.bH == 0).sum())); put('g.ef.tie', i_((pc_.w == pc_.l).sum()))
thrs = J_[(J_.tutor == 'path') & (J_.plan == 'tuned')].set_index('sid').thr.astype(float)
# the tuned level sits on a short list of levels: how many settings pick each end of it
put('g.thr.level.lo', f2(min(GR.THRS))); put('g.thr.level.hi', f2(max(GR.THRS)))
put('g.thr.atlo', i_((thrs == min(GR.THRS)).sum())); put('g.thr.athi', i_((thrs == max(GR.THRS)).sum()))
for c in GR.CAPS:
    put(f'g.thr.c{int(round(c * 100))}.nlevels', i_(sum(t < c for t in GR.THRS)))
x = PT[(PT.bH == .05) & (PT.hard < PT.tuned)]
assert (x.f == .05).all()
put('g.hard.b05.beats.thrlo', i_((thrs[x.index] == min(GR.THRS)).sum()))
for c in GR.CAPS:
    th = thrs[meta.c == c]
    t = f'c{int(round(c * 100))}'
    put(f'g.thr.{t}.lo', f2(th.min())); put(f'g.thr.{t}.med', f2(th.median())); put(f'g.thr.{t}.hi', f2(th.max()))
for b in (0., .02, .05):
    th = thrs[meta.bH == b]
    put(f'g.thr.b{int(b * 100):02d}.med', f2(th.median()))
# the chain is the same plan order across factors?
order_same = ((PT.tuned <= PT.switch) & (PT.switch <= PT.random)).sum()
put('g.order.tsr', i_(order_same))
put('g.switch.beats.random', i_((PT.switch < PT.random).sum()))
put('g.tuned.beats.random', i_((PT.tuned < PT.random).sum()))
put('g.ef.beats.random', i_((PT.easyfirst < PT.random).sum()))
# whole graph tutor
BF = pivot('bfs').join(meta)
put('g.bfs.ratio.lo', f1((BF.random / PT.random).min())); put('g.bfs.ratio.hi', f1((BF.random / PT.random).max())); put('g.bfs.ratio.med', f1((BF.random / PT.random).median()))
# CurriculumTutor
CT = J_[J_.tutor == 'ct']
CTR = CT[CT.plan == 'random'].set_index('sid').join(meta[[]])
assert (CTR.n == 1000).all()
for c in GR.CAPS:
    x = CTR[CTR.c == c]
    t = f'c{int(round(c * 100))}'
    put(f'g.ct.{t}.med', med(x.med.median())); put(f'g.ct.{t}.medlo', med(x.med.min())); put(f'g.ct.{t}.medhi', med(x.med.max()))
    put(f'g.ct.{t}.false', f2(x.false_mean.mean())); put(f'g.ct.{t}.falselo', f2(x.false_mean.min())); put(f'g.ct.{t}.falsehi', f2(x.false_mean.max()))
    put(f'g.ct.{t}.never', f1(100 * x.never.mean())); put(f'g.ct.{t}.neverhi', f1(100 * x.never.max()))
    for pl in ('easyfirst', 'e3h', 'k16', 'easy', 'hard', 'switch'):
        y = CT[(CT.plan == pl) & (CT.c == c)]
        put(f'g.ct.{pl}.{t}.false', f2(y.false_mean.mean())); put(f'g.ct.{pl}.{t}.falsehi', f2(y.false_mean.max()))
        put(f'g.ct.{pl}.{t}.never', f1(100 * y.never.mean()))
        put(f'g.ct.{pl}.{t}.med', med(y.med.median()))
for name, col, vals in (('g', 'g', GR.GS), ('J', 'J', GR.JS), ('f', 'f', (.05, .10, .20)), ('b', 'bH', (0., .02, .05))):
    for v in vals:
        x = CTR[CTR[col] == v]
        t = f'{name}{int(round(v * 100)):02d}'
        put(f'g.ct.by.{t}.false', f2(x.false_mean.mean()))
        put(f'g.ct.by.{t}.falsec', f2(x[x.c <= .7].false_mean.mean()))
        put(f'g.ct.by.{t}.med', med(x.med.median()))
put('g.ct.lowfalse', i_((CTR[CTR.c > .8].false_mean < .1).sum())); put('g.ct.lowfalse.n', i_(len(CTR[CTR.c > .8])))
put('g.ct.highfalse', i_((CTR[CTR.c <= .7].false_mean >= .1).sum())); put('g.ct.highfalse.n', i_(len(CTR[CTR.c <= .7])))
put('g.ct.falsemax.above', f2(CTR[CTR.c > .8].false_mean.max())); put('g.ct.falsemin.below', f2(CTR[CTR.c <= .7].false_mean.min()))
put('g.ct.falsemax.below', f2(CTR[CTR.c <= .7].false_mean.max()))
# the exception to the line: g = .25 at cap .85
ab_ = CTR[CTR.c > .8]
x = CTR[(CTR.g == .25) & (CTR.c == .85)]
put('g.ct.g25.c85.n', i_(len(x))); put('g.ct.g25.c85.ge10', i_((x.false_mean >= .1).sum())); put('g.ct.g25.c85.mean', f2(x.false_mean.mean()))
put('g.ct.above.ge10', i_((ab_.false_mean >= .1).sum()))
put('g.ct.overlap', i_((ab_.false_mean >= CTR[CTR.c <= .7].false_mean.min()).sum()))
assert (ab_[ab_.g >= .35].false_mean < CTR[CTR.c <= .7].false_mean.min()).all()     # no overlap for g of .35 or more
assert (CTR[(CTR.c == .85) & (CTR.g >= .35)].false_mean.max() < CTR[(CTR.c == .85) & (CTR.g == .25)].false_mean.max())
# what moves false marks: the plan against the factors and the cap
for c in GR.CAPS:
    t = f'c{int(round(c * 100))}'
    x = CTR[CTR.c == c]
    y = CT[(CT.plan == 'easyfirst') & (CT.c == c)]
    fall = x.false_mean.mean() - y.false_mean.mean()
    rng = {k: x.groupby(k).false_mean.mean().max() - x.groupby(k).false_mean.mean().min() for k in ('g', 'J', 'f', 'bH')}
    put(f'g.ct.{t}.fall.ef', f3(fall)); put(f'g.ct.{t}.range.g', f3(rng['g']))
    if c <= .7:
        assert fall > max(rng.values())                 # below the line the plan moves them more than any factor
    else:
        assert rng['g'] == max(rng.values()) and rng['g'] > fall    # above it g moves them most, more than random to all easy first
put('g.ct.capfall', f3(CTR[CTR.c == .6].false_mean.mean() - CTR[CTR.c == 1].false_mean.mean()))
# CurriculumTutor stops by itself: it declares every concept, and it does not reach the budget
rnd_ = D[(D.tutor == 'ct') & (D.plan == 'random')]
assert (rnd_.declared == 40).all() and (rnd_.asked < 2000).all()
assert (rnd_[rnd_.tc == INF].false >= 1).all()
put('g.ct.askedmax', i_(rnd_[rnd_.arm == 'joint'].asked.max()))
easy_ct = JJ[(JJ.tutor == 'ct') & (JJ.plan == 'easy') & (JJ.c == .6)]
put('g.ct.easy.c60.budget', i_(rhu(100 * (easy_ct.asked >= 2000).mean())))
assert (JJ[(JJ.tutor == 'ct') & (JJ.plan == 'easy') & (JJ.c == .7)].asked < 2000).all()
# answers-only plans inside CurriculumTutor against random, same seeds (first 200)
JCT = JJ[JJ.tutor == 'ct']
for pa, tag in (('easyfirst', 'ef'), ('e3h', 'e3'), ('k16', 'k16')):
    pc = paired_counts(JCT, pa, 'random', tutor='ct').join(meta)
    wins = pc.w > pc.l
    put(f'g.ct.{tag}.wins', i_(wins.sum()))
    for c in GR.CAPS:
        put(f'g.ct.{tag}.c{int(round(c * 100))}.wins', i_(wins[pc.c == c].sum()))
    for b in (0., .02, .05):
        put(f'g.ct.{tag}.b{int(b * 100):02d}.wins', i_(wins[pc.bH == b].sum()))
# labeled arms
LAB = SG[SG.arm != 'joint']
for arm, tag in (('bH_eq_f', 'eq'), ('bH_above_f', 'gt'), ('slow_row', 'slow'), ('J1', 'J1'), ('cap_table', 'cap')):
    x = LAB[LAB.arm == arm]
    for sid, y in x.groupby('sid'):
        r = y.iloc[0]
        t = f"{tag}.f{int(round(r.f * 100)):02d}.b{int(round(r.bH * 100)):02d}.c{int(round(r.c * 100))}"
        for pl in ('easy', 'hard', 'random', 'switch', 'tuned', 'easyfirst', 'e3h'):
            z = y[(y.tutor == 'path') & (y.plan == pl)]
            put(f'g.lab.{t}.{pl}', med(z.med.iloc[0]))
        z = y[(y.tutor == 'ct') & (y.plan == 'random')].iloc[0]
        put(f'g.lab.{t}.ct', med(z.med)); put(f'g.lab.{t}.false', f2(z.false_mean)); put(f'g.lab.{t}.never', f1(100 * z.never))
base_g = J_[(J_.g == .45) & (J_.J == .9) & (J_.f == .1) & (J_.bH == 0)]
for c in GR.CAPS:
    y = base_g[base_g.c == c]
    t = f'base.c{int(round(c * 100))}'
    for pl in ('easy', 'hard', 'random', 'switch', 'tuned', 'easyfirst', 'e3h'):
        z = y[(y.tutor == 'path') & (y.plan == pl)]
        put(f'g.{t}.{pl}', med(z.med.iloc[0]))
    z = y[(y.tutor == 'ct') & (y.plan == 'random')].iloc[0]
    put(f'g.{t}.ct', med(z.med)); put(f'g.{t}.false', f2(z.false_mean)); put(f'g.{t}.never', f1(100 * z.never))
    put(f'g.{t}.hard.reach', i_(rhu(100 * y[(y.tutor == 'path') & (y.plan == 'hard')].reach.iloc[0])))
    z = y[(y.tutor == 'ct') & (y.plan == 'easy')].iloc[0]
    put(f'g.{t}.ct.easy.false', f2(z.false_mean)); put(f'g.{t}.ct.easy.declared', 'x')
    V['sw.g.' + t + '.ct.easy.declared'] = f1(z.asked)

# ------------------------------------------------------------------ part C: speed x start arms
cells_a = GR.arms()
DA, na = load_part('arms', cells_a)
assert na == len(cells_a)
SA = summarize(DA)
SA.to_csv(os.path.join(OUT, 'arms_summary.csv.gz'), index=False)
for (b, m0, c, sp), y in SA.groupby(['bH', 'm0', 'c', 'speed']):
    t = f"c.b{int(round(b * 100)):02d}.m{int(round(m0 * 100)):02d}.c{int(round(c * 100))}.s{int(round(sp * 100))}"
    z = y[(y.tutor == 'ct') & (y.plan == 'random')].iloc[0]
    put(f'{t}.med', med(z.med)); put(f'{t}.never', i_(rhu(100 * z.never))); put(f'{t}.false', f2(z.false_mean))
    for pl, tag in (('easyfirst', 'ef'), ('e3h', 'e3')):
        z = y[(y.tutor == 'ct') & (y.plan == pl)].iloc[0]
        put(f'{t}.{tag}.false', f2(z.false_mean))
    for pl in ('tuned', 'switch', 'random', 'easyfirst', 'e3h', 'hard', 'easy'):
        z = y[(y.tutor == 'path') & (y.plan == pl)].iloc[0]
        put(f'{t}.path.{pl}', med(z.med))
    z = y[(y.tutor == 'path') & (y.plan == 'tuned')].iloc[0]
    put(f'{t}.thr', f2(float(z.thr)))
    put(f'{t}.path.hard.reach', i_(rhu(100 * y[(y.tutor == 'path') & (y.plan == 'hard')].reach.iloc[0])))
# caps, of 4, where a plan beats random student by student on the chain, bH = 0, per start and speed
for m0, tm in ((.05, 'm05'), (.3, 'm30'), (.65, 'm65')):
    for sp, ts in ((1., 's100'), (.5, 's50'), (.25, 's25')):
        d_ = DA[(DA.bH == 0) & (DA.m0 == m0) & (DA.speed == sp)]
        for pa, tag in (('easyfirst', 'ef'), ('e3h', 'e3')):
            pc = paired_counts(d_, pa, 'random')
            put(f'c.b00.{tm}.{ts}.{tag}.wins', i_((pc.w > pc.l).sum()))
# the arms' students are seeds 4242 to 5241, so the 200 of Figures 7 and 12 are their first 200
rA_ = DA[(DA.tutor == 'ct') & (DA.plan == 'random') & (DA.bH == 0) & (DA.m0 == .05) & (DA.speed == 1)]
assert rA_.seed.min() == GR.CT1000[0] and rA_.seed.max() == GR.CT1000[-1]
for c, x in rA_.groupby('c'):
    t = f'c.b00.m05.c{int(round(c * 100))}.s100'
    y = x[x.seed < GR.CT1000[0] + 200]
    assert len(x) == 1000 and len(y) == 200
    put(f'{t}.never1', f1(100 * (x.tc == INF).mean())); put(f'{t}.false3', f3(x.false.mean()))
    put(f'{t}.first200.never1', f1(100 * (y.tc == INF).mean())); put(f'{t}.first200.false3', f3(y.false.mean()))
rB_ = D[(D.tutor == 'ct') & (D.plan == 'random') & (D.arm == 'cap_table') & (D.c == .8)]
assert len(rB_) == 1000
put('g.bl.c80.first200.false3', f3(rB_[rB_.seed < GR.CT1000[0] + 200].false.mean())); put('g.bl.c80.false3', f3(rB_.false.mean()))
# CurriculumTutor stops by itself in the arms too
rnd_ = DA[(DA.tutor == 'ct') & (DA.plan == 'random')]
assert (rnd_.declared == 40).all() and (rnd_.asked < 8000).all() and (rnd_[rnd_.tc == INF].false >= 1).all()
put('c.ct.askedmax', i_(rnd_.asked.max()))

# ------------------------------------------------------------------ figure: false marks against the cap, baseline factors, 1,000 students
EB = dict(ecolor='#333333', elinewidth=.7, capsize=2, capthick=.7, zorder=4)
plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'legend.frameon': False, 'pdf.fonttype': 42})
bl = SG[(SG.g == .45) & (SG.J == .9) & (SG.f == .1) & (SG.bH == 0) & (SG.tutor == 'ct') & (SG.plan == 'random')].sort_values('c')
bl = bl[bl.arm.isin(['joint', 'cap_table'])].drop_duplicates('c')
if len(bl) >= 3:
    fig, ax = plt.subplots(figsize=(5.2, 2.7))
    ax.errorbar(bl.c, bl.false_mean, yerr=[np.minimum(bl.false_sd, bl.false_mean), bl.false_sd], fmt='-o', ms=3, color='#D55E00', ecolor='#D55E00', elinewidth=.7, capsize=2, capthick=.7, clip_on=False, zorder=3)
    ax.axvline(.8, ls=':', color='#777777'); ax.text(.83, ax.get_ylim()[1] * .92, 'learned line 0.8', fontsize=7, color='#777777')
    ax.set_xlabel('cap c (1 means no cap)'); ax.set_ylabel('false marks per student\n(mean, $\\pm$SD cut at 0)')
    ax.set_xlim(0, 1.02); ax.set_ylim(bottom=0)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'fs_false_vs_cap.pdf'), metadata={'CreationDate': None}); plt.close(fig)
    for _, r in bl.iterrows():
        put(f'g.bl.c{int(round(r.c * 100))}.false', f2(r.false_mean))

# ------------------------------------------------------------------ controls, read from their logs
import re
tg = open(os.path.join(HERE, 'logs', 'test_graph.log')).read()
m = re.search(r"compared \{'ef': (\d+), 'xt': (\d+), 'sp': (\d+)\} mismatches \{\}", tg)
assert m, 'graph control did not pass'
put('ctl.rows', f'{sum(int(x) for x in m.groups()):,}')
ts = open(os.path.join(HERE, 'logs', 'test_solver.log')).read()
assert 'total bad 0' in ts
nb = int(re.search(r'bracket cells (\d+)', ts).group(1)); ng = int(re.search(r'goal grid cells (\d+)', ts).group(1)); ns = int(re.search(r'speed and start checks (\d+)', ts).group(1))
put('ctl.solver', str(nb + ng + ns))
# the earlier 1,000-student check of speed and start, cell by cell
ref = pd.read_csv(os.path.join(HERE, 'start_speed_1000.csv'))
ctr_ = DA[(DA.tutor == 'ct') & (DA.plan == 'random') & (DA.bH == 0)]
bad = 0
for _, r in ref.iterrows():
    x = ctr_[(ctr_.c == r.c) & (ctr_.speed == r.speed) & (ctr_.m0 == float(r.start))]
    a = (len(x), float(np.median(x.tc)), round(float((x.tc == INF).mean()), 3), round(float(x.false.mean()), 3), float(np.median(x.asked)))
    b = (int(r.n), float(r.closure_median), float(r.never), float(r.wrong_marks), float(r.asked_median))
    bad += a != b
assert bad == 0
put('ctl.speed', str(len(ref)))
part_secs = {n: int(re.search(r'done (\d+) s', open(os.path.join(HERE, 'logs', n + '.log')).read().replace('one concept done', 'done').replace('arms done', 'done').replace('graph done', 'done')).group(1)) for n in ('one', 'arms', 'graph')}
secs = sum(part_secs.values())
put('run.min', i_(rhu(secs / 60)))
# Q10: the 8 other speed and start pairs crossed with the joint grid, at the wall-clock seconds per setting of the arms and of the graph part
cross = 8 * Ns
put('cross.n', i_(cross))
put('cross.hours.lo', i_(rhu(cross * part_secs['arms'] / len(cells_a) / 3600))); put('cross.hours.hi', i_(rhu(cross * part_secs['graph'] / len(cells_g) / 3600)))
# part 6.3: multiple testing on the joint grid, 3 pairwise gaps per setting
put('mult.int', i_(Ns * 3)); put('mult.false', i_(rhu(Ns * 3 * .05)))
# easy questions per concept: all easy first asks them once, and k easy first repeats them when k is larger
import rules as RU  # noqa: E402
n_es = [len(v) for v in RU.ES.values()]
put('es.lo', i_(min(n_es))); put('es.hi', i_(max(n_es))); put('es.mean', f1(float(np.mean(n_es))))
put('n.one', i_(A.sid.nunique())); put('n.graph', i_(len(cells_g))); put('n.arms', i_(len(cells_a)))
put('n.ctstudents', f'{1000:,}')
assert not any(v == 'nan' for v in V.values()), [k for k, v in V.items() if v == 'nan'][:10]
with open(os.path.join(OUT, 'sweep_gen.tex'), 'w') as fh:
    fh.write('% generated by sweep2/analyze.py from out/one, out/graph, out/arms -- do not edit\n')
    for k, v in sorted(V.items()):
        fh.write(f'\\expandafter\\def\\csname v@{k}\\endcsname{{{v}}}\n')
print(len(V), 'keys', flush=True)
