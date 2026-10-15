"""Check 1. Is the tutor's belief correct? Bin every belief and see how often the student truly knows the concept.
"""

import math

import matplotlib.pyplot as plt

from cursim.curriculum import build_curriculum

from ..registry import experiment
from ..style import ACCENT
from ..style import GREY

from .common import population, spec_from


@experiment('check1_calibration',
            "Check 1. Is the tutor's belief correct? Bin every belief and see how often the student truly knows the concept.",
            defaults=dict(n_learners=50, n_steps=120, threshold=0.9),
            curriculum='abstract', theme='dark')
def calibration(n_learners=50, n_steps=120, threshold=0.9, n_bins=10,
                seed0=4242, cur=None, **run_kw):
    if n_learners < 1 or n_steps < 1:
        raise ValueError("calibration needs at least one learner and one "
                         "question.")
    """Every time the tutor updates a belief, record (belief, true state)
    for that concept, then bin by belief. Both are read at the same
    instant: after the tutor's update and after the student's transition,
    i.e. the state going into the next question."""
    cur = cur or build_curriculum()
    spec = spec_from(threshold, n_steps, run_kw)
    runs = population(cur, spec, n_learners, seed0)
    pairs = [(t["belief_after"], float(t["true_after"]))
             for r in runs for t in r["trace"]]
    edges = [i / n_bins for i in range(n_bins + 1)]
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        inb = [(b, y) for b, y in pairs
               if lo <= b < hi or (hi == 1.0 and b == 1.0)]
        n = len(inb)
        frac = sum(y for _, y in inb) / n if n else float("nan")
        mean_b = sum(b for b, _ in inb) / n if n else float("nan")
        se = math.sqrt(frac * (1 - frac) / n) if n and 0 < frac < 1 else 0.0
        rows.append(dict(belief_lo=lo, belief_hi=hi, mean_belief=mean_b,
                         n=n, frac_truly_known=frac, ci95=1.96 * se,
                         gap=(frac - mean_b) if n else float("nan")))

    fig, ax = plt.subplots(figsize=(5.2, 4.4))
    ax.plot([0, 1], [0, 1], "--", color="#5a6377", lw=1,
            label="perfect calibration")
    xs = [r["mean_belief"] for r in rows if r["n"]]
    ys = [r["frac_truly_known"] for r in rows if r["n"]]
    es = [r["ci95"] for r in rows if r["n"]]
    ax.errorbar(xs, ys, yerr=es, fmt="o-", color=ACCENT, capsize=3, lw=1.6,
                label="tutor")
    # bin counts sit on two alternating rows so neighbouring labels
    # never collide when bins are close together
    for i, r in enumerate([x for x in rows if x["n"]]):
        ax.annotate(f"n={r['n']}", (r["mean_belief"], -0.055 - 0.05 * (i % 2)),
                    ha="center", fontsize=7, color=GREY, annotation_clip=False)
    ax.set_xlim(0, 1); ax.set_ylim(-0.02, 1.02)
    ax.set_xlabel("tutor's belief that the concept is known (bin mean)")
    ax.set_ylabel("fraction of those moments where it truly is")
    ax.set_title("Check 1: is the tutor's belief calibrated?")
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()

    worst = max((abs(r["gap"]) for r in rows if r["n"] >= 20),
                default=float("nan"))
    n_all = sum(r["n"] for r in rows)
    mean_b = sum(r["mean_belief"] * r["n"] for r in rows if r["n"]) / n_all
    mean_t = sum(r["frac_truly_known"] * r["n"] for r in rows if r["n"]) / n_all
    summary = (f"{len(pairs)} (belief, truth) pairs from {n_learners} learners x "
               f"{n_steps} questions. Overall: mean belief {mean_b:.4f}, fraction "
               f"truly known {mean_t:.4f}. Largest per-bin gap with n>=20: "
               f"{worst:.3f}. Note: successive pairs on one concept are dependent, "
               f"so per-bin CIs are nominal; the overall comparison is the robust one.")
    return {"tables": {"calibration": rows}, "figures": {"calibration": fig},
            "summary": summary}
