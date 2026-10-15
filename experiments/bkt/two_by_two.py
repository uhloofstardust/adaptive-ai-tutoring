"""The 2x2. Two student models (prerequisites irrelevant / prerequisite-gated) by two question-selection rules (anything unmastered / prerequisite-ready only).
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


@experiment('s1s2_x_q1q2',
            'The 2x2. Two student models (prerequisites irrelevant / prerequisite-gated) by two question-selection rules (anything unmastered / prerequisite-ready only).',
            defaults=dict(n_learners=60, n_steps=40, threshold=0.9),
            curriculum='abstract', theme='dark')
def two_by_two(n_learners=400, n_steps=40, threshold=0.9, seed0=4242,
               cur=None, **_):
    """Two student models by two question-selection rules.

    The prediction under test, written down before running:

        S1 (prerequisites irrelevant)   Q1 good, Q2 good
        S2 (prerequisites gate p(T))    Q1 bad,  Q2 good

    i.e. the scheduler is invisible against S1 and decisive against S2.
    If the scheduler mattered against S1 too, or did not matter against
    S2, the setup could not tell schedulers apart and the result would
    be a bug rather than a finding.

    Scored on concepts the student TRULY knows at the end, which is the
    student's own state and owes nothing to what the tutor believes.
    """
    if n_learners < 2:
        raise ValueError("two_by_two needs at least 2 learners to report an "
                         "interval; got %d." % n_learners)
    if n_steps < 1:
        raise ValueError("two_by_two needs at least 1 question; got %d."
                         % n_steps)
    cur = cur or build_curriculum()
    n_c = len(cur.concepts)
    rows, cells = [], {}
    for sname, sm in STUDENT_MODELS.items():
        for qname, sched in (("Q1", "uniform_unmastered"),
                             ("Q2", "uniform_zpd")):
            spec = spec_2x2(sname, sched, n_steps, threshold, sm)
            runs = population(cur, spec, n_learners, seed0)
            known = [sum(1 for v in r["truth"].values() if v >= 0.999)
                     for r in (x["trace"][-1] for x in runs)]
            wasted = [sum(1 for t in x["trace"]
                          if t["zpd"] and t["concept"] not in t["zpd"])
                      for x in runs]
            cells[(sname, qname)] = known
            rows.append(dict(
                student=sname, scheduler=qname, sched_key=sched,
                n_learners=n_learners, n_steps=n_steps, n_concepts=n_c,
                learned_mean=st.mean(known),
                learned_sd=st.stdev(known) if len(known) > 1 else 0.0,
                learned_frac=st.mean(known) / n_c,
                asked_outside_zpd=st.mean(wasted)))

    # within each student, Q2 minus Q1, learner by learner (paired seeds)
    paired_rows, diffs = [], {}
    for sname in STUDENT_MODELS:
        d = [b - a for a, b in zip(cells[(sname, "Q1")], cells[(sname, "Q2")])]
        diffs[sname] = d
        m = st.mean(d)
        se = (st.stdev(d) / math.sqrt(len(d))) if len(d) > 1 else 0.0
        wins = sum(1 for x in d if x > 0)
        paired_rows.append(dict(
            student=sname, diff_Q2_minus_Q1=m, ci95=1.96 * se,
            better_with_Q2=wins, n=len(d),
            favours="Q2" if m > 1.96 * se else ("Q1" if -m > 1.96 * se
                                                else "neither"),
            scheduler_matters=bool(abs(m) > 1.96 * se)))

    # the interaction: does the sign of (Q2 - Q1) depend on which student
    # it is? This, not either column on its own, is the claim.
    #
    # Seed i is the same person in all four cells, so the two per-student
    # differences are paired, not independent: treating them as independent
    # (sqrt(var/n + var/n)) ignores a positive correlation and gives an SE
    # that is too wide. The per-seed difference of differences is the right
    # statistic.
    a, b = diffs["S1"], diffs["S2"]
    per_seed = [y - x for x, y in zip(a, b)]
    inter = st.mean(per_seed)
    inter_se = (st.stdev(per_seed) / math.sqrt(len(per_seed))
                if len(per_seed) > 1 else 0.0)
    # Emit the correlation and the interval the unpaired formula WOULD
    # have given, so the claim that pairing matters here is checkable
    # from the CSV instead of being asserted in prose.
    if len(a) > 1:
        ma, mb = st.mean(a), st.mean(b)
        cov = sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (len(a) - 1)
        sa, sb = st.stdev(a), st.stdev(b)
        corr = cov / (sa * sb) if sa and sb else float("nan")
        unpaired_se = math.sqrt(sa ** 2 / len(a) + sb ** 2 / len(b))
    else:
        corr, unpaired_se = float("nan"), 0.0
    paired_rows.append(dict(
        student="interaction (S2 minus S1)", diff_Q2_minus_Q1=inter,
        ci95=1.96 * inter_se, better_with_Q2=-1, n=len(a),
        favours="-", scheduler_matters=bool(abs(inter) > 1.96 * inter_se),
        corr_S1_S2=corr, ci95_if_unpaired=1.96 * unpaired_se))

    fig, ax = plt.subplots(figsize=(5.6, 3.9))
    xs = [0, 1]
    w = 0.34
    for i, (q, col) in enumerate((("Q1", GREY), ("Q2", ACCENT))):
        m = [st.mean(cells[(s, q)]) for s in STUDENT_MODELS]
        e = [1.96 * st.stdev(cells[(s, q)]) / math.sqrt(n_learners)
             for s in STUDENT_MODELS]
        ax.bar([x + (i - .5) * w for x in xs], m, w, yerr=e, capsize=4,
               color=col, label=f"{q}: " + ("anything not mastered" if q == "Q1"
                                            else "only prerequisite-ready"))
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{s}\n{STUDENT_MODELS[s]['label'].split(':')[1].strip()}"
                        for s in STUDENT_MODELS], fontsize=8.5)
    ax.set_ylabel(f"concepts truly known at the end (of {n_c})")
    ax.set_title("Does the question-selection rule matter?")
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    ax.set_ylim(0, n_c * 1.12)
    fig.tight_layout()

    s1, s2, ix = paired_rows[0], paired_rows[1], paired_rows[2]
    # read the verdict off the two marginals, so it can never assert a
    # sign flip the table denies, nor deny an interaction the table reports
    if not ix["scheduler_matters"]:
        verdict = "no interaction detected at this budget"
    elif {s1["favours"], s2["favours"]} == {"Q1", "Q2"}:
        verdict = "the sign of the scheduler effect flips with the student model"
    else:
        verdict = ("the size, not the sign, of the scheduler effect depends on "
                   f"the student (S1 favours {s1['favours']}, "
                   f"S2 favours {s2['favours']})")
    summary = (
        f"{n_learners} learners x {n_steps} questions on {cur.name}, "
        f"{n_c} concepts. S1: Q2 minus Q1 = {s1['diff_Q2_minus_Q1']:+.2f} "
        f"[{s1['diff_Q2_minus_Q1']-s1['ci95']:+.2f}, "
        f"{s1['diff_Q2_minus_Q1']+s1['ci95']:+.2f}] "
        f"(favours {s1['favours']}). "
        f"S2: {s2['diff_Q2_minus_Q1']:+.2f} "
        f"[{s2['diff_Q2_minus_Q1']-s2['ci95']:+.2f}, "
        f"{s2['diff_Q2_minus_Q1']+s2['ci95']:+.2f}] "
        f"(favours {s2['favours']}). Interaction {ix['diff_Q2_minus_Q1']:+.2f} "
        f"[{ix['diff_Q2_minus_Q1']-ix['ci95']:+.2f}, "
        f"{ix['diff_Q2_minus_Q1']+ix['ci95']:+.2f}]: {verdict}. "
        f"Note the budget matters: at a budget long enough for everything to "
        f"be learned anyway, every cell saturates and no scheduler can differ.")
    return {"tables": {"two_by_two": rows, "paired": paired_rows},
            "figures": {"two_by_two": fig}, "summary": summary}
