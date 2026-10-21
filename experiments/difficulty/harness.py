"""Easy/hard questions on the real 40-concept graph (layered_40), using the real
continuous learner, using the copy of the simulator files in simcore/ (see simcore/PROVENANCE.md).

Learning rules (the professor's idea, two readings, plus today's simulator):
  current : the real Learner.answer, untouched (gain on observed answer, toward 1)
  rule    : learning keyed to GENUINE solving (solved ~ Bernoulli(m_eff)).
            EASY: m += lr*readiness*rhoE*(0.45 if solved else 0.10)*max(0, cE - m)
            HARD: m += lr*readiness*(min(1, beta*0.45)*(1-m) if solved else bH*(1-m))
            cap reading : rhoE=1,   cE<1
            slow reading: rhoE<1,   cE=1
Easy/hard label per question: within each concept, difficulty <= concept median -> EASY.
Forgetting OFF (meeting notes: forgetting = 0).
"""
import math, os, random, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # this folder, for simcore/
from simcore.curriculum import build_curriculum
from simcore.students.continuous import Learner, PROFILES, SimConfig
from simcore.schedulers.curriculum_tutor_paper import CurriculumTutorPaper
import dataclasses

CUR = build_curriculum('layered_40')
LEARNED = SimConfig().learned_threshold          # 0.80, the simulator's own "learned"
END = 'G01'                                      # deepest node, tier 6

def _closure(c, acc):
    for p in CUR.concepts[c].prereqs:
        if p not in acc:
            acc.add(p); _closure(p, acc)
    return acc
PATH = sorted(_closure(END, set()) | {END}, key=lambda c: (CUR.concepts[c].tier, c))
TOPO = CUR.topo_order()
CHILDREN = {c: [] for c in CUR.ids()}
for c in CUR.concepts.values():
    for p in c.prereqs: CHILDREN[p].append(c.cid)
SINKS = [c for c in CUR.ids() if not CHILDREN[c]]

LABEL = {}
for c in CUR.concepts.values():
    med = statistics.median(q.difficulty for q in c.questions)
    for q in c.questions:
        LABEL[q.qid] = 'E' if q.difficulty <= med else 'H'
BYCLASS = {(c.cid, k): [q for q in c.questions if LABEL[q.qid] == k]
           for c in CUR.concepts.values() for k in 'EH'}

RULES = {
    'current':        None,
    'slow_bH0':       dict(rhoE=0.3, cE=1.0, beta=2.0, bH=0.0),
    'slow_bH05':      dict(rhoE=0.3, cE=1.0, beta=2.0, bH=0.05),
    'cap60_bH0':      dict(rhoE=1.0, cE=0.6, beta=2.0, bH=0.0),
    'cap60_bH05':     dict(rhoE=1.0, cE=0.6, beta=2.0, bH=0.05),
    'cap85_bH0':      dict(rhoE=1.0, cE=0.85, beta=2.0, bH=0.0),
}

class EHLearner(Learner):
    def __init__(self, *a, rule=None, **kw):
        super().__init__(*a, **kw)
        self.rule = rule
        self.solved_hard = 0
    def answer(self, q, now_h):
        if self.rule is None:
            return super().answer(q, now_h)
        r = self.rule
        cid = q.concept_id
        m = self._refresh(cid, now_h)
        m_eff = m ** (1.0 + self.cfg.difficulty_exponent * q.difficulty)
        guess = 1.0 / self.cfg.n_options
        solved = self.rng.random() < m_eff
        correct = (self.rng.random() > self.p.slip) if solved else (self.rng.random() < guess)
        alpha = self.p.learning_rate * self.readiness(cid, now_h)
        if LABEL[q.qid] == 'E':
            g = r['rhoE'] * (self.cfg.gain_correct if solved else self.cfg.gain_wrong)
            gain = g * max(0.0, r['cE'] - m)
        else:
            gain = (min(1.0, r['beta'] * self.cfg.gain_correct) * (1 - m)) if solved else r['bH'] * (1 - m)
            self.solved_hard += solved
        self.mastery[cid] = min(1.0, m + alpha * gain)
        self.last_seen[cid] = now_h
        self.exposures[cid] += 1
        p_correct = m_eff * (1 - self.p.slip) + (1 - m_eff) * guess
        return {"concept_id": cid, "qid": q.qid, "correct": bool(correct), "p_correct": p_correct,
                "difficulty": q.difficulty, "mastery_before": m, "mastery_after": self.mastery[cid]}

# ---- within-concept difficulty choice -------------------------------------------
def choose_class(dpol, m_true, n_right_here):
    if dpol == 'easy':   return 'E'
    if dpol == 'hard':   return 'H'
    if dpol == 'random': return None
    if dpol == 'switch': return 'H' if m_true >= 0.40 else 'E'      # oracle threshold (sees true m)
    if dpol == 'e3h':    return 'H' if n_right_here >= 3 else 'E'   # realistic: easy until 3 right, then hard
    raise ValueError(dpol)

def pick(cid, cls, rng, last_qid):
    pool = CUR.concepts[cid].questions if cls is None else BYCLASS[(cid, cls)]
    qs = [q for q in pool if q.qid != last_qid] or pool
    return rng.choice(qs)

# ---- concept choice ---------------------------------------------------------------
class OracleOrder:
    """Teach concepts in a fixed order; move on when TRUE mastery >= thr (upper bound, sees truth)."""
    def __init__(self, order, thr=LEARNED): self.order, self.thr = order, thr
    def concept(self, learner, now_h):
        for c in self.order:
            if learner.true_mastery(c, now_h) < self.thr: return c
        return None
    def observe(self, *a): pass
    def declared(self): return set()

class CT(CurriculumTutorPaper):
    """The published CurriculumTutor (real class). evidence='all' is the paper (difficulty-blind CUSUM);
    evidence='hard' is one change: only HARD-question answers count toward the mastery test."""
    def __init__(self, evidence='all', **kw):
        super().__init__(**kw); self.evidence = evidence; self._last_cls = None
    def concept(self, learner, now_h, rng, last_qid):
        q = self.select(CUR, None, now_h, rng, last_qid)
        return None if q is None else q.concept_id
    def observe_cls(self, cid, correct, now_h, cls):
        if self.evidence == 'hard' and cls == 'E':
            # still counts as a bandit pull/reward, but not as mastery evidence
            self.last_asked[cid] = self.t
            self.n[cid] = self.n.get(cid, 0) + 1
            self.s[cid] = self.s.get(cid, 0) + (1 if correct else 0)
            return
        self.observe(cid, correct, now_h)
    def declared(self): return set(self.learned)

def run(rule_name, cpol, dpol, seed, budget=2000, profile='average', overrides=None,
        checkpoints=(100, 200, 300, 500, 1000, 2000)):
    prof = PROFILES[profile]
    if overrides: prof = dataclasses.replace(prof, **overrides)
    L = EHLearner(CUR, prof, seed=seed, forgetting=False, rule=RULES[rule_name])
    rng = random.Random(seed + 77777)
    if cpol == 'path':  S = OracleOrder(PATH)
    elif cpol == 'bfs': S = OracleOrder(TOPO)
    elif cpol == 'ct':  S = CT('all')
    elif cpol == 'ct_hard': S = CT('hard')
    else: raise ValueError(cpol)
    now_h, last_qid = 0.0, None
    right_here = {}
    out = dict(t_end=None, t_end09=None, t_decl=None, m_end_at_decl=None, path_mean_at_decl=None,
               idle_at=None, curve={})
    for t in range(1, budget + 1):
        if isinstance(S, CT):
            cid = S.concept(L, now_h, rng, last_qid)
        else:
            cid = S.concept(L, now_h)
        if cid is None:
            if out['idle_at'] is None: out['idle_at'] = t
            now_h += 1/60
        else:
            cls = choose_class(dpol, L.true_mastery(cid, now_h), right_here.get(cid, 0))
            q = pick(cid, cls, rng, last_qid)
            res = L.answer(q, now_h)
            if res['correct']: right_here[cid] = right_here.get(cid, 0) + 1
            if isinstance(S, CT): S.observe_cls(cid, res['correct'], now_h, LABEL[q.qid])
            last_qid = q.qid
            now_h += 1/60
        mE = L.true_mastery(END, now_h)
        if out['t_end'] is None and mE >= LEARNED: out['t_end'] = t
        if out['t_end09'] is None and mE >= 0.9: out['t_end09'] = t
        if out['t_decl'] is None and END in S.declared():
            out['t_decl'] = t; out['m_end_at_decl'] = mE
            out['path_mean_at_decl'] = statistics.mean(L.true_mastery(c, now_h) for c in PATH)
        if t in checkpoints:
            snap = L.snapshot(now_h)
            learned = [c for c, v in snap.items() if v >= LEARNED]
            out['curve'][t] = dict(
                learned=len(learned),
                declared=len(S.declared()),
                max_tier=max((CUR.concepts[c].tier for c in learned), default=-1),
                sinks=sum(1 for c in SINKS if snap[c] >= LEARNED),
                path_learned=sum(1 for c in PATH if snap[c] >= LEARNED),
                mean_m=statistics.mean(snap.values()),
                end_m=snap[END])
    return out
