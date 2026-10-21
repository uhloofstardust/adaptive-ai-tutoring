"""All figures for the report, from data/*.csv only. Writes figs/*.pdf (vector)."""
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
def save(fig, name): fig.tight_layout(); fig.savefig(os.path.join(FIG, name)); plt.close(fig)

# F1 one-step gain
rows = load('single_gain.csv'); G = group(rows, 'model')
fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.4), sharey=True)
titles = {'today': 'Today\'s simulator', 'idea, learn from marked answer': 'Idea, learning from the\nmarked answer',
          'idea, learn from solving': 'Idea, learning only from\nreally solving'}
for ax, (k, t) in zip(axs, titles.items()):
    rs = G[(k,)]; m = [float(r['m']) for r in rs]
    ax.plot(m, [float(r['gain_easy']) for r in rs], color=C['blue'], label='easy question')
    ax.plot(m, [float(r['gain_hard']) for r in rs], color=C['red'], label='hard question')
    ax.set_title(t, fontsize=9); ax.set_xlabel('mastery before the question')
axs[0].set_ylabel('expected gain\nfrom one question'); axs[0].legend(loc='upper right', fontsize=7)
save(fig, 'f1_gain.pdf')

# F2 switch point vs bH
rows = load('single_switch.csv'); G = group(rows, 'cE')
fig, ax = plt.subplots(figsize=(4.6, 2.6))
for (cE,), col in zip(sorted(G), (C['sky'], C['blue'], C['purple'])):
    rs = sorted(G[(cE,)], key=lambda r: float(r['bH']))
    ax.plot([float(r['bH']) for r in rs], [float(r['switch_m']) for r in rs], marker='o', ms=3, color=col, label=f'easy limit {cE}')
ax.set_xlabel('what one failed hard question teaches')
ax.set_ylabel('mastery at which hard\nstarts to teach more'); ax.legend(fontsize=7)
ax.set_ylim(-0.06, 0.42)
ax.text(0.1, -0.045, 'a value of 0 means hard is always better', ha='right', va='bottom', fontsize=7, color=C['grey'])
save(fig, 'f2_switch.pdf')

# F3 trajectories
rows = load('single_traj.csv'); G = group(rows, 'version', 'policy')
fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.5), sharey=True)
for ax, v, t in zip(axs, ('capped at 0.6', 'slow (30% speed)'), ('Reading (b): easy capped at 0.6', 'Reading (a): easy at 30% speed, no cap')):
    for pol, col in (('easy only', C['blue']), ('hard only', C['red']), ('best switch rule', C['green'])):
        rs = sorted(G[(v, pol)], key=lambda r: int(r['q']))
        ax.plot([int(r['q']) for r in rs], [float(r['mean_m']) for r in rs], color=col, label=pol)
    ax.axhline(0.9, ls=':', color=C['grey']); ax.text(60, 0.91, 'target 0.9', ha='right', fontsize=7, color=C['grey'])
    ax.set_title(t, fontsize=9); ax.set_xlabel('questions asked')
axs[0].set_ylabel('average true mastery'); axs[1].legend(*axs[0].get_legend_handles_labels(), loc='center right', bbox_to_anchor=(1.0, 0.5), fontsize=7)
save(fig, 'f3_traj.pdf')

# F4 different students
sw = [float(r['best_switch']) for r in load('single_hetero.csv')]
ad = load('single_adapt.csv')
fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.5))
axs[0].hist(sw, bins=20, color=C['blue']); axs[0].set_xlabel('best switch point for this student'); axs[0].set_ylabel('students (of 400)')
x = np.arange(len(ad)); w = 0.26
for i, (k, lab, col) in enumerate((('oracle_mean', 'best for each student (knows true mastery)', C['green']),
                                   ('best_fixed_mean', 'best fixed plan for everyone', C['orange']),
                                   ('answer_rule_mean', 'simple rule from answers', C['purple']))):
    axs[1].bar(x + (i - 1) * w, [float(r[k]) for r in ad], w, color=col, label=lab)
axs[1].set_xticks(x); axs[1].set_xticklabels([f"0.02 to {r['prior_hi']}" for r in ad])
axs[1].set_xlabel('starting mastery spread across students'); axs[1].set_ylabel('average questions to 0.9')
axs[1].set_ylim(0, 24); axs[1].legend(fontsize=6.5, loc='upper right')
save(fig, 'f4_students.pdf')

# F5 CUSUM fooled
rows = load('single_cusum.csv')
fig, ax = plt.subplots(figsize=(4.6, 2.8)); x = np.arange(len(rows)); w = 0.36
b1 = ax.bar(x - w / 2, [100 * float(r['blind_false_rate']) for r in rows], w, color=C['red'], label='mastery test as in the paper')
b2 = ax.bar(x + w / 2, [100 * float(r['aware_false_rate']) for r in rows], w, color=C['green'], label='test that knows easy is easier')
for bars in (b1, b2):
    for b in bars:
        v = b.get_height(); ax.text(b.get_x() + b.get_width() / 2, v + 2, (f'{v:.1f}' if abs(v - round(v)) > 1e-9 else f'{v:.0f}') + '%', ha='center', fontsize=7)
ax.set_xticks(x); ax.set_xticklabels([f"ceiling {r['ceiling']}" for r in rows]); ax.set_ylabel('% wrongly marked "learned"')
ax.set_ylim(0, 112); ax.set_yticks([0, 20, 40, 60, 80, 100]); ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.16), fontsize=7, ncol=2)
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

# F7 median questions to the end node (G01 + all its prerequisites truly learned), random within concept
ef = load('ef_rows.csv'); E = group(ef, 'rule', 'cpol', 'dpol')
fig, ax = plt.subplots(figsize=(6.4, 2.8)); w = 0.26; x = np.arange(3)
for i, (r, col) in enumerate((('current', C['grey']), ('slow_bH0', C['blue']), ('cap60_bH0', C['orange']))):
    vals = [med_reach(E[(r, c, 'random')], 't_closure')[0] for c in ('path', 'bfs', 'ct')]
    bars = ax.bar(x + (i - 1) * w, vals, w, color=col, label=VERS[r])
    for b, v in zip(bars, vals): ax.text(b.get_x() + w / 2, v + 15, f'{v:g}', ha='center', fontsize=6.5)
ax.set_xticks(x); ax.set_xticklabels(['tutor walks only\nG01\'s chain (best case)', 'tutor teaches the whole\ngraph in order (best case)', 'CurriculumTutor\n(the real algorithm)'])
ax.set_ylabel('median questions until G01\nand its prerequisites\nare all learned'); ax.legend(fontsize=7, loc='upper left')
save(fig, 'f7_reach.pdf')

# F8 concepts learned at t and deepest level reached at t (CurriculumTutor, random within concept; 100 students)
gr = load('graph_rows.csv'); R = group([r for r in gr if r['group'] == 'main' and r['cpol'] == 'ct' and r['dpol'] == 'random'], 'rule')
ts = [100, 200, 300, 500, 1000, 2000]
fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.5))
for r, col in (('current', C['grey']), ('slow_bH0', C['blue']), ('cap60_bH0', C['orange'])):
    rs = R[(r,)]
    axs[0].plot(ts, [statistics.mean(float(x[f'learned@{t}']) for x in rs) for t in ts], marker='o', ms=3, color=col, label=VERS[r])
    axs[1].plot(ts, [statistics.mean(float(x[f'max_tier@{t}']) for x in rs) for t in ts], marker='o', ms=3, color=col, label=VERS[r])
axs[0].set_ylabel('concepts truly learned (of 40)'); axs[1].set_ylabel('average deepest level\ntruly learned')
axs[1].set_yticks(range(-1, 7)); axs[1].set_yticklabels(['none'] + list('ABCDEFG'))
for ax in axs: ax.set_xlabel('questions asked'); ax.axvline(500, ls=':', color=C['grey'])
axs[0].legend(fontsize=7, loc='center right'); axs[0].text(560, 2, 'usual budget: 500 questions', fontsize=7, color=C['grey'])
save(fig, 'f8_progress.pdf')

# F9 what a failed hard question teaches (chain tutor)
X = load('extra_rows.csv'); XG = group(X, 'group', 'rule', 'cpol', 'dpol')
bhs = [('slow_bH0', 0), ('slow_bH005', 0.005), ('slow_bH01', 0.01), ('slow_bH02', 0.02), ('slow_bH05', 0.05)]
fig, ax = plt.subplots(figsize=(5.0, 2.8))
for pol, lab, col in (('hard', 'hard only', C['red']), ('switch', 'easy, then hard at 0.4 (best case)', C['green']),
                      ('random', 'random (the paper)', C['grey']), ('easyfirst', 'all easy first', C['blue'])):
    xs, ys = [], []
    for r, b in bhs:
        m, reach = med_reach(XG[('bh_sweep', r, 'path', pol)], 't_end')
        if m < INF: xs.append(b); ys.append(m)
    ax.plot(xs, ys, marker='o', ms=3, color=col, label=lab)
hm, hr = med_reach(XG[('bh_sweep', 'slow_bH0', 'path', 'hard')], 't_end')
ax.text(0.012, 445, f'at 0, hard only: {100*hr:.0f}% reach G01\nwithin 2000 questions', fontsize=7, color=C['red'], va='top')
ax.set_xlabel('what one failed hard question teaches'); ax.set_ylabel('median questions to G01\n(tutor walks G01\'s chain)')
ax.legend(fontsize=7)
save(fig, 'f9_bh.pdf')

# F10 easy first vs random, chain tutor
vers = ['slow_bH0', 'slow_bH02', 'slow_bH05', 'cap60_bH0', 'cap85_bH0', 'slow_b1', 'cap60_b1']
short = ['slow easy', 'slow, fail\nteaches .02', 'slow, fail\nteaches .05', 'cap 0.6', 'cap 0.85', 'slow,\nsmaller jump', 'cap 0.6,\nsmaller jump']
fig, ax = plt.subplots(figsize=(7.0, 3.1)); x = np.arange(len(vers)); w = 0.28
for i, (pol, lab, col) in enumerate((('random', 'random (the paper)', C['grey']), ('easyfirst', 'all easy first (3-5 easy)', C['blue']))):
    ax.bar(x + (i - 0.5) * w, [med_reach(E[(r, 'path', pol)], 't_end')[0] for r in vers], w, color=col, label=lab)
e3 = [med_reach(XG[('newpol', r, 'path', 'e3h')], 't_end')[0] for r in vers]
ax.scatter(x, e3, marker='D', s=16, color=C['green'], zorder=3, label='easy until 3 right answers, then hard')
for i, r in enumerate(vers):
    wn, ls, _, n = paired(E[(r, 'path', 'easyfirst')], E[(r, 'path', 'random')], 't_end')
    ax.text(i, max([med_reach(E[(r, 'path', p)], 't_end')[0] for p in ('random', 'easyfirst')] + [e3[i]]) + 12,
            f'easy-first faster\nfor {wn}/{n}', ha='center', fontsize=6)
ax.set_xticks(x); ax.set_xticklabels(short, fontsize=7); ax.set_ylabel('median questions to G01'); ax.set_ylim(0, 540)
ax.legend(fontsize=7, loc='upper center', bbox_to_anchor=(0.5, -0.28), ncol=3)
save(fig, 'f10_easyfirst.pdf')

# F11 how many easy questions before hard
fig, ax = plt.subplots(figsize=(5.0, 2.7)); Ks = [2, 4, 8, 12, 16]
for r, col in (('slow_bH0', C['blue']), ('slow_bH05', C['sky']), ('cap60_bH0', C['orange']), ('cap60_b1', C['purple'])):
    ax.plot(Ks, [med_reach(E[(r, 'path', f'k{k}')], 't_end')[0] for k in Ks], marker='o', ms=3, color=col, label=VERS[r])
    ax.axhline(med_reach(E[(r, 'path', 'random')], 't_end')[0], color=col, ls=':', lw=0.9)
ax.set_xticks(Ks); ax.set_xlabel('easy questions asked first on each concept, then hard only')
ax.set_ylabel('median questions to G01'); ax.set_ylim(0, 900); ax.legend(fontsize=7)
ax.text(16, 860, 'dotted = random', ha='right', fontsize=7, color=C['grey'])
save(fig, 'f11_dose.pdf')

# F12 CurriculumTutor: false "learned" and whole-chain truly learned
vers2 = ['slow_bH0', 'slow_bH02', 'slow_bH05', 'cap60_bH0', 'cap85_bH0', 'slow_b1', 'cap60_b1']
short2 = ['slow\neasy', 'slow,\nfail\n.02', 'slow,\nfail\n.05', 'cap\n0.6', 'cap\n0.85', 'slow,\nsmall\njump', 'cap\n0.6,\nsmall\njump']
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.0)); x = np.arange(len(vers2)); w = 0.2
pols = [('random', 'random (the paper)', C['grey'], lambda r: E[(r, 'ct', 'random')]),
        ('easyfirst', 'all easy first', C['blue'], lambda r: E[(r, 'ct', 'easyfirst')]),
        ('e3h', 'easy until 3 right, then hard', C['green'], lambda r: XG[('newpol', r, 'ct', 'e3h')]),
        ('k16', '16 easy first', C['purple'], lambda r: E[(r, 'ct', 'k16')])]
for i, (p, lab, col, get) in enumerate(pols):
    fd = [statistics.mean(float(x_['false_decl@2000'] if 'false_decl@2000' in x_ else x_['false_decl']) for x_ in get(r)) for r in vers2]
    cl = [100 * med_reach(get(r), 't_closure')[1] for r in vers2]
    axs[0].bar(x + (i - 1.5) * w, fd, w, color=col, label=lab); axs[1].bar(x + (i - 1.5) * w, cl, w, color=col, label=lab)
axs[0].set_ylabel('concepts wrongly marked\n"learned" per student'); axs[1].set_ylabel('% of students with all 14\nchain concepts truly learned')
for ax in axs: ax.set_xticks(x); ax.set_xticklabels(short2, fontsize=6.5)
axs[0].legend(fontsize=7); axs[1].set_ylim(0, 105)
save(fig, 'f12_ct.pdf')
print('figures written:', sorted(os.listdir(FIG)))
