"""Simulated students: what the learner truly knows.

    continuous   mastery in [0,1], difficulty, prerequisites, time decay
    bkt          known/unknown coin per concept (S1)
    bkt_prereq   the same, learning slowed until prerequisites are known (S2)

To add one: write a class with the same interface as `Learner`
(`answer`, `true_mastery`, `snapshot`, `mean_mastery`, `n_learned`) and add
an entry to LEARNERS.
"""

from ..params import STUDENT_MODELS
from .bkt import BKTLearner
from .continuous import Learner, LearnerProfile, PROFILES, SimConfig

LEARNERS = {
    "bkt": (BKTLearner,
            "S1. Plain BKT student: a known/unknown coin per concept, no "
            "forgetting, no difficulty, and prerequisites do not affect "
            "learning at all", {}),
    "bkt_prereq": (BKTLearner,
                   "S2. Same, but a concept learns at pT_low until every "
                   "prerequisite is truly known, so order starts to matter",
                   # carry S2's own numbers, so selecting this learner
                   # anywhere gives the same student the experiments use
                   {"prereq_gated_pT": True,
                    "pT_low": STUDENT_MODELS["S2"]["pT_low"]}),
    "continuous": (Learner,
                   "Original cursim student: continuous mastery, difficulty, "
                   "prerequisites, time decay", {}),
}


def learner_kwargs(name: str) -> dict:
    """Extra constructor arguments for a registered learner."""
    entry = LEARNERS[name]
    return dict(entry[2]) if len(entry) > 2 else {}
