"""The tutor's assumed parameters differ from the student's real ones: one student with the assumption swept, then a population of students against one fixed tutor.
"""

import random

import matplotlib.pyplot as plt

from cursim.curriculum import build_curriculum
from cursim.params import BKT_PARAMS
from cursim.simulation import run_one

from ..registry import experiment
from ..style import ACCENT
from ..style import GOOD
from ..style import GREY

from .common import PARAM_GRIDS, calib_gap, detect_stats, gap_ci, population, spec_from


@experiment('mismatch',
            "The tutor's assumed parameters differ from the student's real ones: one student with the assumption swept, then a population of students against one fixed tutor.",
            defaults=dict(n_learners=40, n_steps=120, threshold=0.9, vary=('p_G', 'p_S', 'p_T')),
            curriculum='abstract', theme='dark')
def mismatch(n_learners=200, n_steps=120, threshold=0.9, seed0=4242,
             vary="p_G", cur=None, **run_kw):
    """The tutor's assumed parameters differ from the student's real ones.

    (a) one student: the student is fixed at the true values and the
        tutor's assumption for `vary` is swept. The tutor is wrong by a
        known amount, so the calibration gap should grow with the error
        and vanish at the truth. `vary` is one parameter name or a
        sequence of them; each is swept in turn and tagged in the
        `parameter` column.
    (b) many students: every learner draws their own true parameters
        from a spread, while the tutor uses one fixed set. This is the
        realistic case, and the question is whether a single tutor model
        stays usable across a population it does not match.
    """
    cur = cur or build_curriculum()
    truth = dict(BKT_PARAMS)
    rows = []

    # ---- (a) one true student, tutor's assumption swept
    GRIDS = PARAM_GRIDS
    varies = [vary] if isinstance(vary, str) else list(vary)
    bad = [v for v in varies if v not in GRIDS]
    if bad:
        raise ValueError(f"mismatch(vary=...) accepts {sorted(GRIDS)}, "
                         f"got {bad}")
    for name in varies:
        for v in GRIDS[name]:
            spec = spec_from(threshold, n_steps, run_kw)
            spec.student_params = truth
            spec.tutor_params = dict(truth, **{name: v})
            runs = population(cur, spec, n_learners, seed0)
            mb, mt = calib_gap(runs)
            rows.append(dict(arm="one student", parameter=name,
                             tutor_value=v, student_value=truth[name],
                             error=v - truth[name],
                             calib_mean_belief=mb, calib_frac_known=mt,
                             calib_gap=mt - mb, calib_gap_ci95=gap_ci(runs),
                             **detect_stats(runs, threshold)))

    # ---- (b) a population of students, one fixed tutor
    pop_rows = []
    for spread in (0.0, 0.05, 0.10, 0.15):
        runs = []
        for i in range(n_learners):
            r = random.Random(seed0 + 9000 + i)
            sp = dict(truth)
            for k in ("p_G", "p_S", "p_T"):
                sp[k] = min(0.45, max(0.02, truth[k] + r.uniform(-spread, spread)))
            spec = spec_from(threshold, n_steps, run_kw)
            spec.student_params = sp
            spec.tutor_params = truth          # one model for everybody
            runs.append(run_one(cur, spec, seed=seed0 + i, keep_trace=True))
        mb, mt = calib_gap(runs)
        pop_rows.append(dict(arm="population", spread=spread,
                             calib_mean_belief=mb, calib_frac_known=mt,
                             calib_gap=mt - mb, calib_gap_ci95=gap_ci(runs),
                             **detect_stats(runs, threshold)))

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.6))
    a1.axhline(0, ls="--", lw=1, color=GREY)
    # one colour per swept parameter; solid = calibration gap, dashed =
    # false alarms, so a reader compares parameters by colour and metric
    # by line style rather than by reading the legend twice.
    pal = (ACCENT, GOOD, "#e2a03f")
    for i, name in enumerate(varies):
        sub = [r for r in rows if r["parameter"] == name]
        col = pal[i % len(pal)]
        a1.plot([r["error"] for r in sub], [r["calib_gap"] for r in sub],
                "o-", color=col, lw=1.7, label=f"{name}: calibration gap")
        a1.plot([r["error"] for r in sub],
                [r["false_alarm_rate"] for r in sub],
                "s--", color=col, lw=1.4, label=f"{name}: false alarms")
    a1.axvline(0, ls=":", lw=1, color=GREY)
    a1.set_xlabel("tutor's assumed value minus the student's true value")
    a1.set_ylabel("rate")
    a1.set_title("One student, tutor's assumption swept", fontsize=10.5)
    a1.legend(frameon=False, fontsize=7.5,
              ncol=2 if len(varies) > 1 else 1)

    a2.axhline(0, ls="--", lw=1, color=GREY)
    a2.plot([r["spread"] for r in pop_rows],
            [r["calib_gap"] for r in pop_rows], "o-", color=ACCENT, lw=1.7,
            label="calibration gap")
    a2.plot([r["spread"] for r in pop_rows],
            [r["false_alarm_rate"] for r in pop_rows], "s--", color=GOOD,
            lw=1.4, label="false alarm rate")
    a2.set_xlabel("spread of the students' true parameters (uniform +/-)")
    a2.set_ylabel("rate")
    a2.set_title("A population, one fixed tutor model", fontsize=10.5)
    a2.legend(frameon=False, fontsize=8.5)
    fig.tight_layout()

    parts = []
    for name in varies:
        sub = [r for r in rows if r["parameter"] == name]
        at_truth = min(sub, key=lambda r: abs(r["error"]))
        worst = max(sub, key=lambda r: abs(r["calib_gap"]))
        parts.append(
            f"{name}: gap {at_truth['calib_gap']:+.3f} "
            f"+/-{at_truth['calib_gap_ci95']:.3f} when the tutor is right, "
            f"{worst['calib_gap']:+.3f} +/-{worst['calib_gap_ci95']:.3f} at "
            f"its worst ({name}={worst['tutor_value']}, error "
            f"{worst['error']:+.2f})")
    widest = pop_rows[-1]
    summary = (
        f"(a) One student, {n_learners} learners, the tutor's assumption "
        f"swept one parameter at a time. " + "; ".join(parts) + ". "
        f"(b) A population with spread +/-{widest['spread']:.2f} against one "
        f"fixed tutor: gap {widest['calib_gap']:+.3f} "
        f"+/-{widest['calib_gap_ci95']:.3f}, false alarms "
        f"{widest['false_alarm_rate']:.1%} against "
        f"{pop_rows[0]['false_alarm_rate']:.1%} when every student matches the "
        f"tutor exactly. The spread rows share a seed block, so they are a "
        f"paired trend rather than four independent estimates.")
    return {"tables": {"mismatch_one": rows, "mismatch_population": pop_rows},
            "figures": {"mismatch": fig}, "summary": summary}
