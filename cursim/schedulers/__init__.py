"""Question-selection policies. See base.py for how to add one.

    baselines   random, curriculum_tutor (= uniform_zpd), uniform_unmastered
    review      continuous, adaptive_review
    lookahead   predictive
    bandits     maple, naive_maple, ucb
    forgetting  lowest_recall, recall_threshold, proportional_review
    curriculum_tutor_paper  the published algorithm + two knobs (depth, revision)
"""

from .base import SCHEDULERS, Scheduler, pick_question, register_scheduler, zpd
from . import baselines, review, lookahead, bandits, forgetting, curriculum_tutor_paper  # noqa: F401  (registers)
from .baselines import (CurriculumTutorScheduler, RandomScheduler,
                        UniformUnmasteredScheduler)
from .review import AdaptiveReviewScheduler, ContinuousScheduler
from .lookahead import PredictiveScheduler
from .bandits import MapleScheduler, NaiveMapleScheduler, UCBScheduler
from .forgetting import (LowestRecallScheduler, ProportionalReviewScheduler,
                         RecallThresholdScheduler)

__all__ = ["SCHEDULERS", "Scheduler", "pick_question", "register_scheduler",
           "zpd"]
