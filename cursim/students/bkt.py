"""The plain BKT student: the sanity-check learner.

Each concept is a hidden known/unknown coin with the four BKT parameters.
No forgetting and no difficulty by default; prerequisites optionally gate
learning (S2). Same interface as the continuous Learner, so every
scheduler, mastery model and metric works unchanged.
"""

import random
from typing import Dict, Optional

from ..curriculum import Curriculum, Question
from ..params import BKT_PARAMS, STUDENT_MODELS
from .continuous import SimConfig


class BKTLearner:
    """A student who IS a BKT process, nothing more.

    Each concept is a hidden coin: known or not. No forgetting, no
    question difficulty, and (by default) prerequisites have no effect
    on learning. Same interface as Learner so every scheduler, mastery
    model and metric works unchanged.

    Records the exact step at which each concept was learned, which is
    what the detection-delay check needs.

    prereq_gated_pT is the ONE hook for the prerequisite-based
    student model: when on, a concept whose prerequisites are not
    all truly known learns with pT_low instead of p_T. Off by default,
    and turned on by selecting the `bkt_prereq` entry in LEARNERS
    rather than by setting the flag by hand. pT_low defaults to S2's
    value in data/params.json, so there is exactly one S2 in the repo.
    """

    def __init__(self, curriculum: Curriculum, profile=None, seed: int = 0,
                 cfg=None, forgetting: bool = False, params=None,
                 prereq_gated_pT: bool = False,
                 pT_low: Optional[float] = None):
        self.cur = curriculum
        self.p = {**BKT_PARAMS, **(params or {})}
        self.cfg = cfg or SimConfig()
        self.rng = random.Random(seed)
        self.prereq_gated_pT = prereq_gated_pT
        # S2's slow rate lives in data/params.json. Reading it here means
        # every path that switches gating on gets the SAME student; passing
        # pT_low explicitly is a deliberate override, not a second S2.
        self.pT_low = (STUDENT_MODELS["S2"]["pT_low"] if pT_low is None
                       else pT_low)
        self.step = 0
        self.known: Dict[str, bool] = {}
        self.learned_step: Dict[str, Optional[int]] = {}
        self.exposures: Dict[str, int] = {}
        self.last_seen: Dict[str, Optional[float]] = {}
        for cid in curriculum.ids():
            k = self.rng.random() < self.p["p_L0"]
            self.known[cid] = k
            self.learned_step[cid] = 0 if k else None
            self.exposures[cid] = 0
            self.last_seen[cid] = None

    def _pT(self, cid: str) -> float:
        if not self.prereq_gated_pT:
            return self.p["p_T"]
        pre = self.cur.concepts[cid].prereqs
        return self.p["p_T"] if all(self.known[p] for p in pre) else self.pT_low

    def answer(self, q: Question, now_h: float) -> dict:
        cid = q.concept_id
        self.step += 1
        before = self.known[cid]
        p_correct = (1.0 - self.p["p_S"]) if before else self.p["p_G"]
        correct = self.rng.random() < p_correct
        # learn AFTER answering, exactly as the tutor's BKT update assumes
        if not before and self.rng.random() < self._pT(cid):
            self.known[cid] = True
            self.learned_step[cid] = self.step
        self.exposures[cid] += 1
        self.last_seen[cid] = now_h
        return {"concept_id": cid, "qid": q.qid, "correct": bool(correct),
                "p_correct": p_correct, "difficulty": q.difficulty,
                "state_before": before, "state_after": self.known[cid],
                "mastery_before": float(before),
                "mastery_after": float(self.known[cid]),
                "readiness": 1.0,
                "exposures_before": self.exposures[cid] - 1}

    # -- same evaluation interface as Learner ----------------------------
    def true_mastery(self, cid: str, now_h: float) -> float:
        return float(self.known[cid])

    def snapshot(self, now_h: float) -> Dict[str, float]:
        return {c: float(k) for c, k in self.known.items()}

    def mean_mastery(self, now_h: float) -> float:
        return sum(self.known.values()) / len(self.known)

    def n_learned(self, now_h: float, thr: Optional[float] = None) -> int:
        return sum(1 for k in self.known.values() if k)
