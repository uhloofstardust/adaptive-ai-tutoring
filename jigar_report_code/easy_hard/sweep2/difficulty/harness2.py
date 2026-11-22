"""Easy-first vs random WITHIN a concept, on layered_40. Builds on harness.py (same learner, labels, tutors).

Within-concept question policies (none of them see the student's true state, except 'switch'):
  random     any item of the concept, uniformly (what the CurriculumTutor paper does)
  easyfirst  ask each of the concept's EASY items once, easiest first (3-5 of them), then HARD items only
  k<K>       the first K questions on a concept are EASY (cycling through the easy items easiest first), then HARD only
             (easyfirst == k<number of easy items>)
  switch     ORACLE reference: hard once TRUE mastery >= 0.40, else easy
Metrics per student: t_end (true G01 >= 0.80), t_closure (G01 AND all 13 prerequisites >= 0.80),
questions spent per chain concept until it first reached 0.80, and for CurriculumTutor the declaration bookkeeping.
"""
import os, random, statistics, sys, dataclasses
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H

H.RULES.update({
    'slow_b1':  dict(rhoE=0.3, cE=1.0, beta=1.0, bH=0.0),    # hard solve gives 0.45 (not 0.9): less extreme
    'cap60_b1': dict(rhoE=1.0, cE=0.6, beta=1.0, bH=0.0),
    'slow_bH02': dict(rhoE=0.3, cE=1.0, beta=2.0, bH=0.02),
})
EASY_SORTED = {c: sorted(H.BYCLASS[(c, 'E')], key=lambda q: (q.difficulty, q.qid)) for c in H.CUR.ids()}

def choose(dpol, cid, asked_here, m_true):
    """Return ('E', item) for a fixed easy item, ('E'|'H'|None, None) for a random draw from that class/bank."""
    if dpol == 'random':
        return None, None
    if dpol == 'switch':
        return ('H' if m_true >= 0.40 else 'E'), None
    if dpol == 'easyfirst':
        K = len(EASY_SORTED[cid])
    elif dpol.startswith('k'):
        K = int(dpol[1:])
    else:
        raise ValueError(dpol)
    if asked_here < K:
        es = EASY_SORTED[cid]
        return 'E', es[asked_here % len(es)]
    return 'H', None

def run2(rule, cpol, dpol, seed, budget=2000, profile='average', overrides=None, checkpoints=(500, 1000, 2000)):
    prof = H.PROFILES[profile]
    if overrides: prof = dataclasses.replace(prof, **overrides)
    L = H.EHLearner(H.CUR, prof, seed=seed, forgetting=False, rule=H.RULES[rule])
    rng = random.Random(seed + 77777)
    S = {'path': lambda: H.OracleOrder(H.PATH), 'bfs': lambda: H.OracleOrder(H.TOPO),
         'ct': lambda: H.CT('all')}[cpol]()
    now_h, last_qid = 0.0, None
    asked = {c: 0 for c in H.CUR.ids()}
    q_to_learn = {}
    out = dict(t_end=None, t_closure=None, t_decl=None, m_end_at_decl=None, closure_ok_at_decl=None,
               easy_share=None, cp={})
    n_easy = n_all = 0
    for t in range(1, budget + 1):
        cid = S.concept(L, now_h, rng, last_qid) if isinstance(S, H.CT) else S.concept(L, now_h)
        if cid is not None:
            cls, item = choose(dpol, cid, asked[cid], L.true_mastery(cid, now_h))
            q = item if item is not None else H.pick(cid, cls, rng, last_qid)
            res = L.answer(q, now_h)
            asked[cid] += 1
            n_all += 1; n_easy += (H.LABEL[q.qid] == 'E')
            if isinstance(S, H.CT): S.observe(cid, res['correct'], now_h)
            if cid not in q_to_learn and res['mastery_after'] >= H.LEARNED: q_to_learn[cid] = asked[cid]
            last_qid = q.qid
        now_h += 1 / 60
        mE = L.true_mastery(H.END, now_h)
        if out['t_end'] is None and mE >= H.LEARNED: out['t_end'] = t
        if out['t_closure'] is None and all(L.true_mastery(c, now_h) >= H.LEARNED for c in H.PATH):
            out['t_closure'] = t
        if out['t_decl'] is None and H.END in S.declared():
            out['t_decl'] = t; out['m_end_at_decl'] = mE
            out['closure_ok_at_decl'] = all(L.true_mastery(c, now_h) >= H.LEARNED for c in H.PATH)
        if t in checkpoints:
            snap = L.snapshot(now_h)
            dec = S.declared()
            out['cp'][t] = dict(learned=sum(v >= H.LEARNED for v in snap.values()),
                                declared=len(dec),
                                false_decl=sum(1 for c in dec if snap[c] < H.LEARNED))
    out['easy_share'] = n_easy / max(n_all, 1)
    out['q_chain'] = [q_to_learn.get(c) for c in H.PATH]      # questions spent per chain concept until learned
    return out
