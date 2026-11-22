"""Scheduler interface, the registry, and helpers shared by every policy.

A scheduler picks the next question. It sees the curriculum graph and the
tutor's mastery model, never the learner. To add one: subclass `Scheduler`
in a new module under this package, decorate it with
`@register_scheduler("name")`, and import the module in `__init__.py`.
Nothing else changes; experiments refer to schedulers by name.
"""

import random
from typing import Dict, Optional, Type

from ..curriculum import Curriculum, Question
from ..mastery import MasteryModel

SCHEDULERS: Dict[str, Type["Scheduler"]] = {}


def register_scheduler(*names: str):
    """Class decorator: make a Scheduler selectable under one or more
    names (a second name is an alias for the same class)."""
    def deco(cls):
        for n in names:
            if n in SCHEDULERS:
                raise ValueError(f"scheduler name {n!r} already registered")
            SCHEDULERS[n] = cls
        return cls
    return deco


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


def pick_question(cur, cid, rng, target_difficulty=None,
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
