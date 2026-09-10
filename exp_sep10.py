"""Sep 10 experiment: two new schedulers and a new mastery model.

  A. Does the predictive scheduler (Schodde et al. 2017) beat the ones
     we already had?
  B. Does MAPLE's difficulty ranking help (MAPLE vs naive MAPLE)?
  C. Does BKT forgetting (p_F) beat time-decay forgetting?

Same 30 learners, same seeds, in every condition. Run:  python3 exp_sep10.py
"""
import csv, math, statistics as st
from cursim.curriculum import build_curriculum
from cursim.simulation import RunSpec, run_condition, paired

N = 30

# (label, scheduler, mastery model)
ARMS = [
    ("CT + binary (paper's original)", "curriculum_tutor", "binary"),
    ("CT + time decay",                "curriculum_tutor", "continuous_forget"),
    ("CT + BKT forget (p_F)",          "curriculum_tutor", "bkt_forget"),
    ("Predictive + BKT forget",        "predictive",       "bkt_forget"),
    ("MAPLE + BKT forget",             "maple",            "bkt_forget"),
    ("Naive MAPLE + BKT forget",       "naive_maple",      "bkt_forget"),
]


def ci(vals):
    m = st.mean(vals)
    e = 1.96 * st.stdev(vals) / math.sqrt(len(vals))
    return m, e


def main():
    cur = build_curriculum()
    res, rows = {}, []
    for label, sch, mm in ARMS:
        r = run_condition(cur, RunSpec(scheduler=sch, mastery_model=mm,
                                       label=label), n_learners=N)
        res[label] = r
        rows.append(dict(
            arm=label, scheduler=sch, mastery=mm, n=N,
            learned=round(r.mean("final_learned"), 3),
            usable=round(r.mean("retained_usable"), 3),
            mean_mastery=round(r.mean("final_mastery"), 4),
            covered=round(r.mean("coverage"), 2)))

    with open("results_sep10.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

    print(f"{N} learners, identical seeds in every arm\n")
    print(f"{'arm':34s} {'learned':>8s} {'usable':>16s} {'covered':>8s}")
    for label, *_ in ARMS:
        r = res[label]
        lm, le = ci([x["final_learned"] for x in r.per_learner])
        um, ue = ci([x["retained_usable"] for x in r.per_learner])
        print(f"  {label:32s} {lm:6.2f}  {um:6.2f} +/- {ue:4.2f}  "
              f"{r.mean('coverage'):6.2f}")

    print("\nhead-to-head, learner by learner (on 'usable after a 3-day break')")
    pairs = [
        ("CT + time decay",              "CT + BKT forget (p_F)"),
        ("CT + BKT forget (p_F)",        "Predictive + BKT forget"),
        ("Naive MAPLE + BKT forget",     "MAPLE + BKT forget"),
        ("CT + BKT forget (p_F)",        "MAPLE + BKT forget"),
    ]
    for a, b in pairs:
        d = paired(res[a], res[b], "retained_usable")
        print(f"  {b} minus {a}:\n"
              f"      {d['mean_diff']:+6.2f}  better for {d['wins']:2d}/{d['n']}"
              f"  sign p {d['p_sign']:.4f}")

    print("\n-> results_sep10.csv")


if __name__ == "__main__":
    main()
