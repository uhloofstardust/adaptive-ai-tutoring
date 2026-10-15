"""Bandit schedulers over concepts: MAPLE (Segal et al., 2018) and UCB1.
"""

import math

from .base import Scheduler, pick_question, register_scheduler


@register_scheduler('maple')
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
        return pick_question(cur, cid, rng,
                              target_difficulty=model.belief(cid, now_h),
                              last_qid=last_qid)


@register_scheduler('naive_maple')
class NaiveMapleScheduler(MapleScheduler):
    """Same bandit, but with no difficulty ranking to start from."""
    name = "naive_maple"

    def __init__(self, **kw):
        super().__init__(ranked=False, **kw)


@register_scheduler('ucb')
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
        return pick_question(cur, cid, rng, last_qid=last_qid)
