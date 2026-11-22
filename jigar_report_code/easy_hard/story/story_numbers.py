"""Every result the story prints that is not already a sweep key. Reads the study's data, the sweep's raw runs and
summaries, and this folder's many-run file. Writes gen.tex (keys st.*). Asserts guard the statements the text makes in words."""
import glob, json, math, os, statistics, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); U = os.path.dirname(HERE)
D = os.path.join(U, 'repo', 'experiments', 'difficulty'); SW = os.path.join(U, 'sweep2')
sys.path.insert(0, D); sys.path.insert(0, SW)
os.environ.setdefault('NUMBA_CACHE_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), '.numba_cache'))
import numpy as np, pandas as pd
from common import load, group, num, INF, med_reach, paired
import solve_one as SO, grids as GRD, make_single2 as M
V = {}
def put(k, v):
    k = 'st.' + k; assert k not in V, k; V[k] = str(v)
def hu(x, d=0):
    """Round half up, one rounding everywhere in this document."""
    f = 10 ** d; r = math.floor(x * f + .5 + 1e-9) / f
    return f'{r:.{d}f}'
def f1(x): return hu(x, 1)
def f2(x): return hu(x, 2)
def pc(x): return hu(100 * x)
def med(x): return 'never' if x == INF else (f'{x:.0f}' if abs(x - round(x)) < 1e-9 else hu(x, 1))
s_ = lambda m, d: m ** (1 + 1.2 * d)
P_ = lambda m, d: .93 * s_(m, d) + .25 * (1 - s_(m, d))
def easy(m, c=.6, g=.45, f=.10):
    s = s_(m, .2); return s * g * max(0, 1 - m / c) + (1 - s) * f * max(0, 1 - m / c)
def hard(m, J=.9, b=0.):
    s = s_(m, .8); return s * J * (1 - m) + (1 - s) * b * (1 - m)
def root(fn, lo, hi):
    for _ in range(80):
        mid = (lo + hi) / 2
        if fn(mid) > 0: hi = mid
        else: lo = mid
    return (lo + hi) / 2

# ---- one question
put('s.e05', f1(100 * s_(.05, .2))); put('s.h05', f1(100 * s_(.05, .8)))
for m, t in ((.1, 'm10'),):
    put(f'gain.e.{t}', hu(easy(m), 3)); put(f'gain.h.{t}', hu(hard(m), 3))
put('gain.e0', hu(easy(0), 3)); put('gain.e05.c60', hu(easy(.05, .6), 3)); put('gain.e05.none', hu(easy(.05, 1.), 3))
put('gain.e30.c60', hu(easy(.3, .6), 3)); put('gain.e30.none', hu(easy(.3, 1.), 3))
assert abs(easy(.05, .6) - easy(.05, 1.)) < .01 < easy(.3, 1.) - easy(.3, .6) < easy(.5, 1.) - easy(.5, .6)    # 'differs little near the start, increasingly as m rises'
put('gain.ll.e0', hu(P_(0, .2) * .45 + (1 - P_(0, .2)) * .10, 3)); put('gain.ll.h0', hu(P_(0, .8) * .9, 3))
for c, t in ((.6, 'c60'), (.7, 'c70'), (.85, 'c85'), (1., 'none')):
    put(f'cross.{t}', f2(root(lambda m: hard(m) - easy(m, c), .02, .95)))
for b, t in ((.05, 'b05'), (.10, 'b10')):
    put(f'cross.c60.{t}', f2(root(lambda m: hard(m, .9, b) - easy(m, .6), .02, .95)))
assert all(r['hard_always'] == '0' for r in load('single_switch.csv'))

# ---- today
GR = group(load('graph_rows.csv'), 'group', 'rule', 'cpol', 'dpol', 'profile', 'override')
G = lambda r, c, d: GR[('main', r, c, d, 'average', '')]
today = [med_reach(G('current', 'path', d), 't_end')[0] for d in ('random', 'easy', 'hard', 'switch', 'e3h')]
put('today.lo', med(min(today))); put('today.hi', med(max(today)))

# ---- one concept
S = {(r['version'], r['policy']): r for r in load('single_schedule.csv')}
VT = (('capped at 0.6', 'c60'), ('capped at 0.7', 'c70'), ('capped at 0.85', 'c85'), ('no cap', 'none'), ('capped at 0.6, failed hard teaches 0.05', 'c60b'))
for v, t in VT:
    b, fx, e, h = S[(v, 'best switch rule')], S[(v, 'best fixed')], S[(v, 'easy only')], S[(v, 'hard only')]
    put(f't1.{t}.best', f1(float(b['exact_best']))); put(f't1.{t}.sw', f2(float(b['switch_m'])))
    put(f't1.{t}.fix', f1(float(fx['mean_q']))); put(f't1.{t}.k', fx['best_fixed_k'])
    put(f't1.{t}.easy', 'never' if e['exact_easy'] == 'never' else f1(float(e['exact_easy']))); put(f't1.{t}.hard', f1(float(h['exact_hard'])))
put('t1.c60.medq', med(float(S[('capped at 0.6', 'best switch rule')]['median_q']))); put('t1.none.medq', med(float(S[('no cap', 'best switch rule')]['median_q'])))
put('t1.c60.fixgap', pc(float(S[('capped at 0.6', 'best fixed')]['mean_q']) / float(S[('capped at 0.6', 'best switch rule')]['exact_best']) - 1))

# ---- one concept, the sweep's exact grid: the switch, the crossing and the marked-answer rule across settings
OC = pd.read_csv(os.path.join(SW, 'out', 'analysis', 'one_concept.csv.gz'))
OP = OC[(OC.arm == 'proposed') & (OC.speed == 1) & (OC.start == .05) & (OC.goal == .9)].copy(); assert len(OP) == 912
OP['gap'] = (OP.thr_value - OP.best_K2e5) / OP.best_K2e5
sE, sH = OP[OP.hard_start == 0], OP[OP.hard_start == 1]
put('one.startE.n', len(sE)); put('one.startE.thr1', int((sE.gap <= .01).sum())); put('one.startH.n', len(sH))
assert (sH.bH == sH.f).all() and (sH.thr_best == 0).all()                 # 'in the other 47, all with b_H = f, it starts hard'
ltf, eqf = OP[OP.bH < OP.f], OP[OP.bH == OP.f]
assert (ltf.hard_start == 0).all() and (ltf.bH <= ltf.f / 2 + 1e-12).all()   # 'starts easy in all settings with b_H at most f/2'; on this grid b_H < f means that
for col in ('f', 'c', 'g'):
    assert eqf[eqf.hard_start == 0].groupby(col).size().nunique() > 1      # 'at b_H = f it also depends on f, the cap and g'
for t, c_, b_ in (('c60', .6, 0.), ('c70', .7, 0.), ('c85', .85, 0.), ('none', 1., 0.), ('c60b', .6, .05)):
    z = OP[(OP.g == .45) & (OP.J == .9) & (OP.f == .10) & (OP.bH == b_) & (OP.c == c_)].iloc[0]
    assert f2(z.thr_best) == V[f'st.t1.{t}.sw'] and z.gap <= .01           # same level as the study's run; 'within 1% in every row'
    put(f't1.{t}.swq', f1(z.thr_value))
def first_cross(g, J, f, b, c):
    ms = np.linspace(0, .9, 9001)[1:]; se, sh = s_(ms, .2), s_(ms, .8)
    w = (sh * J + (1 - sh) * b) * (1 - ms) > (se * g + (1 - se) * f) * np.maximum(0, 1 - ms / c)
    return ms[w.argmax()] if w.any() else np.nan                           # nan: no crossing below 0.9, which counts as not within
dc = (ltf.thr_best - [first_cross(z.g, z.J, z.f, z.bH, z.c) for z in ltf.itertuples()]).abs()
put('one.cross.w10', int((dc <= .10).sum())); put('one.cross.n', len(ltf))
lvl = np.arange(100) / 100
def hard_all(z):
    pe, ph = P_(lvl, .2), P_(lvl, .8)
    return bool((((ph * z.J + (1 - ph) * z.bH) * (1 - lvl)) > ((pe * z.g + (1 - pe) * z.f) * np.maximum(0, 1 - lvl / z.c))).all())
HA = OP.apply(hard_all, axis=1); put('ll.allhard', int(HA.sum()))
assert HA[(OP.g == .45) & (OP.J == .9) & (OP.f == .10) & (OP.bH == 0)].all() and not HA.all()    # 'at the baseline values hard leads at every level'

# ---- different students: many runs per student
PO = {f"{float(r.hi):g}": r for _, r in pd.read_csv(os.path.join(HERE, 'pooled.csv')).iterrows()}
PS = pd.read_csv(os.path.join(HERE, 'pooled_students.csv'))
het = [float(r['best_switch']) for r in load('single_hetero.csv')]
put('het.lo', f2(min(het))); put('het.hi', f2(max(het)))
chance = []
for hi, t in (('0.3', 's30'), ('0.6', 's60'), ('0.85', 's85')):
    r = PO[hi]; k = int(r.k)
    put(f'f4.{t}.k', k); put(f'f4.{t}.floor', k + 1); assert r.f_min == k + 1
    for n in 'ofa':
        put(f'f4.{t}.{n}.med', med(r[f'{n}_med'])); put(f'f4.{t}.{n}.p95', med(r[f'{n}_p95'])); put(f'f4.{t}.{n}.mean', f2(r[f'{n}_mean'])); put(f'f4.{t}.{n}.sd', f2(r[f'{n}_sd']))
        chance.append(r[f'{n}_chance'])
    put(f'f4.{t}.f.low', f2(r.f_mean - r.f_sd))
    for g_ in ('fo', 'af'):
        put(f'f4.{t}.{g_}.d', f2(r[f'{g_}_d'])); put(f'f4.{t}.{g_}.lo', f2(r[f'{g_}_lo'])); put(f'f4.{t}.{g_}.hi', f2(r[f'{g_}_hi']))
    nslow = int(round(r.fo_slower * 400)); put(f'f4.{t}.fo.nslower', nslow); assert nslow >= 398   # 'almost every student is slower on average'
    put(f'f4.{t}.fo.pct', pc(r.fo_d / r.o_mean)); assert r.f_med - r.o_med <= 1                     # 'comes close in medians'
    y = PS[PS.hi == float(hi)].copy(); y['gap'] = y.f - y.o; put(f'f4.{t}.fo.medloss', f2(y.gap.median()))
    q = y.m0.quantile([1 / 3, 2 / 3]).values; tl, tm, th = y[y.m0 <= q[0]].gap.mean(), y[(y.m0 > q[0]) & (y.m0 <= q[1])].gap.mean(), y[y.m0 > q[1]].gap.mean()
    put(f'f4.{t}.third.low', f2(tl)); put(f'f4.{t}.third.high', f2(th))
    q = y.l.quantile([1 / 3, 2 / 3]).values; ts, tf = y[y.l <= q[0]].gap.mean(), y[y.l > q[1]].gap.mean()
    put(f'f4.{t}.third.slow', f2(ts)); put(f'f4.{t}.third.fast', f2(tf)); assert ts > tf            # 'falls most on slow learners at every range'
    assert (tl > th) if t == 's30' else (th > tm)                                                   # 'low starters lose most at the narrowest; at wider ranges high starters lose too'
    top = y[y.gap >= y.gap.quantile(.95)]; assert top.l.median() < y.l.median() and top.m0.median() < y.m0.median()   # the worst losses: slow, low start, so sent to hard before ready
    if t == 's85':
        ab = y[y.m0 >= y.c]; put('f4.abovecap.n', len(ab)); put('f4.abovecap.loss', f2(ab.gap.mean())); assert ab.gap.mean() > y.gap.mean()
put('f4.chance.lo', pc(min(chance))); put('f4.chance.hi', pc(max(chance))); put('f4.students.lo', pc(1 - max(chance))); put('f4.students.hi', pc(1 - min(chance)))
assert hu(float(PO['0.85'].af_lo), 2).startswith('-')    # 'level at the widest range'
put('f4.fo.max', hu(max(float(PO[h_].fo_max) for h_ in PO)))
s = 0.4 ** 1.96; put('wait.s', hu(s, 3)); put('wait.mean', f1(1 / s)); put('wait.sd', f1(math.sqrt(1 - s) / s))
te, _ = M.pop(400, 900, .3); put('fastover', sum(st_[2] * .45 > st_[0] for st_ in te)); put('J.below', sum(st_[1] < .9 for st_ in te))

# ---- the graph
cur = json.load(open(os.path.join(D, 'data', 'curricula', 'layered_40.json')))
pre = {p for c in cur['concepts'] for p in c['prereqs']}; put('sinks', sum(c['cid'] not in pre for c in cur['concepts']))
import harness as H
ds = {k: [q.difficulty for c in H.CUR.concepts.values() for q in c.questions if H.LABEL[q.qid] == k] for k in 'EH'}
for k, t in (('E', 'easy'), ('H', 'hard')):
    put(f'd.{t}.lo', f2(min(ds[k]))); put(f'd.{t}.hi', f2(max(ds[k]))); put(f'd.{t}.mean', f2(sum(ds[k]) / len(ds[k])))
E = group(load('ef_rows.csv'), 'rule', 'cpol', 'dpol'); XG = group(load('extra_rows.csv'), 'group', 'rule', 'cpol', 'dpol')
RT = (('current', 'today'), ('nocap_bH0', 'none'), ('c60_bH0', 'c60'), ('c70_bH0', 'c70'), ('c85_bH0', 'c85'))
for r, t in RT:
    for d in ('easy', 'hard', 'switch'):
        put(f't2.{t}.{d}', med(med_reach(G(r, 'path', d), 't_end')[0]))
    put(f't2.{t}.hard.reach', pc(med_reach(G(r, 'path', 'hard'), 't_end')[1]))
T2 = {t: {d: med_reach(G(r, 'path', d), 't_end')[0] for d in ('easy', 'switch')} for r, t in RT}
assert T2['today']['switch'] >= T2['today']['easy']                        # 'no faster today'
assert 1 < T2['none']['easy'] / T2['none']['switch'] < 1.10                # 'modestly faster with no cap'
assert T2['c60']['easy'] == INF and T2['c70']['easy'] == INF and T2['c85']['easy'] / T2['c85']['switch'] > 1.25    # 'much faster at caps of 0.85 or below'
assert all(float(V[f'st.t2.{t}.hard.reach']) == 2 for t in ('none', 'c60', 'c70', 'c85'))    # caption: 'under hard only with b_H = 0, 2% of students do'
def r500(rows):
    v = [num(z['t_closure']) for z in rows]; return sum(x <= 500 for x in v) / len(v)
for r, t in RT:
    for pl, get in (('random', lambda: E[(r, 'ct', 'random')]), ('easyfirst', lambda: E[(r, 'ct', 'easyfirst')]), ('e3h', lambda: XG[('newpol', r, 'ct', 'e3h')])):
        put(f'ctq.{t}.{pl}.med', med(med_reach(get(), 't_closure')[0])); put(f'ctq.{t}.{pl}.r500', pc(r500(get())))
    put(f'f7.{t}.whole', med(med_reach(E[(r, 'bfs', 'random')], 't_closure')[0]))
    put(f'f7.{t}.chain', med(med_reach(E[(r, 'path', 'random')], 't_closure')[0]))
VE = ('nocap_bH0', 'nocap_bH02', 'nocap_bH05', 'c60_bH0', 'c70_bH0', 'c85_bH0', 'nocap_J60', 'c60_J60')
put('nvers', len(VE))
efw = e3w = 0
for r in VE:
    w, l, *_ = paired(E[(r, 'path', 'easyfirst')], E[(r, 'path', 'random')], 't_end'); efw += w > l
    w, l, *_ = paired(XG[('newpol', r, 'path', 'e3h')], E[(r, 'path', 'random')], 't_end'); e3w += w > l
assert efw == 8 and e3w == 8
for r, t in (('nocap_bH0', 'none'), ('c60_bH0', 'c60')):
    put(f'ef.{t}.rnd', med(med_reach(E[(r, 'path', 'random')], 't_end')[0])); put(f'ef.{t}.ef', med(med_reach(E[(r, 'path', 'easyfirst')], 't_end')[0])); put(f'ef.{t}.e3', med(med_reach(XG[('newpol', r, 'path', 'e3h')], 't_end')[0]))
    for k in (2, 4, 8, 16):
        put(f'k.{t}.k{k}', med(med_reach(E[(r, 'path', f'k{k}')], 't_end')[0]))

# ---- the mastery test
cu = {r['cap']: r for r in load('single_cusum.csv')}
for c, t in (('0.6', 'c60'), ('0.7', 'c70')):
    put(f'cu.{t}.b', f1(100 * float(cu[c]['blind_false_rate']))); put(f'cu.{t}.a', f1(100 * float(cu[c]['aware_false_rate'])))
up, dn = math.log(.9 / .25), math.log(.1 / .75); h = math.log(1 / .0004)
put('cusum.up', f2(up)); put('cusum.dn', f2(-dn)); put('cusum.h', f2(h)); put('cusum.need', math.ceil(h / up)); assert 6 * up < h < 7 * up
put('cusum.max3', f2(3 * up)); put('cusum.max5', f2(5 * up)); assert 5 * up < h                # 'easy questions alone add at most ..., both below'
put('cusum.more.e3', math.ceil((h - 3 * up) / up)); put('cusum.more.ef', math.ceil((h - 5 * up) / up))
assert 5 * up + dn + 3 * up > h                                            # 'or more with wrong answers in between'
put('Pc60', pc(P_(.6, .2))); put('Pc70', pc(P_(.7, .2)))
SG = pd.read_csv(os.path.join(SW, 'out', 'analysis', 'graph_summary.csv.gz')); J = SG[SG.arm == 'joint']; CT = J[J.tutor == 'ct']
base = CT[(CT.g == .45) & (CT.J == .9) & (CT.f == .1) & (CT.bH == 0)]
fd = lambda z: float(z.get('false_decl@2000') or z.get('false_decl'))
pol = {'easyfirst': lambda r: E[(r, 'ct', 'easyfirst')], 'e3h': lambda r: XG[('newpol', r, 'ct', 'e3h')], 'k16': lambda r: E[(r, 'ct', 'k16')]}
for r, c, t in (('nocap_bH0', 1., 'none'), ('c60_bH0', .6, 'c60'), ('c70_bH0', .7, 'c70'), ('c85_bH0', .85, 'c85')):
    z = base[(base.c == c) & (base.plan == 'random')].iloc[0]; assert z.n == 1000
    put(f'ct.{t}.random.any', pc(z.false_any)); put(f'ct.{t}.random.chain', pc(z.reach)); put(f'ct.{t}.random.never', pc(z.never))
    for p, g_ in pol.items():
        x = g_(r); n = len(x)
        put(f'ct.{t}.{p}.any', pc(sum(fd(y) > 0 for y in x) / n)); put(f'ct.{t}.{p}.chain', pc(sum(num(y['t_closure']) < INF for y in x) / n))
# every student who never learns the chain under random has a false mark
cells = {tuple(c[k] for k in 'g J f bH c arm'.split()): c['sid'] for c in GRD.graph()}
sid60 = cells[(.45, .9, .10, 0., .6, 'joint')]
rawall60 = pd.read_csv(os.path.join(SW, 'out', 'graph', f's{sid60:05d}.csv.gz')); raw60 = rawall60[(rawall60.tutor == 'ct') & (rawall60.plan == 'random')]
nev = raw60[raw60.t_closure.isna()]; assert len(raw60) == 1000 and (nev.false >= 1).all(); put('stuck.n', len(nev))
# a real hard solve lifts the student past the line: the sweep's own run, logged. At b_H = 0 a hard answer raises m only when really solved.
import rules as RU
class LogLearner(RU.FactorLearner):
    solved = cross = 0
    def answer(self, q, now_h):
        res = super().answer(q, now_h)
        if RU.H.LABEL[q.qid] == 'H' and res['mastery_before'] < RU.H.LEARNED and res['mastery_after'] > res['mastery_before']:
            LogLearner.solved += 1; LogLearner.cross += res['mastery_after'] >= RU.H.LEARNED
        return res
RU.FactorLearner = LogLearner
fm = [RU.run_student(RU.rule(.45, .9, .10, 0., .6), 'ct', 'e3h', s_d)['false'] for s_d in GRD.HOLD]
ref = rawall60[(rawall60.tutor == 'ct') & (rawall60.plan == 'e3h')].sort_values('seed').false.tolist(); assert fm == ref     # same students as the sweep
put('e3.solve.cross', f1(100 * LogLearner.cross / LogLearner.solved)); assert LogLearner.cross / LogLearner.solved > .99
# the test counting only hard answers
for pl, t in (('random', 'rnd'), ('easyfirst', 'ef')):
    x = XG[('cthard', 'c60_bH0', 'ct_hard', pl)]
    put(f'hardtest.{t}.any', hu(100 * sum(float(y['false_decl']) > 0 for y in x) / len(x), 1)); put(f'hardtest.{t}.med', med(med_reach(x, 't_closure')[0]))

# ---- the sweep: raw runs, same 200 seeds per plan
frames = []
for f in sorted(glob.glob(os.path.join(SW, 'out', 'graph', '*.csv.gz'))):
    d = pd.read_csv(f, usecols=['sid', 'tutor', 'plan', 'seed', 't_closure', 'false'])
    frames.append(d[d.plan.isin(['random', 'easyfirst', 'e3h', 'hard', 'easy', 'k16', 'tuned', 'k2', 'k4', 'k8', 'k12']) & d.tutor.isin(['ct', 'path']) & (d.seed < 4442)])
RAW = pd.concat(frames, ignore_index=True); RAW['tc'] = RAW.t_closure.fillna(np.inf)
INFO = pd.DataFrame(GRD.graph()).set_index('sid')
def wins(tutor, plan, sids):
    a = RAW[(RAW.tutor == tutor) & (RAW.plan == plan) & RAW.sid.isin(sids)].set_index(['sid', 'seed']).tc
    b = RAW[(RAW.tutor == tutor) & (RAW.plan == 'random') & RAW.sid.isin(sids)].set_index(['sid', 'seed']).tc
    j = pd.concat([a.rename('a'), b.rename('b')], axis=1, join='inner')
    return pd.DataFrame({'w': (j.a < j.b).groupby('sid').sum(), 'l': (j.a > j.b).groupby('sid').sum()})
jsids = INFO.index[INFO.arm == 'joint']; assert len(jsids) == 432
lab = INFO.index[INFO.arm.isin(['bH_eq_f', 'bH_above_f'])]; put('lab.n', len(lab))
for tut, tt in (('ct', 'ct'), ('path', 'chain')):
    for pl, t in (('e3h', 'e3'), ('easyfirst', 'ef')):
        w = wins(tut, pl, lab); put(f'lab.{tt}.{t}.loss', int((w.l > w.w).sum())); put(f'lab.{tt}.{t}.win', int((w.w > w.l).sum()))
LB = SG[SG.arm.isin(['bH_eq_f', 'bH_above_f']) & (SG.tutor == 'ct') & SG.plan.isin(['easyfirst', 'e3h'])]; assert LB.false_any.max() <= .03   # 'also in the labeled settings'
low = INFO.loc[jsids]; low = low.index[(low.f == .05) & (low.bH == 0)]; put('low.n', len(low))
for pl, t in (('e3h', 'e3'), ('easyfirst', 'ef')):
    w = wins('ct', pl, low); put(f'low.ct.{t}.loss', int((w.l > w.w).sum()))
mm = RAW[(RAW.tutor == 'ct') & RAW.sid.isin(jsids)].groupby(['sid', 'plan']).tc.median().unstack('plan')
put('ctmed.ef.lower', int((mm.easyfirst < mm.e3h).sum())); put('ctmed.e3.lower', int((mm.e3h < mm.easyfirst).sum()))
sav = 1 - mm.e3h / mm.random; put('save.e3', pc(sav.median())); put('save.e3.lo', pc(sav.quantile(.1))); put('save.e3.hi', pc(sav.quantile(.9)))
put('save.e3.min', pc(sav.min())); put('save.e3.max', pc(sav.max())); assert sav.min() < 0
# b_H = f and above on the graph: the grid's 48 settings at f = 0.05, then the labeled settings at g = 0.45, J = 0.9
wj = wins('ct', 'e3h', jsids); nw = INFO.loc[wj.index[wj.w <= wj.l]]; put('e3.notwin.n', len(nw)); assert ((nw.f == .05) & (nw.bH == .05)).all()
e05 = INFO.loc[jsids]; e05 = e05.index[(e05.f == .05) & (e05.bH == .05)]; put('eqf05.n', len(e05))
w = wins('ct', 'e3h', e05); put('eqf05.ct.e3.win', int((w.w > w.l).sum()))
wl_ = wins('ct', 'e3h', lab).join(INFO[['f', 'bH']]); assert (wl_.index.size == 16) and (INFO.loc[lab].g == .45).all() and (INFO.loc[lab].J == .9).all()
x = wl_[(wl_.f == .10) & (wl_.bH == .10)]; put('eqf10.ct.e3.win', int((x.w > x.l).sum())); put('eqf10.ct.e3.loss', int((x.l > x.w).sum()))
x = wl_[(wl_.f == .20) & (wl_.bH == .20)]; put('eqf20.ct.e3.loss', int((x.l > x.w).sum())); put('eqf20.n', len(x)); assert (x.l > x.w).all()
x = wl_[wl_.bH > wl_.f]; assert (x.l > x.w).all() and len(x) == 8          # 'if a failed hard question teaches more than a failed easy one, easy until 3 right costs questions'
ml = RAW[(RAW.tutor == 'ct') & RAW.sid.isin(lab)].groupby(['sid', 'plan']).tc.median().unstack('plan')
assert ((ml.hard < ml.easyfirst) & (ml.hard < ml.e3h)).all()               # 'hard only beats both'
gtf = ml.index[INFO.loc[ml.index].bH > INFO.loc[ml.index].f]; assert (ml.loc[gtf].easyfirst < ml.loc[gtf].e3h).all()    # 'all easy first beats easy until 3 right'
hl = RAW[(RAW.tutor == 'ct') & RAW.sid.isin(lab) & (RAW.plan == 'hard')]; assert (hl.tc < np.inf).all() and (hl['false'] == 0).all()    # 'with no false marks'
m5 = mm.loc[e05]; assert ((m5.hard < m5.e3h) & (m5.hard < m5.easyfirst)).sum() > len(e05) / 2     # 'at b_H at or above f that plan is usually hard only'
cc = RAW[(RAW.tutor == 'path') & RAW.sid.isin(e05)].groupby(['sid', 'plan']).tc.median().unstack('plan'); put('eqf05.chain.hard.tuned', int((cc.hard < cc.tuned).sum()))
s105 = INFO.loc[jsids]; s105 = s105.index[(s105.f == .10) & (s105.bH == .05)]; bx = mm.loc[s105, ['random', 'easyfirst', 'e3h', 'hard', 'easy', 'k16']].min(axis=1)
put('f10b05.ct.hard10', int((mm.loc[s105].hard <= 1.10 * bx).sum())); put('f10b05.n', len(s105))
# on the chain tutor: all easy first against the best fixed k
KS = ['k2', 'k4', 'k8', 'k12', 'k16']; mc = RAW[(RAW.tutor == 'path') & RAW.sid.isin(jsids)].groupby(['sid', 'plan']).tc.median().unstack('plan'); bk = mc[KS].min(axis=1); ak = mc[KS].idxmin(axis=1)
put('k.ef.w10', int((mc.easyfirst <= 1.10 * bk).sum())); put('k.low.ef10', int((mc.loc[low].easyfirst <= 1.10 * bk.loc[low]).sum())); put('k.low.best8', int((ak.loc[low] == 'k8').sum()))
assert ak.loc[low].value_counts().idxmax() == 'k8' and (ak.loc[low] == 'k8').sum() > len(low) / 2 and int(V['st.k.low.ef10']) == 0    # 'in none of them', '8 is usually best'
sav = 1 - mm.easyfirst / mm.random; put('save.ef', pc(sav.median()))
for c, t in ((.6, 'c60'), (.7, 'c70'), (.85, 'c85'), (1., 'none')):
    for p in ('random', 'easyfirst', 'e3h'):
        x = CT[(CT.c == c) & (CT.plan == p)].false_any
        put(f'sw.{t}.{p}.any', pc(x.mean())); put(f'sw.{t}.{p}.anylo', pc(x.min())); put(f'sw.{t}.{p}.anyhi', pc(x.max()))
assert all(pc(CT[(CT.c == c) & (CT.plan == p)].false_any.mean()) == '1' for c in (.6, .7, .85, 1.) for p in ('easyfirst', 'e3h'))
y = CT[(CT.plan == 'random') & (CT.c == .85)]; put('g25.c85.any', pc(y[y.g == .25].false_any.mean()))
bl = SG[(SG.g == .45) & (SG.J == .9) & (SG.f == .1) & (SG.bH == 0) & (SG.tutor == 'ct') & (SG.plan == 'random') & SG.arm.isin(['joint', 'cap_table'])].drop_duplicates('c').set_index('c')
for c, t in ((.8, 'c80'), (.82, 'c82'), (.85, 'c85')):
    put(f'bl.{t}.any', pc(bl.loc[c, 'false_any']))
# one concept, finer b_H: hard only within 10% of the best plan at b_H = 0.8 f
K = 200000; i0 = round(.05 * K); n8 = n8t = 0
for g_ in GRD.GS:
    for J_ in GRD.JS:
        for f_ in (.05, .10, .15, .20):
            for c_ in GRD.CAPS:
                b_ = .8 * f_
                best = SO.backward(g_, J_, f_, b_, c_, K, .9, 0, False, 0.)[0][i0]; hd = SO.backward(g_, J_, f_, b_, c_, K, .9, 2, False, 0.)[0][i0]
                n8 += hd <= 1.10 * best; n8t += 1
put('fine.hard10', n8); put('fine.n', n8t)

# ---- speed and start, CurriculumTutor
SA = pd.read_csv(os.path.join(SW, 'out', 'analysis', 'arms_summary.csv.gz')); A = SA[(SA.tutor == 'ct') & (SA.bH == 0)]
for m0, a in ((.05, 'm05'), (.3, 'm30'), (.65, 'm65')):
    for sp, b in ((1., 's100'), (.5, 's50'), (.25, 's25')):
        for pl in ('random', 'easyfirst', 'e3h'):
            x = A[(A.m0 == m0) & (A.c == .6) & (A.speed == sp) & (A.plan == pl)].iloc[0]
            put(f'arm.{a}.{b}.{pl}.med', med(x.med)); put(f'arm.{a}.{b}.{pl}.any', pc(x.false_any)); put(f'arm.{a}.{b}.{pl}.never', pc(x.never))
        for c, t in ((.85, 'c85'), (1., 'none')):
            x = A[(A.m0 == m0) & (A.c == c) & (A.speed == sp) & (A.plan == 'random')].iloc[0]; put(f'arm.{a}.{b}.{t}.any', pc(x.false_any)); put(f'arm.{a}.{b}.{t}.random.med', med(x.med))
            x = A[(A.m0 == m0) & (A.c == c) & (A.speed == sp) & (A.plan == 'e3h')].iloc[0]; put(f'arm.{a}.{b}.{t}.e3h.any', pc(x.false_any)); put(f'arm.{a}.{b}.{t}.e3h.med', med(x.med))

# guards: 'fewer false marks than random in every cell'; 'saves at every speed from 0.05'; 'fooled for most at x0.25 from 0.05 and 0.3'
B = A[(A.c == .6)].pivot_table(index=['m0', 'speed'], columns='plan', values=['false_any', 'med', 'never'])
assert (B['false_any']['e3h'] < B['false_any']['random']).all()
assert all(B['med']['e3h'].loc[(.05, s)] < B['med']['random'].loc[(.05, s)] for s in (1., .5, .25))
assert B['med']['e3h'].loc[(.65, 1.)] > B['med']['random'].loc[(.65, 1.)] and B['med']['random'].loc[(.65, .25)] == INF
assert all(B['false_any']['e3h'].loc[(m, .25)] > .5 for m in (.05, .3))
B2 = A[A.plan.isin(['random', 'e3h'])].pivot_table(index=['m0', 'speed', 'c'], columns='plan', values=['false_any', 'med'])
assert (B2['med']['e3h'].loc[(.65, .5)] >= B2['med']['random'].loc[(.65, .5)]).all()      # 'at that start and x0.5, it saves no questions at any cap'
assert (B2['false_any']['e3h'].loc[(.65, .25)] < B2['false_any']['random'].loc[(.65, .25)]).all()     # 'at x0.25 it protects at every cap'
assert all(B2['med']['e3h'].loc[(.65, .25, c)] < B2['med']['random'].loc[(.65, .25, c)] for c in (.6, .7, .85))     # 'and saves questions at caps of 0.85 or below'
assert (B2['med']['e3h'].loc[(.65, 1.)] > B2['med']['random'].loc[(.65, 1.)]).all() and all(.65 > float(V[f'st.cross.{t}']) for t in ('c60', 'c70', 'c85', 'none'))  # 'above the crossing at every cap', and it costs questions
rd = B2['false_any']['random']; assert all(rd.loc[(m, 1., c)] < .05 for m in (.05, .3, .65) for c in (.85, 1.)) and all(rd.loc[(.65, .5, c)] < .05 for c in (.85, 1.)) and all(rd.loc[(m, .5, .85)] > .3 for m in (.05, .3))   # 'false marks need a low cap only at the simulator's speed, or at x0.5 from a high start'
assert all(rd.loc[(.05, .5, c)] > .25 for c in (.6, .7, .85, 1.))          # 'at slower speeds from a low start, they are common at any cap'
# ---- real students: the one rough check
for p, t in ((.62, 'p62'), (.65, 'p65')):
    put(f'real.{t}', f2(root(lambda m: P_(m, .2) - p, .01, .99)))
put('right.m05', pc(P_(.05, .2)))
mr = root(lambda m: P_(m, .2) - .65, .01, .99); lg = lambda p: math.log(p / (1 - p))
gain = lg(P_(mr + easy(mr, 1.), .2)) - lg(.65)        # one easy question at 65% right, no cap
put('speed.gain', f2(gain)); put('speed.lo', hu(gain / .22)); put('speed.hi', hu(gain / .09))     # published: median 0.09, interval top 0.22 (Koedinger et al. 2023)
put('speed.x.lo', f2(.09 / gain)); put('speed.x.hi', f2(.22 / gain))
assert easy(mr, .6) == 0; mix = (lg(P_(mr + hard(mr), .2)) - lg(.65)) / 2     # at cap 0.6 an easy question gains 0 at that start, so half easy, half hard gains half a hard question's
put('speed.mix', f2(mix)); put('speed.mix.x.lo', f2(.09 / mix)); put('speed.mix.x.hi', f2(.22 / mix))
dall = sum(ds['E'] + ds['H'], 0.) / len(ds['E'] + ds['H']); put('d.all.mean', f2(dall))
for p, t in ((.62, 'p62'), (.65, 'p65')):
    put(f'real.avg.{t}', f2(root(lambda m: P_(m, dall) - p, .01, .99)))

with open(os.path.join(HERE, 'gen.tex'), 'w') as fh:
    for k, v in sorted(V.items()): fh.write(f'\\expandafter\\def\\csname v@{k}\\endcsname{{{v}}}\n')
print(len(V), 'keys')
for k, v in sorted(V.items()):
    if k.startswith(('st.f4', 'st.lab', 'st.low', 'st.ctmed', 'st.save', 'st.hardtest', 'st.fine', 'st.real', 'st.speed', 'st.ctq', 'st.d.', 'st.cross', 'st.ct.', 'st.stuck', 'st.sinks', 'st.fastover', 'st.J.below', 'st.gain.ll', 'st.t1.c60.fixgap', 'st.arm.m')): print(k[3:], v, end=' | ')
