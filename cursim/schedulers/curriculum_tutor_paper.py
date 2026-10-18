"""CurriculumTutor as published (Shabana et al., AIED 2022, Algorithm 2),
and the two knobs this thesis adds to it, one at a time.

The published algorithm
-----------------------
  * The ZPD starts as the concepts with no prerequisites. Each concept in
    the ZPD is an arm of a Bernoulli bandit; the reward is 1 for a correct
    answer, 0 for a wrong one.
  * Each step the arm is chosen by KL-UCB (paper section 5).
  * After every answer a CUSUM change-point test runs on that concept:
        U <- max(0, U + log p1(x) / p0(x))
    with p0 = Bernoulli(p_guess) (not learned) and p1 = Bernoulli(1-p_slip)
    (learned). When U exceeds h the concept is marked learned, and it never
    comes back: the paper has no forgetting.
  * A concept joins the ZPD once all its prerequisites are learned.
  * The paper sets h = ln(1/0.0004). p_guess and p_slip are "defined by
    the user"; the tutor here uses the shared BKT values (p_G, p_S).

Not fixed by the paper, chosen here: the KL-UCB exploration term is ln(t)
(c = 0 in ln t + c ln ln t), t counts questions asked so far; a concept's
question is drawn at random from its questions; the paper stops when the
ZPD is empty, and here the questions left over are left unasked
(`leftover="idle"`, the default). `leftover="revise"` spends them on
revision instead: a robustness variant, not the published algorithm.

The two knobs (everything else is the published algorithm)
----------------------------------------------------------
  depth_h   how deep to study a topic before moving on: the CUSUM
            threshold h. Larger h needs more correct answers in a row.
            Default is the paper's ln(1/0.0004).
  revision  the revision budget: the share of all questions spent asking
            about already-learned topics (least recently asked first;
            `revise_order="random"` is only a robustness check).
            Default 0, which is the published algorithm.

With both at their defaults this IS CurriculumTutor. Neither knob reads
the learner's state or the break length.
"""

import math

from ..params import BKT_PARAMS
from .base import Scheduler, pick_question, register_scheduler

PAPER_H = math.log(1.0 / 0.0004)


def kl_bern(p, q):
    eps = 1e-12
    p = min(max(p, eps), 1 - eps)
    q = min(max(q, eps), 1 - eps)
    return p * math.log(p / q) + (1 - p) * math.log((1 - p) / (1 - q))


def kl_ucb_index(mean, n, t):
    """Largest q in [mean, 1] with n * kl(mean, q) <= ln t."""
    if n == 0:
        return float("inf")
    bound = math.log(max(t, 2)) / n
    lo, hi = mean, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if kl_bern(mean, mid) <= bound:
            lo = mid
        else:
            hi = mid
    return lo


@register_scheduler("curriculum_tutor_paper")
class CurriculumTutorPaper(Scheduler):
    name = "curriculum_tutor_paper"

    def __init__(self, depth_h=PAPER_H, revision=0.0, revise_order="oldest",
                 leftover="idle", p_guess=BKT_PARAMS["p_G"], p_slip=BKT_PARAMS["p_S"]):
        self.h = depth_h
        self.revision = revision
        self.leftover = leftover          # "idle" (paper) or "revise"
        self.revise_order = revise_order   # "oldest" (default) or "random"
        self.llr_right = math.log((1 - p_slip) / p_guess)
        self.llr_wrong = math.log(p_slip / (1 - p_guess))
        self.learned = set()
        self.u = {}            # CUSUM statistic per concept
        self.n = {}            # KL-UCB pulls per concept
        self.s = {}            # KL-UCB rewards per concept
        self.last_asked = {}   # step each concept was last asked
        self.t = 0
        self.credit = 0.0
        self.revising_now = False
        self.n_revision = 0
        self.finished_at = None   # first question with an empty ZPD

    def stats(self):
        """What the tutor did, for the experiment tables."""
        return dict(revision_share=self.n_revision / max(self.t, 1),
                    tutor_learned=len(self.learned),
                    finished=self.finished_at is not None)

    # -- ZPD ------------------------------------------------------------
    def zpd(self, cur):
        return [cid for cid, c in cur.concepts.items()
                if cid not in self.learned
                and all(p in self.learned for p in c.prereqs)]

    # -- feedback --------------------------------------------------------
    def observe(self, cid, correct, now_h):
        self.last_asked[cid] = self.t
        if self.revising_now:
            return                       # revision answers change nothing
        self.n[cid] = self.n.get(cid, 0) + 1
        self.s[cid] = self.s.get(cid, 0) + (1 if correct else 0)
        u = self.u.get(cid, 0.0)
        u = max(0.0, u + (self.llr_right if correct else self.llr_wrong))
        self.u[cid] = u
        if u > self.h:
            self.learned.add(cid)

    # -- choice ----------------------------------------------------------
    def select(self, cur, model, now_h, rng, last_qid):
        self.t += 1
        z = self.zpd(cur)
        want_revision = False
        if self.learned:
            self.credit = min(self.credit + self.revision, 1.0)
            if self.credit >= 1.0 - 1e-9:
                want_revision = True
        if not z and self.learned:
            if self.finished_at is None:
                self.finished_at = self.t
            if self.leftover == "idle":
                # the paper stops when the ZPD is empty: no question is
                # asked, unless the revision budget asks for one
                if not want_revision:
                    return None
            else:
                want_revision = True   # spare questions go to revision
        self.revising_now = want_revision
        if want_revision:
            self.credit = max(0.0, self.credit - 1.0)
            self.n_revision += 1
            if self.revise_order == "random":
                cid = rng.choice(sorted(self.learned))
            else:
                cid = min(sorted(self.learned),
                          key=lambda c: self.last_asked.get(c, -1))
        else:
            if not z:                    # nothing learned, nothing to teach
                z = cur.ids()
            cid = max(z, key=lambda c: (
                kl_ucb_index(self.s.get(c, 0) / self.n[c], self.n[c], self.t)
                if self.n.get(c, 0) else float("inf"), rng.random()))
        return pick_question(cur, cid, rng, None, last_qid)
