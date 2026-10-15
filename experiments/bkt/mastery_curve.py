"""Concepts truly known against questions asked, for all four 2x2 cells, plus how many questions are enough to know every concept.
"""

import math
import statistics as st

import matplotlib.pyplot as plt

from cursim.curriculum import build_curriculum
from cursim.params import STUDENT_MODELS

from ..registry import experiment
from ..style import ACCENT
from ..style import GREY

from .common import population, spec_2x2


@experiment('mastery_curve',
            'Concepts truly known against questions asked, for all four 2x2 cells, plus how many questions are enough to know every concept.',
            defaults=dict(n_learners=200, n_steps=300, threshold=0.9),
            curriculum='abstract', theme='dark')
def mastery_curve(n_learners=400, n_steps=300, threshold=0.9, seed0=4242,
                  cur=None, **_):
    """Concepts the student TRULY knows, against questions asked.

    The 2x2's four cells plotted over time instead of collapsed to a
    single end-of-run number. Two questions are answered at once:

      (1) how the arms separate as the budget grows, which is the
          better/worse pair the whiteboard sketches;
      (2) how many questions are enough for a learner to know every
          concept, reported as a median over learners with the
          non-finishers counted rather than dropped.

    Read off `learned_step`, which records the step each concept
    became known (0 if known before the first question, None if never).
    That is the student's own hidden state, so the curve owes nothing
    to what the tutor believes.
    """
    if n_learners < 2:
        raise ValueError("mastery_curve needs at least 2 learners to report "
                         "an interval; got %d." % n_learners)
    if n_steps < 1:
        raise ValueError("mastery_curve needs at least 1 question; got %d."
                         % n_steps)
    cur = cur or build_curriculum()
    n_c = len(cur.concepts)
    rows, done_rows, curves, finishes = [], [], {}, {}

    for sname, sm in STUDENT_MODELS.items():
        for qname, sched in (("Q1", "uniform_unmastered"),
                             ("Q2", "uniform_zpd")):
            spec = spec_2x2(sname, sched, n_steps, threshold, sm)
            runs = population(cur, spec, n_learners, seed0)

            # per learner: concepts known at each step, and the step at
            # which the last one landed (None if they never finished)
            per_learner, finish = [], []
            for r in runs:
                ls = r["learned_step"]
                steps = [v for v in ls.values() if v is not None]
                counts = [sum(1 for v in steps if v <= t)
                          for t in range(n_steps + 1)]
                per_learner.append(counts)
                finish.append(max(steps) if len(steps) == n_c else None)

            mean_curve, ci_curve, allknown = [], [], []
            for t in range(n_steps + 1):
                col = [c[t] for c in per_learner]
                m = st.mean(col)
                sd = st.stdev(col) if len(col) > 1 else 0.0
                mean_curve.append(m)
                ci_curve.append(1.96 * sd / math.sqrt(len(col)))
                allknown.append(sum(1 for v in col if v >= n_c) / len(col))
                rows.append(dict(student=sname, scheduler=qname,
                                 sched_key=sched, step=t,
                                 mean_known=m, ci95=ci_curve[-1],
                                 frac_all_known=allknown[-1],
                                 n_concepts=n_c, n_learners=n_learners))
            curves[(sname, qname)] = (mean_curve, ci_curve, allknown)
            finishes[(sname, qname)] = finish

            reached = [f for f in finish if f is not None]
            done_rows.append(dict(
                student=sname, scheduler=qname, n_learners=n_learners,
                n_steps=n_steps, n_concepts=n_c,
                frac_reached_all=len(reached) / len(finish),
                median_questions_to_all=(st.median(reached) if reached
                                         else float("nan")),
                mean_questions_to_all=(st.mean(reached) if reached
                                       else float("nan")),
                n_censored=len(finish) - len(reached),
                final_mean_known=mean_curve[-1]))

    # ------------------------------------------------------------ figure
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.8, 3.7))
    style = {("S1", "Q1"): (ACCENT, "--"), ("S1", "Q2"): (ACCENT, "-"),
             ("S2", "Q1"): ("#e2a03f", "--"), ("S2", "Q2"): ("#e2a03f", "-")}
    xs = list(range(n_steps + 1))
    for key, (mean_curve, ci_curve, allknown) in curves.items():
        col, ls = style.get(key, (GREY, "-"))
        lab = f"{key[0]} / {key[1]}"
        a1.plot(xs, mean_curve, ls, color=col, lw=1.8, label=lab)
        a1.fill_between(xs, [m - c for m, c in zip(mean_curve, ci_curve)],
                        [m + c for m, c in zip(mean_curve, ci_curve)],
                        color=col, alpha=0.13, lw=0)
        a2.plot(xs, allknown, ls, color=col, lw=1.8, label=lab)
    a1.axhline(n_c, ls=":", lw=1, color=GREY)
    a1.set_xlabel("questions asked")
    a1.set_ylabel("concepts truly known")
    a1.set_title(f"Mastery over time (of {n_c}, shaded = 95% CI)",
                 fontsize=10.5)
    a1.legend(frameon=False, fontsize=8.5, loc="lower right")
    a2.set_ylim(-0.03, 1.03)
    a2.set_xlabel("questions asked")
    a2.set_ylabel("fraction of learners knowing every concept")
    a2.set_title("How many learners have finished", fontsize=10.5)
    a2.legend(frameon=False, fontsize=8.5, loc="upper left")
    fig.tight_layout()

    # ------------------------------ paired contrast: Q2 minus Q1, by learner
    paired = []
    for sname in STUDENT_MODELS:
        a, b = finishes[(sname, "Q1")], finishes[(sname, "Q2")]
        # seed i is the SAME learner in both arms, so pair before differencing
        d = [y - x for x, y in zip(a, b) if x is not None and y is not None]
        if len(d) > 1:
            m = st.mean(d)
            ci = 1.96 * st.stdev(d) / math.sqrt(len(d))
        else:
            m, ci = float("nan"), float("nan")
        med = st.median(d) if d else float("nan")
        resolved = (m + ci < 0) or (m - ci > 0)
        paired.append(dict(
            student=sname, diff_Q2_minus_Q1=m, ci95=ci,
            median_diff_Q2_minus_Q1=med,
            n_paired=len(d), n_dropped=len(a) - len(d),
            faster_with_Q2=sum(1 for v in d if v < 0),
            sign_resolved=resolved,
            # "unresolved" means this run cannot tell the sign, NOT that
            # the effect is zero. Reporting it as "neither" once let a
            # sign-unstable estimate be written up as "costs S1 nothing";
            # across six independent blocks of 400 the S1 effect is in
            # fact a small COST, about +1 question, which two_by_two and
            # restriction_only already implied.
            favours=("Q2" if m + ci < 0 else "Q1" if m - ci > 0
                     else "unresolved at this n")))

    # ----------------------------------------------------------- summary
    def cell(sname, qname):
        return next(r for r in done_rows
                    if r["student"] == sname and r["scheduler"] == qname)

    bits = []
    for sname in STUDENT_MODELS:
        q1, q2 = cell(sname, "Q1"), cell(sname, "Q2")
        pr = next(x for x in paired if x["student"] == sname)
        if q1["n_censored"] or q2["n_censored"]:
            bits.append(
                f"{sname}: {q1['final_mean_known']:.2f} known under Q1 vs "
                f"{q2['final_mean_known']:.2f} under Q2 after {n_steps} "
                f"questions ({q1['frac_reached_all']:.0%} vs "
                f"{q2['frac_reached_all']:.0%} of learners reached all {n_c})")
        else:
            bits.append(
                f"{sname} reaches all {n_c} after a median "
                f"{q1['median_questions_to_all']:.0f} questions under Q1 "
                f"and {q2['median_questions_to_all']:.0f} under Q2; paired "
                f"MEAN difference {pr['diff_Q2_minus_Q1']:+.1f} "
                f"+/-{pr['ci95']:.1f}, paired MEDIAN difference "
                f"{pr['median_diff_Q2_minus_Q1']:+.1f} "
                f"({pr['favours']})")
    # A median over finishers only is biased whenever many learners did
    # not finish, so quote it only when nearly everyone did, and say so
    # plainly otherwise rather than reporting a number built on a tail.
    worst_cens = max(r["n_censored"] for r in done_rows) / n_learners
    if worst_cens <= 0.05:
        fastest = min(done_rows, key=lambda r: r["median_questions_to_all"])
        slowest = max(done_rows, key=lambda r: r["median_questions_to_all"])
        tail = (f" Every arm gets every learner to all {n_c} concepts inside "
                f"{n_steps} questions, at a median of "
                f"{fastest['median_questions_to_all']:.0f} "
                f"({fastest['student']}/{fastest['scheduler']}) to "
                f"{slowest['median_questions_to_all']:.0f} "
                f"({slowest['student']}/{slowest['scheduler']}).")
    else:
        tail = (f" No median to full mastery is quoted: up to "
                f"{worst_cens:.0%} of learners in some arm never reach all "
                f"{n_c} concepts inside {n_steps} questions, so a median "
                f"over the finishers would describe the fast tail only.")
    caveats = (
        " Every arm asks the same fixed number of questions, so a "
        "difference here is time to latent mastery, not effort saved. "
        "The mean and median paired differences are both given because "
        "they are not interchangeable, and an interval covering zero "
        "means this run cannot resolve the sign, not that the effect is "
        "zero: the S1 contrast is a small cost to Q2 that needs far more "
        "learners than this to separate, and two_by_two and "
        "restriction_only are the places it shows up.")
    summary = (f"{n_learners} learners per cell, {n_steps} questions, "
               f"paired by shared seed and shared initial known-set. "
               + "; ".join(bits) + "." + tail + caveats)

    return {"tables": {"mastery_curve": rows, "questions_to_all": done_rows,
                       "paired": paired},
            "figures": {"mastery_curve": fig}, "summary": summary}
