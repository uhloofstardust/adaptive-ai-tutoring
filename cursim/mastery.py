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

from .params import BKT_PARAMS


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

    def __init__(self, cids: List[str], p_L0=BKT_PARAMS["p_L0"],
                 p_T=BKT_PARAMS["p_T"], p_S=BKT_PARAMS["p_S"],
                 p_G=BKT_PARAMS["p_G"], forget_per_day=0.0, floor=0.02,
                 p_F=0.0):
        self.p_L0, self.p_T, self.p_S, self.p_G = p_L0, p_T, p_S, p_G
        self.p_F = p_F          # BKT forget: chance a known skill is lost
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
        post = num / (num + rest) if (num + rest) > 0 else b
        # full BKT transition (Schodde et al. 2017): a known skill can be
        # lost with probability p_F, not just gained with p_T.
        self.b[cid] = post * (1 - self.p_F) + (1 - post) * self.p_T
        self.t[cid] = now_h


    def expected_gain(self, cid: str, now_h: float) -> float:
        """One-step lookahead: how much would asking this move the belief?

        Averages the post-answer belief over a right and a wrong answer,
        weighted by how likely each is. This is the quantity the
        predictive scheduler maximizes.
        """
        b = self._decayed(cid, now_h)
        p_right = b * (1 - self.p_S) + (1 - b) * self.p_G
        after = []
        for correct in (True, False):
            if correct:
                num, rest = b * (1 - self.p_S), (1 - b) * self.p_G
            else:
                num, rest = b * self.p_S, (1 - b) * (1 - self.p_G)
            post = num / (num + rest) if (num + rest) > 0 else b
            after.append(post * (1 - self.p_F) + (1 - post) * self.p_T)
        return (p_right * after[0] + (1 - p_right) * after[1]) - b


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

    def expected_gain(self, cid, now_h):
        return self.core.expected_gain(cid, now_h)


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

    def expected_gain(self, cid, now_h):
        return self.core.expected_gain(cid, now_h)


def make_model(kind: str, cids, **kw) -> MasteryModel:
    if kind == "bkt":                 # plain BKT tutor, shared params, no decay
        kw.setdefault("threshold", 0.9)
        return ContinuousMastery(cids, forget_per_day=0.0, **kw)
    if kind == "binary":
        return BinaryMastery(cids, **kw)
    if kind == "continuous":
        return ContinuousMastery(cids, forget_per_day=0.0, **kw)
    if kind == "bkt_forget":          # Schodde-style: forgetting inside BKT
        kw.setdefault("p_F", 0.05)
        return ContinuousMastery(cids, forget_per_day=0.0, **kw)
    if kind == "continuous_forget":
        kw.setdefault("forget_per_day", 0.10)
        return ContinuousMastery(cids, **kw)
    raise ValueError(kind)


# What the UI and the experiments pick from. Add a kind to make_model
# and a line here; nothing else needs editing.
MASTERY_MODELS = {
    "bkt":              "Plain BKT tutor, same parameters as the BKT student, "
                        "mastered = belief >= threshold",
    "binary":           "CurriculumTutor-style: BKT belief latched once it "
                        "crosses the threshold, never revised down. Uses its "
                        "own p_T = 0.06, not the shared value",
    "continuous":       "BKT belief used as-is, threshold 0.80",
    "continuous_forget": "BKT belief that decays 10%/day between practices",
    "bkt_forget":       "BKT with a forget probability p_F inside the update",
}
