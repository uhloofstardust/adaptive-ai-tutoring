"""Figures for the one-story document. Reads the study's data and the sweep's summaries; writes story/figs only.
One bar rule: a count of questions shows the median with a quartile bar; a share shows a 95% Wilson interval."""
import csv, gzip, os, shutil, statistics, sys
os.environ.setdefault('NUMBA_CACHE_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), '.numba_cache'))
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); U = os.path.dirname(HERE)
D = os.path.join(U, 'repo', 'experiments', 'difficulty'); sys.path.insert(0, D)
import matplotlib; matplotlib.use('pdf')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from common import load, group, num, INF, quart, wilson, VERS
import hetero as H, make_single as MS, make_single2 as M
FIG = os.path.join(HERE, 'figs')
C = dict(blue='#0072B2', orange='#E69F00', green='#009E73', red='#D55E00', purple='#CC79A7', sky='#56B4E9', grey='#777777')
plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 100, 'legend.frameon': False, 'pdf.fonttype': 42})
EB = dict(ecolor='#333333', elinewidth=.7, capsize=1.6, capthick=.7, zorder=4)
def save(fig, name):
    fig.tight_layout(); fig.savefig(os.path.join(FIG, name), metadata={'CreationDate': None}); plt.close(fig)
# figures that already follow the rule, or carry no bars
for n in ('f1_gain', 'f6_graph', 'f7_reach', 'f11_dose', 'f5_cusum'):
    shutil.copy(os.path.join(D, 'figs', n + '.pdf'), os.path.join(FIG, n + '.pdf'))

# ---- mastery over questions: median with a quartile band, same students as the study's run (seed 11)
def traj(p, policy, n=4000, seed=11, steps=60):
    rng = np.random.default_rng(seed); m = np.full(n, .05); out = []
    for q in range(400):
        if q <= steps: out.append(np.percentile(m, [25, 50, 75]).tolist() + [m.mean()])
        hard = policy(m, q); s = MS.solve(m, np.where(hard, MS.DH, MS.DE)); ok = rng.random(n) < s
        newE = MS.easy_new(m, np.where(ok, p['g'], p['f']), p); newH = np.minimum(1, m + np.where(ok, p['J'], p['bH']) * (1 - m))
        m = np.where(hard, newH, newE)
    return np.array(out)
S = {(r['version'], r['policy']): r for r in load('single_schedule.csv')}
TR = group(load('single_traj.csv'), 'version', 'policy')
fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.6), sharey=True)
for ax, v, p, t in zip(axs, ('capped at 0.6', 'no cap'), (MS.CAP, MS.NOCAP), ('Easy capped at 0.6', 'No cap')):
    thr = float(S[(v, 'best switch rule')]['switch_m'])
    for pol, f, col, lab in (('easy only', lambda m, q: np.zeros(m.shape, bool), C['blue'], 'easy only'), ('hard only', lambda m, q: np.ones(m.shape, bool), C['red'], 'hard only'), ('best switch rule', lambda m, q: m >= thr, C['green'], 'best switch')):
        a = traj(p, f); ref = sorted(TR[(v, pol)], key=lambda r: int(r['q']))
        assert all(abs(a[i, 3] - float(ref[i]['mean_m'])) < 1e-4 for i in range(61)), (v, pol)     # same students as the study's Figure 3
        q = np.arange(31); a = a[:31]
        ax.fill_between(q, a[:, 0], a[:, 2], color=col, alpha=.18, lw=0)
        ax.plot(q, a[:, 1], color=col, label=lab, clip_on=False, zorder=3)
    ax.axhline(.9, ls=':', color=C['grey']); ax.text(30, .915, 'goal 0.9', ha='right', fontsize=7, color=C['grey'])
    ax.set_title(t, fontsize=9); ax.set_xlabel('questions asked'); ax.set_xlim(0, 30)
axs[0].set_ylabel('true mastery of the middle student\n(band: middle half of students)'); axs[0].set_ylim(0, 1.02)
axs[0].legend(loc='center right', fontsize=7, bbox_to_anchor=(1.0, .36))
save(fig, 'traj_median.pdf')

# ---- different students: same runs as the study's Figure 4, medians with quartile bars
AD = {r['prior_hi']: r for r in load('single_adapt.csv')}
R = {}
for hi in (.30, .60, .85):
    tr, trm = M.pop(300, 100, hi); te, tem = M.pop(400, 900, hi)
    thr = np.array([H.oracle_threshold(s) for s in te])
    bk = min(range(0, 25), key=lambda k: H.simulate(M.fixed(k), tr, trm, 5000).mean())
    br = min(range(1, 8), key=lambda r: H.simulate(M.probe(r), tr, trm, 5000).mean())
    R[hi] = dict(o=H.simulate(lambda s: 'H' if s['m'] >= thr[s['student']] else 'E', te, tem, 7000), f=H.simulate(M.fixed(bk), te, tem, 7000), a=H.simulate(M.probe(br), te, tem, 7000), k=bk, n=br)
    A = AD[str(hi)]
    assert abs(R[hi]['o'].mean() - float(A['oracle_mean'])) < 1e-3 and abs(R[hi]['f'].mean() - float(A['best_fixed_mean'])) < 1e-3 and abs(R[hi]['a'].mean() - float(A['answer_rule_mean'])) < 1e-3
pd.DataFrame({f'{k}_{hi}': v[k] for hi, v in R.items() for k in 'ofa'}).to_csv(os.path.join(HERE, 'students_f4.csv'), index=False)
pd.DataFrame([{'hi': hi, 'k': v['k'], 'n_row': v['n']} for hi, v in R.items()]).to_csv(os.path.join(HERE, 'students_f4_settings.csv'), index=False)
sw = [float(r['best_switch']) for r in load('single_hetero.csv')]
fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.6), gridspec_kw={'width_ratios': [.8, 1.2]})
axs[0].hist(sw, bins=np.arange(0, .72, .02), color=C['blue']); axs[0].set_xlabel('best switch for this student'); axs[0].set_ylabel('students (of 400)'); axs[0].set_xlim(left=0)
PO = {r['hi']: r for r in csv.DictReader(open(os.path.join(HERE, 'pooled.csv')))}
x = np.arange(3); w = .26; hs = ('0.3', '0.6', '0.85')
for i, (k, lab, col) in enumerate((('o', 'switch tuned to each student (sees true m)', C['green']), ('f', 'best fixed plan for everyone', C['orange']), ('a', 'simple rule from answers', C['purple']))):
    med_ = np.array([float(PO[h][f'{k}_med']) for h in hs]); lo = np.array([float(PO[h][f'{k}_q1']) for h in hs]); hi_ = np.array([float(PO[h][f'{k}_q3']) for h in hs])
    axs[1].bar(x + (i - 1) * w, med_, w, color=col, label=lab, zorder=2)
    axs[1].errorbar(x + (i - 1) * w, med_, yerr=[med_ - lo, hi_ - med_], fmt='none', **EB)
axs[1].set_xticks(x); axs[1].set_xticklabels([f'0.02 to {h}' for h in hs]); axs[1].set_xlabel('range of starting mastery'); axs[1].set_ylabel('median questions to 0.9')
axs[1].set_ylim(0, 21); axs[1].legend(fontsize=6.5, loc='upper right')
save(fig, 'students_median.pdf')

# ---- the mastery test on the graph: students with a false mark, students with the whole chain learned, both as shares
E = group(load('ef_rows.csv'), 'rule', 'cpol', 'dpol'); XG = group(load('extra_rows.csv'), 'group', 'rule', 'cpol', 'dpol')
vers = ['nocap_bH0', 'nocap_bH02', 'nocap_bH05', 'c60_bH0', 'c70_bH0', 'c85_bH0', 'nocap_J60', 'c60_J60']
short = ['no cap', 'no cap,\n$b_H$ .02', 'no cap,\n$b_H$ .05', 'cap 0.6', 'cap 0.7', 'cap 0.85', 'no cap,\n$J$ 0.6', 'cap 0.6,\n$J$ 0.6']
pols = [('random', 'random', C['grey'], lambda r: E[(r, 'ct', 'random')]), ('easyfirst', 'all easy first', C['blue'], lambda r: E[(r, 'ct', 'easyfirst')]),
        ('e3h', 'easy until 3 right, then hard', C['green'], lambda r: XG[('newpol', r, 'ct', 'e3h')]), ('k16', '16 easy first', C['purple'], lambda r: E[(r, 'ct', 'k16')])]
fig, axs = plt.subplots(2, 1, figsize=(7.0, 4.6), sharex=True); x = np.arange(len(vers)); w = .2
SG0 = pd.read_csv(os.path.join(U, 'sweep2', 'out', 'analysis', 'graph_summary.csv.gz'))
RV = dict(nocap_bH0=(.9, 0., 1.), nocap_bH02=(.9, .02, 1.), nocap_bH05=(.9, .05, 1.), c60_bH0=(.9, 0., .6), c70_bH0=(.9, 0., .7), c85_bH0=(.9, 0., .85), nocap_J60=(.6, 0., 1.), c60_J60=(.6, 0., .6))
def thousand(r):
    J_, b_, c_ = RV[r]
    x_ = SG0[(SG0.arm == 'joint') & (SG0.tutor == 'ct') & (SG0.plan == 'random') & (SG0.g == .45) & (SG0.f == .1) & (SG0.J == J_) & (SG0.bH == b_) & (SG0.c == c_)]
    assert len(x_) == 1 and x_.n.iloc[0] == 1000
    return x_.iloc[0]
for i, (p, lab, col, get) in enumerate(pols):
    n = [len(get(r)) for r in vers]
    a = [sum(float(z.get('false_decl@2000') or z.get('false_decl')) > 0 for z in get(r)) for r in vers]
    b = [sum(num(z['t_closure']) < INF for z in get(r)) for r in vers]
    if p == 'random':
        n = [1000] * len(vers); a = [int(round(thousand(r).false_any * 1000)) for r in vers]; b = [int(round(thousand(r).reach * 1000)) for r in vers]
    for ax, k in ((axs[0], a), (axs[1], b)):
        sh = np.array([100 * u / v for u, v in zip(k, n)]); W = np.array([wilson(u, v) for u, v in zip(k, n)]) * 100
        ax.bar(x + (i - 1.5) * w, sh, w, color=col, label=lab, zorder=2)
        ax.errorbar(x + (i - 1.5) * w, sh, yerr=[np.maximum(0, sh - W[:, 0]), np.maximum(0, W[:, 1] - sh)], fmt='none', **EB)
axs[0].set_ylabel('% of students with at least\none concept falsely marked'); axs[1].set_ylabel('% of students with all 14\nchain concepts truly learned')
for ax in axs: ax.set_ylim(0, 105)
axs[1].set_xticks(x); axs[1].set_xticklabels(short, fontsize=7); axs[0].legend(fontsize=7, ncol=4, loc='lower center', bbox_to_anchor=(.5, 1.0))
save(fig, 'ct_shares.pdf')

# ---- false marks against the cap, baseline factors, 1,000 students
SG = pd.read_csv(os.path.join(U, 'sweep2', 'out', 'analysis', 'graph_summary.csv.gz'))
bl = SG[(SG.g == .45) & (SG.J == .9) & (SG.f == .1) & (SG.bH == 0) & (SG.tutor == 'ct') & (SG.plan == 'random') & SG.arm.isin(['joint', 'cap_table'])].drop_duplicates('c').sort_values('c')
k = (bl.false_any * bl.n).round().astype(int).values; n = bl.n.values
W = np.array([wilson(a, b) for a, b in zip(k, n)]) * 100; sh = 100 * k / n
fig, ax = plt.subplots(figsize=(5.0, 2.5))
ax.errorbar(bl.c, sh, yerr=[np.maximum(0, sh - W[:, 0]), np.maximum(0, W[:, 1] - sh)], fmt='-o', ms=3, color=C['red'], ecolor='#333333', elinewidth=.7, capsize=1.6, capthick=.7, clip_on=False, zorder=3)
ax.axvline(.8, ls=':', color=C['grey']); ax.text(.79, 2, 'learned line 0.8', fontsize=7, color=C['grey'], ha='right')
ax.set_xlabel('cap c (1 means no cap)'); ax.set_ylabel('% of students with at least\none concept falsely marked'); ax.set_xlim(0, 1.02); ax.set_ylim(bottom=0)
save(fig, 'false_vs_cap.pdf')
# ---- easy first against random on the chain, quartile bars; labels count easy until 3 right
from common import paired
def bars(ax, xs, groups, key, w, color, label, top=2000):
    meds, lo, hi = [], [], []
    for rs in groups:
        q1, q2, q3 = quart([num(r[key]) for r in rs])
        meds.append(q2); lo.append(q2 - q1); hi.append((top if q3 == INF else q3) - q2)
    ax.bar(xs, meds, w, color=color, label=label, zorder=2); ax.errorbar(xs, meds, yerr=[lo, hi], fmt='none', **EB)
    return [m + h for m, h in zip(meds, hi)]
fig, ax = plt.subplots(figsize=(7.0, 3.3)); x = np.arange(len(vers)); w = .26; tops = {}
for i, (pol, lab, col) in enumerate((('random', 'random', C['grey']), ('easyfirst', 'all easy first (3-5 easy)', C['blue']), ('e3h', 'easy until 3 right, then hard', C['green']))):
    groups = [E[(r, 'path', pol)] if pol != 'e3h' else XG[('newpol', r, 'path', 'e3h')] for r in vers]
    ends = bars(ax, x + (i - 1) * w, groups, 't_end', w, col, lab)
    for k_, e in enumerate(ends): tops[k_] = max(tops.get(k_, 0), e)
for i, r in enumerate(vers):
    wn, ls, _, n = paired(XG[('newpol', r, 'path', 'e3h')], E[(r, 'path', 'random')], 't_end')
    ax.text(i, tops[i] + 6, f'3 right faster\nthan random\nfor {wn}/{n}', ha='center', fontsize=6)
ax.set_xticks(x); ax.set_xticklabels(short, fontsize=7); ax.set_ylabel('median questions to G01'); ax.set_ylim(0, max(tops.values()) * 1.22)
ax.legend(fontsize=7, loc='upper center', bbox_to_anchor=(.5, -.2), ncol=3)
save(fig, 'f10_easyfirst.pdf')
print('story figures:', sorted(os.listdir(FIG)))
