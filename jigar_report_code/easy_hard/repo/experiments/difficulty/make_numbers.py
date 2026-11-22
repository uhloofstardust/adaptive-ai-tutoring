"""Every simulation number quoted in report.tex, computed from data/*.csv only.
Writes gen/numbers.tex (keys used as \\V{key}) and gen/t_*.tex tables."""
import os, sys, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
GEN = os.path.join(HERE, 'gen'); os.makedirs(GEN, exist_ok=True)
V = {}
def fm(x, d=1):
    if x == INF: return '$>$2000'
    if abs(x - round(x)) < 1e-9: return f'{int(round(x))}'
    return f'{x:.{d}f}'
def pct(x): return f'{100 * x:.0f}'
def pct1(x):
    v = round(100 * x, 1)
    return f'{v:.0f}' if abs(v - round(v)) < 1e-9 else f'{v:.1f}'
def put(k, v): assert k not in V, k; V[k] = v

# ---------- single concept ----------
S = {(r['version'], r['policy']): r for r in load('single_schedule.csv')}
cap, nocap, capb, nocapb, c70, c85 = 'capped at 0.6', 'no cap', 'capped at 0.6, failed hard teaches 0.05', 'no cap, failed hard teaches 0.05', 'capped at 0.7', 'capped at 0.85'
put('s.cap.sw', f"{float(S[(cap,'best switch rule')]['switch_m']):.2f}")
put('s.nocap.sw', f"{float(S[(nocap,'best switch rule')]['switch_m']):.2f}")
for tag, v in (('cap', cap), ('nocap', nocap), ('capb', capb), ('nocapb', nocapb), ('c70', c70), ('c85', c85)):
    put(f's.{tag}.exact', S[(v,'best switch rule')]['exact_best'])
    put(f's.{tag}.opt', f"{float(S[(v,'best switch rule')]['mean_q']):.1f}")
    put(f's.{tag}.fixk', S[(v, 'best fixed')]['best_fixed_k'])
    put(f's.{tag}.fix', f"{float(S[(v,'best fixed')]['mean_q']):.1f}")
    h = S[(v, 'hard only')]
    put(f's.{tag}.hardreach', pct(float(h['reach400'])))
    put(f's.{tag}.hard', f"{float(h['mean_q']):.1f}" if h['mean_q'] else '')
    e = S[(v, 'easy only')]
    put(f's.{tag}.easy', f"{float(e['mean_q']):.1f}" if e['mean_q'] else 'never')
put('s.hardmed', fm(float(S[(cap, 'hard only')]['median_q'])))
SW = {(r['c'], r['bH']): r for r in load('single_switch.csv')}
for c in ('0.6', '0.7', '0.85', '1.0'):
    put(f'sw.{c}', f"{float(SW[(c,'0.0')]['switch_m']):.3f}")
    _ab = [float(b) for (cc, b), r in SW.items() if cc == c and r['hard_always'] == '1']
    put(f'sw.{c}.always', f'{min(_ab):.2f}' if _ab else 'none on grid')
SU = {r['version']: r for r in load('single_success.csv')}
put('succ.cap', pct(float(SU[cap]['overall_p_right']))); put('succ.nocap', pct(float(SU[nocap]['overall_p_right'])))
for m in ('0.4', '0.9'):
    put(f'pr.{m}.e', pct(float(SU[f'P at mastery {m}']['overall_p_right'])))
    put(f'pr.{m}.h', pct(float(SU[f'P at mastery {m}']['p_right_on_hard'])))
sw = [float(r['best_switch']) for r in load('single_hetero.csv')]
put('het.min', f'{min(sw):.2f}'); put('het.med', f'{statistics.median(sw):.2f}'); put('het.max', f'{max(sw):.2f}')
for r in load('single_adapt.csv'):
    h = r['prior_hi']
    put(f'ad.{h}.o', f"{float(r['oracle_mean']):.1f}"); put(f'ad.{h}.f', f"{float(r['best_fixed_mean']):.1f}")
    put(f'ad.{h}.gap', f"{float(r['gap_fixed_minus_oracle']):.1f}"); put(f'ad.{h}.r', f"{float(r['answer_rule_mean']):.1f}")
    put(f'ad.{h}.fr', f"{float(r['fixed_minus_rule']):+.1f}".replace('-', '$-$'))
    fr = float(r['fixed_minus_rule'])
    put(f'ad.{h}.phrase', f"{abs(fr):.1f} questions {'slower' if fr < 0 else 'faster'}")
    put(f'ad.{h}.n_row', r['answer_rule_n_row'])
for r in load('single_cusum.csv'):
    c = r['cap']
    put(f'cu.{c}.b', pct1(float(r['blind_false_rate']))); put(f'cu.{c}.a', pct1(float(r['aware_false_rate'])))
    put(f'cu.{c}.q', fm(float(r['blind_median_q'])))

# ---------- graph: rows.csv (100 students), ef_rows.csv (200), extra_rows.csv (200) ----------
GR = group(load('graph_rows.csv'), 'group', 'rule', 'cpol', 'dpol', 'profile', 'override')
def g(rule, cpol, dpol, grp='main', prof='average', ov=''): return GR[(grp, rule, cpol, dpol, prof, ov)]
E = group(load('ef_rows.csv'), 'rule', 'cpol', 'dpol')
X = group(load('extra_rows.csv'), 'group', 'rule', 'cpol', 'dpol', 'extra')
def x(grp, rule, cpol, dpol, extra=''): return X[(grp, rule, cpol, dpol, extra)]
# today
put('g.cur.path.min', fm(min(med_reach(g('current', 'path', d), 't_end')[0] for d in ('random', 'easy', 'hard', 'switch', 'e3h'))))
put('g.cur.path.max', fm(max(med_reach(g('current', 'path', d), 't_end')[0] for d in ('random', 'easy', 'hard', 'switch', 'e3h'))))
# Fig 7 numbers (ef, random, closure)
for r in ('current', 'nocap_bH0', 'c60_bH0', 'c70_bH0'):
    for c in ('path', 'bfs', 'ct'):
        m, reach = med_reach(E[(r, c, 'random')], 't_closure')
        put(f'f7.{r}.{c}', fm(m))
        v = [num(z['t_closure']) for z in E[(r, c, 'random')]]
        put(f'f7.{r}.{c}.r500', pct(sum(t <= 500 for t in v) / len(v)))
        put(f'f7.{r}.{c}.n500', str(sum(t <= 500 for t in v)))
        put(f'f7.{r}.{c}.never', pct1(1 - reach))
for r in ('nocap_bH0', 'c60_bH0', 'c70_bH0'):
    a = med_reach(E[(r, 'bfs', 'random')], 't_closure')[0]; b = med_reach(E[(r, 'path', 'random')], 't_closure')[0]
    put(f'ratio.{r}', f'{a / b:.1f}')
ctmeds = [med_reach(E[(r, 'ct', d)], 't_closure')[0] for r in ('nocap_bH0', 'c60_bH0', 'c70_bH0', 'c85_bH0') for d in ('random', 'easyfirst', 'k8')]
put('ct.min', fm(min(ctmeds))); put('ct.max', fm(max(ctmeds)))
r500 = [sum(num(z['t_closure']) <= 500 for z in E[(r, 'ct', d)]) / 200 for r in ('nocap_bH0', 'c60_bH0', 'c70_bH0', 'c85_bH0') for d in ('random', 'easyfirst', 'k8')]
put('ct.r500.max', pct(max(r500)))
# Fig 8 (rows, ct random)
for r in ('current', 'nocap_bH0', 'c60_bH0'):
    rs = g(r, 'ct', 'random')
    put(f'f8.{r}.l500', f"{statistics.mean(float(z['learned@500']) for z in rs):.0f}")
# graph table T2 (rows.csv, 100 students): chain tutor with each within-concept choice, whole graph with switch
def cell(rs, key='t_end'):
    m, reach = med_reach(rs, key)
    return fm(m) if m < INF else f'never ({pct(reach)}\\%)' if reach == 0 else f'$>$2000 ({pct(reach)}\\%)'
T2 = []
for r in ('current', 'nocap_bH0', 'nocap_bH05', 'c60_bH0', 'c70_bH0', 'c85_bH0'):
    T2.append(' & '.join([VERS[r].replace('failed hard teaches', 'a failed hard teaches')] + [cell(g(r, 'path', d)) for d in ('easy', 'hard', 'random', 'switch')] + [cell(g(r, 'bfs', 'switch'))]) + r' \\')
open(os.path.join(GEN, 't_graph.tex'), 'w').write('\\gdef\\TGraph{' + '\n'.join(T2) + '}\n')
put('hardonly.reach', pct(med_reach(g('nocap_bH0', 'path', 'hard'), 't_end')[1]))
# capped easy-only on chain never
put('g.cap.easy.reach', pct(med_reach(g('c60_bH0', 'path', 'easy'), 't_end')[1]))
# profiles and prerequisite sensitivity (rows, nocap_bH0 path switch)
put('prof.fast', fm(med_reach(g('nocap_bH0', 'path', 'switch', 'profile', 'fast'), 't_end')[0]))
put('prof.avg', fm(med_reach(g('nocap_bH0', 'path', 'switch'), 't_end')[0]))
put('prof.slow', fm(med_reach(g('nocap_bH0', 'path', 'switch', 'profile', 'slow'), 't_end')[0]))
pq = [med_reach(g('nocap_bH0', 'path', 'switch', 'prereq', 'average', f'prereq_sensitivity={s}'), 't_end')[0] for s in ('0.0', '0.4', '1.0')] + [med_reach(g('nocap_bH0', 'path', 'switch'), 't_end')[0]]
put('preq.min', fm(min(pq))); put('preq.max', fm(max(pq)))
# bH sweep (extra)
for r, tag in (('nocap_bH0', '0'), ('nocap_bH005', '005'), ('nocap_bH01', '01'), ('nocap_bH02', '02'), ('nocap_bH05', '05')):
    for d in ('hard', 'switch', 'random', 'easyfirst'):
        m, reach = med_reach(x('bh_sweep', r, 'path', d), 't_end')
        put(f'bh.{tag}.{d}', fm(m))
        if d == 'hard': put(f'bh.{tag}.hardreach', pct(reach))
# prior knowledge (extra)
for im in ('0.1', '0.3'):
    for d in ('hard', 'switch'):
        m, reach = med_reach(x('prior', 'nocap_bH0', 'path', d, f"overrides={{'init_mastery': {im}}}"), 't_end')
        put(f'prior.{im}.{d}', fm(m)); put(f'prior.{im}.{d}.r', pct(reach))
# skipping prerequisites (extra)
for r, d in (('current', 'random'), ('nocap_bH0', 'switch'), ('c60_bH0', 'switch')):
    put(f'dir.{r}', fm(med_reach(x('direct', r, 'path', d, ';order=G01only'), 't_end')[0]))
    m, reach = med_reach(x('direct', r, 'path', d, "overrides={'prereq_sensitivity': 1.0};order=G01only"), 't_end')
    put(f'dir1.{r}', fm(m)); put(f'dir1.{r}.r', pct(reach))
    put(f'chain1.{r}', fm(med_reach(x('direct', r, 'path', d, "overrides={'prereq_sensitivity': 1.0}"), 't_end')[0]))
put('chain.current', fm(med_reach(E[('current', 'path', 'random')], 't_end')[0]))
put('chain.nocap_bH0', fm(med_reach(E[('nocap_bH0', 'path', 'switch')], 't_end')[0]))
put('chain.c60_bH0', fm(med_reach(E[('c60_bH0', 'path', 'switch')], 't_end')[0]))
# absolute labels (extra)
for r in ('nocap_bH0', 'c60_bH0'):
    for d in ('random', 'switch'):
        put(f'abs.{r}.{d}', pct1(med_reach(x('absolute', r, 'path', d, 'labels=absolute'), 't_end')[1]))

# ---------- easy first vs random ----------
VE = ['nocap_bH0', 'nocap_bH02', 'nocap_bH05', 'c60_bH0', 'c70_bH0', 'c85_bH0', 'nocap_J60', 'c60_J60']
T3 = []; e3wins = 0; efmix_ok = 0
for r in VE:
    rnd, ef = E[(r, 'path', 'random')], E[(r, 'path', 'easyfirst')]
    e3, mix = x('newpol', r, 'path', 'e3h'), x('newpol', r, 'path', 'efmix')
    w, l, d, n = paired(ef, rnd, 't_end')
    w3, l3, d3, _ = paired(e3, rnd, 't_end'); e3wins += w3 > l3
    wm, lm, dm, _ = paired(ef, mix, 't_end'); efmix_ok += wm >= lm
    ks = {k: med_reach(E[(r, 'path', f'k{k}')], 't_end')[0] for k in (2, 4, 8, 12, 16)}
    bk = min(ks, key=ks.get)
    dd = f'{d:+g}'.replace('-', '$-$')
    T3.append(' & '.join([VERS[r], fm(med_reach(rnd, 't_end')[0]), fm(med_reach(ef, 't_end')[0]), f'{w} / {l}', dd,
                          fm(med_reach(mix, 't_end')[0]), fm(med_reach(e3, 't_end')[0]), f'{bk} ({fm(ks[bk])})']) + r' \\')
    put(f'ef.{r}.rnd', fm(med_reach(rnd, 't_end')[0])); put(f'ef.{r}.ef', fm(med_reach(ef, 't_end')[0]))
    put(f'ef.{r}.w', str(w)); put(f'ef.{r}.l', str(l)); put(f'ef.{r}.d', dd)
    put(f'ef.{r}.e3', fm(med_reach(e3, 't_end')[0])); put(f'ef.{r}.bestk', str(bk)); put(f'ef.{r}.bestkv', fm(ks[bk]))
open(os.path.join(GEN, 't_easyfirst.tex'), 'w').write('\\gdef\\TEasy{' + '\n'.join(T3) + '}\n')
put('ef.nocap_bH0.k8', fm(med_reach(E[('nocap_bH0', 'path', 'k8')], 't_end')[0])); put('ef.c60_bH0.k12', fm(med_reach(E[('c60_bH0', 'path', 'k12')], 't_end')[0]))
put('e3.wins', str(e3wins)); put('efmix.ok', str(efmix_ok)); put('nvers', str(len(VE)))
close = min(VE, key=lambda r: (lambda w, l, d, n: w - l)(*paired(E[(r, 'path', 'easyfirst')], x('newpol', r, 'path', 'efmix'), 't_end')))
w, l, d, n = paired(E[(close, 'path', 'easyfirst')], x('newpol', close, 'path', 'efmix'), 't_end')
put('efmix.close.ver', VERS[close]); put('efmix.close.w', str(w)); put('efmix.close.l', str(l))
put('efmix.close.ef', fm(med_reach(E[(close, 'path', 'easyfirst')], 't_end')[0])); put('efmix.close.mix', fm(med_reach(x('newpol', close, 'path', 'efmix'), 't_end')[0]))
gaps = [paired(E[(r, 'path', 'easyfirst')], x('newpol', r, 'path', 'efmix'), 't_end') for r in VE]
put('efmix.clear', str(sum(1 for w_, l_, d_, n_ in gaps if w_ - l_ >= 40)))
clear = [(w_, l_) for w_, l_, d_, n_ in gaps if w_ - l_ >= 40]
put('efmix.minw', str(min(w_ for w_, l_ in clear)) if clear else 'none'); put('efmix.maxl', str(max(l_ for w_, l_ in clear)) if clear else 'none')
put('ef.cur.rnd', fm(med_reach(E[('current', 'path', 'random')], 't_end')[0])); put('ef.cur.ef', fm(med_reach(E[('current', 'path', 'easyfirst')], 't_end')[0]))
for r in ('nocap_bH0', 'c60_bH0', 'c70_bH0', 'c85_bH0', 'nocap_J60'):
    hv = [float(z['m_handover']) for z in x('handover', r, 'path', 'easyfirst') if z['m_handover'] not in ('', 'None')]
    put(f'hand.{r}', f'{statistics.median(hv):.2f}')
# CurriculumTutor bookkeeping (closure metric)
def fd(rs): return statistics.mean(float(z.get('false_decl@2000') or z.get('false_decl')) for z in rs)
def clo(rs): return med_reach(rs, 't_closure')[1]
main3 = ('nocap_bH0', 'nocap_bH02', 'nocap_bH05', 'c60_bH0', 'c70_bH0')
put('fd.rnd.min', f"{min(fd(E[(r,'ct','random')]) for r in main3):.2f}"); put('fd.rnd.max', f"{max(fd(E[(r,'ct','random')]) for r in main3):.2f}")
allv = VE
put('fd.rnd.top', f"{max(fd(E[(r,'ct','random')]) for r in allv):.2f}")
put('fd.ef.min', f"{min(fd(E[(r,'ct','easyfirst')]) for r in allv):.2f}"); put('fd.ef.max', f"{max(fd(E[(r,'ct','easyfirst')]) for r in allv):.2f}")
put('fd.k16.min', f"{min(fd(E[(r,'ct','k16')]) for r in allv):.2f}"); put('fd.k16.max', f"{max(fd(E[(r,'ct','k16')]) for r in allv):.2f}")
put('fd.e3.max', f"{max(fd(x('newpol', r, 'ct', 'e3h')) for r in allv):.2f}")
put('fd.rnd.min7', f"{min(fd(E[(r,'ct','random')]) for r in allv):.2f}"); put('fd.rnd.max7', f"{max(fd(E[(r,'ct','random')]) for r in allv):.2f}")
put('fd.rnd.gt', str(sum(fd(E[(r,'ct','random')]) > fd(E[(r,'ct','easyfirst')]) for r in allv)))
put('cth.rnd.nocap.reach', pct1(clo(x('cthard', 'nocap_bH0', 'ct_hard', 'random')))); put('ct.rnd.nocap.reach', pct1(clo(E[('nocap_bH0', 'ct', 'random')])))
put('clo.rnd.c60J60', pct(clo(E[('c60_J60', 'ct', 'random')]))); put('clo.ef.c60J60', pct(clo(E[('c60_J60', 'ct', 'easyfirst')])))
put('clo.e3.c60J60', pct(clo(x('newpol', 'c60_J60', 'ct', 'e3h'))))
put('clo.rnd.nocapJ60', pct(clo(E[('nocap_J60', 'ct', 'random')]))); put('clo.ef.nocapJ60', pct(clo(E[('nocap_J60', 'ct', 'easyfirst')])))
put('cth.rnd.max', f"{max(fd(x('cthard', r, 'ct_hard', 'random')) for r in allv):.2f}")
put('cth.rnd.nocap', fm(med_reach(x('cthard', 'nocap_bH0', 'ct_hard', 'random'), 't_closure')[0]))
put('ct.rnd.nocap', fm(med_reach(E[('nocap_bH0', 'ct', 'random')], 't_closure')[0]))
put('cth.e3.nocap', fm(med_reach(x('cthard', 'nocap_bH0', 'ct_hard', 'e3h'), 't_closure')[0]))
for r in ('nocap_bH0', 'c60_bH0', 'c60_J60'):
    w, l, d, n = paired(E[(r, 'ct', 'easyfirst')], E[(r, 'ct', 'random')], 't_closure')
    put(f'ctp.{r}.w', str(w)); put(f'ctp.{r}.l', str(l)); put(f'ctp.{r}.d', f'{d:+g}'.replace('-', '$-$'))
    w, l, d, n = paired(x('newpol', r, 'ct', 'e3h'), E[(r, 'ct', 'random')], 't_closure')
    put(f'cte3.{r}.w', str(w)); put(f'cte3.{r}.l', str(l))
# students who never reach the end under CurriculumTutor (random): are they stuck behind a wrong "learned"?
for r in ('nocap_bH0', 'c60_bH0', 'c60_J60'):
    rs = E[(r, 'ct', 'random')]
    nev = [z for z in rs if z['t_closure'] in ('', 'None')]
    put(f'stuck.{r}.n', str(len(nev)))
    put(f'stuck.{r}.false', str(sum(float(z['false_decl@2000']) >= 1 for z in nev)))
    put(f'stuck.{r}.all40', str(sum(float(z['declared@2000']) == 40 for z in nev)))
    for T in (1000, 1500, 2000):
        put(f'stuck.{r}.by{T}', str(sum(num(z['t_closure']) <= T for z in rs)))
# 'easy until 3 right' against random INSIDE CurriculumTutor, whole chain, all 7 versions
cw = 0; lost = []
for r in VE:
    w, l, d, n = paired(x('newpol', r, 'ct', 'e3h'), E[(r, 'ct', 'random')], 't_closure')
    if w > l: cw += 1
    else: lost.append(VERS[r])
put('cte3.wins7', str(cw)); put('cte3.lost', '; '.join(lost))
# success rate split by question type (one concept, best plan)
for tag, v in (('cap', cap), ('nocap', nocap), ('c70', c70)):
    o, h, sh = float(SU[v]['overall_p_right']), float(SU[v]['p_right_on_hard']), float(SU[v]['share_hard'])
    put(f'succ.{tag}.hard', pct(h)); put(f'succ.{tag}.easy', pct((o - sh * h) / (1 - sh)))
for r in load('single_adapt.csv'):
    put(f"ad.{r['prior_hi']}.k", r['best_fixed_k'])
with open(os.path.join(GEN, 'numbers.tex'), 'w') as f:
    f.write('% generated by make_numbers.py from data/*.csv -- do not edit\n')
    for k, v in sorted(V.items()):
        f.write(f'\\expandafter\\def\\csname v@{k}\\endcsname{{{v}}}\n')
print(len(V), 'numbers;', 'tables: t_graph.tex, t_easyfirst.tex')
