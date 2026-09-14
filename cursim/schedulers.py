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

    def observe(self, cid: str, correct: bool, now_h: float):
        """Told what happened after each answer. Most policies ignore it."""
        pass

    def select(self, cur: Curriculum, model: MasteryModel, now_h: float,
               rng: random.Random, last_qid: Optional[str]) -> Question:
        raise NotImplementedError


def zpd(cur, model, now_h):
    """Concepts the tutor may teach now: not believed mastered, and every
    prerequisite believed mastered. This is CurriculumTutor's ZPD."""
    return [cid for cid, c in cur.concepts.items()
            if not model.is_mastered(cid, now_h)
            and all(model.is_mastered(p, now_h) for p in c.prereqs)]


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
        eligible = zpd(cur, model, now_h)
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


class PredictiveScheduler(Scheduler):
    """Schodde, Bergmann & Kopp (HRI 2017), simplified.

    Instead of sampling, look one step ahead: for every concept the
    student is ready for, ask "if I posed this, how much would my belief
    about them move, on average?" Then pick the biggest expected move.
    Ties broken randomly so it does not get stuck.
    """
    name = "predictive"

    def select(self, cur, model, now_h, rng, last_qid):
        best, best_g = [], -1.0
        for cid, c in cur.concepts.items():
            if model.is_mastered(cid, now_h):
                continue
            if not all(model.is_mastered(p, now_h) for p in c.prereqs):
                continue
            g = model.expected_gain(cid, now_h)
            if g > best_g + 1e-12:
                best, best_g = [cid], g
            elif abs(g - best_g) <= 1e-12:
                best.append(cid)
        if not best:
            best = cur.ids()
        cid = rng.choice(best)
        return _pick_question(cur, cid, rng,
                              target_difficulty=model.belief(cid, now_h),
                              last_qid=last_qid)


class MapleScheduler(Scheduler):
    """Segal et al. (2018), simplified to concepts instead of items.

    Every concept gets a weight. Easy concepts (low tier) start heavy.
    Sample a concept in proportion to its weight, plus a little noise so
    it keeps exploring. After each answer, shift weight toward or away
    from the harder concepts.
    """
    name = "maple"

    def __init__(self, gamma=0.10, step=0.30, ranked=True):
        self.gamma, self.step, self.ranked = gamma, step, ranked
        self.w = None
        self.tier = None

    def _init(self, cur, rng):
        ids = cur.ids()
        self.tier = {c: cur.concepts[c].tier for c in ids}
        if self.ranked:                      # easier concepts start heavier
            self.w = {c: math.exp(-0.6 * self.tier[c]) for c in ids}
        else:                                # "naive": no difficulty info
            self.w = {c: rng.uniform(0.5, 1.5) for c in ids}
        self._normalize()

    def _normalize(self):
        tot = sum(self.w.values())
        for c in self.w:
            self.w[c] = max(self.w[c] / tot, 1e-9)

    def observe(self, cid, correct, now_h):
        if self.w is None:
            return
        # succeeded -> harder concepts become more attractive, and vice versa
        d = self.step if correct else -self.step
        here = self.tier[cid]
        for c in self.w:
            if self.tier[c] > here:
                self.w[c] *= math.exp(d)
        self._normalize()

    def select(self, cur, model, now_h, rng, last_qid):
        if self.w is None:
            self._init(cur, rng)
        ids = cur.ids()
        sc = []
        for c in ids:
            v = self.w[c] * (1 - self.gamma) + rng.uniform(0, 1) * self.gamma
            if model.is_mastered(c, now_h):
                v *= 0.05                    # mostly done, rarely revisit
            sc.append(max(v, 1e-12))
        tot = sum(sc)
        r, acc = rng.uniform(0, tot), 0.0
        cid = ids[-1]
        for c, v in zip(ids, sc):
            acc += v
            if acc >= r:
                cid = c
                break
        return _pick_question(cur, cid, rng,
                              target_difficulty=model.belief(cid, now_h),
                              last_qid=last_qid)


class NaiveMapleScheduler(MapleScheduler):
    """Same bandit, but with no difficulty ranking to start from."""
    name = "naive_maple"

    def __init__(self, **kw):
        super().__init__(ranked=False, **kw)


class UCBScheduler(Scheduler):
    """Plain UCB1 over concepts.

    Reward = 1 if the student got it right. Each ready concept gets
    mean reward + sqrt(2 ln t / n), so rarely-tried concepts get a
    bonus. Untried concepts are tried first.
    """
    name = "ucb"

    def __init__(self, c=1.0):
        self.c, self.n, self.s, self.t = c, {}, {}, 0

    def observe(self, cid, correct, now_h):
        self.n[cid] = self.n.get(cid, 0) + 1
        self.s[cid] = self.s.get(cid, 0.0) + (1.0 if correct else 0.0)
        self.t += 1

    def select(self, cur, model, now_h, rng, last_qid):
        ready = [cid for cid, c in cur.concepts.items()
                 if not model.is_mastered(cid, now_h)
                 and all(model.is_mastered(p, now_h) for p in c.prereqs)]
        if not ready:
            ready = cur.ids()
        fresh = [cid for cid in ready if self.n.get(cid, 0) == 0]
        if fresh:
            cid = rng.choice(fresh)
        else:
            t = max(self.t, 1)
            cid = max(ready, key=lambda k: self.s[k] / self.n[k] +
                      self.c * math.sqrt(2.0 * math.log(t) / self.n[k]))
        return _pick_question(cur, cid, rng, last_qid=last_qid)


SCHEDULERS = {
    "random": RandomScheduler,
    "curriculum_tutor": CurriculumTutorScheduler,
    "continuous": ContinuousScheduler,
    "adaptive_review": AdaptiveReviewScheduler,
    "predictive": PredictiveScheduler,
    "maple": MapleScheduler,
    "naive_maple": NaiveMapleScheduler,
    "ucb": UCBScheduler,
}
