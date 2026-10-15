"""Do the published belief models and schedulers beat time-decay?

BKT forgetting (p_F, Schodde et al. 2017), the predictive scheduler
(Schodde et al. 2017) and MAPLE (Segal et al. 2018), against
CurriculumTutor with the binary and time-decay beliefs.

Caution when reading it: Predictive and MAPLE are run only on the
`bkt_forget` belief, while the time-decay arm uses a different belief
model. The two are not crossed, so a gap between those arms mixes the
effect of the scheduler with the effect of the belief model.
"""

import math
import statistics as st

from cursim.curriculum import build_curriculum
from cursim.simulation import RunSpec, run_condition
from cursim.stats import paired

from ..registry import experiment

# (label, scheduler, mastery model)
ARMS = [
    ("CT + binary (paper's original)", "curriculum_tutor", "binary"),
    ("CT + time decay", "curriculum_tutor", "continuous_forget"),
    ("CT + BKT forget (p_F)", "curriculum_tutor", "bkt_forget"),
    ("Predictive + BKT forget", "predictive", "bkt_forget"),
    ("MAPLE + BKT forget", "maple", "bkt_forget"),
    ("Naive MAPLE + BKT forget", "naive_maple", "bkt_forget"),
]
HEAD_TO_HEAD = [
    ("CT + time decay", "CT + BKT forget (p_F)"),
    ("CT + BKT forget (p_F)", "Predictive + BKT forget"),
    ("Naive MAPLE + BKT forget", "MAPLE + BKT forget"),
    ("CT + BKT forget (p_F)", "MAPLE + BKT forget"),
]


def _ci(vals):
    return 1.96 * st.stdev(vals) / math.sqrt(len(vals))


@experiment("belief_schedulers",
            "BKT forgetting, the predictive scheduler and MAPLE against "
            "CurriculumTutor with time-decay beliefs.",
            defaults=dict(n_learners=30), curriculum="layered_40")
def belief_schedulers(n_learners=30, cur=None, **_):
    cur = cur or build_curriculum("layered_40")
    res, arms = {}, []
    for label, sched, mm in ARMS:
        r = run_condition(cur, RunSpec(scheduler=sched, mastery_model=mm,
                                       label=label), n_learners=n_learners)
        res[label] = r
        arms.append(dict(
            arm=label, scheduler=sched, mastery=mm, n=n_learners,
            learned=round(r.mean("final_learned"), 3),
            usable=round(r.mean("retained_usable"), 3),
            usable_ci95=round(_ci([x["retained_usable"]
                                   for x in r.per_learner]), 3),
            mean_mastery=round(r.mean("final_mastery"), 4),
            covered=round(r.mean("coverage"), 2)))
    h2h = []
    for a, b in HEAD_TO_HEAD:
        d = paired(res[a], res[b], "retained_usable")
        h2h.append(dict(comparison=f"{b} - {a}", mean_diff=d["mean_diff"],
                        wins=d["wins"], n=d["n"], p_sign=d["p_sign"]))
    best = max(arms, key=lambda r: r["usable"])
    return {"tables": {"arms": arms, "head_to_head": h2h}, "figures": {},
            "summary": f"{n_learners} learners on {cur.name}. Best arm: "
                       f"{best['arm']} ({best['usable']:.2f} concepts usable "
                       f"after the break). Predictive and MAPLE are not run "
                       f"on the time-decay belief, so they are not compared "
                       f"with it like for like."}
