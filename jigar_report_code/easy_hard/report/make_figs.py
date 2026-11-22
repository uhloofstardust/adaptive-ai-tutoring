"""Figures for the report, with the report's own names and symbols. Reads the study's data, the sweep's summaries and my BKT
projects; writes report/figs only. A count of questions shows the median with a quartile bar, a share shows a 95% Wilson interval,
and exact calculations show no bars. Every numeric axis starts at 0."""
import csv, json, os, shutil, sys
os.environ.setdefault('NUMBA_CACHE_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), '.numba_cache'))
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); U = os.path.dirname(HERE); HOME = os.path.expanduser('~')
D = os.path.join(U, 'repo', 'experiments', 'difficulty'); sys.path.insert(0, D)
import matplotlib; matplotlib.use('pdf')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from common import load, group, num, INF, quart, wilson, med_reach, paired
import make_single as MS
FIG = os.path.join(HERE, 'figs'); os.makedirs(FIG, exist_ok=True)
C = dict(blue='#0072B2', orange='#E69F00', green='#009E73', red='#D55E00', purple='#CC79A7', sky='#56B4E9', grey='#777777')
plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 100, 'legend.frameon': False, 'pdf.fonttype': 42, 'mathtext.default': 'regular'})
EB = dict(ecolor='#333333', elinewidth=.7, capsize=1.6, capthick=.7, zorder=4)
GES, GEF, GHS, GHF = (r'$\gamma_E^{solve}$', r'$\gamma_E^{fail}$', r'$\gamma_H^{solve}$', r'$\gamma_H^{fail}$')
CAP = r'$m_{cap}$'
def save(fig, name):
    fig.tight_layout(); fig.savefig(os.path.join(FIG, name), metadata={'CreationDate': None}); plt.close(fig)

# ---- BKT: what the belief does. Exact calculations from fixed answers.
def trace(seq, init, learn, slip, guess, forget=0.):
    k, out = init, []
    for a in seq:
        n = k * (1 - slip) if a else k * slip
        o = (1 - k) * guess if a else (1 - k) * (1 - guess)
        k = n / (n + o); k = k * (1 - forget) + (1 - k) * learn; out.append(k)
    return out
fig, axs = plt.subplots(1, 2, figsize=(6.0, 2.15), sharey=True)
SEQ = [0, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1]; x = np.arange(1, len(SEQ) + 1)
PB = pd.read_csv(os.path.join(HOME, 'bkt-project', 'results', 'params.csv'))
med = [PB[c].median() for c in ('pL0', 'pT', 'pS', 'pG')]; assert [round(v, 2) for v in med] == [.7, .15, .2, .15]
for t, a in zip(x, SEQ):
    if not a: axs[0].axvspan(t - .5, t + .5, color='#eeeeee', lw=0, zorder=0)
for pf, col in ((0., C['blue']), (.10, C['orange']), (.25, C['red'])):
    axs[0].plot(x, trace(SEQ, *med, pf), marker='o', ms=2.5, lw=1.3, color=col, label=rf'$p_{{forget}}$ = {pf:.2f}', clip_on=False, zorder=3)
axs[0].set_title('One answer sequence, three forgetting values', fontsize=8); axs[0].set_xlabel('question number on the concept'); axs[0].set_ylabel(r'belief $p_{know}$ after the answer')
axs[0].legend(fontsize=6, loc='lower center', ncol=3, columnspacing=.5, handlelength=.8, handletextpad=.4, borderaxespad=.2); axs[0].set_xlim(0, len(SEQ) + .5); axs[0].set_ylim(0, 1.02); axs[0].set_xticks([0, 5, 10])
cl = pd.read_csv(os.path.join(HOME, 'bkt-project', 'data', 'cleaned.csv'))
pair = cl[(cl.user_id == 78283) & (cl.skill_id == 311)].sort_values('order_id'); seq2 = pair.correct.tolist(); assert len(seq2) == 17
sk = pd.read_csv(os.path.join(HOME, 'sbkt-project', 'results', 'params_temporal.csv')).set_index('skill_id').loc[311]
st = pd.read_csv(os.path.join(HOME, 'sbkt-project', 'results', 'params_students.csv')).set_index('user_id').loc[78283]
assert [round(float(sk[c]), 2) for c in ('pL0', 'pT', 'pS', 'pG')] == [.65, .05, .25, .30] and [round(float(st[c]), 2) for c in ('pL0', 'pT', 'pS', 'pG')] == [.75, .60, .10, .05]
x2 = np.arange(1, len(seq2) + 1)
for t, a in zip(x2, seq2):
    if not a: axs[1].axvspan(t - .5, t + .5, color='#eeeeee', lw=0, zorder=0)
axs[1].plot(x2, trace(seq2, *[float(sk[c]) for c in ('pL0', 'pT', 'pS', 'pG')]), marker='o', ms=2.5, lw=1.3, color=C['blue'], label="concept's fitted numbers", clip_on=False, zorder=3)
axs[1].plot(x2, trace(seq2, *[float(st[c]) for c in ('pL0', 'pT', 'pS', 'pG')]), marker='o', ms=2.5, lw=1.3, color=C['green'], label="student's fitted numbers", clip_on=False, zorder=3)
axs[1].set_title('One real student, two sets of numbers', fontsize=8); axs[1].set_xlabel('question number on the concept'); axs[1].legend(fontsize=7, loc='lower right'); axs[1].set_xlim(0, len(seq2) + .5); axs[1].set_xticks([0, 5, 10, 15])
save(fig, 'bkt_traces.pdf')

# ---- one question: expected gain
G = group(load('single_gain.csv'), 'model')
fig, axs = plt.subplots(2, 2, figsize=(4.8, 3.3), sharex=True, sharey=True)
PANELS = ((0, 0, 'today, marked answer', 'Existing gains (0.45, 0.10),\nlearning from the marked answer'),
          (0, 1, 'today, really solving', 'Existing gains (0.45, 0.10),\nlearning from really solving'),
          (1, 0, 'proposed, marked answer', f'Easy-hard rule, {CAP} = 0.6,\nlearning from the marked answer'),
          (1, 1, 'proposed, really solving', f'Easy-hard rule, {CAP} = 0.6,\nlearning from really solving (as studied)'))
for i, j, k, t in PANELS:
    ax = axs[i, j]; rs = G[(k,)]; m = [float(r['m']) for r in rs]
    ax.plot(m, [float(r['gain_easy']) for r in rs], color=C['blue'], label='easy question', clip_on=False, zorder=3)
    ax.plot(m, [float(r['gain_hard']) for r in rs], color=C['red'], label='hard question', clip_on=False, zorder=3)
    ax.set_title(t, fontsize=7.2)
rs = G[('proposed, really solving, no cap',)]
axs[1, 1].plot([float(r['m']) for r in rs], [float(r['gain_easy']) for r in rs], color=C['blue'], ls=':', lw=1.2, label='easy question, no cap', clip_on=False, zorder=3)
axs[1, 1].legend(loc='upper right', fontsize=6.5); axs[0, 0].legend(loc='upper right', fontsize=6.5)
for ax in axs[1]: ax.set_xlabel('mastery $m$ before the question')
for ax in axs[:, 0]: ax.set_ylabel('expected gain\nfrom one question')
axs[0, 0].set_xlim(0, 1); axs[0, 0].set_ylim(0, .31)
save(fig, 'gain.pdf')
fig, axs = plt.subplots(1, 2, figsize=(4.8, 1.9), sharey=True)
for ax, k, t in ((axs[0], 'today, marked answer', 'Existing gains (0.45, 0.10),\nlearning from the marked answer'), (axs[1], 'proposed, really solving', f'Easy-hard rule, {CAP} = 0.6,\nlearning from really solving')):
    rs = G[(k,)]; m = [float(r['m']) for r in rs]
    ax.plot(m, [float(r['gain_easy']) for r in rs], color=C['blue'], label='easy question', clip_on=False, zorder=3)
    ax.plot(m, [float(r['gain_hard']) for r in rs], color=C['red'], label='hard question', clip_on=False, zorder=3)
    ax.set_title(t, fontsize=7.2); ax.set_xlabel('mastery $m$ before the question'); ax.set_xlim(0, 1)
rs = G[('proposed, really solving, no cap',)]
axs[1].plot([float(r['m']) for r in rs], [float(r['gain_easy']) for r in rs], color=C['blue'], ls=':', lw=1.2, label='easy question, no cap', clip_on=False, zorder=3)
axs[1].legend(loc='upper right', fontsize=6.5); axs[0].set_ylabel('expected gain\nfrom one question'); axs[0].set_ylim(0, .31)
save(fig, 'gain_two.pdf')

# ---- one concept: mastery over questions. Same students as the study's run (seed 11).
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
fig, axs = plt.subplots(1, 2, figsize=(5.0, 2.15), sharey=True)
for ax, v, p, t in zip(axs, ('capped at 0.6', 'no cap'), (MS.CAP, MS.NOCAP), (f'{CAP} = 0.6', 'No cap')):
    thr = float(S[(v, 'best switch rule')]['switch_m'])
    for pol, f, col, lab in (('easy only', lambda m, q: np.zeros(m.shape, bool), C['blue'], 'easy only'), ('hard only', lambda m, q: np.ones(m.shape, bool), C['red'], 'hard only'), ('best switch rule', lambda m, q: m >= thr, C['green'], 'best switch level')):
        a = traj(p, f); ref = sorted(TR[(v, pol)], key=lambda r: int(r['q']))
        assert all(abs(a[i, 3] - float(ref[i]['mean_m'])) < 1e-4 for i in range(61)), (v, pol)
        q = np.arange(31); a = a[:31]
        ax.fill_between(q, a[:, 0], a[:, 2], color=col, alpha=.18, lw=0)
        ax.plot(q, a[:, 1], color=col, label=lab, clip_on=False, zorder=3)
        if pol == 'hard only': ax.plot(q, a[:, 3], color=col, ls='--', lw=1.1, label='hard only, mean', clip_on=False, zorder=3)
    ax.axhline(.9, ls=':', color=C['grey']); ax.text(30, .915, 'goal 0.9', ha='right', fontsize=7, color=C['grey'])
    ax.set_title(t, fontsize=9); ax.set_xlabel('questions asked'); ax.set_xlim(0, 30)
axs[0].set_ylabel('true mastery $m$'); axs[0].set_ylim(0, 1.02)
axs[0].legend(loc='center right', fontsize=7, bbox_to_anchor=(1.0, .36))
save(fig, 'traj.pdf')

# ---- students who differ
sw = [float(r['best_switch']) for r in load('single_hetero.csv')]
fig, axs = plt.subplots(1, 2, figsize=(6.2, 2.9), gridspec_kw={'width_ratios': [.8, 1.2]})
axs[0].hist(sw, bins=np.arange(0, .72, .02), color=C['blue']); axs[0].set_xlabel('best switch level: the true mastery $m$\nat which this student should switch\nfrom easy to hard questions', fontsize=8); axs[0].set_ylabel('number of students (of 400)', fontsize=8); axs[0].set_title('Initial mastery $m_0$ = 0.05', fontsize=8); axs[0].set_xlim(left=0)
PO = {r['hi']: r for r in csv.DictReader(open(os.path.join(U, 'story', 'pooled.csv')))}
x = np.arange(3); w = .26; hs = ('0.3', '0.6', '0.85')
for i, (k, lab, col) in enumerate((('o', "each student's own best switch (reads $m$)", C['green']), ('f', 'best fixed plan (one count for all)', C['orange']), ('a', 'back to easy (uses only answers)', C['purple']))):
    med_ = np.array([float(PO[h][f'{k}_med']) for h in hs]); lo = np.array([float(PO[h][f'{k}_q1']) for h in hs]); hi_ = np.array([float(PO[h][f'{k}_q3']) for h in hs])
    axs[1].bar(x + (i - 1) * w, med_, w, color=col, label=lab, zorder=2)
    axs[1].errorbar(x + (i - 1) * w, med_, yerr=[med_ - lo, hi_ - med_], fmt='none', **EB)
    axs[1].plot(x + (i - 1) * w, [float(PO[h][f'{k}_mean']) for h in hs], ls='none', marker='D', ms=3.2, mfc='white', mec='#333333', mew=.7, zorder=5, label='mean' if i == 2 else None)
axs[1].set_xticks(x); axs[1].set_xticklabels([f'0.02 to {h}' for h in hs]); axs[1].set_xlabel('range from which each student\'s\ninitial mastery $m_0$ is drawn', fontsize=8); axs[1].set_ylabel('questions to reach the goal\n(true mastery $m$ = 0.9)', fontsize=8); axs[1].set_title('Questions to the goal, by plan (bar: median;\nblack line: quartile bar, 25th to\n75th percentile of runs; diamond: mean)', fontsize=8)
axs[1].set_ylim(0, 40); axs[1].legend(fontsize=6.5, loc='upper right')
save(fig, 'students.pdf')

# ---- the graph has no symbols to rename
from matplotlib.patches import FancyArrowPatch
cur_ = json.load(open(os.path.join(D, 'data', 'curricula', 'layered_40.json'))); cs = {c['cid']: c for c in cur_['concepts']}
def anc(c, acc):
    for p_ in cs[c]['prereqs']:
        if p_ not in acc: acc.add(p_); anc(p_, acc)
    return acc
chain = anc('G01', set()) | {'G01'}; assert len(chain) == 14
by_t = {}
for c in sorted(cs.values(), key=lambda c: (c['tier'], c['cid'])): by_t.setdefault(c['tier'], []).append(c['cid'])
pos = {cid: ((i + 1) / (len(row) + 1), -t) for t, row in by_t.items() for i, cid in enumerate(row)}
children = {c: [] for c in cs}
for c in cs.values():
    for p_ in c['prereqs']: children[p_].append(c['cid'])
fig, ax = plt.subplots(figsize=(4.4, 2.3))
for c in cs.values():
    for p_ in c['prereqs']:
        on = c['cid'] in chain and p_ in chain; skip = cs[c['cid']]['tier'] - cs[p_]['tier'] > 1
        ax.add_patch(FancyArrowPatch(pos[p_], pos[c['cid']], arrowstyle='-', connectionstyle=f"arc3,rad={-0.12 if skip else 0.0}", color=C['red'] if on else '#cccccc', lw=1.3 if on else .5, zorder=2 if on else 1, shrinkA=3, shrinkB=3))
for cid, (x0, y0) in pos.items():
    ax.scatter([x0], [y0], s=26, zorder=3, color=C['red'] if cid in chain else 'white', edgecolor=C['red'] if cid in chain else '#555555', marker='s' if not children[cid] else 'o', lw=.8)
x0, y0 = pos['G01']; ax.text(x0 + .025, y0 - .05, 'G01', ha='left', va='top', fontsize=8, zorder=4, fontweight='bold')
for t_ in by_t: ax.text(-.02, -t_, f'layer {"ABCDEFG"[t_]}', ha='right', va='center', fontsize=7.5, color=C['grey'])
ax.set_xlim(-.14, 1.02); ax.set_ylim(-6.5, .5); ax.axis('off')
save(fig, 'graph.pdf')

# ---- plans on the graph
E = group(load('ef_rows.csv'), 'rule', 'cpol', 'dpol'); XG = group(load('extra_rows.csv'), 'group', 'rule', 'cpol', 'dpol')
vers = ['nocap_bH0', 'nocap_bH02', 'nocap_bH05', 'c60_bH0', 'c70_bH0', 'c85_bH0', 'nocap_J60', 'c60_J60']
short = ['no cap', f'no cap,\n{GHF} = 0.02', f'no cap,\n{GHF} = 0.05', 'cap 0.6', 'cap 0.7', 'cap 0.85', f'no cap,\n{GHS} = 0.6', f'cap 0.6,\n{GHS} = 0.6']
def bars(ax, xs, groups, key, w, color, label, top=2000):
    meds, lo, hi = [], [], []
    for rs in groups:
        q1, q2, q3 = quart([num(r[key]) for r in rs])
        meds.append(q2); lo.append(q2 - q1); hi.append((top if q3 == INF else q3) - q2)
    ax.bar(xs, meds, w, color=color, label=label, zorder=2); ax.errorbar(xs, meds, yerr=[lo, hi], fmt='none', **EB)
    return [m + h for m, h in zip(meds, hi)]
fig, ax = plt.subplots(figsize=(7.0, 3.0)); x = np.arange(len(vers)); w = .26; tops = {}
for i, (pol, lab, col) in enumerate((('random', 'random', C['grey']), ('easyfirst', 'all easy first', C['blue']), ('e3h', 'easy until 3 right', C['green']))):
    groups = [E[(r, 'path', pol)] if pol != 'e3h' else XG[('newpol', r, 'path', 'e3h')] for r in vers]
    ends = bars(ax, x + (i - 1) * w, groups, 't_end', w, col, lab)
    for k_, e in enumerate(ends): tops[k_] = max(tops.get(k_, 0), e)
for i, r in enumerate(vers):
    wn, ls, _, n = paired(XG[('newpol', r, 'path', 'e3h')], E[(r, 'path', 'random')], 't_end')
    ax.text(i, tops[i] + 6, f'3 right faster\nthan random\nfor {wn}/{n}', ha='center', fontsize=6)
ax.set_xticks(x); ax.set_xticklabels(short, fontsize=7); ax.set_ylabel('median questions to G01'); ax.set_ylim(0, max(tops.values()) * 1.24)
ax.legend(fontsize=7, loc='upper center', bbox_to_anchor=(.5, -.22), ncol=3)
save(fig, 'easyfirst.pdf')

# ---- how many easy questions first
fig, ax = plt.subplots(figsize=(5.0, 2.6)); ks = [2, 4, 8, 12, 16]; allhi = []
NAMES = dict(nocap_bH0='no cap', nocap_bH05=f'no cap, {GHF} = 0.05', c60_bH0='cap 0.6', c60_J60=f'cap 0.6, {GHS} = 0.6')
for (r, col), nudge in zip((('nocap_bH0', C['blue']), ('nocap_bH05', C['sky']), ('c60_bH0', C['orange']), ('c60_J60', C['purple'])), (-.24, -.08, .08, .24)):
    ys, lo, hi = [], [], []
    for k in ks:
        q1, q2, q3 = quart([num(z['t_end']) for z in E[(r, 'path', f'k{k}')]])
        q3 = 2000 if q3 == INF else q3
        ys.append(q2); lo.append(q2 - q1); hi.append(q3 - q2); allhi.append(q3)
    xs = [k + nudge for k in ks]
    ax.plot(xs, ys, marker='o', ms=3, color=col, label=NAMES[r])
    ax.errorbar(xs, ys, yerr=[lo, hi], fmt='none', ecolor=col, elinewidth=.7, capsize=1.6, capthick=.7)
    rnd = med_reach(E[(r, 'path', 'random')], 't_end')[0]
    ax.axhline(rnd, color=col, ls=':', lw=.9); allhi.append(rnd)
ax.set_xticks([0] + ks); ax.set_xlim(0, 17); ax.set_xlabel('$n_E$, easy questions asked first on each concept, then hard only')
top = max(a for a in allhi if a < INF) * 1.08
ax.set_ylabel('median questions to G01'); ax.set_ylim(0, top); ax.legend(fontsize=7, loc='upper center', ncol=2)
ax.text(.4, top * .03, 'dotted = random', ha='left', fontsize=7, color=C['grey'])
save(fig, 'dose.pdf')

# ---- the mastery test on the graph
pols = [('random', 'random', C['grey'], lambda r: E[(r, 'ct', 'random')]), ('easyfirst', 'all easy first', C['blue'], lambda r: E[(r, 'ct', 'easyfirst')]),
        ('e3h', 'easy until 3 right', C['green'], lambda r: XG[('newpol', r, 'ct', 'e3h')]), ('k16', '16 easy first', C['purple'], lambda r: E[(r, 'ct', 'k16')])]
# the short report prints this figure at full text width, so it gets its own wider file with larger labels
for FS, XF, LF, NAME, YL in (((5.4, 3.5), 6.3, 7, 'false_marks.pdf', ('students with a\nfalse mark (%)', 'students with whole\nchain learned (%)')), ((6.7, 3.0), 8, 8, 'false_marks_wide.pdf', ('false mark (%)', 'whole chain\nlearned (%)'))):
    fig, axs = plt.subplots(2, 1, figsize=FS, sharex=True); x = np.arange(len(vers)); w = .2
    SG = pd.read_csv(os.path.join(U, 'sweep2', 'out', 'analysis', 'graph_summary.csv.gz'))
    RV = dict(nocap_bH0=(.9, 0., 1.), nocap_bH02=(.9, .02, 1.), nocap_bH05=(.9, .05, 1.), c60_bH0=(.9, 0., .6), c70_bH0=(.9, 0., .7), c85_bH0=(.9, 0., .85), nocap_J60=(.6, 0., 1.), c60_J60=(.6, 0., .6))
    def thousand(r):
        J_, b_, c_ = RV[r]
        x_ = SG[(SG.arm == 'joint') & (SG.tutor == 'ct') & (SG.plan == 'random') & (SG.g == .45) & (SG.f == .1) & (SG.J == J_) & (SG.bH == b_) & (SG.c == c_)]
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
    axs[0].set_ylabel(YL[0]); axs[1].set_ylabel(YL[1])
    for ax in axs: ax.set_ylim(0, 105)
    axs[1].set_xticks(x); axs[1].set_xticklabels(short, fontsize=XF); axs[0].legend(fontsize=LF, ncol=4, loc='lower center', bbox_to_anchor=(.5, 1.0))
    save(fig, NAME)

# ---- false marks against the cap, main values, 1,000 students
bl = SG[(SG.g == .45) & (SG.J == .9) & (SG.f == .1) & (SG.bH == 0) & (SG.tutor == 'ct') & (SG.plan == 'random') & SG.arm.isin(['joint', 'cap_table'])].drop_duplicates('c').sort_values('c')
k = (bl.false_any * bl.n).round().astype(int).values; n = bl.n.values
W = np.array([wilson(a, b) for a, b in zip(k, n)]) * 100; sh = 100 * k / n
fig, ax = plt.subplots(figsize=(5.0, 2.2))
ax.errorbar(bl.c, sh, yerr=[np.maximum(0, sh - W[:, 0]), np.maximum(0, W[:, 1] - sh)], fmt='-o', ms=3, color=C['red'], ecolor='#333333', elinewidth=.7, capsize=1.6, capthick=.7, clip_on=False, zorder=3)
ax.axvline(.8, ls=':', color=C['grey']); ax.text(.79, 2, 'learned level 0.8', fontsize=7, color=C['grey'], ha='right')
ax.set_xlabel(f'cap {CAP} (1 means no cap)'); ax.set_ylabel('% of students with at least\none false mark'); ax.set_xlim(0, 1.02); ax.set_ylim(bottom=0)
save(fig, 'false_vs_cap.pdf')
# ---- BKT student and BKT tutor: belief against truth, and what wrong numbers do. Read from the committed result files.
SD = os.path.join(HERE, 'sep_data')
c4 = pd.read_csv(os.path.join(SD, 'check1_calibration_400learners.csv')).dropna(); mo = pd.read_csv(os.path.join(SD, 'mismatch_one.csv'))
fig, axs = plt.subplots(1, 3, figsize=(6.2, 2.1), gridspec_kw={'width_ratios': [.85, 1.1, 1.1]})
ax = axs[0]; ax.plot([0, 1], [0, 1], ls=':', color=C['grey'], lw=1)
ax.errorbar(c4.mean_belief, c4.frac_truly_known, yerr=c4.ci95, fmt='o', ms=3, color=C['blue'], ecolor='#333333', elinewidth=.7, capsize=1.6, capthick=.7, zorder=3, clip_on=False)
ax.set_xlim(0, 1); ax.set_ylim(0, 1.02); ax.set_xlabel(r"tutor's belief $p_{know}$"); ax.set_ylabel('share truly knowing'); ax.set_title('Right numbers', fontsize=8)
NM = (('p_T', r'$p_{learn}$', C['red']), ('p_G', r'$p_{guess}$', C['blue']), ('p_S', r'$p_{slip}$', C['orange']))
for pn, lab, col in NM:
    z = mo[mo.parameter == pn].sort_values('error')
    axs[1].errorbar(z.error, z.calib_gap, yerr=z.calib_gap_ci95, fmt='-o', ms=2.5, lw=1.2, color=col, ecolor=col, elinewidth=.7, capsize=1.4, capthick=.7, label=lab)
    k_ = (z.false_alarm_rate * z.n_declared).round().astype(int).values; n_ = z.n_declared.values; W_ = np.array([wilson(a, b) for a, b in zip(k_, n_)]) * 100; sh_ = 100 * k_ / n_
    axs[2].errorbar(z.error, sh_, yerr=[np.maximum(0, sh_ - W_[:, 0]), np.maximum(0, W_[:, 1] - sh_)], fmt='-o', ms=2.5, lw=1.2, color=col, ecolor=col, elinewidth=.7, capsize=1.4, capthick=.7, label=lab)
axs[1].axhline(0, color=C['grey'], lw=.6, ls=':'); axs[1].axvline(0, color=C['grey'], lw=.6, ls=':'); axs[2].axvline(0, ymax=.6, color=C['grey'], lw=.6, ls=':')
axs[1].set_ylabel('gap: truly known minus belief', fontsize=8); axs[2].set_ylabel('false marks (% of marks)'); axs[2].set_ylim(bottom=0)
axs[1].set_title('Wrong numbers: gap', fontsize=8); axs[2].set_title('Wrong numbers: false marks', fontsize=8)
for ax in axs[1:]:
    ax.set_xlabel("tutor's value minus true value", fontsize=7.5); ax.set_xticks([-.2, -.1, 0, .1, .2]); ax.tick_params(axis='x', labelsize=7.5)
axs[2].legend(fontsize=6.5, loc='upper center', bbox_to_anchor=(.5, 1.0), handlelength=1.2)
save(fig, 'tutor_numbers.pdf')

# ---- plain report (A4, 1 inch margins, text width 6.27 in): print-size copies, included at their natural size, so every label
# prints at 7.5 to 8.5 pt. Each keeps the printed height of the scaled figure it replaces, so the page count does not change.
def plain_figs():
    rc = {'font.size': 8.5, 'xtick.labelsize': 8, 'ytick.labelsize': 8, 'legend.fontsize': 8, 'axes.titlesize': 8.5}
    with plt.rc_context(rc):
        # the concept graph, beside its caption at .4 of the text width
        fig, ax = plt.subplots(figsize=(3.1, 1.65))
        for c in cs.values():
            for p_ in c['prereqs']:
                on = c['cid'] in chain and p_ in chain; skip = cs[c['cid']]['tier'] - cs[p_]['tier'] > 1
                ax.add_patch(FancyArrowPatch(pos[p_], pos[c['cid']], arrowstyle='-', connectionstyle=f"arc3,rad={-0.12 if skip else 0.0}", color=C['red'] if on else '#c4c4c4', lw=1.0 if on else .4, zorder=2 if on else 1, shrinkA=2, shrinkB=2))
        for cid, (x0, y0) in pos.items():
            ax.scatter([x0], [y0], s=15, zorder=3, color=C['red'] if cid in chain else 'white', edgecolor=C['red'] if cid in chain else '#555555', marker='s' if not children[cid] else 'o', lw=.6)
        x0, y0 = pos['G01']; ax.text(x0 + .03, y0 - .1, 'G01', ha='left', va='top', fontsize=8, zorder=4, fontweight='bold')
        for t_ in by_t: ax.text(-.015, -t_, 'ABCDEFG'[t_], ha='right', va='center', fontsize=8, color=C['grey'])
        ax.set_xlim(-.07, 1.02); ax.set_ylim(-6.6, .45); ax.axis('off'); fig.subplots_adjust(0, 0, 1, 1); fig.savefig(os.path.join(FIG, 'graph_plain.pdf'), metadata={'CreationDate': None}); plt.close(fig)
        # expected gain from one question
        fig, axs = plt.subplots(1, 2, figsize=(6.2, 2.35), sharey=True)
        for ax, k, t in ((axs[0], 'today, marked answer', 'Existing right-answer rule'), (axs[1], 'proposed, really solving', f'Easy-hard rule, cap {CAP} = 0.6')):
            rs = G[(k,)]; m = [float(r['m']) for r in rs]
            ax.plot(m, [float(r['gain_easy']) for r in rs], color=C['blue'], label='easy question\n(difficulty $d$ = 0.2)', clip_on=False, zorder=3)
            ax.plot(m, [float(r['gain_hard']) for r in rs], color=C['red'], label='hard question\n(difficulty $d$ = 0.8)', clip_on=False, zorder=3)
            ax.set_title(t); ax.set_xlabel('true mastery $m$\nbefore the question'); ax.set_xlim(0, 1); ax.set_xticks([0, .5, 1])
        rs = G[('proposed, really solving, no cap',)]
        axs[1].plot([float(r['m']) for r in rs], [float(r['gain_easy']) for r in rs], color=C['blue'], ls=':', lw=1.2, label='easy question,\nwith no cap', clip_on=False, zorder=3)
        axs[1].legend(loc='upper left', bbox_to_anchor=(1.02, 1.0), handlelength=1.6); axs[0].set_ylabel('expected gain: rise\nin true mastery $m$\nfrom one question'); axs[0].set_ylim(0, .31)
        save(fig, 'gain_plain.pdf')
        # mastery over questions on one concept, the same students as traj.pdf
        fig, axs = plt.subplots(1, 2, figsize=(6.2, 2.35), sharey=True)
        for ax, v, p, t in zip(axs, ('capped at 0.6', 'no cap'), (MS.CAP, MS.NOCAP), (f'Easy-hard rule, cap {CAP} = 0.6', 'Easy-hard rule, no cap')):
            thr = float(S[(v, 'best switch rule')]['switch_m'])
            for pol, f, col, lab in (('easy only', lambda m, q: np.zeros(m.shape, bool), C['blue'], 'easy only'), ('hard only', lambda m, q: np.ones(m.shape, bool), C['red'], 'hard only'), ('best switch rule', lambda m, q: m >= thr, C['green'], 'best switch (easy until the\nbest switch level, then hard)')):
                a = traj(p, f); ref = sorted(TR[(v, pol)], key=lambda r: int(r['q']))
                assert all(abs(a[i, 3] - float(ref[i]['mean_m'])) < 1e-4 for i in range(61)), (v, pol)
                q = np.arange(31); a = a[:31]
                ax.fill_between(q, a[:, 0], a[:, 2], color=col, alpha=.18, lw=0)
                ax.plot(q, a[:, 1], color=col, label=lab, clip_on=False, zorder=3)
                if pol == 'hard only': ax.plot(q, a[:, 3], color=col, ls='--', lw=1.1, label='hard only, mean\n(dashed)', clip_on=False, zorder=3)
            ax.axhline(.9, ls=':', color=C['grey']); ax.text(30, .86, 'goal $m$ = 0.9', ha='right', va='top', fontsize=7.5, color=C['grey'])
            ax.set_title(t); ax.set_xlabel('questions asked'); ax.set_xlim(0, 30)
        axs[0].set_ylabel('true mastery $m$\nof the concept'); axs[0].set_ylim(0, 1.02); axs[0].set_yticks([0, .5, 1])
        axs[1].legend(loc='upper left', bbox_to_anchor=(1.02, 1.0), handlelength=1.6, title='Plan (solid line: median\nmastery at each question;\nband: 25th to 75th\npercentile)', title_fontsize=7.5, alignment='left')
        save(fig, 'traj_plain.pdf')
        # the mastery test on the graph, the same counts as false_marks_wide.pdf
        fig, axs = plt.subplots(2, 1, figsize=(6.2, 4.7), sharex=True); x = np.arange(len(vers)); w = .21
        PLAB = {'random': 'random', 'easyfirst': 'all easy first (then hard)', 'e3h': 'easy until 3 right (then hard)', 'k16': '16 easy first (then hard)'}
        for i, (p, lab, col, get) in enumerate(pols):
            n = [len(get(r)) for r in vers]
            a = [sum(float(z.get('false_decl@2000') or z.get('false_decl')) > 0 for z in get(r)) for r in vers]
            b = [sum(num(z['t_closure']) < INF for z in get(r)) for r in vers]
            if p == 'random':
                n = [1000] * len(vers); a = [int(round(thousand(r).false_any * 1000)) for r in vers]; b = [int(round(thousand(r).reach * 1000)) for r in vers]
            for ax, k in ((axs[0], a), (axs[1], b)):
                sh = np.array([100 * u / v for u, v in zip(k, n)]); W = np.array([wilson(u, v) for u, v in zip(k, n)]) * 100
                ax.bar(x + (i - 1.5) * w, sh, w, color=col, label=PLAB[p], zorder=2)
                ax.errorbar(x + (i - 1.5) * w, sh, yerr=[np.maximum(0, sh - W[:, 0]), np.maximum(0, W[:, 1] - sh)], fmt='none', **EB)
        axs[0].set_ylabel('% of students'); axs[1].set_ylabel('% of students')
        axs[0].set_title('Top: students with at least one false mark\n(a concept marked learned that is not truly learned)', loc='left', fontsize=8.5)
        axs[1].set_title('Bottom: students who finish (truly learn G01 and the 13 concepts it needs)\nwithin 2,000 questions', loc='left', fontsize=8.5)
        for ax in axs:
            ax.set_ylim(0, 105); ax.set_yticks([0, 25, 50, 75, 100])
            ax.yaxis.grid(True, color='#d9d9d9', lw=.6); ax.set_axisbelow(True)
        eq = lambda g, v: '$' + g.strip('$') + r'\!=\!' + v + '$'
        short_p = ['no cap', 'no cap,\n' + eq(GHF, '0.02'), 'no cap,\n' + eq(GHF, '0.05'), 'cap 0.6', 'cap 0.7', 'cap 0.85', 'no cap,\n' + eq(GHS, '0.6'), 'cap 0.6,\n' + eq(GHS, '0.6')]
        axs[1].set_xticks(x); axs[1].set_xticklabels(short_p, fontsize=7.5); axs[1].set_xlabel('Setting: the cap ' + CAP + ' on easy questions, at the main gain sizes unless named.\n' + GHS + ': gain size after solving a hard question (main 0.9); ' + GHF + ': gain size after failing one (main 0).', fontsize=7.5); axs[0].legend(ncol=2, loc='lower center', bbox_to_anchor=(.5, 1.27), title='Plan inside the concept, as in Table 3 (black lines: 95% Wilson intervals)', title_fontsize=8.5)
        save(fig, 'false_marks_plain.pdf')
plain_figs()

print('report figures:', sorted(os.listdir(FIG)))
