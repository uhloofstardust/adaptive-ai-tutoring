"""Experiment 4: how forgetful must a learner be before modelling it
matters?

Memory half-life is swept as a continuous dial with everything else held
fixed, for the three tutors. The crossover points, where the best tutor
changes, are the result. The default grid brackets two crossovers
(roughly 8 and 18 days on layered_40) that a coarser grid only located
somewhere between neighbouring points.
"""

from cursim.curriculum import build_curriculum

from ..registry import experiment
from .common import THREE_TUTORS, condition_row, run_conditions
from .plots import fig_halflife_sweep

HALF_LIVES = (5, 7, 8, 9, 10, 12, 16, 18, 19, 20, 22)


@experiment("halflife_sweep",
            "Sweep the learner's memory half-life and find where the best "
            "tutor changes.",
            defaults=dict(n_learners=30, half_lives=HALF_LIVES),
            curriculum="layered_40")
def halflife_sweep(n_learners=30, half_lives=HALF_LIVES, cur=None, **_):
    cur = cur or build_curriculum("layered_40")
    labels = [c[2] for c in THREE_TUTORS]
    series = {label: [] for label in labels}
    rows, leaders = [], []
    for hl in half_lives:
        res = run_conditions(
            cur, THREE_TUTORS, n_learners,
            profile_overrides={"forget_half_life_days": hl})
        for label, r in res.items():
            series[label].append(r.mean("retained_usable"))
            rows.append(condition_row(f"4_halflife_{hl}", label, r))
        leaders.append(max(labels, key=lambda k: series[k][-1]))
    changes = [f"{leaders[i - 1]} -> {leaders[i]} between {half_lives[i - 1]}d "
               f"and {half_lives[i]}d" for i in range(1, len(leaders))
               if leaders[i] != leaders[i - 1]]
    table = [dict(half_life_days=hl, best=ld,
                  **{k: round(series[k][i], 2) for k in labels})
             for i, (hl, ld) in enumerate(zip(half_lives, leaders))]
    return {"tables": {"conditions": rows, "best_by_half_life": table},
            "figures": {"halflife_sweep": fig_halflife_sweep(
                list(half_lives), series)},
            "summary": f"{n_learners} learners per cell on {cur.name}. "
                       f"Best tutor changes: "
                       f"{'; '.join(changes) or 'it never changes'}."}
