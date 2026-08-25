"""Run the Phase 1 experiments and write the figures.

    python run_experiments.py             # all four, plus figures
    python run_experiments.py --exp 1     # one experiment
    python run_experiments.py --selftest  # invariant checks

Everything is seeded. Conditions share learner seeds, so every
comparison is paired: learner i is the same person in every
condition, and differences are the tutor's doing.
"""

import csv
import os
import statistics
import sys

from cursim.curriculum import build_curriculum
from cursim.learner import PROFILES, LearnerProfile, SimConfig
from cursim.plots import (fig_curriculum, fig_experiment1, fig_experiment2,
                          fig_experiment3, fig_experiment4,
                          fig_trajectories)
from cursim.simulation import RunSpec, paired, run_condition, table

N_LEARNERS = 30
FIG = "figures"
DATA = "data"
ROWS = []          # accumulated for results.csv


def record(exp, condition, result):
    ROWS.append({
        "experiment": exp, "condition": condition,
        "n_learners": len(result.per_learner),
        "final_mastery": round(result.mean("final_mastery"), 4),
        "final_learned": round(result.mean("final_learned"), 2),
        "retained_mastery": round(result.mean("retained_mastery"), 4),
        "retained_usable": round(result.mean("retained_usable"), 2),
        "coverage": round(result.mean("coverage"), 2),
        "sd_retained_usable": round(result.sd("retained_usable"), 2),
    })


def mean_curve(res):
    n = min(len(r["curve"]) for r in res.per_learner)
    return [statistics.mean(r["curve"][i] for r in res.per_learner)
            for i in range(n)]


# --------------------------------------------------------------------
def experiment1(cur):
    """Binary vs continuous mastery, scheduling rule held fixed.

    Only the tutor's representation changes. The learner is identical
    in every condition: continuous mastery, real forgetting.
    """
    print("\n" + "=" * 74)
    print("EXPERIMENT 1  binary vs continuous mastery "
          "(CurriculumTutor gate held fixed)")
    print("=" * 74)
    res = {}
    for mm, label in [("binary", "binary (permanent)"),
                      ("continuous", "continuous"),
                      ("continuous_forget", "continuous + forgetting")]:
        spec = RunSpec(scheduler="curriculum_tutor", mastery_model=mm,
                       label=label)
        res[label] = run_condition(cur, spec, n_learners=N_LEARNERS)
        record("1_representation", label, res[label])
    table(res, keys=("final_learned", "retained_usable",
                     "retained_mastery"))

    a, b = res["binary (permanent)"], res["continuous + forgetting"]
    for k in ("final_learned", "retained_usable", "retained_mastery"):
        d = paired(a, b, k)
        print(f"  paired (continuous+forgetting - binary) {k:18s}"
              f" {d['mean_diff']:+7.3f}   better for {d['wins']}/{d['n']}"
              f"   sign p {d['p_sign']:.4f}")
    fig_experiment1(res, f"{FIG}/fig2_representation.png")
    fig_trajectories({k: mean_curve(v) for k, v in res.items()},
                     f"{FIG}/fig3_trajectories.png",
                     "Learning under three mastery representations")
    print("  -> figures/fig2_representation.png, fig3_trajectories.png")
    return res


def experiment2(cur):
    """Forgetting, in both directions.

    World A: the learner forgets. Does a tutor that models forgetting
    do better than one that cannot?
    World B: the learner does not forget. Does modelling forgetting
    cost anything when there is nothing to model?
    """
    print("\n" + "=" * 74)
    print("EXPERIMENT 2  no forgetting vs forgetting")
    print("=" * 74)
    conds = [("curriculum_tutor", "binary", "CT + binary"),
             ("curriculum_tutor", "continuous_forget",
              "CT + forgetting model"),
             ("adaptive_review", "continuous_forget",
              "adaptive review")]
    rows, out = {}, {}
    for forgets, world in [(True, "learner forgets"),
                           (False, "learner does not forget")]:
        rows[world] = {}
        print(f"\n  {world}:")
        res = {}
        for sch, mm, label in conds:
            spec = RunSpec(scheduler=sch, mastery_model=mm,
                           learner_forgets=forgets, label=label)
            res[label] = run_condition(cur, spec, n_learners=N_LEARNERS)
            rows[world][label] = res[label].mean("retained_usable")
            record(f"2_{world.replace(' ', '_')}", label, res[label])
        table(res, keys=("final_learned", "retained_usable"))
        base = res["CT + binary"]
        for label in ("CT + forgetting model", "adaptive review"):
            d = paired(base, res[label], "retained_usable")
            print(f"  paired ({label} - CT + binary) retained_usable"
                  f" {d['mean_diff']:+7.3f}  better for {d['wins']}/{d['n']}"
                  f"  sign p {d['p_sign']:.4f}")
        out[world] = res
    fig_experiment2(rows, f"{FIG}/fig4_forgetting.png")
    print("  -> figures/fig4_forgetting.png")
    return out


def experiment3(cur):
    """Learner types against tutoring condition."""
    print("\n" + "=" * 74)
    print("EXPERIMENT 3  learner types")
    print("=" * 74)
    conds = [("curriculum_tutor", "binary", "CT + binary"),
             ("curriculum_tutor", "continuous_forget",
              "CT + forgetting model"),
             ("adaptive_review", "continuous_forget", "adaptive review")]
    matrix = {}
    for prof in ("fast", "average", "slow", "forgetful"):
        matrix[prof] = {}
        res = {}
        for sch, mm, label in conds:
            spec = RunSpec(scheduler=sch, mastery_model=mm, profile=prof,
                           label=label)
            res[label] = run_condition(cur, spec, n_learners=N_LEARNERS)
            matrix[prof][label] = res[label].mean("retained_usable")
            record(f"3_{prof}", label, res[label])
        best = max(matrix[prof], key=lambda k: matrix[prof][k])
        d = paired(res["CT + binary"], res[best], "retained_usable")
        print(f"  {prof:10s} " +
              "  ".join(f"{k}: {v:5.1f}" for k, v in matrix[prof].items()) +
              f"   | best={best}, vs CT+binary {d['mean_diff']:+.2f} "
              f"({d['wins']}/{d['n']}, p {d['p_sign']:.3f})")
    fig_experiment3(matrix, f"{FIG}/fig5_learner_types.png")
    print("  -> figures/fig5_learner_types.png")
    return matrix


def experiment4(cur):
    """Sweep the learner's forgetting speed."""
    print("\n" + "=" * 74)
    print("EXPERIMENT 4  forgetting-rate sweep")
    print("=" * 74)
    half_lives = [5, 7, 9, 12, 16, 22]
    conds = [("curriculum_tutor", "binary", "CT + binary"),
             ("curriculum_tutor", "continuous_forget",
              "CT + forgetting model"),
             ("adaptive_review", "continuous_forget", "adaptive review")]
    series = {label: [] for _, _, label in conds}
    saved = PROFILES["average"]
    print(f"  {'half-life':>10s} " +
          "".join(f"{l:>24s}" for _, _, l in conds))
    for hl in half_lives:
        PROFILES["average"] = LearnerProfile("average",
                                             forget_half_life_days=hl)
        line = f"  {hl:>8d}d  "
        for sch, mm, label in conds:
            spec = RunSpec(scheduler=sch, mastery_model=mm, label=label)
            r = run_condition(cur, spec, n_learners=N_LEARNERS)
            v = r.mean("retained_usable")
            series[label].append(v)
            record(f"4_halflife_{hl}", label, r)
            line += f"{v:>24.1f}"
        print(line)
    PROFILES["average"] = saved
    fig_experiment4(half_lives, series, f"{FIG}/fig6_forgetting_sweep.png")
    print("  -> figures/fig6_forgetting_sweep.png")
    return series


# --------------------------------------------------------------------
def selftest():
    cur = build_curriculum()
    cfg = SimConfig()

    assert cur.is_dag() and len(cur.concepts) == 40
    nq = [len(c.questions) for c in cur.concepts.values()]
    assert 5 <= min(nq) and max(nq) <= 10
    print(f"curriculum PASSED: 40 concepts, DAG, {min(nq)}-{max(nq)} "
          f"questions each, {len(cur.all_questions())} total")

    from cursim.learner import Learner
    l1 = Learner(cur, PROFILES["average"], seed=1, cfg=cfg)
    deep = [c for c in cur.concepts.values() if c.prereqs][0]
    r_low = l1.readiness(deep.cid, 0.0)
    for p in deep.prereqs:
        l1.mastery[p] = 0.95
    r_high = l1.readiness(deep.cid, 0.0)
    assert r_high > r_low + 0.3, (r_low, r_high)
    print(f"prerequisites PASSED: readiness for '{deep.cid}' rises "
          f"{r_low:.2f} -> {r_high:.2f} when its prerequisites are strong")

    l2 = Learner(cur, PROFILES["average"], seed=2, cfg=cfg)
    q = cur.concepts["greetings"].questions[0]
    for i in range(12):
        l2.answer(q, i * 0.02)
    m_end = l2.true_mastery("greetings", 0.25)
    m_later = l2.true_mastery("greetings", 0.25 + 30 * 24)
    assert m_end > 0.5 and m_later < m_end
    print(f"learning+forgetting PASSED: {m_end:.3f} after practice, "
          f"{m_later:.3f} after 30 idle days")

    from cursim.mastery import BinaryMastery, ContinuousMastery
    bm = BinaryMastery(cur.ids())
    for _ in range(8):
        bm.observe("greetings", True, 0.0)
    assert bm.is_mastered("greetings", 0.0)
    for _ in range(8):
        bm.observe("greetings", False, 500.0)
    assert bm.is_mastered("greetings", 500.0), "binary must be permanent"
    cm = ContinuousMastery(cur.ids(), forget_per_day=0.10)
    for _ in range(8):
        cm.observe("greetings", True, 0.0)
    hot = cm.belief("greetings", 0.0)
    cold = cm.belief("greetings", 30 * 24.0)
    assert cold < hot
    print(f"mastery models PASSED: binary stays mastered after 8 wrong "
          f"answers; continuous decays {hot:.2f} -> {cold:.2f}")

    a = run_condition(cur, RunSpec(label="x"), n_learners=4)
    b = run_condition(cur, RunSpec(label="x"), n_learners=4)
    d = paired(a, b, "retained_usable")
    assert d["wins"] == 0 and d["losses"] == 0 and d["mean_diff"] == 0
    print("pairing PASSED: a condition against itself differs by exactly "
          "0 for every learner")

    seen = set()
    for sch in ("curriculum_tutor", "continuous", "adaptive_review",
                "random"):
        r = run_condition(cur, RunSpec(scheduler=sch,
                                       mastery_model="continuous",
                                       n_sessions=4,
                                       questions_per_session=10),
                          n_learners=2)
        seen.add(round(r.mean("final_mastery"), 6))
    assert len(seen) == 4, "schedulers should not behave identically"
    print("scheduler swap PASSED: all four schedulers run and differ")
    print("\nALL SELF-TESTS PASSED")


def main():
    os.makedirs(FIG, exist_ok=True)
    os.makedirs(DATA, exist_ok=True)
    cur = build_curriculum()
    cur.to_json(f"{DATA}/curriculum.json")
    fig_curriculum(cur, f"{FIG}/fig1_curriculum.png")
    print(f"curriculum: {len(cur.concepts)} concepts, "
          f"{len(cur.all_questions())} questions -> "
          f"{DATA}/curriculum.json, {FIG}/fig1_curriculum.png")
    print(f"population: {N_LEARNERS} learners per condition, "
          "paired across conditions")

    which = None
    if "--exp" in sys.argv:
        which = int(sys.argv[sys.argv.index("--exp") + 1])
    if which in (None, 1):
        experiment1(cur)
    if which in (None, 2):
        experiment2(cur)
    if which in (None, 3):
        experiment3(cur)
    if which in (None, 4):
        experiment4(cur)

    if ROWS:
        path = f"{DATA}/results.csv"
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(ROWS[0]))
            w.writeheader()
            w.writerows(ROWS)
        print(f"\nwrote {path} ({len(ROWS)} condition rows)")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        main()
