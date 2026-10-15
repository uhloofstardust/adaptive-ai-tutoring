"""Students differ in one parameter: which single fixed assumption should the tutor use, and how much would a perfectly adapting tutor buy over it?
"""

import random

import matplotlib.pyplot as plt

from cursim.curriculum import build_curriculum
from cursim.params import BKT_PARAMS
from cursim.simulation import run_one
from cursim.stats import bootstrap_diff_half_width
from cursim.stats import pooled

from ..registry import experiment
from ..style import ACCENT
from ..style import GOOD
from ..style import GREY

from .common import PARAM_GRIDS, calib_gap, detect_stats, gap_ci, gap_contrib, loss_contrib, spec_from


@experiment('tutor_choice',
            'Students differ in one parameter: which single fixed assumption should the tutor use, and how much would a perfectly adapting tutor buy over it?',
            defaults=dict(n_learners=600, n_steps=120, threshold=0.9, vary=('p_S', 'p_G', 'p_T')),
            curriculum='abstract', theme='dark')
def tutor_choice(n_learners=600, n_steps=120, threshold=0.9, seed0=4242,
                 vary=("p_S", "p_G"), spreads=(0.05, 0.10, 0.15),
                 cur=None, **run_kw):
    """Students differ in one parameter. What should the single tutor use?

    The meeting asked this twice: "students have p(S) in a range, should
    the tutor help?", and "if student parameters are in a certain range,
    typically p(S) and p(guess), what should the tutor be?"

    For each spread we run a grid of fixed tutor assumptions, plus an
    ORACLE tutor handed each learner's own true parameters. The oracle
    is not a proposal: no tutor can see a student's parameters. It is an
    upper bound, and the only number that makes "should the tutor adapt"
    answerable, because it says what a perfectly adapting tutor would
    buy over the best single fixed choice. A small gap means adapting is
    not worth building.

    Scored on the Brier score, mean (belief - truth)^2 per pair.

    Three candidate scores were tried and two are wrong here:

      pooled signed gap  cancels. A tutor overconfident about half its
        students and underconfident about the other half scores zero,
        and under a symmetric spread that is exactly the error adapting
        removes, so the study would be blind to its own question.
      mean |belief - truth|  is not a proper scoring rule: it is
        minimised by the median, so while most concepts are still
        unknown it rewards a tutor that simply stays pessimistic. At 40
        questions it picks p_S=0.02 over the true 0.10, at every sample
        size tried.
      Brier  is proper, so it is minimised in expectation by the true
        probability. At this study's horizon of 120 questions it does
        recover the true parameter, at 120, 300 and 600 learners alike,
        with a margin of about 0.002. It is the score.

    Horizon matters and is a real limit: at 40 questions the Brier
    curve is nearly flat (0.1676 at the truth against 0.1677 at
    p_S=0.02) and the minimum moves with the sample, so neither score
    identifies the parameter reliably there. Do not read this study at
    short horizons.

    The other two stay in the table as diagnostics. False alarms alone
    cannot be the score either: a tutor that never declares mastery has
    none.
    """
    if n_learners < 2:
        raise ValueError("tutor_choice needs at least 2 learners to report "
                         "an interval; got %d." % n_learners)
    varies = [vary] if isinstance(vary, str) else list(vary)
    bad = [v for v in varies if v not in PARAM_GRIDS]
    if bad:
        raise ValueError(f"tutor_choice(vary=...) accepts "
                         f"{sorted(PARAM_GRIDS)}, got {bad}")
    cur = cur or build_curriculum()
    truth = dict(BKT_PARAMS)
    rows = []
    contrib = {}          # (parameter, spread, arm, value) -> per-learner parts
    contrib_mae, contrib_brier = {}, {}

    def population(name, spread, tutor_of):
        """One cell. tutor_of(true_params) picks that learner's tutor."""
        runs = []
        for i in range(n_learners):
            r = random.Random(seed0 + 9000 + i)     # same students in every
            sp = dict(truth)                        # arm, so arms are paired
            sp[name] = min(0.45, max(0.02,
                                     truth[name] + r.uniform(-spread, spread)))
            spec = spec_from(threshold, n_steps, run_kw)
            spec.student_params = sp
            spec.tutor_params = tutor_of(sp)
            runs.append(run_one(cur, spec, seed=seed0 + i, keep_trace=True))
        return runs

    for name in varies:
        for spread in spreads:
            arms = [("fixed", v, (lambda v: lambda sp: dict(truth, **{name: v}))(v))
                    for v in PARAM_GRIDS[name]]
            arms.append(("oracle", float("nan"), lambda sp: dict(sp)))
            for arm, value, tutor_of in arms:
                runs = population(name, spread, tutor_of)
                mb, mt = calib_gap(runs)
                key = (name, spread, arm, value)
                contrib[key] = gap_contrib(runs)
                contrib_mae[key] = loss_contrib(runs, "abs")
                contrib_brier[key] = loss_contrib(runs, "sq")
                rows.append(dict(
                    parameter=name, spread=spread, tutor_arm=arm,
                    tutor_value=value, n_learners=n_learners,
                    mae=pooled(contrib_mae[key]),
                    brier=pooled(contrib_brier[key]),
                    calib_mean_belief=mb, calib_frac_known=mt,
                    calib_gap=mt - mb, abs_calib_gap=abs(mt - mb),
                    calib_gap_ci95=gap_ci(runs),
                    **detect_stats(runs, threshold)))

    # -------------------------------------------------- best fixed vs oracle
    verdict = []
    for name in varies:
        for spread in spreads:
            cell = [r for r in rows
                    if r["parameter"] == name and r["spread"] == spread]
            fixed = [r for r in cell if r["tutor_arm"] == "fixed"]
            oracle = next(r for r in cell if r["tutor_arm"] == "oracle")
            # Select on Brier: it is proper, so it is minimised by the
            # true probability. See the docstring for why the signed
            # gap and MAE both fail here.
            best = min(fixed, key=lambda r: r["brier"])
            atruth = min(fixed, key=lambda r: abs(r["tutor_value"]
                                                  - truth[name]))
            kb = (name, spread, "fixed", best["tutor_value"])
            ko = (name, spread, "oracle", oracle["tutor_value"])
            verdict.append(dict(
                parameter=name, spread=spread,
                best_fixed_value=best["tutor_value"],
                best_fixed_mae=best["mae"], oracle_mae=oracle["mae"],
                oracle_buys_mae=best["mae"] - oracle["mae"],
                mae_ci95=bootstrap_diff_half_width(contrib_mae[kb], contrib_mae[ko]),
                best_fixed_brier=best["brier"],
                oracle_brier=oracle["brier"],
                oracle_buys_brier=best["brier"] - oracle["brier"],
                brier_ci95=bootstrap_diff_half_width(contrib_brier[kb],
                                          contrib_brier[ko]),
                at_truth_value=atruth["tutor_value"],
                at_truth_mae=atruth["mae"],
                best_fixed_abs_gap=best["abs_calib_gap"],
                at_truth_abs_gap=atruth["abs_calib_gap"],
                oracle_abs_gap=oracle["abs_calib_gap"],
                oracle_buys=best["abs_calib_gap"] - oracle["abs_calib_gap"],
                ci95=bootstrap_diff_half_width(contrib[kb], contrib[ko]),
                ci95_marginal=max(best["calib_gap_ci95"],
                                  oracle["calib_gap_ci95"]),
                best_fixed_false_alarm=best["false_alarm_rate"],
                oracle_false_alarm=oracle["false_alarm_rate"],
                best_fixed_delay=best["delay_on_concept_mean"],
                oracle_delay=oracle["delay_on_concept_mean"]))

    # ------------------------------------------------------------ figure
    fig, axes = plt.subplots(1, len(varies), figsize=(4.9 * len(varies), 3.7),
                             squeeze=False)
    pal = (ACCENT, GOOD, "#e2a03f", "#d96f6f")
    for ax, name in zip(axes[0], varies):
        for j, spread in enumerate(spreads):
            cell = [r for r in rows if r["parameter"] == name
                    and r["spread"] == spread]
            fixed = sorted((r for r in cell if r["tutor_arm"] == "fixed"),
                           key=lambda r: r["tutor_value"])
            oracle = next(r for r in cell if r["tutor_arm"] == "oracle")
            col = pal[j % len(pal)]
            ax.plot([r["tutor_value"] for r in fixed],
                    [r["brier"] for r in fixed], "o-", color=col,
                    lw=1.7, label=f"fixed tutor, spread +/-{spread:.2f}")
            ax.axhline(oracle["brier"], ls="--", lw=1.2, color=col,
                       alpha=0.75)
        ax.axvline(truth[name], ls=":", lw=1, color=GREY)
        ax.set_xlabel(f"tutor's assumed {name}")
        ax.set_ylabel("Brier score per pair")
        ax.set_title(f"Students vary in {name}\n(dashed = oracle tutor)",
                     fontsize=10)
        ax.legend(frameon=False, fontsize=7.5)
    fig.tight_layout()

    # ----------------------------------------------------------- summary
    bits = []
    for name in varies:
        wide = max(spreads)
        v = next(x for x in verdict
                 if x["parameter"] == name and x["spread"] == wide)
        buys, ci = v["oracle_buys_brier"], v["brier_ci95"]
        if buys > ci:
            word = f"buys {buys:.4f} +/-{ci:.4f} of per-pair error"
        elif buys < -ci:
            word = (f"COSTS {abs(buys):.4f} +/-{ci:.4f} of per-pair error")
        else:
            word = (f"changes per-pair error by {buys:+.4f}, inside the "
                    f"+/-{ci:.4f} this run can resolve")
        bits.append(
            f"{name} at spread +/-{wide:.2f}: best fixed tutor "
            f"({name}={v['best_fixed_value']:.2f}) scores Brier "
            f"{v['best_fixed_brier']:.4f}, the oracle "
            f"{v['oracle_brier']:.4f}, so knowing every student's own "
            f"{name} {word}")
    summary = (
        f"{n_learners} learners per cell, {n_steps} questions, the same "
        f"students in every arm so the arms are paired. " + "; ".join(bits)
        + ". Scored on the Brier score, which is proper and so is "
        "minimised by the true probability. The pooled signed gap "
        "cancels per-student over- and underconfidence, exactly the "
        "error adapting removes, and mean |belief - truth| is improper "
        "and rewards a pessimistic tutor early in a run; both are kept "
        "as diagnostics only. The "
        "oracle is an upper bound, not a proposal: no tutor can see a "
        "student's parameters. An interval covering zero here means this "
        "run could not resolve a difference of that size, which is not "
        "the same as showing there is none; no equivalence margin was "
        "set in advance.")
    return {"tables": {"tutor_choice": rows, "verdict": verdict},
            "figures": {"tutor_choice": fig}, "summary": summary}
