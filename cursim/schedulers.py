"""Schedulers: which question to ask next.

All of them see the curriculum graph and the tutor's mastery model.
None of them sees the learner. Swapping schedulers with the mastery
model held fixed isolates the value of the policy; swapping mastery
models with the scheduler held fixed isolates the value of the
representation.

    RandomScheduler        uniform over all questions. Floor.
    CurriculumTutor        the original paper's rule: uniform among
                           concepts that are not mastered and whose
                           prerequisites are all mastered, then a
                           uniform question inside the concept
                           (equal-difficulty assumption).
    ContinuousScheduler    soft prerequisites and a learning zone on
                           the continuous belief, plus difficulty
                           matched to the belief. No review.
    AdaptiveReview         the above plus a review term that grows
                           with time since a concept was practised,
                           so faded concepts come back.
"""

import math
import random
from typing import Optional

from .curriculum import Curriculum, Question
from .mastery import MasteryModel


class Scheduler:
    name = "base"

    def select(self, cur: Curriculum, model: MasteryModel, now_h: float,
               rng: random.Random, last_qid: Optional[str]) -> Question:
        raise NotImplementedError


def _pick_question(cur, cid, rng, target_difficulty=None,
                   last_qid=None) -> Question:
    qs = [q for q in cur.concepts[cid].questions if q.qid != last_qid]
    if not qs:
        qs = cur.concepts[cid].questions
    if target_difficulty is None:
        return rng.choice(qs)
    # closest difficulty to the target, ties broken randomly
    best = min(abs(q.difficulty - target_difficulty) for q in qs)
    near = [q for q in qs
            if abs(q.difficulty - target_difficulty) <= best + 0.05]
    return rng.choice(near)


class RandomScheduler(Scheduler):
    name = "random"

    def select(self, cur, model, now_h, rng, last_qid):
        cid = rng.choice(cur.ids())
        return _pick_question(cur, cid, rng, None, last_qid)


class CurriculumTutorScheduler(Scheduler):
    """The original rule, faithful to the paper's assumptions."""
    name = "curriculum_tutor"

    def select(self, cur, model, now_h, rng, last_qid):
        eligible = []
        for cid, c in cur.concepts.items():
            if model.is_mastered(cid, now_h):
                continue
            if all(model.is_mastered(p, now_h) for p in c.prereqs):
                eligible.append(cid)
        if not eligible:
            # everything the tutor can reach is mastered in its view;
            # the paper has nothing more to teach, so it revisits
            eligible = cur.ids()
        cid = rng.choice(eligible)
        return _pick_question(cur, cid, rng, None, last_qid)


class ContinuousScheduler(Scheduler):
    """Soft prerequisites, learning zone, difficulty matching."""
    name = "continuous"

    def __init__(self, prereq_ok=0.45, zone_lo=0.15, zone_hi=0.85,
                 gate_penalty=0.30):
        self.prereq_ok = prereq_ok
        self.zone_lo, self.zone_hi = zone_lo, zone_hi
        self.gate_penalty = gate_penalty

    def _score(self, cur, model, cid, now_h):
        b = model.belief(cid, now_h)
        pre = cur.concepts[cid].prereqs
        gate = 1.0
        if pre and min(model.belief(p, now_h) for p in pre) < self.prereq_ok:
            gate = self.gate_penalty
        if b > self.zone_hi:
            base = 0.10
        elif b >= self.zone_lo:
            base = 1.0
        else:
            base = 0.75
        return base * gate

    def select(self, cur, model, now_h, rng, last_qid):
        best, best_s = None, -1.0
        for cid in cur.ids():
            s = self._score(cur, model, cid, now_h) * rng.uniform(0.93, 1.07)
            if s > best_s:
                best, best_s = cid, s
        # ask a question the learner can plausibly reach: difficulty
        # tracking the belief rather than a uniform draw
        return _pick_question(cur, best, rng,
                              target_difficulty=model.belief(best, now_h),
                              last_qid=last_qid)


class AdaptiveReviewScheduler(ContinuousScheduler):
    """Continuous scheduling plus spaced review of faded concepts."""
    name = "adaptive_review"

    def __init__(self, review_weight=0.8, tau_days=2.5, **kw):
        super().__init__(**kw)
        self.review_weight = review_weight
        self.tau_days = tau_days
        self.last_practised = {}

    def _urgency(self, cid, now_h):
        t0 = self.last_practised.get(cid)
        if t0 is None:
            return 0.35                     # unseen: mild novelty pull
        days = (now_h - t0) / 24.0
        return 1.0 - math.exp(-days / self.tau_days)

    def select(self, cur, model, now_h, rng, last_qid):
        best, best_s = None, -1.0
        for cid in cur.ids():
            b = model.belief(cid, now_h)
            s = self._score(cur, model, cid, now_h)
            u = self._urgency(cid, now_h)
            # a well-known concept is worth revisiting only when it has
            # had time to fade; a shaky one is worth it right away
            s += self.review_weight * u * (b ** 2)
            s *= rng.uniform(0.93, 1.07)
            if s > best_s:
                best, best_s = cid, s
        self.last_practised[best] = now_h
        return _pick_question(cur, best, rng,
                              target_difficulty=model.belief(best, now_h),
                              last_qid=last_qid)


SCHEDULERS = {
    "random": RandomScheduler,
    "curriculum_tutor": CurriculumTutorScheduler,
    "continuous": ContinuousScheduler,
    "adaptive_review": AdaptiveReviewScheduler,
}
