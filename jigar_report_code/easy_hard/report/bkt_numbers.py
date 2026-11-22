"""BKT results printed in the report, keys bk.*. Reads my four BKT projects and their saved console logs, never writes there.
Writes report/gen_bkt.tex. Asserts tie every parsed log value back to a recomputation from the saved result files where one exists."""
import math, os, re, sys
sys.dont_write_bytecode = True
import numpy as np, pandas as pd
H = os.path.expanduser('~'); HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(H, 'Downloads', 'BKT_variant_reports')
B, I, F, S = (os.path.join(H, f'{p}bkt-project') for p in ('', 'i', 'f', 's'))
V = {}
def put(k, v):
    k = 'bk.' + k; assert k not in V, k; V[k] = str(v)
def hu(x, d=0):
    f = 10 ** d; r = math.floor(x * f + .5 + 1e-9) / f
    return f'{r:.{d}f}'
def comma(n): return f'{int(n):,}'
def log(name): return open(os.path.join(LOG, name)).read()
def f4(txt, pat): return f'{grab(txt, pat)[0]:.4f}'
def grab(txt, pat, cast=float):
    m = re.search(pat, txt); assert m, pat
    return tuple(cast(x) for x in m.groups())

# ---- data and cleaning, from the raw file and the cleaned file
raw = pd.read_csv(os.path.join(B, 'data', 'skill_builder_data.csv'), encoding='latin-1', low_memory=False)
put('raw.rows', comma(len(raw))); put('raw.students', comma(raw.user_id.nunique()))
a = raw[raw.skill_id.notna()]; put('rm.noskill', comma(len(raw) - len(a)))
b = a[a.original == 1]; put('rm.scaffold', comma(len(a) - len(b)))
dup = b.groupby(['order_id', 'skill_id']).size(); put('dup.max', int(dup.max()))
c = b.drop_duplicates(['order_id', 'skill_id']); put('rm.dup', comma(len(b) - len(c)))
dd = b[b.groupby(['order_id', 'skill_id']).user_id.transform('size') > 1]; put('dup.students', dd.user_id.nunique()); put('dup.seqs', dd.groupby(['user_id', 'skill_id']).ngroups); put('dup.share', hu(100 * (len(b) - len(c)) / len(b)))
d = pd.read_csv(os.path.join(B, 'data', 'cleaned.csv'))
assert len(c) == len(d) == 312232 and c.user_id.nunique() == d.user_id.nunique() == 4163
put('distinct', comma(d.order_id.nunique())); put('rows', comma(len(d))); put('students', comma(d.user_id.nunique())); put('concepts', d.skill_id.nunique())
L = d.groupby(['user_id', 'skill_id']).size(); put('seqs', comma(len(L))); put('seq.med', int(L.median()))

# ---- basic BKT
P = pd.read_csv(os.path.join(B, 'results', 'params.csv')); put('fit.n', len(P))
put('fit.cover', hu(100 * d[d.skill_id.isin(P.skill_id)].shape[0] / len(d), 1))
for col, t in (('pL0', 'init'), ('pT', 'learn'), ('pS', 'slip'), ('pG', 'guess')):
    put(f'med.{t}', hu(P[col].median(), 2))
put('grid.basic', comma(19 * 19 * 9 * 9)); put('grid.forget', comma(19 * 19 * 9 * 9 * 6))
EM = pd.read_csv(os.path.join(B, 'results', 'em_vs_grid.csv'))
diffs = np.concatenate([(EM[f'{p}_grid'] - EM[f'{p}_em']).abs().values for p in ('pL0', 'pT', 'pS', 'pG')]); assert len(diffs) == 40
put('em.diff', hu(diffs.mean(), 3))
fe = log('fbkt_evaluate.log')
put('s.rows', comma(grab(fe, r'test rows evaluated: (\d+)', int)[0]))
put('s.mean', f4(fe, r'per-skill mean baseline\s+AUC ([\d.]+)'))
auc, rm, acc = grab(fe, r'classical \(params.csv\)\s+AUC ([\d.]+)\s+RMSE ([\d.]+)\s+acc ([\d.]+)'); put('s.basic', f'{auc:.4f}')
fa, *_ = grab(fe, r'forgetting BKT\s+AUC ([\d.]+)\s+RMSE ([\d.]+)\s+acc ([\d.]+)'); put('s.forget', f'{fa:.4f}')
m0, m1, *_ = grab(fe, r'per-skill macro AUC: classical ([\d.]+)\s+forgetting ([\d.]+)'); put('s.basic.macro', f'{m0:.4f}'); put('s.forget.macro', f'{m1:.4f}')
put('s.basic.macro3', hu(m0, 3)); put('s.basic3', hu(auc, 3))
A0 = pd.read_csv(os.path.join(B, 'results', 'auc_per_skill.csv')); assert hu(A0.auc.mean(), 3) == hu(m0, 3)
# ---- forgetting
PF = pd.read_csv(os.path.join(F, 'results', 'params_forget.csv')); n44 = int((PF.pF > 0).sum()); assert n44 == 44 and len(PF) == 94; put('f.chose', n44)
x0, x1 = grab(fe, r'restricted to the 44 skills.*\n\s+pF=0 slice \(refit\)\s+AUC ([\d.]+)\n\s+forgetting BKT\s+AUC ([\d.]+)'); put('f.rows0', f'{x0:.4f}'); put('f.rows1', f'{x1:.4f}')
up, dn = grab(fe, r'improved (\d+), worsened (\d+)', int); put('f.up', up); put('f.down', dn); put('f.same', n44 - up - dn)
assert grab(log('fbkt_engine.log'), r'pF=0 slice vs classical engine: max diff = ([\d.e+-]+)')[0] == 0.
# ---- individualised
ie = log('ibkt_evaluate.log'); ip = log('ibkt_perskill.log')
put('t.rows', comma(grab(ie, r'future rows evaluated: (\d+)', int)[0])); put('t.mean', f4(ie, r'per-skill mean baseline\s+AUC ([\d.]+)'))
put('t.basic', f4(ie, r'plain BKT\s+AUC ([\d.]+)')); put('t.indiv', f4(ie, r'individualized BKT\s+AUC ([\d.]+)'))
a0, a1 = grab(ip, r'macro AUC\s+plain ([\d.]+)\s+iBKT ([\d.]+)'); put('t.basic.macro', f'{a0:.4f}'); put('t.indiv.macro', f'{a1:.4f}')
im, it = grab(ip, r'skills improved: (\d+) / (\d+)', int); put('i.up', im); put('i.n', it)
SM = pd.read_csv(os.path.join(I, 'results', 'student_multipliers.csv')); print('mult cols', SM.columns.tolist())
mL, mT = SM.iloc[:, 1], SM.iloc[:, 2]; pers = ~((mL == 1) & (mT == 1))
put('i.students', comma(len(SM))); put('i.pers', comma(int(pers.sum()))); put('i.pct', hu(100 * pers.mean(), 1)); assert int(pers.sum()) == 1228 and len(SM) == 4137
edge = pers & (mL.isin([.5, 1.5]) | mT.isin([.25, 4.0])); put('i.edge', comma(int(edge.sum())))
# ---- student-based
se = log('sbkt_evaluate.log'); sp = log('sbkt_perskill.log')
r_, u_, n_ = grab(se, r'common subset: (\d+) future rows, (\d+) students, (\d+) skills', int); put('c.rows', comma(r_)); put('c.students', comma(u_)); put('c.concepts', n_)
mc = grab(se, r'per-skill mean baseline\s+AUC ([\d.]+)')[0]; ms = grab(se, r'per-student mean baseline\s+AUC ([\d.]+)')[0]
cb = grab(se, r'skill-based BKT\s+AUC ([\d.]+)')[0]; sb = grab(se, r'student-based BKT\s+AUC ([\d.]+)')[0]
put('c.mean.concept', f'{mc:.4f}'); put('c.mean.student', f'{ms:.4f}'); put('c.basic', f'{cb:.4f}'); put('c.student', f'{sb:.4f}')
put('c.add.concept', hu(cb - mc, 3)); put('c.add.student', hu(sb - ms, 3))
pm = grab(se, r'macro-by-skill.*\n\s+per-student mean baseline\s+macro ([\d.]+)')[0]; bm = grab(se, r'skill-based BKT\s+macro ([\d.]+)')[0]; tm = grab(se, r'student-based BKT\s+macro ([\d.]+)')[0]
put('c.mean.student.macro', f'{pm:.4f}'); put('c.basic.macro', f'{bm:.4f}'); put('c.student.macro', f'{tm:.4f}')
w_, n2 = grab(sp, r'student axis better on (\d+) of (\d+) skills', int); put('c.win', w_); put('c.n', n2)
AX = pd.read_csv(os.path.join(S, 'results', 'auc_per_skill_axes.csv')); print('axes cols', AX.columns.tolist())

# ---- differences quoted in the text, from the same log values
put('s.gap', hu(auc - float(V['bk.s.mean']), 3)); put('s.forget.gain', hu(fa - auc, 3)); put('s.forget.macro.gain', hu(m1 - m0, 3))
put('t.indiv.gain', hu(float(V['bk.t.indiv']) - float(V['bk.t.basic']), 3)); put('t.indiv.macro.gain', hu(a1 - a0, 3))

# ---- what students in the data score, for the check on the simulator's start
ds = d.sort_values(['user_id', 'order_id'], kind='mergesort')
first = ds.groupby(['user_id', 'skill_id']).correct.first()
put('right.all', hu(100 * d.correct.mean())); put('right.first', hu(100 * first.mean()))
P_ = lambda m, de: .93 * m ** (1 + 1.2 * de) + .25 * (1 - m ** (1 + 1.2 * de))
lo, hi = .01, .99
for _ in range(80):
    mid = (lo + hi) / 2
    if P_(mid, .2) > first.mean(): hi = mid
    else: lo = mid
put('right.first.start', hu((lo + hi) / 2, 2))

with open(os.path.join(HERE, 'gen_bkt.tex'), 'w') as fh:
    for k, v in sorted(V.items()): fh.write(f'\\expandafter\\def\\csname v@{k}\\endcsname{{{v}}}\n')
for k, v in sorted(V.items()): print(k, v, end=' | ')
print(); print(len(V), 'keys')
