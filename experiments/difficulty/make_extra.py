"""Extra graph runs for the report -> data/extra_rows.csv.gz. Builds on harness.py and harness2.py.
New within-concept policies:
  e3h    easy until 3 CORRECT answers on this concept (guesses count), then hard only (realistic: uses only answers)
  efmix  the same easy budget as easyfirst (the concept's 3-5 easy items, once each) but interleaved:
         while easy items are left, each question is easy with probability 1/2; then hard only
New tutor: ct_hard = CurriculumTutor whose mastery test counts only answers to HARD questions.
Also: bH sweep on the chain, teaching G01 directly (skipping prerequisites), absolute difficulty labels,
hard-only from a higher starting mastery, and the true mastery at the moment easy-first hands over to hard."""
import csv, os, random, statistics, sys, dataclasses, itertools
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H, harness2 as H2
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
H.RULES.update({'slow_bH005': dict(rhoE=0.3, cE=1.0, beta=2.0, bH=0.005),
                'slow_bH01': dict(rhoE=0.3, cE=1.0, beta=2.0, bH=0.01)})
SEEDS = list(range(4242, 4442))

def run3(rule, cpol, dpol, seed, budget=2000, overrides=None, order=None, labels=None):
    prof = H.PROFILES['average']
    if overrides: prof = dataclasses.replace(prof, **overrides)
    L = H.EHLearner(H.CUR, prof, seed=seed, forgetting=False, rule=H.RULES[rule])
    rng = random.Random(seed + 77777)
    if cpol == 'path':   S = H.OracleOrder(order or H.PATH)
    elif cpol == 'bfs':  S = H.OracleOrder(H.TOPO)
    elif cpol == 'ct':   S = H.CT('all')
    elif cpol == 'ct_hard': S = H.CT('hard')
    LAB = labels or H.LABEL
    assert LAB is H.LABEL or LAB == H.LABEL, 'tutor and learner labels differ'
    BYC = {(c.cid, k): [q for q in c.questions if LAB[q.qid] == k] for c in H.CUR.concepts.values() for k in 'EH'}
    ES = {c: sorted(BYC[(c, 'E')], key=lambda q: (q.difficulty, q.qid)) for c in H.CUR.ids()}
    now_h, last_qid = 0.0, None
    asked = {c: 0 for c in H.CUR.ids()}; right = {c: 0 for c in H.CUR.ids()}; easy_used = {c: 0 for c in H.CUR.ids()}
    m_at_first_hard = {}
    out = dict(t_end=None, t_closure=None)
    for t in range(1, budget + 1):
        cid = S.concept(L, now_h, rng, last_qid) if isinstance(S, H.CT) else S.concept(L, now_h)
        if cid is not None:
            m_true = L.true_mastery(cid, now_h)
            item, cls = None, None
            if dpol == 'random': cls = None
            elif dpol == 'switch': cls = 'H' if m_true >= 0.40 else 'E'
            elif dpol == 'hard': cls = 'H'
            elif dpol == 'easy': cls = 'E'
            elif dpol == 'e3h': cls = 'H' if right[cid] >= 3 else 'E'
            elif dpol in ('easyfirst', 'efmix') or dpol.startswith('k'):
                K = len(ES[cid]) if dpol in ('easyfirst', 'efmix') else int(dpol[1:])
                if easy_used[cid] < K and (dpol != 'efmix' or rng.random() < 0.5):
                    cls, item = 'E', ES[cid][easy_used[cid] % len(ES[cid])] if ES[cid] else None
                else:
                    cls = 'H'
            pool = BYC.get((cid, cls)) if cls else None
            if item is None:
                if cls and not pool: pool = H.CUR.concepts[cid].questions      # class missing in this concept
                pool = pool or H.CUR.concepts[cid].questions
                qs = [q for q in pool if q.qid != last_qid] or pool
                q = rng.choice(qs)
            else:
                q = item
            if LAB[q.qid] == 'E': easy_used[cid] += 1
            elif cid not in m_at_first_hard: m_at_first_hard[cid] = m_true
            res = L.answer(q, now_h)
            asked[cid] += 1; right[cid] += res['correct']
            if isinstance(S, H.CT): S.observe_cls(cid, res['correct'], now_h, LAB[q.qid])
            last_qid = q.qid
        now_h += 1 / 60
        if out['t_end'] is None and L.true_mastery(H.END, now_h) >= H.LEARNED: out['t_end'] = t
        if out['t_closure'] is None and all(L.true_mastery(c, now_h) >= H.LEARNED for c in H.PATH): out['t_closure'] = t
        if out['t_closure'] is not None and cpol in ('path',) and order is None: break
    snap = L.snapshot(now_h); dec = S.declared()
    out['false_decl'] = sum(1 for c in dec if snap[c] < H.LEARNED)
    out['m_handover'] = statistics.median(m_at_first_hard[c] for c in H.PATH if c in m_at_first_hard) if any(c in m_at_first_hard for c in H.PATH) else None
    return out

def job(cond):
    grp, rule, cpol, dpol, extra = cond
    kw = dict(extra or {})
    labels = None
    if kw.pop('labels', None) == 'absolute':
        gm = statistics.median(q.difficulty for q in H.CUR.all_questions())
        labels = {q.qid: ('E' if q.difficulty <= gm else 'H') for q in H.CUR.all_questions()}
    saved = dict(H.LABEL)
    if labels:                      # the LEARNER's gain rule reads H.LABEL too, so both sides must switch
        H.LABEL.clear(); H.LABEL.update(labels)
    rows = []
    for sd in SEEDS:
        o = run3(rule, cpol, dpol, sd, labels=labels, **kw)
        rows.append(dict(group=grp, rule=rule, cpol=cpol, dpol=dpol,
                         extra=';'.join(f'{k}={v}' for k, v in (extra or {}).items() if k != 'order') + (';order=G01only' if (extra or {}).get('order') else ''),
                         seed=sd, t_end=o['t_end'], t_closure=o['t_closure'], false_decl=o['false_decl'],
                         m_handover=None if o['m_handover'] is None else round(o['m_handover'], 4)))
    H.LABEL.clear(); H.LABEL.update(saved)
    return rows

RULES8 = ['current', 'slow_bH0', 'slow_bH02', 'slow_bH05', 'cap60_bH0', 'cap85_bH0', 'slow_b1', 'cap60_b1']
def conditions():
    for r, c, d in itertools.product(RULES8, ('path', 'bfs', 'ct'), ('e3h', 'efmix')):
        yield ('newpol', r, c, d, None)
    for r, d in itertools.product(RULES8, ('random', 'easyfirst', 'e3h', 'k8')):
        yield ('cthard', r, 'ct_hard', d, None)
    for r in ('slow_bH0', 'slow_bH005', 'slow_bH01', 'slow_bH02', 'slow_bH05'):
        for d in ('hard', 'switch', 'random', 'easyfirst'):
            yield ('bh_sweep', r, 'path', d, None)
    for r, d in (('current', 'random'), ('slow_bH0', 'switch'), ('cap60_bH0', 'switch'), ('slow_bH0', 'random')):
        yield ('direct', r, 'path', d, {'order': ['G01']})
        yield ('direct', r, 'path', d, {'order': ['G01'], 'overrides': {'prereq_sensitivity': 1.0}})
        yield ('direct', r, 'path', d, {'overrides': {'prereq_sensitivity': 1.0}})
    for r, d in itertools.product(('slow_bH0', 'cap60_bH0'), ('random', 'easy', 'switch', 'hard')):
        yield ('absolute', r, 'path', d, {'labels': 'absolute'})
    for im in (0.10, 0.30):
        for d in ('hard', 'switch'):
            yield ('prior', 'slow_bH0', 'path', d, {'overrides': {'init_mastery': im}})
    for r in ('slow_bH0', 'cap60_bH0', 'cap85_bH0', 'slow_b1'):
        yield ('handover', r, 'path', 'easyfirst', None)

if __name__ == '__main__':
    # self-check: run3 must reproduce harness2.run2 on shared policies
    for r, c, d in (('slow_bH0', 'path', 'easyfirst'), ('cap60_bH0', 'ct', 'random'), ('slow_bH05', 'bfs', 'k8'), ('current', 'ct', 'switch')):
        for sd in (4242, 4300):
            a = run3(r, c, d, sd); b = H2.run2(r, c, d, sd)
            assert (a['t_end'], a['t_closure']) == (b['t_end'], b['t_closure']), (r, c, d, sd, a, b)
    print('run3 == run2 on shared policies: ok', flush=True)
    conds = list(conditions()); print(len(conds), 'conditions x', len(SEEDS), flush=True)
    from common import open_out
    with Pool(int(os.environ.get('WORKERS', 12))) as pool, open_out(os.path.join(OUT, 'extra_rows.csv.gz')) as f:
        w = None
        for rows in pool.imap(job, conds):
            if w is None: w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader()
            w.writerows(rows)
    print('done')
