"""Choose each review rule's fade threshold r_review.

Done on the tuning learners (seeds 4242 onward). The comparison of rules in
`forgetting_rules` uses fresh learners, so a chosen value is never graded
on the data it was chosen on. The score is "robust": usable concepts
averaged over breaks of 0 to 10 days, since a tutor cannot know the break.
"""

from cursim.curriculum import build_curriculum
from cursim.simulation import RunSpec, run_condition

from ..registry import experiment
from .common import add_robust_score, usable_ci
from .plots import fig_review_tuning

RULES = ("lowest_recall", "recall_threshold", "proportional_review")
R_REVIEW = (0.4, 0.55, 0.7, 0.8, 0.9)
RATES = (0.05, 0.10)
MAX_BREAK = 10


@experiment("review_tuning",
            "Pick the fade threshold of each review rule, on tuning "
            "learners.",
            defaults=dict(n_learners=30, r_review=R_REVIEW, rates=RATES),
            curriculum="layered_40")
def review_tuning(n_learners=30, r_review=R_REVIEW, rates=RATES, cur=None,
                  **_):
    cur = cur or build_curriculum("layered_40")
    rows = []
    for rule in RULES:
        for rate in rates:
            for r in r_review:
                res = run_condition(cur, RunSpec(
                    scheduler=rule, scheduler_params={"r_review": r},
                    mastery_model="continuous_forget",
                    model_forget_per_day=rate,
                    break_days=tuple(range(MAX_BREAK + 1)),
                    label=f"{rule} r={r} rate={rate}"),
                    n_learners=n_learners)
                add_robust_score(res, MAX_BREAK)
                m, e = usable_ci(res, "robust")
                rows.append(dict(rule=rule, belief_decay_per_day=rate,
                                 r_review=r, robust=round(m, 2),
                                 robust_ci95=round(e, 2),
                                 usable_3d=round(res.mean("retained_usable"),
                                                 2)))
    best = {}
    for rule in RULES:
        mean_by_r = {r: sum(x["robust"] for x in rows
                            if x["rule"] == rule and x["r_review"] == r)
                     / len(rates) for r in r_review}
        best[rule] = max(mean_by_r, key=mean_by_r.get)
    return {"tables": {"tuning": rows},
            "figures": {"review_tuning": fig_review_tuning(
                RULES, rates, r_review, rows)},
            "summary": f"{n_learners} tuning learners on {cur.name}. Best "
                       f"r_review averaged over the two decay rates: "
                       f"{', '.join(f'{k} {v}' for k, v in best.items())}."}
