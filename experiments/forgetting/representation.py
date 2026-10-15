"""Experiment 1: does continuous mastery beat binary mastery?

Hold CurriculumTutor's question-selection rule fixed and change only what
the tutor believes. The simulated learner is identical in every arm
(continuous mastery, real forgetting, same seeds), so a difference is
attributable to the representation alone.
"""

from cursim.curriculum import build_curriculum

from ..registry import experiment
from .common import condition_row, mean_curve, paired_row, run_conditions
from .plots import fig_representation, fig_trajectories

ARMS = [("curriculum_tutor", "binary", "binary (permanent)"),
        ("curriculum_tutor", "continuous", "continuous"),
        ("curriculum_tutor", "continuous_forget", "continuous + forgetting")]
METRICS = ("final_learned", "retained_usable", "retained_mastery")


@experiment("representation",
            "Binary vs continuous mastery with the scheduling rule held "
            "fixed: what does the permanent-mastery assumption cost?",
            defaults=dict(n_learners=30), curriculum="layered_40")
def representation(n_learners=30, cur=None, **_):
    cur = cur or build_curriculum("layered_40")
    res = run_conditions(cur, ARMS, n_learners)
    rows = [condition_row("1_representation", label, r)
            for label, r in res.items()]
    a, b = res["binary (permanent)"], res["continuous + forgetting"]
    pairs = [paired_row("binary (permanent)", "continuous + forgetting",
                        k, a, b) for k in METRICS]
    top = pairs[1]
    summary = (
        f"{n_learners} learners on {cur.name}. Concepts still usable after "
        f"the break: "
        + ", ".join(f"{r['condition']} {r['retained_usable']:.1f}" for r in rows)
        + f". Continuous + forgetting minus binary: {top['mean_diff']:+.2f}, "
        f"better for {top['wins']}/{top['n']} learners (sign p "
        f"{top['p_sign']:.4f}).")
    return {"tables": {"conditions": rows, "paired": pairs},
            "figures": {
                "representation": fig_representation(res),
                "trajectories": fig_trajectories(
                    {k: mean_curve(v) for k, v in res.items()},
                    "Learning under three mastery representations")},
            "summary": summary}
