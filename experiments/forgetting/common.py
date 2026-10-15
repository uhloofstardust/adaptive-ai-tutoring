"""Shared building blocks for the forgetting experiments.

Every condition is a (scheduler, mastery model) pair run on the same
learner seeds, so learner i is the same simulated person in every
condition and comparisons are paired.
"""

import statistics
from typing import Dict, List, Tuple

from cursim.simulation import RunResult, RunSpec, run_condition
from cursim.stats import paired

# (scheduler, mastery model, label)
Condition = Tuple[str, str, str]

# The three tutors compared in experiments 2-4.
THREE_TUTORS: List[Condition] = [
    ("curriculum_tutor", "binary", "CT + binary"),
    ("curriculum_tutor", "continuous_forget", "CT + forgetting model"),
    ("adaptive_review", "continuous_forget", "adaptive review"),
]

PRIMARY = "retained_usable"      # concepts still above 0.50 after the break


def condition_row(experiment: str, label: str, result: RunResult) -> dict:
    """One summary row for a condition: population means of the metrics."""
    return {
        "experiment": experiment, "condition": label,
        "n_learners": len(result.per_learner),
        "final_mastery": round(result.mean("final_mastery"), 4),
        "final_learned": round(result.mean("final_learned"), 2),
        "retained_mastery": round(result.mean("retained_mastery"), 4),
        "retained_usable": round(result.mean("retained_usable"), 2),
        "coverage": round(result.mean("coverage"), 2),
        "sd_retained_usable": round(result.sd("retained_usable"), 2),
    }


def paired_row(label_a: str, label_b: str, key: str, a: RunResult,
               b: RunResult, **extra) -> dict:
    """b minus a on `key`, learner by learner."""
    d = paired(a, b, key)
    return {**extra, "comparison": f"{label_b} - {label_a}", "metric": key,
            "mean_diff": d["mean_diff"], "sd": d["sd"], "wins": d["wins"],
            "losses": d["losses"], "n": d["n"], "p_sign": d["p_sign"]}


def run_conditions(cur, conds: List[Condition], n_learners: int,
                   **spec_kw) -> Dict[str, RunResult]:
    """Run each condition over the same population; keyed by label."""
    out = {}
    for scheduler, mastery_model, label in conds:
        spec = RunSpec(scheduler=scheduler, mastery_model=mastery_model,
                       label=label, **spec_kw)
        out[label] = run_condition(cur, spec, n_learners=n_learners)
    return out


def mean_curve(res: RunResult) -> List[float]:
    """Mean true mastery after each session, across learners."""
    n = min(len(r["curve"]) for r in res.per_learner)
    return [statistics.mean(r["curve"][i] for r in res.per_learner)
            for i in range(n)]
