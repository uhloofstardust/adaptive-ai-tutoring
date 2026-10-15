"""Baselines: random, CurriculumTutor's rule, and its unrestricted variant.
"""

from .base import Scheduler, pick_question, register_scheduler, zpd


@register_scheduler('random')
class RandomScheduler(Scheduler):
    name = "random"

    def select(self, cur, model, now_h, rng, last_qid):
        cid = rng.choice(cur.ids())
        return pick_question(cur, cid, rng, None, last_qid)


@register_scheduler('curriculum_tutor', 'uniform_zpd')
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
        return pick_question(cur, cid, rng, None, last_qid)


@register_scheduler('uniform_unmastered')
class UniformUnmasteredScheduler(Scheduler):
    """Q1: uniform over every concept the tutor does not yet believe
    mastered, whether or not its prerequisites are ready.

    The contrast with uniform_zpd (Q2) is the whole point: Q2 refuses to
    ask a concept until its prerequisites are believed mastered, Q1 will
    ask anything still outstanding. Against a student for whom
    prerequisites do not matter the two are interchangeable; against one
    who cannot learn a concept before its prerequisites, Q1 wastes
    questions on concepts that cannot yet be learned.

    Note this is NOT the same as `random`, which also re-asks concepts
    already believed mastered.
    """
    name = "uniform_unmastered"

    def select(self, cur, model, now_h, rng, last_qid):
        eligible = [cid for cid in cur.ids()
                    if not model.is_mastered(cid, now_h)]
        if not eligible:
            eligible = cur.ids()
        return pick_question(cur, rng.choice(eligible), rng, last_qid=last_qid)
