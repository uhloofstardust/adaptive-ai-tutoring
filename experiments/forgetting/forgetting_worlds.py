"""Experiment 2: does modelling forgetting help, and what does it cost?

Two worlds, three tutors in each. In the first the learner forgets; in
the second forgetting is switched off entirely. Modelling forgetting
should help in the first and cost something in the second, where
revision time is taken from new material.
"""

from cursim.curriculum import build_curriculum

from ..registry import experiment
from .common import (THREE_TUTORS, condition_row, paired_row,
                     run_conditions)
from .plots import fig_worlds

WORLDS = [(True, "learner forgets"), (False, "learner does not forget")]


@experiment("forgetting_worlds",
            "Modelling forgetting in both directions: a learner who forgets "
            "and one who never does.",
            defaults=dict(n_learners=30), curriculum="layered_40")
def forgetting_worlds(n_learners=30, cur=None, **_):
    cur = cur or build_curriculum("layered_40")
    rows, pairs, usable = [], [], {}
    for forgets, world in WORLDS:
        res = run_conditions(cur, THREE_TUTORS, n_learners,
                             learner_forgets=forgets)
        usable[world] = {k: v.mean("retained_usable") for k, v in res.items()}
        exp = f"2_{world.replace(' ', '_')}"
        rows += [condition_row(exp, label, r) for label, r in res.items()]
        base = res["CT + binary"]
        for label in ("CT + forgetting model", "adaptive review"):
            pairs.append(paired_row("CT + binary", label, "retained_usable",
                                    base, res[label], world=world))
    parts = []
    for world, vals in usable.items():
        best = max(vals, key=vals.get)
        parts.append(f"{world}: best is {best} ({vals[best]:.1f})")
    return {"tables": {"conditions": rows, "paired": pairs},
            "figures": {"worlds": fig_worlds(usable)},
            "summary": f"{n_learners} learners on {cur.name}. "
                       + "; ".join(parts) + "."}
