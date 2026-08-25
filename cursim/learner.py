"""The simulated learner: the ground truth the tutor cannot see.

Design decisions that matter for the research claims:

1. Mastery is CONTINUOUS in the learner, always. Binary mastery is a
   property of the tutor's model, not of the person, so the binary vs
   continuous experiment swaps the tutor's representation while the
   learner stays fixed. Comparing two different learners would not be
   an experiment about tutoring.

2. Prerequisites act on the LEARNER, not only on the scheduler. A
   concept whose prerequisites are weak is genuinely harder to learn:
   the learning gain is scaled by prerequisite readiness. Without
   this the curriculum graph is decoration and no graph-respecting
   scheduler could ever show a benefit.

3. Question difficulty raises the mastery needed to answer, via
   m_eff = m ** (1 + k*d). This is what makes item selection within a
   concept a real decision.

4. Forgetting is continuous-time exponential decay toward a floor,
   applied lazily at read time, so a concept decays whether or not it
   is practised. That makes the scheduling problem restless.
"""

import math
import random
from dataclasses import dataclass
from typing import Dict, Optional

from .curriculum import Curriculum, Question


@dataclass
class LearnerProfile:
    name: str
    learning_rate: float = 1.00     # multiplier on every learning gain
    forget_half_life_days: float = 14.0
    slip: float = 0.07              # P(wrong | fully mastered)
    prereq_sensitivity: float = 0.8  # 0 = prereqs irrelevant, 1 = strict
    init_mastery: float = 0.05


PROFILES = {
    "average": LearnerProfile("average"),
    "fast": LearnerProfile("fast", learning_rate=1.35,
                           forget_half_life_days=18.0, slip=0.05),
    "slow": LearnerProfile("slow", learning_rate=0.70,
                           forget_half_life_days=12.0, slip=0.10),
    # forgetful differs by memory, not by ability
    "forgetful": LearnerProfile("forgetful", learning_rate=1.1,
                                forget_half_life_days=6.0, slip=0.07),
}


@dataclass
class SimConfig:
    n_options: int = 4              # MCQ, so guessing is 1/n
    gain_correct: float = 0.45
    gain_wrong: float = 0.10        # exposure still teaches a little
    difficulty_exponent: float = 1.2  # k in m ** (1 + k*d)
    mastery_floor: float = 0.02
    learned_threshold: float = 0.80


class Learner:
    """One simulated student. Hidden state is per concept."""

    def __init__(self, curriculum: Curriculum, profile: LearnerProfile,
                 seed: int, cfg: Optional[SimConfig] = None,
                 forgetting: bool = True):
        self.cur = curriculum
        self.p = profile
        self.cfg = cfg or SimConfig()
        self.forgetting = forgetting
        self.rng = random.Random(seed)
        self.mastery: Dict[str, float] = {}
        self.last_seen: Dict[str, Optional[float]] = {}
        self.exposures: Dict[str, int] = {}
        for cid in curriculum.ids():
            self.mastery[cid] = max(0.0, self.rng.gauss(
                profile.init_mastery, 0.03))
            self.last_seen[cid] = None
            self.exposures[cid] = 0

    # -- forgetting ---------------------------------------------------
    def _decay_rate(self, cid: str) -> float:
        """Per-hour rate. Later-tier concepts are more fragile."""
        tier = self.cur.concepts[cid].tier
        hl_h = self.p.forget_half_life_days * 24.0 * (1.0 - 0.06 * tier)
        return math.log(2.0) / max(6.0, hl_h)

    def _refresh(self, cid: str, now_h: float) -> float:
        if not self.forgetting or self.last_seen[cid] is None:
            return self.mastery[cid]
        dt = max(0.0, now_h - self.last_seen[cid])
        if dt > 0:
            fl = self.cfg.mastery_floor
            self.mastery[cid] = max(fl, fl + (self.mastery[cid] - fl) *
                                    math.exp(-self._decay_rate(cid) * dt))
            self.last_seen[cid] = now_h
        return self.mastery[cid]

    # -- prerequisites ------------------------------------------------
    def readiness(self, cid: str, now_h: float) -> float:
        """How prepared this learner is for the concept, from the true
        mastery of its prerequisites. 1.0 for a root concept."""
        pre = self.cur.concepts[cid].prereqs
        if not pre:
            return 1.0
        weakest = min(self._refresh(p, now_h) for p in pre)
        s = self.p.prereq_sensitivity
        return (1.0 - s) + s * weakest

    # -- answering ----------------------------------------------------
    def answer(self, q: Question, now_h: float) -> dict:
        cid = q.concept_id
        m_before = self._refresh(cid, now_h)

        m_eff = m_before ** (1.0 + self.cfg.difficulty_exponent * q.difficulty)
        guess = 1.0 / self.cfg.n_options
        p_correct = m_eff * (1 - self.p.slip) + (1 - m_eff) * guess
        correct = self.rng.random() < p_correct

        gain = (self.cfg.gain_correct if correct else self.cfg.gain_wrong)
        alpha = self.p.learning_rate * self.readiness(cid, now_h)
        self.mastery[cid] = min(1.0, m_before + alpha * gain *
                                (1.0 - m_before))
        self.last_seen[cid] = now_h
        self.exposures[cid] += 1
        return {"concept_id": cid, "qid": q.qid, "correct": bool(correct),
                "p_correct": p_correct, "difficulty": q.difficulty,
                "mastery_before": m_before,
                "mastery_after": self.mastery[cid],
                "readiness": self.readiness(cid, now_h),
                "exposures_before": self.exposures[cid] - 1}

    # -- evaluation access (logs only, never given to the tutor) ------
    def true_mastery(self, cid: str, now_h: float) -> float:
        return self._refresh(cid, now_h)

    def snapshot(self, now_h: float) -> Dict[str, float]:
        return {cid: self._refresh(cid, now_h) for cid in self.mastery}

    def mean_mastery(self, now_h: float) -> float:
        s = self.snapshot(now_h)
        return sum(s.values()) / len(s)

    def n_learned(self, now_h: float, thr: Optional[float] = None) -> int:
        thr = self.cfg.learned_threshold if thr is None else thr
        return sum(1 for v in self.snapshot(now_h).values() if v >= thr)
