"""All figures, from data/*.csv only. Writes figs/*.pdf (vector). Version with the proposed rule.
Axes rule: every numeric axis starts at 0, except Figure 8 right y, whose start is labeled "none".
Bars rule: mean, +/-SD cut at the real range; median, quartile bar; share, 95% Wilson interval.
Axis limits are set after the bars are drawn, and no axis top is typed in."""
import os, sys, json, math
import matplotlib; matplotlib.use('pdf')
import matplotlib.pyplot as plt
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
FIG = os.path.join(HERE, 'figs'); os.makedirs(FIG, exist_ok=True)
C = dict(blue='#0072B2', orange='#E69F00', green='#009E73', red='#D55E00', purple='#CC79A7', sky='#56B4E9', grey='#777777', yellow='#F0E442')
plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 100,
                     'legend.frameon': False, 'pdf.fonttype': 42})
EB = dict(ecolor='#333333', elinewidth=.7, capsize=1.6, capthick=.7, zorder=4)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, name), metadata={'CreationDate': None})   # no date: same bytes on every run
    plt.close(fig)


def qstats(rs, key):
    """(25th, 50th, 75th percentile). A quartile that is infinite is capped by the caller."""
    return quart([num(r[key]) for r in rs])


def bar_median(ax, xs, groups, key, w, color, label, top):
    """Median bars with quartile whiskers. Non-finishers count as infinite; a median at infinity draws no bar."""
    meds, lo, hi = [], [], []
    for rs in groups:
        q1, q2, q3 = qstats(rs, key)
        if q2 == INF:
            meds.append(0.0); lo.append(0.0); hi.append(0.0)
            continue
        meds.append(q2); lo.append(q2 - q1); hi.append((top if q3 == INF else q3) - q2)
    ax.bar(xs, meds, w, color=color, label=label, zorder=2)
    ax.errorbar(xs, meds, yerr=[lo, hi], fmt='none', **EB)
    return meds, [m + h for m, h in zip(meds, hi)]


# F1 one-question gain, 2 x 2. Going across changes P to s, going down changes the rule. Dotted: no cap.
rows = load('single_gain.csv'); G = group(rows, 'model')
fig, axs = plt.subplots(2, 2, figsize=(7.0, 3.9), sharex=True, sharey=True)
PANELS = ((0, 0, 'today, marked answer', "Today's gains,\nlearning from the marked answer (P)"),
          (0, 1, 'today, really solving', "Today's gains,\nlearning from really solving (s)"),
          (1, 0, 'proposed, marked answer', 'Proposed rule, c = 0.6,\nlearning from the marked answer (P)'),
          (1, 1, 'proposed, really solving', 'Proposed rule, c = 0.6,\nlearning from really solving (s)'))
for i, j, k, t in PANELS:
    ax = axs[i, j]; rs = G[(k,)]; m = [float(r['m']) for r in rs]
    ax.plot(m, [float(r['gain_easy']) for r in rs], color=C['blue'], label='easy question', clip_on=False, zorder=3)
    ax.plot(m, [float(r['gain_hard']) for r in rs], color=C['red'], label='hard question', clip_on=False, zorder=3)
    ax.set_title(t, fontsize=8.2)
rs = G[('proposed, really solving, no cap',)]
axs[1, 1].plot([float(r['m']) for r in rs], [float(r['gain_easy']) for r in rs], color=C['blue'], ls=':', lw=1.2, label='easy question, no cap', clip_on=False, zorder=3)
axs[1, 1].legend(loc='upper right', fontsize=7); axs[0, 0].legend(loc='upper right', fontsize=7)
for ax in axs[1]: ax.set_xlabel('mastery m before the question')
for ax in axs[:, 0]: ax.set_ylabel('expected gain\nfrom one question')
axs[0, 0].set_xlim(0, 1); axs[0, 0].set_ylim(bottom=0)
save(fig, 'f1_gain.pdf')

# F2 one-question crossing vs bH
rows = load('single_switch.csv'); G = group(rows, 'c')
fig, ax = plt.subplots(figsize=(4.6, 2.6))
for (c,), col in zip(sorted(G, key=lambda t: float(t[0])), (C['blue'], C['sky'], C['purple'], C['grey'])):
    rs = sorted(G[(c,)], key=lambda r: float(r['bH']))
    rs = [r for r in rs if r['switch_m'] not in ('', 'None')]
    ax.plot([float(r['bH']) for r in rs], [float(r['switch_m']) for r in rs], marker='o', ms=3, color=col,
            label='no cap' if float(c) == 1 else f'cap {c}', clip_on=False, zorder=3)
ax.set_xlabel('$b_H$, what one failed hard question teaches')
ax.set_ylabel('m at which one hard question\nstarts to teach more'); ax.legend(fontsize=7)
ax.set_xlim(left=0); ax.set_ylim(bottom=0)
save(fig, 'f2_switch.pdf')

# F3 average mastery with a +/-SD band, cut at the real range (no student is below the start or above 1)
rows = load('single_traj.csv'); G = group(rows, 'version', 'policy')
fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.5), sharey=True)
for ax, v, t in zip(axs, ('capped at 0.6', 'no cap'), ('Easy capped at 0.6', 'No cap')):
    for pol, col in (('easy only', C['blue']), ('hard only', C['red']), ('best switch rule', C['green'])):
        rs = sorted(G[(v, pol)], key=lambda r: int(r['q']))
        q = [int(r['q']) for r in rs]; mean = np.array([float(r['mean_m']) for r in rs]); sd = np.array([float(r['sd_m']) for r in rs])
        ax.fill_between(q, np.maximum(mean - sd, 0.05), np.minimum(mean + sd, 1.0), color=col, alpha=.14, lw=0)
        ax.plot(q, mean, color=col, label=pol.replace('best switch rule', 'best switch'), clip_on=False, zorder=3)
    ax.axhline(0.9, ls=':', color=C['grey']); ax.text(60, 0.91, 'goal 0.9', ha='right', fontsize=7, color=C['grey'])
    ax.set_title(t, fontsize=9); ax.set_xlabel('questions asked'); ax.set_xlim(left=0)
axs[0].set_ylabel('average true mastery'); axs[0].set_ylim(0, 1.0)
axs[1].legend(*axs[0].get_legend_handles_labels(), loc='center right', bbox_to_anchor=(1.0, .66), fontsize=7)
save(fig, 'f3_traj.pdf')

# F4 different students
sw = [float(r['best_switch']) for r in load('single_hetero.csv')]
ad = load('single_adapt.csv')
fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.5))
axs[0].hist(sw, bins=20, color=C['blue']); axs[0].set_xlabel('best switch for this student'); axs[0].set_ylabel('students (of 400)')
axs[0].set_xlim(left=0)
x = np.arange(len(ad)); w = 0.26
for i, (k, lab, col) in enumerate((('oracle', 'best for each student (sees true m)', C['green']),
                                   ('best_fixed', 'best fixed plan for everyone', C['orange']),
                                   ('answer_rule', 'simple rule from answers', C['purple']))):
    mean = np.array([float(r[f'{k}_mean']) for r in ad]); sd = np.array([float(r[f'{k}_sd']) for r in ad])
    axs[1].bar(x + (i - 1) * w, mean, w, color=col, label=lab, zorder=2)
    axs[1].errorbar(x + (i - 1) * w, mean, yerr=[np.minimum(sd, mean - 1), sd], fmt='none', **EB)   # no student takes fewer than 1
axs[1].set_xticks(x); axs[1].set_xticklabels([f"0.02 to {r['prior_hi']}" for r in ad])
axs[1].set_xlabel('spread of starting mastery across students'); axs[1].set_ylabel('average questions to 0.9')
axs[1].margins(y=.28); axs[1].set_ylim(bottom=0); axs[1].legend(fontsize=6.5, loc='upper right')
save(fig, 'f4_students.pdf')

# F5 mastery test fooled, with 95% Wilson intervals
rows = load('single_cusum.csv')
fig, ax = plt.subplots(figsize=(4.6, 2.8)); x = np.arange(len(rows)); w = 0.36
for off, key, col, lab in ((-w / 2, 'blind_false_rate', C['red'], 'difficulty-blind test (guess rate 0.25)'),
                           (w / 2, 'aware_false_rate', C['green'], 'test that allows for difficulty (guess rate 0.65)')):
    vals = [100 * float(r[key]) for r in rows]; n = [int(r['n']) for r in rows]
    W = [wilson(round(v * k / 100), k) for v, k in zip(vals, n)]
    ax.bar(x + off, vals, w, color=col, label=lab, zorder=2)
    ax.errorbar(x + off, vals, yerr=[[max(0, v - 100 * a) for v, (a, b) in zip(vals, W)], [max(0, 100 * b - v) for v, (a, b) in zip(vals, W)]], fmt='none', **EB)
    for xx, v, (a, b) in zip(x + off, vals, W):
        ax.text(xx, 100 * b + 2, (f'{v:.1f}' if abs(v - round(v)) > 1e-9 else f'{v:.0f}') + '%', ha='center', fontsize=7)
ax.set_xticks(x); ax.set_xticklabels([f"cap {r['cap']}" for r in rows]); ax.set_ylabel('% wrongly marked "learned"')
ax.set_ylim(0, 112); ax.set_yticks([0, 20, 40, 60, 80, 100]); ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12), fontsize=7, ncol=1)
save(fig, 'f5_cusum.pdf')

# F6 the graph with G01's chain highlighted
G2 = os.path.join(HERE, 'data', 'curricula', 'layered_40.json')
cur = json.load(open(G2)); cs = {c['cid']: c for c in cur['concepts']}


def anc(c, acc):
    for p in cs[c]['prereqs']:
        if p not in acc: acc.add(p); anc(p, acc)
    return acc


chain = anc('G01', set()) | {'G01'}
by_t = {}
for c in sorted(cs.values(), key=lambda c: (c['tier'], c['cid'])): by_t.setdefault(c['tier'], []).append(c['cid'])
pos = {cid: ((i + 1) / (len(row) + 1), -t) for t, row in by_t.items() for i, cid in enumerate(row)}
children = {c: [] for c in cs}
for c in cs.values():
    for p in c['prereqs']: children[p].append(c['cid'])
from matplotlib.patches import FancyArrowPatch
fig, ax = plt.subplots(figsize=(7.0, 3.6))
for c in cs.values():
    for p in c['prereqs']:
        on = c['cid'] in chain and p in chain
        skip = cs[c['cid']]['tier'] - cs[p]['tier'] > 1
        ax.add_patch(FancyArrowPatch(pos[p], pos[c['cid']], arrowstyle='-', connectionstyle=f"arc3,rad={-0.12 if skip else 0.0}",
                                     color=C['red'] if on else '#cccccc', lw=1.5 if on else 0.6, zorder=2 if on else 1, shrinkA=6, shrinkB=6))
for cid, (x0, y0) in pos.items():
    sink = not children[cid]
    ax.scatter([x0], [y0], s=190, zorder=3, color=C['red'] if cid in chain else 'white',
               edgecolor=C['red'] if cid in chain else '#555555', marker='s' if sink else 'o', lw=1)
    ax.text(x0, y0, cid, ha='center', va='center', fontsize=6.5, zorder=4, color='white' if cid in chain else 'black')
for t in by_t: ax.text(-0.02, -t, f'level {"ABCDEFG"[t]}', ha='right', va='center', fontsize=7, color=C['grey'])
ax.set_xlim(-0.12, 1.02); ax.set_ylim(-6.5, 0.5); ax.axis('off')
save(fig, 'f6_graph.pdf')

# F7 median questions until G01's whole chain is truly learned, random within a concept, quartile bars
ef = load('ef_rows.csv'); E = group(ef, 'rule', 'cpol', 'dpol')
RSET = (('current', C['grey']), ('nocap_bH0', C['blue']), ('c60_bH0', C['orange']), ('c70_bH0', C['purple']))
fig, ax = plt.subplots(figsize=(6.4, 2.9)); w = 0.2; x = np.arange(3)
tops = []
for i, (r, col) in enumerate(RSET):
    groups = [E[(r, c, 'random')] for c in ('path', 'bfs', 'ct')]
    meds, ends = bar_median(ax, x + (i - 1.5) * w, groups, 't_closure', w, col, VERS[r], 2000)
    tops += ends
    for xx, v, e in zip(x + (i - 1.5) * w, meds, ends): ax.text(xx, e + 15, f'{v:g}', ha='center', fontsize=6.5)
ax.set_xticks(x); ax.set_xticklabels(['chain tutor\n(sees true m)', 'whole-graph tutor\n(sees true m)', 'CurriculumTutor\n(sees only answers)'])
ax.set_ylabel("median questions until G01\nand its prerequisites\nare all learned"); ax.legend(fontsize=7, loc='upper left'); ax.set_ylim(0, max(tops) * 1.12)
save(fig, 'f7_reach.pdf')

# F8 concepts learned at t and deepest level reached at t (CurriculumTutor, random within concept; 100 students), +/-SD bands
gr = load('graph_rows.csv'); R = group([r for r in gr if r['group'] == 'main' and r['cpol'] == 'ct' and r['dpol'] == 'random'], 'rule')
ts = [100, 200, 300, 500, 1000, 2000]
fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.5))
for r, col in (('current', C['grey']), ('nocap_bH0', C['blue']), ('c60_bH0', C['orange'])):
    rs = R[(r,)]
    for ax, key, lo_, hi_ in ((axs[0], 'learned', 0, 40), (axs[1], 'max_tier', -1, 6)):
        mean = np.array([statistics.mean(float(x_[f'{key}@{t}']) for x_ in rs) for t in ts])
        sd = np.array([statistics.pstdev([float(x_[f'{key}@{t}']) for x_ in rs]) for t in ts])
        ax.fill_between(ts, np.maximum(mean - sd, lo_), np.minimum(mean + sd, hi_), color=col, alpha=.14, lw=0)
        ax.plot(ts, mean, marker='o', ms=3, color=col, label=VERS[r], clip_on=False, zorder=3)
axs[0].set_ylabel('concepts truly learned (of 40)'); axs[1].set_ylabel('average deepest level\ntruly learned')
axs[1].set_yticks(range(-1, 7)); axs[1].set_yticklabels(['none'] + list('ABCDEFG')); axs[1].set_ylim(-1, 6)
for ax in axs:
    ax.set_xlabel('questions asked'); ax.axvline(500, ls=':', color=C['grey']); ax.set_xlim(0, 2000); ax.set_xticks([0, 500, 1000, 1500, 2000])
axs[0].set_ylim(0, 40); axs[0].legend(fontsize=7, loc='lower right'); axs[0].text(530, 1.5, 'usual budget: 500', fontsize=7, color=C['grey'])
save(fig, 'f8_progress.pdf')

# F9 what a failed hard question teaches (chain tutor, no cap), quartile bars
X = load('extra_rows.csv'); XG = group(X, 'group', 'rule', 'cpol', 'dpol')
bhs = [('nocap_bH0', 0), ('nocap_bH005', 0.005), ('nocap_bH01', 0.01), ('nocap_bH02', 0.02), ('nocap_bH05', 0.05)]
fig, ax = plt.subplots(figsize=(5.0, 3.0)); allhi = []
PLANS9 = (('hard', 'hard only', C['red'], .0009), ('switch', 'fixed switch at 0.40 (sees true m)', C['green'], .0006),
          ('random', 'random', C['grey'], .0003), ('easyfirst', 'all easy first', C['blue'], 0.0))
for pol, lab, col, nudge in PLANS9:     # nudged to one side only, so that no point falls below x = 0
    xs, ys, lo, hi = [], [], [], []
    for r, b in bhs:
        q1, q2, q3 = qstats(XG[('bh_sweep', r, 'path', pol)], 't_end')
        if q2 < INF:
            q3 = 2000 if q3 == INF else q3
            xs.append(b + nudge); ys.append(q2); lo.append(q2 - q1); hi.append(q3 - q2); allhi.append(q3)
    ax.plot(xs, ys, marker='o', ms=3, color=col, label=lab, clip_on=False, zorder=3)
    ax.errorbar(xs, ys, yerr=[lo, hi], fmt='none', ecolor=col, elinewidth=.7, capsize=1.6, capthick=.7, zorder=3)
hm, hr = med_reach(XG[('bh_sweep', 'nocap_bH0', 'path', 'hard')], 't_end')
ax.set_xlabel('$b_H$, what one failed hard question teaches'); ax.set_ylabel('median questions to G01\n(chain tutor)')
ax.set_xlim(left=0); ax.set_ylim(0, max(allhi) * 1.05)
ax.text(0.012, max(allhi) * 1.02, f'at 0, hard only: {100*hr:.0f}% reach G01\nwithin 2000 questions', fontsize=7, color=C['red'], va='top')
ax.legend(fontsize=7, loc='center right')
save(fig, 'f9_bh.pdf')

# F10 easy first vs random, chain tutor, quartile bars
vers = ['nocap_bH0', 'nocap_bH02', 'nocap_bH05', 'c60_bH0', 'c70_bH0', 'c85_bH0', 'nocap_J60', 'c60_J60']
short = ['no cap', 'no cap,\n$b_H$ .02', 'no cap,\n$b_H$ .05', 'cap 0.6', 'cap 0.7', 'cap 0.85', 'no cap,\n$J$ 0.6', 'cap 0.6,\n$J$ 0.6']
fig, ax = plt.subplots(figsize=(7.0, 3.3)); x = np.arange(len(vers)); w = 0.26
tops = {}
for i, (pol, lab, col) in enumerate((('random', 'random', C['grey']), ('easyfirst', 'all easy first (3-5 easy)', C['blue']), ('e3h', 'easy until 3 right, then hard', C['green']))):
    groups = [E[(r, 'path', pol)] if pol != 'e3h' else XG[('newpol', r, 'path', 'e3h')] for r in vers]
    meds, ends = bar_median(ax, x + (i - 1) * w, groups, 't_end', w, col, lab, 2000)
    for k, e in enumerate(ends): tops[k] = max(tops.get(k, 0), e)
for i, r in enumerate(vers):
    wn, ls, _, n = paired(E[(r, 'path', 'easyfirst')], E[(r, 'path', 'random')], 't_end')
    ax.text(i, tops[i] + 6, f'all easy first\nfaster for\n{wn}/{n}', ha='center', fontsize=6)
ax.set_xticks(x); ax.set_xticklabels(short, fontsize=7); ax.set_ylabel('median questions to G01'); ax.set_ylim(0, max(tops.values()) * 1.22)
ax.legend(fontsize=7, loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3)
save(fig, 'f10_easyfirst.pdf')

# F11 how many easy questions before hard, quartile bars on the curves, none on the dotted reference lines
fig, ax = plt.subplots(figsize=(5.0, 2.9)); ks = [2, 4, 8, 12, 16]; allhi = []
for (r, col), nudge in zip((('nocap_bH0', C['blue']), ('nocap_bH05', C['sky']), ('c60_bH0', C['orange']), ('c60_J60', C['purple'])), (-.24, -.08, .08, .24)):
    ys, lo, hi = [], [], []
    for k in ks:
        q1, q2, q3 = qstats(E[(r, 'path', f'k{k}')], 't_end')
        q3 = 2000 if q3 == INF else q3
        ys.append(q2); lo.append(q2 - q1); hi.append(q3 - q2); allhi.append(q3)
    xs = [k + nudge for k in ks]
    ax.plot(xs, ys, marker='o', ms=3, color=col, label=VERS[r])
    ax.errorbar(xs, ys, yerr=[lo, hi], fmt='none', ecolor=col, elinewidth=.7, capsize=1.6, capthick=.7)
    rnd = med_reach(E[(r, 'path', 'random')], 't_end')[0]
    ax.axhline(rnd, color=col, ls=':', lw=0.9); allhi.append(rnd)
ax.set_xticks([0] + ks); ax.set_xlim(0, 17); ax.set_xlabel('$k$, easy questions asked first on each concept, then hard only')
top = max(a for a in allhi if a < INF) * 1.08
ax.set_ylabel('median questions to G01'); ax.set_ylim(0, top); ax.legend(fontsize=7, loc='upper center', ncol=2)
ax.text(.4, top * .03, 'dotted = random', ha='left', fontsize=7, color=C['grey'])
save(fig, 'f11_dose.pdf')

# F12 CurriculumTutor: false marks (mean, +/-SD cut at 0) and whole chain truly learned (share, Wilson)
short2 = ['no cap', 'no cap,\n$b_H$ .02', 'no cap,\n$b_H$ .05', 'cap 0.6', 'cap 0.7', 'cap 0.85', 'no cap,\n$J$ 0.6', 'cap 0.6,\n$J$ 0.6']
fig, axs = plt.subplots(2, 1, figsize=(7.0, 5.0), sharex=True); x = np.arange(len(vers)); w = 0.2
pols = [('random', 'random', C['grey'], lambda r: E[(r, 'ct', 'random')]),
        ('easyfirst', 'all easy first', C['blue'], lambda r: E[(r, 'ct', 'easyfirst')]),
        ('e3h', 'easy until 3 right, then hard', C['green'], lambda r: XG[('newpol', r, 'ct', 'e3h')]),
        ('k16', '16 easy first', C['purple'], lambda r: E[(r, 'ct', 'k16')])]
for i, (p, lab, col, get) in enumerate(pols):
    fd = [[float(x_['false_decl@2000'] if 'false_decl@2000' in x_ else x_['false_decl']) for x_ in get(r)] for r in vers]
    mean = np.array([statistics.mean(v) for v in fd]); sd = np.array([statistics.pstdev(v) for v in fd])
    k = [sum(num(z['t_closure']) < INF for z in get(r)) for r in vers]; n = [len(get(r)) for r in vers]
    share = np.array([100 * a / b for a, b in zip(k, n)]); W = [wilson(a, b) for a, b in zip(k, n)]
    xx = x + (i - 1.5) * w
    axs[0].bar(xx, mean, w, color=col, label=lab, zorder=2); axs[0].errorbar(xx, mean, yerr=[np.minimum(sd, mean), sd], fmt='none', **EB)
    axs[1].bar(xx, share, w, color=col, label=lab, zorder=2)
    axs[1].errorbar(xx, share, yerr=[np.maximum(0, share - np.array([100 * a for a, b in W])), np.maximum(0, np.array([100 * b for a, b in W]) - share)], fmt='none', **EB)
axs[0].set_ylabel('false marks per student\n(concepts wrongly marked "learned")'); axs[1].set_ylabel('% of students with all 14\nchain concepts truly learned')
axs[1].set_xticks(x); axs[1].set_xticklabels(short2, fontsize=7)
axs[0].set_ylim(bottom=0); axs[0].legend(fontsize=7, ncol=4, loc='lower center', bbox_to_anchor=(.5, 1.0)); axs[1].set_ylim(0, 105)
save(fig, 'f12_ct.pdf')
print('figures written:', sorted(os.listdir(FIG)))
