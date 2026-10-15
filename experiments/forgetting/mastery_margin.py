"""How far above "usable" should a tutor push a concept before moving on?

CurriculumTutor stops teaching a concept once its belief reaches the
mastery threshold. With forgetting, a concept stopped at 0.8 has little
room before it falls under the 0.50 usable line, so the threshold acts as
a safety margin whose best size depends on how long the break is. The
threshold is swept for CurriculumTutor with the tutor's decaying belief and
with a perfect belief, over breaks of 0 to 12 days.

Run on the tuning learners (seeds 4242) to explore, and on fresh learners
(`base_seed=9000`) to confirm.
"""

from cursim.curriculum import build_curriculum
from cursim.simulation import RunSpec, run_condition

from ..registry import experiment
from .common import UsableAfter, add_robust_score, usable_ci
from .plots import fig_margin

THRESHOLDS = (0.7, 0.8, 0.9, 0.95, 0.98)
BELIEFS = (("continuous_forget", "tutor's decaying belief"),
           ("oracle", "perfect belief (reference)"))
MAX_BREAK = 10
BREAKS = tuple(range(13))


@experiment("mastery_margin",
            "Sweep the mastery threshold of CurriculumTutor under "
            "forgetting: how much margin above usable is worth it.",
            defaults=dict(n_learners=30, thresholds=THRESHOLDS,
                          belief_rate=0.05, base_seed=4242),
            curriculum="layered_40")
def mastery_margin(n_learners=30, thresholds=THRESHOLDS, belief_rate=0.05,
                   base_seed=4242, cur=None, **_):
    cur = cur or build_curriculum("layered_40")
    rows, panels = [], {}
    for belief, name in BELIEFS:
        panels[name] = {}
        for thr in thresholds:
            res = run_condition(cur, RunSpec(
                scheduler="curriculum_tutor", mastery_model=belief,
                threshold=thr, model_forget_per_day=belief_rate,
                break_days=BREAKS, label=f"{belief} {thr}"),
                n_learners=n_learners, base_seed=base_seed)
            add_robust_score(res, MAX_BREAK)
            panels[name][thr] = [usable_ci(UsableAfter(res, d), "v")[0]
                                 for d in BREAKS]
            m, e = usable_ci(res, "robust")
            rows.append(dict(belief=belief, threshold=thr,
                             usable_0d=round(panels[name][thr][0], 2),
                             usable_3d=round(res.mean("retained_usable"), 2),
                             usable_7d=round(panels[name][thr][7], 2),
                             robust=round(m, 2), robust_ci95=round(e, 2),
                             coverage=round(res.mean("coverage"), 1)))
    best = {b: max((r for r in rows if r["belief"] == b),
                   key=lambda r: r["robust"])["threshold"]
            for b, _ in BELIEFS}
    return {"tables": {"margin": rows},
            "figures": {"margin": fig_margin(
                list(BREAKS), panels,
                f"CurriculumTutor, mastery threshold swept "
                f"(belief decay {belief_rate}/day)")},
            "summary": f"{n_learners} learners (seeds from {base_seed}) on "
                       f"{cur.name}. Best threshold by the robust score "
                       f"(mean over breaks of 0 to {MAX_BREAK} days): "
                       f"decaying belief {best['continuous_forget']}, "
                       f"perfect belief {best['oracle']}."}
