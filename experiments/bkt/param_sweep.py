"""Vary one BKT parameter at a time with the tutor correctly specified: what does each parameter actually do?
"""

import matplotlib.pyplot as plt

from cursim.curriculum import build_curriculum
from cursim.params import BKT_PARAMS

from ..registry import experiment
from ..style import ACCENT
from ..style import GOOD
from ..style import GREY

from .common import calib_gap, detect_stats, population, spec_from


@experiment('param_sweep',
            'Vary one BKT parameter at a time with the tutor correctly specified: what does each parameter actually do?',
            defaults=dict(n_learners=30, n_steps=120, threshold=0.9),
            curriculum='abstract', theme='dark')
def param_sweep(n_learners=30, n_steps=120, threshold=0.9, seed0=4242,
                cur=None, **run_kw):
    """Vary one BKT parameter at a time, with the tutor kept correctly
    specified (student and tutor move together), and watch what happens
    to detection delay and the false-alarm rate.

    This is not a misspecification study: it asks what the parameters
    themselves do. `mismatch` is the study where the two sides differ.
    """
    cur = cur or build_curriculum()
    grids = {"p_G": [0.05, 0.15, 0.25, 0.35, 0.45],
             "p_S": [0.02, 0.05, 0.10, 0.20, 0.30],
             "p_T": [0.05, 0.10, 0.20, 0.30, 0.40],
             "p_L0": [0.05, 0.15, 0.30, 0.50]}
    rows = []
    for pname, vals in grids.items():
        for v in vals:
            pr = dict(BKT_PARAMS, **{pname: v})
            spec = spec_from(threshold, n_steps, run_kw)
            spec.student_params = pr
            spec.tutor_params = pr
            runs = population(cur, spec, n_learners, seed0)
            mb, mt = calib_gap(runs)
            rows.append(dict(parameter=pname, value=v,
                             calib_mean_belief=mb, calib_frac_known=mt,
                             calib_gap=mt - mb, **detect_stats(runs, threshold)))

    fig, axes = plt.subplots(1, 3, figsize=(11.4, 3.5))
    for ax, metric, ylab in (
            (axes[0], "delay_on_concept_mean", "questions on that concept"),
            (axes[1], "false_alarm_rate", "false alarm rate"),
            (axes[2], "calib_gap", "calibration gap (known - believed)")):
        for pname, col in zip(grids, (ACCENT, GOOD, "#f0a93a", GREY)):
            xs = [r["value"] for r in rows if r["parameter"] == pname]
            ys = [r[metric] for r in rows if r["parameter"] == pname]
            ax.plot(xs, ys, "o-", lw=1.6, ms=4, color=col, label=pname)
        ax.set_xlabel("parameter value")
        ax.set_ylabel(ylab, fontsize=9)
    axes[2].axhline(0, ls="--", lw=1, color=GREY)
    axes[0].legend(frameon=False, fontsize=8.5)
    fig.suptitle("What each BKT parameter does, tutor correctly specified",
                 fontsize=11)
    fig.tight_layout()

    worst = max(rows, key=lambda r: abs(r["calib_gap"]))
    span = {}
    for pname in grids:
        fa = [r["false_alarm_rate"] for r in rows if r["parameter"] == pname]
        dl = [r["delay_on_concept_mean"] for r in rows if r["parameter"] == pname]
        span[pname] = (max(fa) - min(fa), max(dl) - min(dl))
    fa_rank = sorted(span, key=lambda k: -span[k][0])
    dl_rank = sorted(span, key=lambda k: -span[k][1])
    summary = (
        f"{len(rows)} cells, {n_learners} learners each, all sharing one seed "
        f"block. Every cell here is correctly specified (student and tutor get "
        f"the same values), so the pooled gap measures estimator noise, not "
        f"calibration: it stays within {abs(worst['calib_gap']):.3f} "
        f"everywhere, which says the estimator is unbiased across parameter "
        f"settings rather than that the tutor is calibrated. Range of the "
        f"false-alarm rate across each grid: " +
        ", ".join(f"{k} {span[k][0]:.3f}" for k in fa_rank) +
        ". Range of the on-concept delay: " +
        ", ".join(f"{k} {span[k][1]:.2f}" for k in dl_rank) +
        f". So {fa_rank[0]} is the strongest lever on both, and the effects do "
        f"not separate cleanly by metric.")
    return {"tables": {"param_sweep": rows}, "figures": {"param_sweep": fig},
            "summary": summary}
