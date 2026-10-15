"""Step-by-step trace of one short run: ZPD, question, answer, true state and belief before and after.
"""

from cursim.curriculum import build_curriculum
from cursim.simulation import run_one

from ..registry import experiment

from .common import spec_from


def yn(v):
    if isinstance(v, bool):
        return "known" if v else "not yet"
    return f"{v:.2f}"


@experiment('trace_20_steps',
            'Step-by-step trace of one short run: ZPD, question, answer, true state and belief before and after.',
            defaults=dict(n_steps=20, threshold=0.9, seed=4242),
            curriculum='abstract', theme='dark')
def trace_table(n_steps=20, threshold=0.9, seed=4242, cur=None, **run_kw):
    """One run, one row per question, everything visible."""
    cur = cur or build_curriculum()
    spec = spec_from(threshold, n_steps, run_kw)
    run = run_one(cur, spec, seed=seed, keep_trace=True)
    rows = []
    for t in run["trace"]:
        rows.append(dict(
            step=t["step"], zpd=", ".join(t["zpd"]), asked=t["concept"],
            question=t["qid"], answer="right" if t["correct"] else "wrong",
            pick_in_zpd=(t["concept"] in t["zpd"]) if t["zpd"] else None,
            true_before=yn(t["true_before"]), true_after=yn(t["true_after"]),
            belief_before=round(t["belief_before"], 3),
            belief_after=round(t["belief_after"], 3),
            declared_mastered=bool(t["mastered_after"]),
        ))
    n_learn = sum(1 for t in run["trace"]
                  if t["true_after"] and not t["true_before"])
    summary = (f"{n_steps} questions, seed {seed}, threshold {threshold}. "
               f"The student learned {n_learn} concept(s) during these steps.")
    return {"tables": {"trace": rows}, "figures": {}, "summary": summary,
            "run": run}
