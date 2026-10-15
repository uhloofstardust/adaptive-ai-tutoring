"""Shared building blocks for the BKT validation experiments.

The reference configuration (plain BKT student, BKT tutor, one flat
session), population runner, and the pooled-gap / loss helpers.
"""

import statistics as st
from typing import Dict
from typing import List
from typing import Optional

from cursim.params import BKT_PARAMS
from cursim.simulation import RunSpec
from cursim.simulation import run_one
from cursim.stats import bootstrap_half_width


def sanity_spec(threshold=0.9, n_steps=400, scheduler="uniform_zpd",
                mastery_model="bkt", learner="bkt", prereq_gated_pT=False,
                bkt_params=None):
    """The reference sanity configuration. One flat session: the BKT
    student has no time dynamics, so sessions and gaps are irrelevant."""
    p = bkt_params or BKT_PARAMS
    if p["p_L0"] >= threshold:
        raise ValueError(f"p_L0={p['p_L0']} >= threshold={threshold}: every "
                         "concept would be 'declared' before any question.")
    return RunSpec(scheduler=scheduler, mastery_model=mastery_model,
                   learner=learner, threshold=threshold,
                   prereq_gated_pT=prereq_gated_pT, bkt_params=bkt_params,
                   n_sessions=1, questions_per_session=n_steps,
                   gap_hours=0.0, retention_days=0.0, label="sanity")


RUN_KEYS = ("scheduler", "mastery_model", "learner", "prereq_gated_pT", "bkt_params")


def spec_from(threshold, n_steps, kw):
    return sanity_spec(threshold=threshold, n_steps=n_steps,
                       **{k: kw[k] for k in RUN_KEYS if k in kw})


def population(cur, spec, n_learners, seed0=4242):
    return [run_one(cur, spec, seed=seed0 + i, keep_trace=True)
            for i in range(n_learners)]


def per_concept(run, threshold):
    """For one learner: per concept, when it was truly learned and when the
    tutor first declared it (belief after update >= threshold).

    Requires a student that records learned_step, i.e. a BKT one. The
    continuous student has no binary moment of learning, so there is
    nothing for a detection delay to be measured from.
    """
    trace, learned = run["trace"], run["learned_step"]
    if not learned:
        raise ValueError(
            "detection needs a student that records the step at which each "
            "concept was learned. The 'continuous' student has no such "
            "moment: its mastery is a real number that never flips. Use "
            "learner='bkt' or 'bkt_prereq'.")
    first_declared: Dict[str, Optional[int]] = {c: None for c in learned}
    belief_at: Dict[str, Optional[float]] = {c: None for c in learned}
    asked_at: Dict[str, List[int]] = {c: [] for c in learned}
    for t in trace:
        c = t["concept"]
        asked_at[c].append(t["step"])
        if first_declared[c] is None and t["belief_after"] >= threshold:
            first_declared[c] = t["step"]
            belief_at[c] = t["belief_after"]
    n_steps = trace[-1]["step"] if trace else 0
    out = []
    for c, t_star in learned.items():
        t_d = first_declared[c]
        premature = t_d is not None and (t_star is None or t_d < t_star)
        detected = t_d is not None and t_star is not None and t_d >= t_star
        # "questions overall" delay is only a detection delay for concepts
        # learned DURING the run. For concepts known before step 1 it would
        # just measure how long the ZPD took to reach them, so it is left out.
        delay = (t_d - t_star) if (detected and t_star > 0) else None
        # questions on that concept until declared: valid for all detections
        on_concept = (sum(1 for s in asked_at[c] if t_star < s <= t_d)
                      if detected else None)
        unresolved = t_star is not None and t_d is None
        why = None
        if unresolved:
            if not asked_at[c]:
                why = "never reached by the ZPD"
            elif t_star > n_steps - 50:
                why = "learned in the last 50 questions"
            else:
                why = "asked, not yet over threshold"
        out.append(dict(concept=c, learned_step=t_star, declared_step=t_d,
                        belief_at_declaration=belief_at[c],
                        premature=premature, delay_questions=delay,
                        delay_on_concept=on_concept,
                        known_at_start=(t_star == 0),
                        unresolved=unresolved, unresolved_why=why))
    return out


def spec_2x2(student, scheduler, n_steps, threshold, sm):
    """One cell: a student model crossed with a question-selection rule.

    The tutor is plain BKT with p(T) equal to the student's unblocked
    p(T). Against S2 that makes it mildly misspecified, because the
    student's real p(T) drops while prerequisites are unmet and the
    tutor cannot see prerequisites. That is deliberate and stated: a
    tutor has no access to the student's hidden state.
    """
    params = dict(BKT_PARAMS)
    return RunSpec(scheduler=scheduler, mastery_model="bkt",
                   learner="bkt_prereq" if sm["prereq_gated"] else "bkt",
                   threshold=threshold,
                   student_params=params, tutor_params=params,
                   n_sessions=1, questions_per_session=n_steps,
                   gap_hours=0.0, retention_days=0.0, label=student)


def detect_stats(runs, threshold):
    recs = [x for r in runs for x in per_concept(r, threshold)]
    dec = [x for x in recs if x["declared_step"] is not None]
    on_c = [x["delay_on_concept"] for x in recs
            if x["delay_on_concept"] is not None]
    fa = sum(x["premature"] for x in dec)
    return dict(n_declared=len(dec),
                false_alarm_rate=fa / len(dec) if dec else float("nan"),
                delay_on_concept_mean=st.mean(on_c) if on_c else float("nan"))


def calib_gap(runs):
    """Overall mean belief and fraction truly known, pooled over all pairs.

    The gap (truth minus belief) is a SIGNED pooled average, so it is a
    bias diagnostic, not a calibration summary: opposite-signed bins can
    cancel. `calibration()` is where per-bin behaviour is checked.
    """
    pairs = [(t["belief_after"], float(t["true_after"]))
             for r in runs for t in r["trace"]]
    if not pairs:
        return float("nan"), float("nan")
    mb = sum(b for b, _ in pairs) / len(pairs)
    mt = sum(y for _, y in pairs) / len(pairs)
    return mb, mt


def gap_contrib(runs):
    """Each learner's (sum of truth minus belief, number of pairs).

    The pooled gap is sum(numerators)/sum(denominators) over learners,
    so these are the units a learner-level bootstrap resamples.
    """
    per = []
    for r in runs:
        b = [t["belief_after"] for t in r["trace"]]
        y = [float(t["true_after"]) for t in r["trace"]]
        per.append((sum(y) - sum(b), len(b)) if b else (0.0, 0))
    return per


def loss_contrib(runs, kind="abs"):
    """Per-learner (summed per-pair loss, number of pairs).

    `calib_gap` pools a SIGNED difference, so a tutor that is
    overconfident about half its students and underconfident about the
    other half scores zero. Under a symmetric spread of students that is
    exactly what happens, which makes the signed gap blind by
    construction to the error an adapting tutor would fix. These losses
    do not cancel:

        "abs" -> mean |belief - truth| over pairs
        "sq"  -> Brier score, mean (belief - truth)^2 over pairs

    Same (numerator, denominator) shape as `gap_contrib`, so the same
    paired bootstrap applies.
    """
    per = []
    for r in runs:
        d = [t["belief_after"] - float(t["true_after"]) for t in r["trace"]]
        if kind == "abs":
            per.append((sum(abs(x) for x in d), len(d)))
        else:
            per.append((sum(x * x for x in d), len(d)))
    return per


def gap_ci(runs, n_boot=400, seed=7):
    """95% interval half-width on the pooled gap, resampling LEARNERS
    rather than pairs, because the pairs within one learner are not
    independent."""
    return bootstrap_half_width(gap_contrib(runs), n_boot, seed)


PARAM_GRIDS = {"p_G": [0.05, 0.15, 0.25, 0.35, 0.45],
               "p_S": [0.02, 0.05, 0.10, 0.20, 0.30],
               "p_T": [0.05, 0.10, 0.20, 0.30, 0.40]}
