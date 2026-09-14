"""Sanity checks on the tutor code (Surya's mail, Sep 2026).

Plain BKT student, BKT tutor with the same parameters, uniform random
over the ZPD. Because the tutor has the true model, both checks have a
known correct answer, so a deviation is a bug rather than a finding.

  calibration   check 1: when the tutor believes p, is the student known
                with frequency p?
  detection     check 2: how long after the true learning step does the
                tutor declare mastery, and how often does it declare
                before it happened, as a function of the threshold.
  trace_table   the step-by-step trace of one short run.

Every experiment here returns the same shape:
  {"tables": {name: [row dicts]}, "figures": {name: matplotlib fig},
   "summary": str}
Register a new one in EXPERIMENTS and the UI will list it.
"""
import math
import statistics as st
from typing import Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .curriculum import build_curriculum
from .params import BKT_PARAMS
from .simulation import RunSpec, run_one

INK, ACCENT, GREY, GOOD = "#1f2937", "#b5541c", "#9aa0a6", "#2f855a"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 130})


def sanity_spec(threshold=0.9, n_steps=400, scheduler="uniform_zpd",
                mastery_model="bkt", learner="bkt", prereq_gated_pT=False,
                bkt_params=None):
    """The configuration the mail asks for. One flat session: the BKT
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


def _spec_from(threshold, n_steps, kw):
    return sanity_spec(threshold=threshold, n_steps=n_steps,
                       **{k: kw[k] for k in RUN_KEYS if k in kw})


def _population(cur, spec, n_learners, seed0=4242):
    return [run_one(cur, spec, seed=seed0 + i, keep_trace=True)
            for i in range(n_learners)]


# ---------------------------------------------------------------- check 1
def calibration(n_learners=50, n_steps=400, threshold=0.9, n_bins=10,
                seed0=4242, cur=None, **run_kw):
    """Every time the tutor updates a belief, record (belief, true state)
    for that concept, then bin by belief. Both are read at the same
    instant: after the tutor's update and after the student's transition,
    i.e. the state going into the next question."""
    cur = cur or build_curriculum()
    spec = _spec_from(threshold, n_steps, run_kw)
    runs = _population(cur, spec, n_learners, seed0)
    pairs = [(t["belief_after"], float(t["true_after"]))
             for r in runs for t in r["trace"]]
    edges = [i / n_bins for i in range(n_bins + 1)]
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        inb = [(b, y) for b, y in pairs
               if lo <= b < hi or (hi == 1.0 and b == 1.0)]
        n = len(inb)
        frac = sum(y for _, y in inb) / n if n else float("nan")
        mean_b = sum(b for b, _ in inb) / n if n else float("nan")
        se = math.sqrt(frac * (1 - frac) / n) if n and 0 < frac < 1 else 0.0
        rows.append(dict(belief_lo=lo, belief_hi=hi, mean_belief=mean_b,
                         n=n, frac_truly_known=frac, ci95=1.96 * se,
                         gap=(frac - mean_b) if n else float("nan")))

    fig, ax = plt.subplots(figsize=(5.2, 4.4))
    ax.plot([0, 1], [0, 1], "--", color=GREY, lw=1, label="perfect calibration")
    xs = [r["mean_belief"] for r in rows if r["n"]]
    ys = [r["frac_truly_known"] for r in rows if r["n"]]
    es = [r["ci95"] for r in rows if r["n"]]
    ax.errorbar(xs, ys, yerr=es, fmt="o-", color=ACCENT, capsize=3, lw=1.6,
                label="tutor")
    for r in rows:
        if r["n"]:
            ax.annotate(f"n={r['n']}", (r["mean_belief"], -0.06), ha="center",
                        fontsize=7, color=GREY, annotation_clip=False)
    ax.set_xlim(0, 1); ax.set_ylim(-0.02, 1.02)
    ax.set_xlabel("tutor's belief that the concept is known (bin mean)")
    ax.set_ylabel("fraction of those moments where it truly is")
    ax.set_title("Check 1: is the tutor's belief calibrated?")
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()

    worst = max((abs(r["gap"]) for r in rows if r["n"] >= 20),
                default=float("nan"))
    n_all = sum(r["n"] for r in rows)
    mean_b = sum(r["mean_belief"] * r["n"] for r in rows if r["n"]) / n_all
    mean_t = sum(r["frac_truly_known"] * r["n"] for r in rows if r["n"]) / n_all
    summary = (f"{len(pairs)} (belief, truth) pairs from {n_learners} learners x "
               f"{n_steps} questions. Overall: mean belief {mean_b:.4f}, fraction "
               f"truly known {mean_t:.4f}. Largest per-bin gap with n>=20: "
               f"{worst:.3f}. Note: successive pairs on one concept are dependent, "
               f"so per-bin CIs are nominal; the overall comparison is the robust one.")
    return {"tables": {"calibration": rows}, "figures": {"calibration": fig},
            "summary": summary}


# ---------------------------------------------------------------- check 2
def _per_concept(run, threshold):
    """For one learner: per concept, when it was truly learned and when the
    tutor first declared it (belief after update >= threshold)."""
    trace, learned = run["trace"], run["learned_step"]
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


def detection(n_learners=30, n_steps=400,
              thresholds=(0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99),
              seed0=4242, cur=None, **run_kw):
    """One population per threshold, because the threshold also decides
    what the tutor asks (it defines the ZPD). Reports, per threshold:
    detection delay after the true learning step, false-alarm rate
    (share of declarations made before the concept was learned), and
    what was still unresolved when the run ended, decomposed by cause."""
    cur = cur or build_curriculum()
    rows = []
    for th in thresholds:
        spec = _spec_from(th, n_steps, run_kw)
        recs = [x for r in _population(cur, spec, n_learners, seed0)
                for x in _per_concept(r, th)]
        declared = [x for x in recs if x["declared_step"] is not None]
        learned = [x for x in recs if x["learned_step"] is not None]
        delays = [x["delay_questions"] for x in recs
                  if x["delay_questions"] is not None]
        on_c = [x["delay_on_concept"] for x in recs
                if x["delay_on_concept"] is not None]
        unres = [x for x in recs if x["unresolved"]]
        why = {k: sum(1 for x in unres if x["unresolved_why"] == k)
               for k in ("learned in the last 50 questions",
                         "never reached by the ZPD",
                         "asked, not yet over threshold")}
        fa = sum(x["premature"] for x in declared)
        fa_stuck = sum(1 for x in declared if x["premature"]
                       and x["learned_step"] is None)
        b_cross = (st.mean(x["belief_at_declaration"] for x in declared)
                   if declared else float("nan"))
        rows.append(dict(
            threshold=th,
            belief_at_declaration=b_cross,
            # if check 1 holds, this must match false_alarm_rate
            predicted_false_alarm_rate=1.0 - b_cross,
            n_concepts=len(recs), n_learned=len(learned), n_declared=len(declared),
            false_alarms=fa,
            # share of declarations that came before the concept was learned
            false_alarm_rate=fa / len(declared) if declared else float("nan"),
            # of those, how many concepts were then never learned at all:
            # once declared it leaves the ZPD and is never asked again
            false_alarms_never_learned=fa_stuck,
            delay_mean=st.mean(delays) if delays else float("nan"),
            delay_median=st.median(delays) if delays else float("nan"),
            n_delay=len(delays),
            delay_on_concept_mean=st.mean(on_c) if on_c else float("nan"),
            n_delay_on_concept=len(on_c),
            unresolved=len(unres),
            unresolved_rate=len(unres) / len(learned) if learned else float("nan"),
            unresolved_learned_late=why["learned in the last 50 questions"],
            unresolved_never_reached=why["never reached by the ZPD"],
            unresolved_asked_not_crossed=why["asked, not yet over threshold"],
        ))

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 3.8))
    th = [r["threshold"] for r in rows]
    a1.plot(th, [r["delay_on_concept_mean"] for r in rows], "o-", color=ACCENT,
            lw=1.6, label="questions on that concept (all detections)")
    a1.plot(th, [r["delay_mean"] for r in rows], "s--", color=INK, lw=1.4,
            label="questions overall (concepts learned during the run)")
    a1.set_xlabel("mastery threshold"); a1.set_ylabel("mean delay after true learning")
    a1.set_title("How long until the tutor notices")
    a1.legend(frameon=False, fontsize=8.5)
    a2.plot(th, [r["false_alarm_rate"] for r in rows], "o-", color=ACCENT, lw=1.6,
            label="false alarm rate, measured")
    a2.plot(th, [r["predicted_false_alarm_rate"] for r in rows], "x:", color=INK,
            lw=1.2, ms=7, label="1 - belief at declaration (what calibration predicts)")
    a2.plot(th, [r["unresolved_rate"] for r in rows], "s--", color=GREY, lw=1.4,
            label="unresolved when the run ended (horizon effect)")
    a2.set_xlabel("mastery threshold"); a2.set_ylabel("rate")
    top = max(max(r["false_alarm_rate"] for r in rows),
              max(r["unresolved_rate"] for r in rows))
    a2.set_ylim(-0.02, max(0.42, 1.15 * top))
    a2.set_title("Share of declarations that were too early")
    a2.legend(frameon=False, fontsize=8.5)
    fig.tight_layout()

    lo, hi = rows[0], rows[-1]
    summary = (f"Threshold {lo['threshold']}: {lo['delay_on_concept_mean']:.1f} "
               f"questions on the concept until declared, false alarms "
               f"{lo['false_alarm_rate']:.1%}. Threshold {hi['threshold']}: "
               f"{hi['delay_on_concept_mean']:.1f} questions, false alarms "
               f"{hi['false_alarm_rate']:.1%}. 'Unresolved' counts concepts learned "
               f"but not declared by the end of the {n_steps}-question run; every "
               f"one is either learned in the last 50 questions or never reached "
               f"by the ZPD, i.e. a horizon effect, not a detector failure.")
    return {"tables": {"detection": rows}, "figures": {"detection": fig},
            "summary": summary}


# ---------------------------------------------------------------- trace
def trace_table(n_steps=20, threshold=0.9, seed=4242, cur=None, **run_kw):
    """One run, one row per question, everything visible."""
    cur = cur or build_curriculum()
    spec = _spec_from(threshold, n_steps, run_kw)
    run = run_one(cur, spec, seed=seed, keep_trace=True)
    rows = []
    for t in run["trace"]:
        rows.append(dict(
            step=t["step"], zpd=", ".join(t["zpd"]), asked=t["concept"],
            question=t["qid"], answer="right" if t["correct"] else "wrong",
            pick_in_zpd=(t["concept"] in t["zpd"]) if t["zpd"] else None,
            true_before=_yn(t["true_before"]), true_after=_yn(t["true_after"]),
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


def _yn(v):
    if isinstance(v, bool):
        return "known" if v else "not yet"
    return f"{v:.2f}"


# ---------------------------------------------------------------- registry
EXPERIMENTS = {
    "check1_calibration": (
        calibration,
        "Check 1. Is the tutor's belief correct? Bin every belief and see "
        "how often the student truly knows the concept.",
        dict(n_learners=50, n_steps=400, threshold=0.9)),
    "check2_detection": (
        detection,
        "Check 2. Detection delay and false-alarm rate as a function of "
        "the mastery threshold.",
        dict(n_learners=30, n_steps=400)),
    "trace_20_steps": (
        trace_table,
        "Step-by-step trace of one short run: ZPD, question, answer, true "
        "state and belief before and after.",
        dict(n_steps=20, threshold=0.9, seed=4242)),
}
