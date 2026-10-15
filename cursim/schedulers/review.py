"""Continuous-belief scheduling, with and without a review term.
"""

import math

from .base import Scheduler, pick_question, register_scheduler


@register_scheduler('continuous')
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
        return pick_question(cur, best, rng,
                              target_difficulty=model.belief(best, now_h),
                              last_qid=last_qid)


@register_scheduler('adaptive_review')
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
        return pick_question(cur, best, rng,
                              target_difficulty=model.belief(best, now_h),
                              last_qid=last_qid)
