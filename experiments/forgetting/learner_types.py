"""Experiment 3: does the best strategy depend on the learner?

Four learner profiles crossed with three tutors. `forgetful` learns at
close to normal speed but has a short memory half-life, which keeps
ability and memory separate dials.
"""

from cursim.curriculum import build_curriculum

from ..registry import experiment
from .common import (THREE_TUTORS, condition_row, paired_row,
                     run_conditions)
from .plots import fig_learner_types

PROFILE_NAMES = ("fast", "average", "slow", "forgetful")


@experiment("learner_types",
            "Learner profile against tutoring condition: does the ranking "
            "of tutors change from learner to learner?",
            defaults=dict(n_learners=30), curriculum="layered_40")
def learner_types(n_learners=30, cur=None, **_):
    cur = cur or build_curriculum("layered_40")
    rows, pairs, matrix = [], [], {}
    for prof in PROFILE_NAMES:
        res = run_conditions(cur, THREE_TUTORS, n_learners, profile=prof)
        matrix[prof] = {k: v.mean("retained_usable") for k, v in res.items()}
        rows += [condition_row(f"3_{prof}", label, r)
                 for label, r in res.items()]
        best = max(matrix[prof], key=lambda k: matrix[prof][k])
        pairs.append(paired_row("CT + binary", best, "retained_usable",
                                res["CT + binary"], res[best],
                                profile=prof, best=best))
    ranking = "; ".join(
        f"{p}: {max(m, key=m.get)} ({max(m.values()):.1f})"
        for p, m in matrix.items())
    return {"tables": {"conditions": rows, "paired_best_vs_binary": pairs},
            "figures": {"learner_types": fig_learner_types(matrix)},
            "summary": f"{n_learners} learners on {cur.name}. Best tutor by "
                       f"profile (concepts usable after the break): "
                       f"{ranking}."}
