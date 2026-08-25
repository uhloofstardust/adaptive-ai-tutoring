"""Mastery models: what the TUTOR believes about the learner.

This is the axis the binary-vs-continuous experiment varies. All
models see only (concept_id, correct, time) and never the learner's
true state.

    BinaryMastery      CurriculumTutor's assumptions: a concept is
                       mastered or not, and mastery is permanent.
                       Implemented as a BKT belief that is latched
                       once it crosses a threshold, so the tutor can
                       never revise the judgement downward.

    ContinuousMastery  the belief itself is the estimate, never
                       latched. With forget_per_day > 0 it decays
                       between practices, which is the only way a
                       tutor can notice that mastery has faded.

Swapping these two, with everything else held fixed, isolates the
value of the representation.
"""

from typing import Dict, List, Optional


class MasteryModel:
    name = "base"

    def observe(self, cid: str, correct: bool, now_h: float):
        raise NotImplementedError

    def belief(self, cid: str, now_h: float) -> float:
        """Continuous estimate in [0, 1]."""
        raise NotImplementedError

    def is_mastered(self, cid: str, now_h: float) -> bool:
        raise NotImplementedError


class _BKTCore:
    """Shared Bayesian update. Guess is set for 4-option MCQ."""

    def __init__(self, cids: List[str], p_L0=0.15, p_T=0.12, p_S=0.10,
                 p_G=0.25, forget_per_day=0.0, floor=0.02):
        self.p_L0, self.p_T, self.p_S, self.p_G = p_L0, p_T, p_S, p_G
        self.forget_per_day, self.floor = forget_per_day, floor
        self.b: Dict[str, float] = {c: p_L0 for c in cids}
        self.t: Dict[str, Optional[float]] = {c: None for c in cids}

    def _decayed(self, cid: str, now_h: float) -> float:
        b = self.b[cid]
        if self.t[cid] is None or self.forget_per_day <= 0:
            return b
        days = max(0.0, (now_h - self.t[cid]) / 24.0)
        b = self.floor + (b - self.floor) * ((1 - self.forget_per_day) ** days)
        return max(self.floor, min(0.999, b))

    def update(self, cid: str, correct: bool, now_h: float):
        b = self._decayed(cid, now_h)
        if correct:
            num, rest = b * (1 - self.p_S), (1 - b) * self.p_G
        else:
            num, rest = b * self.p_S, (1 - b) * (1 - self.p_G)
        post = num / (num + rest)
        self.b[cid] = post + (1 - post) * self.p_T
        self.t[cid] = now_h


class BinaryMastery(MasteryModel):
    """CurriculumTutor-style: binary and permanent."""
    name = "binary"

    def __init__(self, cids, threshold=0.97, **kw):
        kw.pop("forget_per_day", None)      # a binary model cannot forget
        kw.setdefault("p_T", 0.06)          # conservative: needs more
        self.core = _BKTCore(cids, **kw)    # evidence before latching
        self.threshold = threshold
        self.latched = {c: False for c in cids}

    def observe(self, cid, correct, now_h):
        self.core.update(cid, correct, now_h)
        if self.core.b[cid] >= self.threshold:
            self.latched[cid] = True        # permanent, never revoked

    def belief(self, cid, now_h):
        # the tutor only has a yes/no: it reports the extremes
        return 1.0 if self.latched[cid] else self.core.b[cid]

    def is_mastered(self, cid, now_h):
        return self.latched[cid]


class ContinuousMastery(MasteryModel):
    """Continuous belief, optionally decaying between practices."""

    def __init__(self, cids, threshold=0.80, forget_per_day=0.0, **kw):
        self.core = _BKTCore(cids, forget_per_day=forget_per_day, **kw)
        self.threshold = threshold
        self.name = ("continuous+forget" if forget_per_day > 0
                     else "continuous")

    def observe(self, cid, correct, now_h):
        self.core.update(cid, correct, now_h)

    def belief(self, cid, now_h):
        return self.core._decayed(cid, now_h)

    def is_mastered(self, cid, now_h):
        return self.belief(cid, now_h) >= self.threshold


def make_model(kind: str, cids, **kw) -> MasteryModel:
    if kind == "binary":
        return BinaryMastery(cids, **kw)
    if kind == "continuous":
        return ContinuousMastery(cids, forget_per_day=0.0, **kw)
    if kind == "continuous_forget":
        kw.setdefault("forget_per_day", 0.10)
        return ContinuousMastery(cids, **kw)
    raise ValueError(kind)
