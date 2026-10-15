"""Do review rules from the literature beat CurriculumTutor, and how much
would a perfect belief add?

Fresh learners (seeds 9000 onward), not the ones used to tune r_review. Each
rule is run with the tutor's decaying belief and with a perfect one, and
measured at breaks of 0 to 12 days. "Robust" is usable concepts averaged
over breaks of 0 to 10 days, since a tutor cannot know the break.

The decay rate the tutor assumes is a parameter. 0.05 per day is close to
the true rate of the average learner; 0.10 is twice it, which checks that
the ranking does not depend on the tutor knowing the rate.
"""

from cursim.curriculum import build_curriculum
from cursim.simulation import RunSpec, run_condition

from ..registry import experiment
from .common import (UsableAfter, add_robust_score, paired_row, usable_ci)
from .plots import fig_break_sweep, fig_estimation_cost

# fade thresholds chosen on the tuning learners (review_tuning)
R_REVIEW = {"lowest_recall": 0.4, "recall_threshold": 0.7,
            "proportional_review": 0.4}
RULE_LABELS = {"lowest_recall": "lowest recall",
               "recall_threshold": "recall threshold",
               "proportional_review": "proportional review"}
MAX_BREAK = 10
BREAKS = tuple(range(13))
FRESH_SEED = 9000


@experiment("forgetting_rules",
            "Review rules from the literature against CurriculumTutor on "
            "fresh learners, each with the tutor's belief and a perfect "
            "one.",
            defaults=dict(n_learners=50, belief_rate=0.05),
            curriculum="layered_40")
def forgetting_rules(n_learners=50, belief_rate=0.05, cur=None, **_):
    cur = cur or build_curriculum("layered_40")
    arms = [("CT + binary", "curriculum_tutor", "binary", None),
            ("CT + decay belief", "curriculum_tutor", "continuous_forget",
             None),
            ("adaptive review + decay belief", "adaptive_review",
             "continuous_forget", None)]
    arms += [(f"{RULE_LABELS[r]} + decay belief", r, "continuous_forget",
              {"r_review": v}) for r, v in R_REVIEW.items()]
    arms += [("CT + oracle belief", "curriculum_tutor", "oracle", None)]
    arms += [(f"{RULE_LABELS[r]} + oracle belief", r, "oracle",
              {"r_review": v}) for r, v in R_REVIEW.items()]

    res = {}
    for label, sched, belief, params in arms:
        res[label] = run_condition(cur, RunSpec(
            scheduler=sched, scheduler_params=params, mastery_model=belief,
            model_forget_per_day=belief_rate, break_days=BREAKS,
            label=label), n_learners=n_learners, base_seed=FRESH_SEED)
        add_robust_score(res[label], MAX_BREAK)

    base, ct = "CT + binary", "CT + decay belief"
    summary_rows = []
    for label in res:
        m3, e3 = usable_ci(res[label], "retained_usable")
        mr, er = usable_ci(res[label], "robust")
        row = dict(arm=label, usable_3d=round(m3, 2), ci95_3d=round(e3, 2),
                   robust=round(mr, 2), ci95_robust=round(er, 2))
        for ref, tag in ((base, "vs_ct_binary"), (ct, "vs_ct_decay")):
            if label != ref:
                d = paired_row(ref, label, "robust", res[ref], res[label])
                row[f"robust_{tag}"] = round(d["mean_diff"], 2)
                row[f"p_{tag}"] = d["p_sign"]
        summary_rows.append(row)

    cost_rows = []
    for r, name in RULE_LABELS.items():
        est, orc = f"{name} + decay belief", f"{name} + oracle belief"
        d3 = paired_row(est, orc, "retained_usable", res[est], res[orc])
        dr = paired_row(est, orc, "robust", res[est], res[orc])
        cost_rows.append(dict(
            rule=name, usable_3d_estimated=round(res[est].mean(
                "retained_usable"), 2),
            usable_3d_oracle=round(res[orc].mean("retained_usable"), 2),
            gain_3d=round(d3["mean_diff"], 2), p_3d=d3["p_sign"],
            gain_robust=round(dr["mean_diff"], 2), p_robust=dr["p_sign"]))
    d3 = paired_row(ct, "CT + oracle belief", "retained_usable", res[ct],
                    res["CT + oracle belief"])
    cost_rows.append(dict(
        rule="CurriculumTutor", usable_3d_estimated=round(
            res[ct].mean("retained_usable"), 2),
        usable_3d_oracle=round(res["CT + oracle belief"].mean(
            "retained_usable"), 2),
        gain_3d=round(d3["mean_diff"], 2), p_3d=d3["p_sign"]))

    curves = []
    for d in BREAKS:
        row = {"break_days": d}
        for label in res:
            row[label] = round(usable_ci(UsableAfter(res[label], d), "v")[0],
                               2)
        curves.append(row)

    real = [a[0] for a in arms if "oracle" not in a[0]]
    series = {l: [c[l] for c in curves] for l in real}
    cis = {l: [usable_ci(UsableAfter(res[l], d), "v")[1] for d in BREAKS]
           for l in real}
    figs = {
        "break_curves": fig_break_sweep(
            list(BREAKS), series, cis,
            f"Fresh learners, tutor assumes {belief_rate}/day"),
        "estimation_cost": fig_estimation_cost(
            [x["rule"] for x in cost_rows],
            [x["usable_3d_estimated"] for x in cost_rows],
            [x["usable_3d_oracle"] for x in cost_rows],
            [usable_ci(res[a], "retained_usable")[1] for a in
             [f"{n} + decay belief" for n in RULE_LABELS.values()] + [ct]])}
    best = max((r for r in summary_rows if "oracle" not in r["arm"]),
               key=lambda r: r["robust"])
    return {"tables": {"summary": summary_rows, "curves": curves,
                       "estimation_cost": cost_rows},
            "figures": figs,
            "summary": f"{n_learners} fresh learners on {cur.name}, tutor "
                       f"assumes {belief_rate}/day. Best real tutor by the "
                       f"robust score: {best['arm']} ({best['robust']} "
                       f"usable, mean over breaks of 0 to {MAX_BREAK} days; "
                       f"CT + binary "
                       f"{next(r['robust'] for r in summary_rows if r['arm'] == base)})."}
