"""Poster experiment: how far is each tutor setting from the best one, at
every break length, for learners who forget at different speeds?

"Best possible" here is the best result any of the settings below reaches at
that break length, picked in hindsight (the envelope). It is a yardstick we
can actually reach, not a theoretical ceiling: a perfect-belief tutor is not
one, because the tutor's cautious decaying belief can beat it at short
breaks (see belief_scheduler_grid and mastery_margin).

Settings: CurriculumTutor as published (binary belief), CurriculumTutor with
the decaying belief at mastery thresholds 0.7 / 0.8 / 0.9, and adaptive
review with the decaying belief. Run on fresh learners (seeds from 9000).
"""

from cursim.curriculum import build_curriculum
from cursim.simulation import RunSpec, run_condition

from ..registry import experiment
from .common import UsableAfter, usable_ci
from .plots import fig_poster_gap

HALF_LIVES = (7, 14, 28)
BREAKS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 18, 21, 25, 28)

# label, scheduler, belief, mastery threshold (None = tutor default)
ARMS = [
    ("CT as published (binary)", "curriculum_tutor", "binary", None),
    ("CT + decay belief, mastered at 0.7", "curriculum_tutor",
     "continuous_forget", 0.7),
    ("CT + decay belief, mastered at 0.8", "curriculum_tutor",
     "continuous_forget", 0.8),
    ("CT + decay belief, mastered at 0.9", "curriculum_tutor",
     "continuous_forget", 0.9),
    ("adaptive review + decay belief", "adaptive_review",
     "continuous_forget", None),
]


def _spec(label, sched, belief, thr, hl, rate, breaks):
    kw = dict(scheduler=sched, mastery_model=belief, label=label,
              profile="average", profile_overrides={"forget_half_life_days": hl},
              break_days=breaks)
    if belief != "binary":
        kw["model_forget_per_day"] = rate
    if thr is not None:
        kw["threshold"] = thr
    return RunSpec(**kw)


@experiment("poster_gap",
            "Gap of each tutor setting to the best setting at every break "
            "length, for fast, average and slow forgetters (fresh learners).",
            defaults=dict(n_learners=50, base_seed=9000, belief_rate=0.05,
                          half_lives=HALF_LIVES, break_days=BREAKS),
            curriculum="layered_40")
def poster_gap(n_learners=50, base_seed=9000, belief_rate=0.05,
               half_lives=HALF_LIVES, break_days=BREAKS, cur=None, **_):
    cur = cur or build_curriculum("layered_40")
    break_days = tuple(break_days)
    labels = [a[0] for a in ARMS]
    curves, gaps, winners, panels = [], [], [], {}
    notes = []
    for hl in half_lives:
        series, cis = {}, {}
        for label, sched, belief, thr in ARMS:
            res = run_condition(
                cur, _spec(label, sched, belief, thr, hl, belief_rate,
                           break_days),
                n_learners=n_learners, base_seed=base_seed)
            pts = [usable_ci(UsableAfter(res, d), "v") for d in break_days]
            series[label] = [p[0] for p in pts]
            cis[label] = [p[1] for p in pts]
        best = [max(series[l][i] for l in labels)
                for i in range(len(break_days))]
        live = [i for i, b in enumerate(best) if b >= 1.0]
        for i, d in enumerate(break_days):
            row = {"half_life_days": hl, "break_days": d,
                   "best_possible": round(best[i], 2)}
            for l in labels:
                row[l] = round(series[l][i], 2)
            curves.append(row)
            if i in live:
                tied = [l for l in labels if series[l][i] >= best[i] - 0.05]
                winners.append(dict(half_life_days=hl, break_days=d,
                                    best_setting=" = ".join(tied),
                                    best_concepts=round(best[i], 2)))
        for l in labels:
            g = [best[i] - series[l][i] for i in live]
            gaps.append(dict(half_life_days=hl, setting=l,
                             worst_gap=round(max(g), 2),
                             mean_gap=round(sum(g) / len(g), 2),
                             breaks_where_best=sum(
                                 1 for i in live
                                 if series[l][i] >= best[i] - 1e-9)))
        panels[hl] = (series, cis, best)
        # a setting counts as "best somewhere" if it is within 0.05 concepts
        # of the best at any break (ties at the 40-concept cap count)
        won = {l for l in labels for i in live
               if series[l][i] >= best[i] - 0.05}
        notes.append(f"half-life {hl}d: {len(won)} of {len(labels)} settings "
                     f"are best at some break")
    return {
        "tables": {"curves": curves, "winners": winners, "gaps": gaps},
        "figures": {"poster_gap": fig_poster_gap(break_days, panels)},
        "summary": (f"{n_learners} fresh learners (seeds from {base_seed}) "
                    f"on {cur.name}, belief decay {belief_rate}/day. "
                    + "; ".join(notes) + "."),
    }
