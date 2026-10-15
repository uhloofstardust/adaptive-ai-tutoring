"""Belief or scheduling? Cross every belief model with
every question-selection rule.

The tutors compared so far differ in both at once, so a gain cannot be
credited to either. Here each belief model is run under each scheduler on
the same learners. The oracle row gives the scheduler a perfect belief
(it reads the learner's true mastery), which bounds what better
estimation alone could buy.
"""

from cursim.curriculum import build_curriculum
from cursim.simulation import RunSpec, run_condition

from ..registry import experiment
from .common import PRIMARY, paired_row, usable_ci
from .plots import fig_grid

BELIEFS = ["binary", "continuous", "continuous_forget", "oracle"]
SCHEDS = ["curriculum_tutor", "continuous", "adaptive_review"]
BASE = ("binary", "curriculum_tutor")        # the paper's CurriculumTutor


@experiment("belief_scheduler_grid",
            "Cross every belief model with every scheduler to separate "
            "belief tracking from question selection.",
            defaults=dict(n_learners=30), curriculum="layered_40")
def belief_scheduler_grid(n_learners=30, cur=None, **_):
    cur = cur or build_curriculum("layered_40")
    res = {(b, s): run_condition(
        cur, RunSpec(scheduler=s, mastery_model=b, label=f"{s}/{b}"),
        n_learners=n_learners) for b in BELIEFS for s in SCHEDS}
    rand = run_condition(cur, RunSpec(scheduler="random",
                                      mastery_model="binary",
                                      label="random"),
                         n_learners=n_learners)
    base = res[BASE]
    label = lambda k: f"{k[1]} + {k[0]}"

    grid = []
    for (b, s), r in res.items():
        m, e = usable_ci(r)
        d = paired_row(label(BASE), label((b, s)), PRIMARY, base, r)
        grid.append(dict(belief=b, scheduler=s, usable=round(m, 2),
                         ci95=round(e, 2), vs_baseline=d["mean_diff"],
                         wins=d["wins"], losses=d["losses"],
                         p_sign=d["p_sign"]))
    m, e = usable_ci(rand)
    d = paired_row(label(BASE), "random", PRIMARY, base, rand)
    grid.append(dict(belief="(ignored)", scheduler="random",
                     usable=round(m, 2), ci95=round(e, 2),
                     vs_baseline=d["mean_diff"], wins=d["wins"],
                     losses=d["losses"], p_sign=d["p_sign"]))

    effects = []
    for s in SCHEDS:                          # change belief, hold scheduler
        for a, b in [("binary", "continuous_forget"),
                     ("continuous_forget", "oracle")]:
            effects.append(paired_row(label((a, s)), label((b, s)), PRIMARY,
                                      res[(a, s)], res[(b, s)],
                                      varied="belief", held=s))
    for b in BELIEFS:                         # change scheduler, hold belief
        for s in SCHEDS[1:]:
            effects.append(paired_row(label((b, SCHEDS[0])), label((b, s)),
                                      PRIMARY, res[(b, SCHEDS[0])],
                                      res[(b, s)], varied="scheduler",
                                      held=b))

    cell = {k: r.mean(PRIMARY) for k, r in res.items()}
    top = max(cell.values())
    gain = lambda k: cell[k] - cell[BASE]
    summary = (
        f"{n_learners} learners on {cur.name}. Baseline (CurriculumTutor, "
        f"binary belief) {cell[BASE]:.2f} usable. Best cell "
        f"{max(cell, key=cell.get)} at {top:.2f}. Swapping only the belief "
        f"to time decay under CurriculumTutor: "
        f"{gain(('continuous_forget', 'curriculum_tutor')):+.2f}; swapping "
        f"only the scheduler to adaptive review under the binary belief: "
        f"{gain(('binary', 'adaptive_review')):+.2f}.")
    return {"tables": {"grid": grid, "effects": effects},
            "figures": {"grid": fig_grid(BELIEFS, SCHEDS, cell,
                                         cell[BASE])},
            "summary": summary}
