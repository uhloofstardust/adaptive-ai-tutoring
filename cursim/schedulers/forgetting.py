"""Question-selection rules for a learner who forgets, from the literature.

The papers these come from choose which already-learned item to review.
Our tutor must also decide when to teach something new, so each rule here
is the same two-step policy and only the review choice differs:

  1. A concept is "learned" once the tutor has believed it at or above
     the mastery threshold, and "faded" when its belief has since fallen
     below `r_review`.
  2. If any learned concept has faded, review one, chosen by the rule.
     Otherwise teach something new: CurriculumTutor's choice, a random
     concept the tutor believes unmastered whose prerequisites it believes
     mastered.

The review choices:

    lowest_recall        the faded concept with the lowest belief (the
                         lowest-recall baseline of Hunziker et al. 2019;
                         generalises Leitner and Pimsleur review)
    recall_threshold     the faded concept nearest r_review, the one that
                         has only just slipped (after Lindsey et al. 2014,
                         who reviewed the item nearest a target recall)
    proportional_review  a faded concept at random, weighted by
                         1 - belief (after Tabibian et al. 2019, whose
                         review rate is proportional to 1 - recall)

The greedy marginal-gain rule of Hunziker et al. 2019 was tried too. With
a BKT belief the expected gain from asking falls as the belief rises, so it
picks the same concept as lowest_recall and gave identical results in every
tuning cell (2026-10-15 log); it is not kept as a separate rule.

Nothing is added to the belief: the rules read it and nothing else.
"""

from .base import Scheduler, pick_question, register_scheduler, zpd


class _FadedReview(Scheduler):
    """Teach new material unless a learned concept has faded."""

    def __init__(self, r_review=0.6, learned_at=0.8):
        self.r_review = r_review
        self.learned_at = learned_at
        self.learned = set()

    def review_choice(self, cur, model, faded, now_h, rng):
        raise NotImplementedError

    def select(self, cur, model, now_h, rng, last_qid):
        beliefs = {c: model.belief(c, now_h) for c in cur.ids()}
        self.learned |= {c for c, b in beliefs.items()
                         if b >= self.learned_at}
        faded = [c for c in self.learned if beliefs[c] < self.r_review]
        if faded:
            cid = self.review_choice(cur, model, sorted(faded), now_h, rng)
        else:
            cid = rng.choice(zpd(cur, model, now_h) or cur.ids())
        return pick_question(cur, cid, rng, target_difficulty=beliefs[cid],
                              last_qid=last_qid)

    @staticmethod
    def smallest(items, key, rng):
        """The item with the smallest key; ties broken at random."""
        lo = min(key(c) for c in items)
        return rng.choice([c for c in items if key(c) <= lo + 1e-12])


@register_scheduler("lowest_recall")
class LowestRecallScheduler(_FadedReview):
    name = "lowest_recall"

    def review_choice(self, cur, model, faded, now_h, rng):
        return self.smallest(faded, lambda c: model.belief(c, now_h), rng)


@register_scheduler("recall_threshold")
class RecallThresholdScheduler(_FadedReview):
    name = "recall_threshold"

    def review_choice(self, cur, model, faded, now_h, rng):
        return self.smallest(
            faded, lambda c: abs(model.belief(c, now_h) - self.r_review), rng)


@register_scheduler("proportional_review")
class ProportionalReviewScheduler(_FadedReview):
    name = "proportional_review"

    def review_choice(self, cur, model, faded, now_h, rng):
        w = [max(1e-6, 1.0 - model.belief(c, now_h)) for c in faded]
        return rng.choices(faded, weights=w, k=1)[0]
