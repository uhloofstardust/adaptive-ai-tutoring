"""Experiment 8: how the ranking of tutors depends on the length of the
break, with a perfect-belief reference.

Earlier experiments fixed the break at 3 days and varied the learner's
memory. Here the learner is fixed and the break varies; every length is
read from the same training run, so the curves differ only by idle time.
The dashed lines give a scheduler a perfect belief (the learner's true
mastery). They are references for what better estimation alone could buy
with these schedulers, not the best possible policy.
"""

from cursim.curriculum import build_curriculum
from cursim.simulation import RunSpec, run_condition

from ..registry import experiment
from .common import THREE_TUTORS, paired_row, usable_ci
from .plots import fig_break_sweep

ORACLES = [("curriculum_tutor", "oracle", "oracle belief + CT"),
           ("adaptive_review", "oracle", "oracle belief + adaptive review")]
BREAKS = (0, 1, 2, 3, 5, 7, 8, 9, 10, 11, 12, 14, 21)


class _Arm:
    """Adapter so per-break values look like a RunResult to `paired`."""
    def __init__(self, res, d):
        self.per_learner = [{"v": r["usable_after"][d]}
                            for r in res.per_learner]


@experiment("break_sweep",
            "Concepts still usable against the length of the break, for "
            "three tutors and a perfect-belief reference.",
            defaults=dict(n_learners=30, break_days=BREAKS,
                          profile="average", half_life_days=None),
            curriculum="layered_40")
def break_sweep(n_learners=30, break_days=BREAKS, profile="average",
                half_life_days=None, cur=None, **_):
    cur = cur or build_curriculum("layered_40")
    break_days = tuple(break_days)
    over = ({"forget_half_life_days": half_life_days}
            if half_life_days else None)
    who = (f"learners with a {half_life_days}-day memory half-life"
           if half_life_days else f"{profile} learners")
    arms = [*THREE_TUTORS, *ORACLES]
    res = {label: run_condition(
        cur, RunSpec(scheduler=s, mastery_model=m, label=label,
                     profile=profile, profile_overrides=over,
                     break_days=break_days),
        n_learners=n_learners) for s, m, label in arms}
    base = THREE_TUTORS[0][2]
    labels = [a[2] for a in arms]

    series = {l: [] for l in labels}
    cis = {l: [] for l in labels}
    curve_rows, paired_rows = [], []
    for d in break_days:
        row = {"break_days": d}
        for l in labels:
            vals = _Arm(res[l], d)
            m, e = usable_ci(vals, "v")
            series[l].append(m)
            cis[l].append(e)
            row[l] = round(m, 2)
            if l != base:
                paired_rows.append(paired_row(
                    base, l, "v", _Arm(res[base], d), vals,
                    break_days=d))
        curve_rows.append(row)

    real = [l for l in labels if "oracle" not in l]
    # a break so long that nothing is left has no meaningful leader
    leaders = [max(real, key=lambda l: series[l][i])
               if max(series[l][i] for l in real) >= 1.0 else "none left"
               for i in range(len(break_days))]
    live = [(d, l) for d, l in zip(break_days, leaders) if l != "none left"]
    changes = [f"{a[1]} -> {b[1]} between {a[0]}d and {b[0]}d"
               for a, b in zip(live, live[1:]) if a[1] != b[1]]
    ceiling = [max(series[o[2]][i] for o in ORACLES)
               for i in range(len(break_days))]
    gap = [round(c - max(series[l][i] for l in real), 2)
           for i, c in enumerate(ceiling)]
    return {
        "tables": {"curves": curve_rows, "paired_vs_ct_binary": paired_rows,
                   "leader": [dict(break_days=d, best_real_tutor=l,
                                   best_oracle_minus_best=g)
                              for d, l, g in zip(break_days, leaders, gap)]},
        "figures": {"break_sweep": fig_break_sweep(
            list(break_days), series, cis,
            f"{who}: what is left after the break")},
        "summary": f"{n_learners} {who} on {cur.name}. Best "
                   f"real tutor changes: "
                   f"{'; '.join(changes) or 'it never changes'}. "
                   f"Best oracle reference minus the best real tutor ranges "
                   f"{min(gap):.1f} to {max(gap):.1f} concepts."}
