"""Turn one run into the single JSON payload the viewer plays back.

The whole trace is shipped to the browser at once, so stepping and
playing are instant and need no round trip. Everything the viewer
draws is computed here, including the graph layout, so Python and the
browser never disagree about the picture.
"""

import json
from typing import Optional

from .curriculum import Curriculum
from .params import BKT_PARAMS
from .schedulers import zpd
from .simulation import RunSpec, run_one


def build_payload(cur: Curriculum, spec: RunSpec, seed: int,
                  run: Optional[dict] = None) -> dict:
    """Run (or take) one run and package it for the viewer."""
    run = run or run_one(cur, spec, seed=seed, keep_trace=True)
    ids = cur.ids()
    pos = cur.layout()

    steps = []
    for t in run["trace"]:
        steps.append({
            "step": t["step"],
            "asked": t["concept"],
            "qid": t["qid"],
            "correct": bool(t["correct"]),
            "zpd": list(t["zpd"] or []),
            "beliefBefore": round(float(t["belief_before"]), 4),
            "beliefAfter": round(float(t["belief_after"]), 4),
            "trueBefore": _num(t["true_before"]),
            "trueAfter": _num(t["true_after"]),
            "declared": bool(t["mastered_after"]),
            # full state after this step, for the graph and the chart grid
            "beliefs": {c: round(float(t["beliefs"][c]), 4) for c in ids},
            "truth": {c: _num(t["truth"][c]) for c in ids},
        })

    return {
        "meta": {
            "curriculum": cur.name or "unnamed",
            "curriculumTitle": cur.title,
            "learner": spec.learner,
            "masteryModel": spec.mastery_model,
            "scheduler": spec.scheduler,
            "threshold": spec.threshold,
            "prereqGatedPT": bool(spec.prereq_gated_pT),
            "seed": seed,
            "nSteps": len(steps),
            "bktParams": dict(spec.bkt_params or BKT_PARAMS),
        },
        "concepts": [
            {"id": c.cid, "name": c.name, "tier": c.tier,
             "prereqs": list(c.prereqs), "nQuestions": len(c.questions),
             "x": pos[c.cid]["x"], "y": pos[c.cid]["y"]}
            for c in cur.concepts.values()],
        "edges": [{"from": a, "to": b} for a, b in cur.edges()],
        # the step at which the student truly learned each concept
        # (0 = knew it before any question, null = never), so the viewer
        # can mark the moment the tutor is trying to detect
        "learnedStep": {c: run["learned_step"].get(c) for c in ids}
        if run.get("learned_step") else {},
        "steps": steps,
    }


def _num(v):
    """Booleans and continuous mastery both become a number in [0,1]."""
    return 1.0 if v is True else 0.0 if v is False else round(float(v), 4)


def payload_json(*args, **kw) -> str:
    return json.dumps(build_payload(*args, **kw), separators=(",", ":"))
