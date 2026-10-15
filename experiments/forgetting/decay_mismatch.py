"""Experiment 9: what if the tutor's idea of how fast the learner forgets
is wrong?

The forgetting-aware tutor decays its belief at a fixed daily rate. In
the earlier experiments that rate was chosen by hand and sits near the
simulator's own, which a sceptical reader would say flatters the tutor.
Here the rate is swept across a wide range, for learners of different
true memory, and compared with the tutor that ignores forgetting. The
question is whether the benefit survives a wrong rate, and how wrong.
"""

from cursim.curriculum import build_curriculum
from cursim.simulation import RunSpec, run_condition

from ..registry import experiment
from .common import PRIMARY, paired_row, usable_ci
from .plots import fig_mismatch

RATES = (0.0, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20, 0.30)
HALF_LIVES = (7, 14, 28)
SCHEDS = ("curriculum_tutor", "adaptive_review")


def matched_rate(half_life_days):
    """Daily decay rate that gives the stated half-life."""
    return 1.0 - 0.5 ** (1.0 / half_life_days)


@experiment("decay_mismatch",
            "Give the tutor a wrong forgetting rate and see whether the "
            "benefit of modelling forgetting survives.",
            defaults=dict(n_learners=30, half_lives=HALF_LIVES,
                          rates=RATES),
            curriculum="layered_40")
def decay_mismatch(n_learners=30, half_lives=HALF_LIVES, rates=RATES,
                   cur=None, **_):
    cur = cur or build_curriculum("layered_40")
    rows, panels, baselines = [], {}, {}
    for hl in half_lives:
        over = {"forget_half_life_days": hl}
        base = run_condition(cur, RunSpec(
            scheduler="curriculum_tutor", mastery_model="binary",
            label="CT + binary", profile_overrides=over),
            n_learners=n_learners)
        baselines[hl] = base.mean(PRIMARY)
        panels[hl] = {s: [] for s in SCHEDS}
        for s in SCHEDS:
            for rate in rates:
                r = run_condition(cur, RunSpec(
                    scheduler=s, mastery_model="continuous_forget",
                    model_forget_per_day=rate, profile_overrides=over,
                    label=f"{s} @ {rate}"), n_learners=n_learners)
                m, e = usable_ci(r)
                panels[hl][s].append((rate, m, e))
                rows.append({**paired_row("CT + binary", f"{s} @ {rate}",
                                          PRIMARY, base, r),
                             "true_half_life_days": hl, "scheduler": s,
                             "assumed_rate": rate,
                             "true_rate": round(matched_rate(hl), 4),
                             "usable": round(m, 2), "ci95": round(e, 2)})
    # lowest and highest assumed rate that still beats the baseline
    # significantly, per true half-life and scheduler
    reach = []
    for hl in half_lives:
        for s in SCHEDS:
            ok = [r["assumed_rate"] for r in rows
                  if r["true_half_life_days"] == hl and r["scheduler"] == s
                  and r["mean_diff"] > 0 and r["p_sign"] < 0.05]
            reach.append(dict(true_half_life_days=hl, scheduler=s,
                              true_rate=round(matched_rate(hl), 4),
                              lowest_ok=min(ok) if ok else None,
                              highest_ok=max(ok) if ok else None,
                              n_rates_ok=len(ok), n_rates=len(rates)))
    summary = "; ".join(
        f"hl {r['true_half_life_days']}d {r['scheduler']}: beats the "
        f"baseline at {r['n_rates_ok']}/{r['n_rates']} assumed rates"
        for r in reach)
    return {"tables": {"sweep": rows, "reach": reach},
            "figures": {"mismatch": fig_mismatch(
                panels, baselines,
                {hl: matched_rate(hl) for hl in half_lives})},
            "summary": f"{n_learners} learners per cell on {cur.name}. "
                       f"{summary}."}
