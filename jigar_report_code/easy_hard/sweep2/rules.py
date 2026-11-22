"""Proposed rule and one student's run, on the study's own harness (a copy of commit e99d515).

easy: m_new = min(max(m, c), m + alpha * (g if solved else f) * max(0, 1 - m/c))
hard: m_new = min(1, m + alpha * (J if solved else bH) * (1 - m))

The loop follows harness2.run2 and make_extra.run3, so random draws stay in the same order.
It stops once the tutor has nothing left to ask: with forgetting off nothing changes after that.
"""
import dataclasses
import os
import random
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'difficulty'))
import harness as H  # noqa: E402

ES = {c: sorted(H.BYCLASS[(c, 'E')], key=lambda q: (q.difficulty, q.qid)) for c in H.CUR.ids()}
DEFAULT_M0 = H.PROFILES['average'].init_mastery
DEFAULT_LR = H.PROFILES['average'].learning_rate


class FactorLearner(H.EHLearner):
    def answer(self, q, now_h):
        r = self.rule
        cid = q.concept_id
        m = self._refresh(cid, now_h)
        m_eff = m ** (1.0 + self.cfg.difficulty_exponent * q.difficulty)
        guess = 1.0 / self.cfg.n_options
        solved = self.rng.random() < m_eff
        correct = (self.rng.random() > self.p.slip) if solved else (self.rng.random() < guess)
        alpha = self.p.learning_rate * self.readiness(cid, now_h)
        if H.LABEL[q.qid] == 'E':
            rate = r['g'] if solved else r['f']
            c = r['c']
            new = min(max(m, c), m + alpha * rate * max(0.0, 1.0 - m / c))
        else:
            rate = r['J'] if solved else r['bH']
            new = min(1.0, m + alpha * rate * (1.0 - m))
        self.mastery[cid] = new
        self.last_seen[cid] = now_h
        self.exposures[cid] += 1
        p_correct = m_eff * (1 - self.p.slip) + (1 - m_eff) * guess
        return {"concept_id": cid, "qid": q.qid, "correct": bool(correct), "p_correct": p_correct,
                "difficulty": q.difficulty, "mastery_before": m, "mastery_after": new}


def rule(g=.45, J=.9, f=.10, bH=0., c=1.):
    return dict(g=g, J=J, f=f, bH=bH, c=c)


def run_student(r, tutor, plan, seed, budget=2000, speed=1.0, m0=None, thr=None):
    """tutor: path, bfs, ct. plan: easy, hard, random, switch (thr, default .40), easyfirst, e3h, k<K>.
    speed scales learning_rate, which multiplies all four factors. m0 is the mean starting mastery."""
    prof = H.PROFILES['average']
    ov = {}
    if speed != 1.0:
        ov['learning_rate'] = DEFAULT_LR * speed
    if m0 is not None and m0 != DEFAULT_M0:
        ov['init_mastery'] = m0
    if ov:
        prof = dataclasses.replace(prof, **ov)
    L = FactorLearner(H.CUR, prof, seed=seed, forgetting=False, rule=r)
    rng = random.Random(seed + 77777)
    S = {'path': lambda: H.OracleOrder(H.PATH), 'bfs': lambda: H.OracleOrder(H.TOPO),
         'ct': lambda: H.CT('all')}[tutor]()
    is_ct = tutor == 'ct'
    t_sw = .40 if thr is None else thr
    now_h, last = 0.0, None
    asked = {c: 0 for c in H.CUR.ids()}
    right = {c: 0 for c in H.CUR.ids()}
    t_end = t_closure = None
    n_asked = n_easy = n_right = 0
    for t in range(1, budget + 1):
        cid = S.concept(L, now_h, rng, last) if is_ct else S.concept(L, now_h)
        if cid is None:
            break
        item, cls = None, None
        if plan == 'random':
            cls = None
        elif plan == 'easy':
            cls = 'E'
        elif plan == 'hard':
            cls = 'H'
        elif plan == 'switch':
            cls = 'H' if L.true_mastery(cid, now_h) >= t_sw else 'E'
        elif plan == 'e3h':
            cls = 'H' if right[cid] >= 3 else 'E'
        else:
            K = len(ES[cid]) if plan == 'easyfirst' else int(plan[1:])
            if asked[cid] < K:
                cls, item = 'E', ES[cid][asked[cid] % len(ES[cid])]
            else:
                cls = 'H'
        q = item if item is not None else H.pick(cid, cls, rng, last)
        res = L.answer(q, now_h)
        asked[cid] += 1
        right[cid] += res['correct']
        n_asked += 1
        n_easy += H.LABEL[q.qid] == 'E'
        n_right += res['correct']
        if is_ct:
            S.observe(cid, res['correct'], now_h)
        last = q.qid
        now_h += 1 / 60
        if t_end is None and L.true_mastery(H.END, now_h) >= H.LEARNED:
            t_end = t
        if t_closure is None and all(L.true_mastery(c, now_h) >= H.LEARNED for c in H.PATH):
            t_closure = t
    snap = L.snapshot(now_h)
    dec = S.declared()
    return dict(t_end=t_end, t_closure=t_closure, false=sum(1 for c in dec if snap[c] < H.LEARNED),
                declared=len(dec), asked=n_asked, easy=n_easy, right=n_right,
                learned=sum(v >= H.LEARNED for v in snap.values()))
