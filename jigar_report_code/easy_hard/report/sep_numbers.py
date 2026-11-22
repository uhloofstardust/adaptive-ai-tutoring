"""Numbers from the semester's other studies, keys sp.*. Reads sep_data/: the result files committed on the shared repo's plain-bkt
branch (see SOURCE_COMMIT.txt; read, not regenerated here) and the log of my rerun of sim/tracer_bakeoff.py. Also reads the study's
own data for one easy-only line. Writes gen_sep.tex. Asserts guard the statements the text makes in words."""
import json, math, os, re, sys
sys.dont_write_bytecode = True
os.environ.setdefault('NUMBA_CACHE_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), '.numba_cache'))
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); SD = os.path.join(HERE, 'sep_data'); U = os.path.dirname(HERE)
V = {}
def put(k, v):
    k = 'sp.' + k; assert k not in V, k; V[k] = str(v)
def hu(x, d=0):
    f = 10 ** d; r = math.floor(abs(x) * f + .5 + 1e-9) / f
    return ('-' if x < 0 and r != 0 else '') + f'{r:.{d}f}'
def sg(x, d=3): return ('+' if x >= 0 else '') + hu(x, d)
csv = lambda n: pd.read_csv(os.path.join(SD, n + '.csv'))
# ---- AUC against the truth, sim/
log = open(os.path.join(SD, 'bakeoff.log')).read(); parts = log.split('=== tracer bake-off')[1:]; assert len(parts) == 2
for txt, t in zip(parts, ('rand', 'rr')):
    g = re.search(r'recovered forgetting rate: ([\d.]+).*\n.*actual rate\s+: ([\d.]+)', txt); put(f'{t}.rec', g.group(1)); put(f'{t}.true', g.group(2))
    m = re.search(r'paired mae_steps.*mean ([-+\d.]+), better for (\d+)/(\d+)', txt); a = re.search(r'paired auc.*mean ([-+\d.]+), better for (\d+)/(\d+) students, sign p ([\d.]+)', txt)
    put(f'{t}.mae.win', m.group(2)); put(f'{t}.n', m.group(3)); assert m.group(2) == m.group(3) == '20'
    w, n = int(a.group(2)), int(a.group(3)); put(f'{t}.auc.win', w); put(f'{t}.auc.lose', n - w); put(f'{t}.auc.p', hu(float(a.group(4)), 3 if float(a.group(4)) < .1 else 2))
    put(f'{t}.bestauc', re.search(r'best by AUC.*: (.*)', txt).group(1).strip()); assert 'f=0.10' in re.search(r'best by MAE.*: (.*)', txt).group(1)
    for lab, tg in (('BKT classical', 'bkt'), ('BKT forget f=0.10', 'f10')):
        r = re.search(lab + r'\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', txt); put(f'{t}.{tg}.auc', r.group(1)); put(f'{t}.{tg}.mae', r.group(3))
assert V['sp.rand.bestauc'].endswith('f=0.05') and V['sp.rr.bestauc'] == 'BKT classical'    # 'AUC prefers a smaller rate or none at all'
assert 2 * .5 ** 20 < .001                                                                  # 'p < 0.001' for 20 of 20
for txt, t in zip(parts, ('rand', 'rr')):
    ll = {m.group(1).strip(): float(m.group(2)) for m in re.finditer(r'^(BKT [^\n]*?)\s+[\d.]+\s+([\d.]+)\s+[\d.]+\s+[\d.]+$', txt, re.M)}; assert len(ll) == 6
    assert min(ll, key=ll.get).endswith('f=0.05')                                            # 'log loss picks 0.05 on both logs'
# ---- belief against truth, BKT student
c1 = csv('check1_calibration').dropna(); c4 = csv('check1_calibration_400learners').dropna()
put('cal.pairs', f'{int(c1.n.sum()):,}'); put('cal.pairs4', f'{int(c4.n.sum()):,}')
put('cal.gap', hu(c1[c1.n >= 20].gap.abs().max(), 3)); put('cal.gap4', hu(c4[c4.n >= 20].gap.abs().max(), 3))
row = c1[(c1.belief_lo == .6)].iloc[0]; put('cal.b', hu(row.mean_belief, 2)); put('cal.t', hu(row.frac_truly_known, 2))
d2 = csv('check2_detection').set_index('threshold')
for b, t in ((.5, 'b50'), (.9, 'b90'), (.99, 'b99')):
    z = d2.loc[b]; put(f'det.{t}.q', hu(z.delay_on_concept_mean, 1)); put(f'det.{t}.fa', hu(100 * z.false_alarm_rate, 1)); put(f'det.{t}.pred', hu(100 * z.predicted_false_alarm_rate, 1))
put('det.maxgap', hu(100 * (d2.false_alarm_rate - d2.predicted_false_alarm_rate).abs().max(), 1)); put('det.n', int(d2.n_declared.iloc[0])); assert (d2.n_declared == 240).all()
# ---- wrong numbers, one student
mo = csv('mismatch_one')
def mm(p, v): return mo[(mo.parameter == p) & (abs(mo.tutor_value - v) < 1e-9)].iloc[0]
z = mm('p_T', .2); put('mis.right.gap', sg(z.calib_gap)); put('mis.right.ci', hu(z.calib_gap_ci95, 3)); put('mis.right.fa', hu(100 * z.false_alarm_rate, 1))
for p, v, t in (('p_T', .4, 'learn'), ('p_G', .45, 'guess'), ('p_S', .3, 'slip')):
    z = mm(p, v); assert abs(z.error - .2) < 1e-9; put(f'mis.{t}.gap', sg(z.calib_gap)); put(f'mis.{t}.fa', hu(100 * z.false_alarm_rate, 1))
z = mm('p_T', .05); put('mis.learnlow.gap', sg(z.calib_gap)); put('mis.learnlow.fa', hu(100 * z.false_alarm_rate, 1))
z = mm('p_G', .05); put('mis.guesslow.gap', sg(z.calib_gap)); put('mis.guesslow.fa', hu(100 * z.false_alarm_rate, 1))
assert abs(mm('p_T', .4).calib_gap) > 1.9 * abs(mm('p_G', .45).calib_gap) and abs(mm('p_T', .4).calib_gap) > 1.9 * abs(mm('p_S', .3).calib_gap)  # 'about twice or more'
assert mm('p_G', .45).false_alarm_rate < mm('p_G', .25).false_alarm_rate < mm('p_T', .4).false_alarm_rate                                       # 'opposite directions'
put('mis.maxgap', hu(mo.calib_gap.abs().max(), 2)); put('mis.maxfa', hu(100 * mo.false_alarm_rate.max())); assert mo.false_alarm_rate.max() == mm('p_G', .05).false_alarm_rate
put('mis.students', 200); put('mis.marks', f"{int(mm('p_T', .2).n_declared):,}"); put('det.students', 30); assert d2.n_declared.iloc[0] == 30 * 8
# ---- students who differ
mp = csv('mismatch_population').set_index('spread'); z = mp.loc[.15]; put('pop.gap', sg(z.calib_gap)); put('pop.fa', hu(100 * z.false_alarm_rate, 1)); put('pop.fa0', hu(100 * mp.loc[0.].false_alarm_rate, 1))
tv = csv('tutor_choice_verdict'); assert set(tv.parameter) == {'p_S', 'p_G'}                 # the oracle test varies p_S and p_G only
assert ((tv.parameter == 'p_S') & (tv.best_fixed_value == .1) | (tv.parameter == 'p_G') & (tv.best_fixed_value == .25)).all()   # 'always the middle of the group'
z = tv[(tv.parameter == 'p_S') & (tv.spread == .15)].iloc[0]; put('or.fixed', hu(z.best_fixed_brier, 4)); put('or.oracle', hu(z.oracle_brier, 4)); put('or.buys', hu(z.oracle_buys_brier, 4)); put('or.ci', hu(z.brier_ci95, 4)); put('or.pct', hu(100 * z.oracle_buys_brier / z.best_fixed_brier))
others = tv[~((tv.parameter == 'p_S') & (tv.spread == .15))]; assert (others.oracle_buys_brier.abs() < others.brier_ci95).all()   # 'nothing measurable in the other five cells'
put('or.n', 600)
# ---- form of the model, 40-concept simulator, August
R = pd.read_csv(os.path.join(SD, 'cursim_results.csv'))
def rr(e, c): return R[(R.experiment == e) & (R.condition == c)].iloc[0]
a = rr('2_learner_forgets', 'CT + binary'); b = rr('2_learner_forgets', 'CT + forgetting model'); put('form.bin', hu(a.final_learned, 2)); put('form.fgt', hu(b.final_learned, 2)); put('form.gain', hu(b.final_learned - a.final_learned, 2)); assert a.n_learners == 30
a = rr('2_learner_does_not_forget', 'CT + binary'); b = rr('2_learner_does_not_forget', 'CT + forgetting model'); put('form.nf.bin', hu(a.final_learned)); put('form.nf.fgt', hu(b.final_learned, 2)); put('form.nf.cost', hu(a.final_learned - b.final_learned, 2))
a = rr('2_learner_forgets', 'CT + binary'); b = rr('2_learner_forgets', 'CT + forgetting model'); put('form.cov.bin', hu(a.coverage, 2)); put('form.cov.fgt', hu(b.coverage, 2))
put('form.cont', hu(rr('1_representation', 'continuous').final_learned, 1))
# ---- easy only inside CurriculumTutor, cap 0.6: marked against truly learned
D = os.path.join(U, 'repo', 'experiments', 'difficulty'); sys.path.insert(0, D)
from common import load, group
G = group(load('graph_rows.csv'), 'group', 'rule', 'cpol', 'dpol', 'profile', 'override')[('main', 'c60_bH0', 'ct', 'easy', 'average', '')]
put('easyonly.marked', hu(sum(float(z['declared@2000']) for z in G) / len(G), 1)); put('easyonly.learned', hu(sum(float(z['learned@2000']) for z in G) / len(G), 1)); put('easyonly.n', len(G)); assert V['sp.easyonly.learned'] == '0.0'
# ---- simulator equations: worked examples, and why hard only is flat on one concept (study constants, single_traj.csv, single_gain.csv)
import numpy as np
import make_single as MS
hl = re.findall(r'half-life ([\d.]+) days at average difficulty', log); assert len(set(hl)) == 1; put('sim48.hl', hl[0])
put('sim.meff.e50', hu(float(MS.solve(.5, MS.DE)), 2)); put('sim.meff.h50', hu(float(MS.solve(.5, MS.DH)), 2))
put('sim.pr.e50', hu(100 * float(MS.pright(.5, MS.DE)))); put('sim.pr.h50', hu(100 * float(MS.pright(.5, MS.DH))))
ph = float(MS.solve(.05, MS.DH)); jump = .05 + MS.CAP['J'] * (1 - .05); assert jump >= MS.GOAL and MS.CAP['bH'] == 0
put('tr.p', hu(100 * ph, 2)); put('tr.jump', hu(jump, 3)); put('tr.wait', hu(1 / ph, 1))
put('tr.share30', hu(100 * (1 - (1 - ph) ** 30), 1)); assert 1 - (1 - ph) ** 30 < .25  # so even the upper quartile is still at the start
gst = open(os.path.join(U, 'story', 'gen.tex')).read(); st_hard = re.search(r'v@st\.t1\.c60\.hard\\endcsname\{([\d.]+)\}', gst).group(1); assert hu(1 / ph, 1) == st_hard, (1 / ph, st_hard)
TR = group(load('single_traj.csv'), 'version', 'policy')
hm = {v: {int(r['q']): float(r['mean_m']) for r in TR[(v, 'hard only')]} for v in ('capped at 0.6', 'no cap')}
assert hm['capped at 0.6'] == hm['no cap']  # hard questions do not depend on the cap
put('tr.mean30', hu(hm['no cap'][30], 3)); put('tr.mean60', hu(hm['no cap'][60], 2))
GN = group(load('single_gain.csv'), 'model'); z = lambda k: [r for r in GN[(k,)] if float(r['m']) == 0][0]
a, b = z('today, marked answer'), z('today, really solving'); assert a['gain_easy'] == a['gain_hard'] and b['gain_easy'] == b['gain_hard']
put('gn.mk0', hu(float(a['gain_easy']), 3)); put('gn.sv0', hu(float(b['gain_easy']), 2))
# ---- students who differ: why the quartile bars are long (story/pooled.csv, story/pooled_students.csv, data/single_hetero.csv)
SU = os.path.join(U, 'story'); PO = pd.read_csv(os.path.join(SU, 'pooled.csv')).set_index('hi'); PS = pd.read_csv(os.path.join(SU, 'pooled_students.csv'))
R = int(re.search(r'^R = (\d+)$', open(os.path.join(SU, 'pooled.py')).read(), re.M).group(1)); assert (PS.groupby('hi').size() == 400).all()
put('st.runs', f'{400 * R:,}'); put('st.per', R)
o3 = PO.loc[.3]; put('st.o3.mean', hu(o3.o_mean, 1)); put('st.o3.p95', hu(o3.o_p95)); put('st.o3.med', hu(o3.o_med)); put('st.o3.q1', hu(o3.o_q1)); put('st.o3.q3', hu(o3.o_q3))
for h, t in ((.3, '30'), (.6, '60'), (.85, '85')): put(f'st.chance.{t}', hu(100 * PO.loc[h].o_chance))
rng = np.random.default_rng(20261108); om = PS[PS.hi == .3].o.to_numpy(); assert abs(om.mean() - o3.o_mean) < 1e-9
bs = [om[rng.integers(0, 400, 400)].mean() for _ in range(4000)]; put('st.o3.lo', hu(np.percentile(bs, 2.5), 2)); put('st.o3.hi', hu(np.percentile(bs, 97.5), 2)); put('st.o3.mean2', hu(om.mean(), 2))
f3 = PO.loc[.3]; put('st.f3.mean', hu(f3.f_mean, 2)); put('st.f3.sd', hu(f3.f_sd, 2)); put('st.f3.low', hu(f3.f_mean - f3.f_sd, 2)); put('st.f3.min', hu(f3.f_min)); assert f3.f_mean - f3.f_sd < f3.f_min
HE = pd.read_csv(os.path.join(D, 'data', 'single_hetero.csv')); put('st.l.lo', hu(HE.l.min(), 2)); put('st.l.hi', hu(HE.l.max(), 2))
sw_med = float(HE.best_switch.median()); pw = sw_med ** (1 + MS.K * MS.DH); put('st.sw.med', hu(sw_med, 2)); put('st.sw.p', hu(pw, 2)); put('st.sw.wait', hu(1 / pw, 1)); put('st.sw.sd', hu(math.sqrt(1 - pw) / pw, 1))
# ---- one concept at the main values: climb with easy questions, then wait for one hard solve
assert all(m_ + MS.CAP['J'] * (1 - m_) >= MS.GOAL - 1e-12 for m_ in np.linspace(0, 1, 1001))  # one solve ends the concept from any m
SC = {(r['version'], r['policy']): r for r in load('single_schedule.csv')}; swl = float(SC[('capped at 0.6', 'best switch rule')]['switch_m'])
crs = float(re.search(r'v@st\.cross\.c60\\endcsname\{([\d.]+)\}', gst).group(1))
put('mech.sw', hu(swl, 2)); put('mech.cross', hu(crs, 2)); put('mech.w.sw', hu(1 / swl ** (1 + MS.K * MS.DH), 1)); put('mech.w.cross', hu(1 / crs ** (1 + MS.K * MS.DH), 1))
# ---- why the mastery test passes h: the balance point of the score (step sizes and h as in Section 2.7)
up, dn, hh = math.log(.9 / .25), math.log(.75 / .10), math.log(1 / .0004)
for k_, v_ in (('up', hu(up, 2)), ('dn', hu(dn, 2)), ('h', hu(hh, 2))): assert re.search(r'v@st\.cusum\.' + k_ + r'\\endcsname\{' + re.escape(v_) + r'\}', gst), k_
pb = dn / (up + dn); put('cu.bal', hu(100 * pb, 1))
inv = lambda e: ((pb - MS.GUESS) / (1 - MS.SLIP - MS.GUESS)) ** (1 / e); put('cu.me', hu(inv(1 + MS.K * MS.DE), 2)); put('cu.mh', hu(inv(1 + MS.K * MS.DH), 2))
put('cu.nmax', math.floor(hh / up)); assert math.floor(hh / up) * up < hh < (math.floor(hh / up) + 1) * up
# ---- starts cut at 0 on the graph: a concept that starts at exactly 0 can never be solved under hard only when a failed hard question teaches nothing
cur_ = json.load(open(os.path.join(D, 'data', 'curricula', 'layered_40.json'))); pre = {c['cid']: c['prereqs'] for c in cur_['concepts']}
def anc(c, acc):
    for q in pre[c]:
        if q not in acc: acc.add(q); anc(q, acc)
    return acc
nch = len(anc('G01', set())) + 1; assert nch == 14
src = open(os.path.join(D, 'simcore', 'students', 'continuous.py')).read(); assert 'init_mastery: float = 0.05' in src and 'profile.init_mastery, 0.03))' in src and 'max(0.0, self.rng.gauss(' in src
pz = 0.5 * (1 + math.erf((0 - .05) / (.03 * math.sqrt(2)))); put('z.one', hu(100 * pz, 1)); put('z.chain', hu(100 * (1 - (1 - pz) ** nch)))
# ---- what "exact calculation" means (solver grid, bracket width in Table 3.2)
kd = int(re.search(r'^K_DEFAULT = (\d+)$', open(os.path.join(D, 'solve_one.py')).read(), re.M).group(1)); put('ex.levels', f'{kd + 1:,}')
wid = [float(r['exact_width']) for r in load('single_schedule.csv') if r['exact_width']]; assert len(wid) == 6 and max(wid) < 1e-4; put('ex.wbound', '0.0001')
# ---- text says hard only takes the same median on the best-case tutor from 0.65 at every cap
gsw = open(os.path.join(U, 'shared', 'sweep_gen.tex')).read()
hv = set(re.findall(r'v@sw\.c\.b00\.m65\.c\d+\.s100\.path\.hard\\endcsname\{([^}]*)\}', gsw)); assert len(hv) == 1, hv
hv = set(re.findall(r'v@sw\.c\.b00\.m30\.c\d+\.s100\.path\.hard\\endcsname\{([^}]*)\}', gsw)); assert len(hv) == 1, hv
with open(os.path.join(HERE, 'gen_sep.tex'), 'w') as fh:
    for k, v in sorted(V.items()): fh.write(f'\\expandafter\\def\\csname v@{k}\\endcsname{{{v}}}\n')
for k, v in sorted(V.items()): print(k[3:], v, end=' | ')
print(); print(len(V), 'keys')
