"""One-step lookahead on the tutor's belief (Schodde et al., HRI 2017).
"""

from .base import Scheduler, pick_question, register_scheduler


@register_scheduler('predictive')
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
        return pick_question(cur, cid, rng,
                              target_difficulty=model.belief(cid, now_h),
                              last_qid=last_qid)
