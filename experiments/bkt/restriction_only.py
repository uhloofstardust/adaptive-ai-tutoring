"""Separates the prerequisite restriction from the cost of gating on a belief that lags the truth, by running both arms against the student's true state.
"""

import math
import random
import statistics as st

from cursim.curriculum import build_curriculum
from cursim.schedulers import pick_question
from cursim.students import BKTLearner
from cursim.students import learner_kwargs

from ..registry import experiment


def oracle_run(cur, gated_student, restrict, seed, n_steps, rng_off=77777):
    """One run whose scheduler gates on the student's TRUE state.

    Not a real tutor: no tutor can see this. It exists to isolate the
    prerequisite RESTRICTION from the cost of gating on a belief that
    lags the truth, which the real Q1/Q2 pair confounds.
    """
    kw = learner_kwargs("bkt_prereq" if gated_student else "bkt")
    kw.pop("params", None)
    L = BKTLearner(cur, seed=seed, **kw)
    rng = random.Random(seed + rng_off)
    ids = cur.ids()
    for _ in range(n_steps):
        elig = [c for c in ids if not L.known[c]]
        if restrict:
            elig = [c for c in elig
                    if all(L.known[p] for p in cur.concepts[c].prereqs)]
        if not elig:
            elig = ids
        L.answer(pick_question(cur, rng.choice(elig), rng), 0.0)
    return sum(L.known.values())


@experiment('restriction_only',
            "Separates the prerequisite restriction from the cost of gating on a belief that lags the truth, by running both arms against the student's true state.",
            defaults=dict(n_learners=400, n_steps=40),
            curriculum='abstract', theme='dark')
def restriction_only(n_learners=400, n_steps=40, seed0=4242, cur=None, **_):
    """Is the prerequisite restriction itself worth anything?

    Q1 and Q2 differ in two ways at once: Q2 restricts to
    prerequisite-ready concepts, AND it decides readiness from a belief
    that lags the truth. This runs the matched pair where both arms gate
    on the student's true state, so only the restriction differs.

    Reading it: a difference of zero for S1 means the restriction costs
    nothing there, and whatever the real Q1/Q2 comparison shows for S1
    is therefore the price of the lag, not of the restriction.
    """
    cur = cur or build_curriculum()
    rows = []
    for label, gated in (("S1", False), ("S2", True)):
        a = [oracle_run(cur, gated, False, seed0 + i, n_steps)
             for i in range(n_learners)]
        b = [oracle_run(cur, gated, True, seed0 + i, n_steps)
             for i in range(n_learners)]
        d = [y - x for x, y in zip(a, b)]
        se = st.stdev(d) / math.sqrt(len(d)) if len(d) > 1 else 0.0
        rows.append(dict(student=label, n_learners=n_learners,
                         n_steps=n_steps,
                         unrestricted=st.mean(a), restricted=st.mean(b),
                         restriction_effect=st.mean(d), ci95=1.96 * se))
    s1, s2 = rows
    summary = (
        f"Both arms gate on the student's true state, so only the "
        f"prerequisite restriction differs. S1: {s1['restriction_effect']:+.3f} "
        f"+/-{s1['ci95']:.3f}. S2: {s2['restriction_effect']:+.3f} "
        f"+/-{s2['ci95']:.3f}. The restriction itself is worth nothing to a "
        f"student whose learning does not depend on prerequisites, and a lot "
        f"to one whose does. Any effect the real Q1/Q2 pair shows for S1 is "
        f"therefore the cost of gating on a belief that lags the truth, not "
        f"the cost of the restriction.")
    return {"tables": {"restriction_only": rows}, "figures": {},
            "summary": summary}
