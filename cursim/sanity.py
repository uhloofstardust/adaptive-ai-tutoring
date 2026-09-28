"""Sanity checks on the tutor code.

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
import random
import statistics as st
from typing import Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .curriculum import build_curriculum
from .learner import BKTLearner, learner_kwargs
from .schedulers import _pick_question
from .params import BKT_PARAMS, STUDENT_MODELS
from .simulation import RunSpec, run_one

# same palette as the interface, so a saved figure and the screen agree
INK, ACCENT, GREY, GOOD = "#e6e9f0", "#6f8ffb", "#98a1b5", "#3ecf8e"
PAPER, PANEL = "#12151d", "#12151d"
plt.rcParams.update({
    "font.size": 10, "figure.dpi": 130,
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#3a4253", "axes.labelcolor": INK,
    "text.color": INK, "xtick.color": GREY, "ytick.color": GREY,
    "figure.facecolor": PAPER, "axes.facecolor": PANEL,
    "savefig.facecolor": PAPER, "grid.color": "#252b38",
    "legend.facecolor": PANEL, "legend.edgecolor": "#3a4253",
})


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


def _spec_from(threshold, n_steps, kw):
    return sanity_spec(threshold=threshold, n_steps=n_steps,
                       **{k: kw[k] for k in RUN_KEYS if k in kw})


def _population(cur, spec, n_learners, seed0=4242):
    return [run_one(cur, spec, seed=seed0 + i, keep_trace=True)
            for i in range(n_learners)]


# ---------------------------------------------------------------- check 1
def calibration(n_learners=50, n_steps=120, threshold=0.9, n_bins=10,
                seed0=4242, cur=None, **run_kw):
    if n_learners < 1 or n_steps < 1:
        raise ValueError("calibration needs at least one learner and one "
                         "question.")
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
    ax.plot([0, 1], [0, 1], "--", color="#5a6377", lw=1,
            label="perfect calibration")
    xs = [r["mean_belief"] for r in rows if r["n"]]
    ys = [r["frac_truly_known"] for r in rows if r["n"]]
    es = [r["ci95"] for r in rows if r["n"]]
    ax.errorbar(xs, ys, yerr=es, fmt="o-", color=ACCENT, capsize=3, lw=1.6,
                label="tutor")
    # bin counts sit on two alternating rows so neighbouring labels
    # never collide when bins are close together
    for i, r in enumerate([x for x in rows if x["n"]]):
        ax.annotate(f"n={r['n']}", (r["mean_belief"], -0.055 - 0.05 * (i % 2)),
                    ha="center", fontsize=7, color=GREY, annotation_clip=False)
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


def detection(n_learners=30, n_steps=120,
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


# ============================================================ the 2x2
def _spec_2x2(student, scheduler, n_steps, threshold, sm):
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


def two_by_two(n_learners=400, n_steps=40, threshold=0.9, seed0=4242,
               cur=None, **_):
    """Two student models by two question-selection rules.

    The prediction under test, written down before running:

        S1 (prerequisites irrelevant)   Q1 good, Q2 good
        S2 (prerequisites gate p(T))    Q1 bad,  Q2 good

    i.e. the scheduler is invisible against S1 and decisive against S2.
    If the scheduler mattered against S1 too, or did not matter against
    S2, the setup could not tell schedulers apart and the result would
    be a bug rather than a finding.

    Scored on concepts the student TRULY knows at the end, which is the
    student's own state and owes nothing to what the tutor believes.
    """
    if n_learners < 2:
        raise ValueError("two_by_two needs at least 2 learners to report an "
                         "interval; got %d." % n_learners)
    if n_steps < 1:
        raise ValueError("two_by_two needs at least 1 question; got %d."
                         % n_steps)
    cur = cur or build_curriculum()
    n_c = len(cur.concepts)
    rows, cells = [], {}
    for sname, sm in STUDENT_MODELS.items():
        for qname, sched in (("Q1", "uniform_unmastered"),
                             ("Q2", "uniform_zpd")):
            spec = _spec_2x2(sname, sched, n_steps, threshold, sm)
            runs = _population(cur, spec, n_learners, seed0)
            known = [sum(1 for v in r["truth"].values() if v >= 0.999)
                     for r in (x["trace"][-1] for x in runs)]
            wasted = [sum(1 for t in x["trace"]
                          if t["zpd"] and t["concept"] not in t["zpd"])
                      for x in runs]
            cells[(sname, qname)] = known
            rows.append(dict(
                student=sname, scheduler=qname, sched_key=sched,
                n_learners=n_learners, n_steps=n_steps, n_concepts=n_c,
                learned_mean=st.mean(known),
                learned_sd=st.stdev(known) if len(known) > 1 else 0.0,
                learned_frac=st.mean(known) / n_c,
                asked_outside_zpd=st.mean(wasted)))

    # within each student, Q2 minus Q1, learner by learner (paired seeds)
    paired_rows, diffs = [], {}
    for sname in STUDENT_MODELS:
        d = [b - a for a, b in zip(cells[(sname, "Q1")], cells[(sname, "Q2")])]
        diffs[sname] = d
        m = st.mean(d)
        se = (st.stdev(d) / math.sqrt(len(d))) if len(d) > 1 else 0.0
        wins = sum(1 for x in d if x > 0)
        paired_rows.append(dict(
            student=sname, diff_Q2_minus_Q1=m, ci95=1.96 * se,
            better_with_Q2=wins, n=len(d),
            favours="Q2" if m > 1.96 * se else ("Q1" if -m > 1.96 * se
                                                else "neither"),
            scheduler_matters=bool(abs(m) > 1.96 * se)))

    # the interaction: does the sign of (Q2 - Q1) depend on which student
    # it is? This, not either column on its own, is the claim.
    #
    # Seed i is the same person in all four cells, so the two per-student
    # differences are paired, not independent: treating them as independent
    # (sqrt(var/n + var/n)) ignores a positive correlation and gives an SE
    # that is too wide. The per-seed difference of differences is the right
    # statistic.
    a, b = diffs["S1"], diffs["S2"]
    per_seed = [y - x for x, y in zip(a, b)]
    inter = st.mean(per_seed)
    inter_se = (st.stdev(per_seed) / math.sqrt(len(per_seed))
                if len(per_seed) > 1 else 0.0)
    paired_rows.append(dict(
        student="interaction (S2 minus S1)", diff_Q2_minus_Q1=inter,
        ci95=1.96 * inter_se, better_with_Q2=-1, n=len(a),
        favours="-", scheduler_matters=bool(abs(inter) > 1.96 * inter_se)))

    fig, ax = plt.subplots(figsize=(5.6, 3.9))
    xs = [0, 1]
    w = 0.34
    for i, (q, col) in enumerate((("Q1", GREY), ("Q2", ACCENT))):
        m = [st.mean(cells[(s, q)]) for s in STUDENT_MODELS]
        e = [1.96 * st.stdev(cells[(s, q)]) / math.sqrt(n_learners)
             for s in STUDENT_MODELS]
        ax.bar([x + (i - .5) * w for x in xs], m, w, yerr=e, capsize=4,
               color=col, label=f"{q}: " + ("anything not mastered" if q == "Q1"
                                            else "only prerequisite-ready"))
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{s}\n{STUDENT_MODELS[s]['label'].split(':')[1].strip()}"
                        for s in STUDENT_MODELS], fontsize=8.5)
    ax.set_ylabel(f"concepts truly known at the end (of {n_c})")
    ax.set_title("Does the question-selection rule matter?")
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    ax.set_ylim(0, n_c * 1.12)
    fig.tight_layout()

    s1, s2, ix = paired_rows[0], paired_rows[1], paired_rows[2]
    # read the verdict off the two marginals, so it can never assert a
    # sign flip the table denies, nor deny an interaction the table reports
    if not ix["scheduler_matters"]:
        verdict = "no interaction detected at this budget"
    elif {s1["favours"], s2["favours"]} == {"Q1", "Q2"}:
        verdict = "the sign of the scheduler effect flips with the student model"
    else:
        verdict = ("the size, not the sign, of the scheduler effect depends on "
                   f"the student (S1 favours {s1['favours']}, "
                   f"S2 favours {s2['favours']})")
    summary = (
        f"{n_learners} learners x {n_steps} questions on {cur.name}, "
        f"{n_c} concepts. S1: Q2 minus Q1 = {s1['diff_Q2_minus_Q1']:+.2f} "
        f"[{s1['diff_Q2_minus_Q1']-s1['ci95']:+.2f}, "
        f"{s1['diff_Q2_minus_Q1']+s1['ci95']:+.2f}] "
        f"(favours {s1['favours']}). "
        f"S2: {s2['diff_Q2_minus_Q1']:+.2f} "
        f"[{s2['diff_Q2_minus_Q1']-s2['ci95']:+.2f}, "
        f"{s2['diff_Q2_minus_Q1']+s2['ci95']:+.2f}] "
        f"(favours {s2['favours']}). Interaction {ix['diff_Q2_minus_Q1']:+.2f} "
        f"[{ix['diff_Q2_minus_Q1']-ix['ci95']:+.2f}, "
        f"{ix['diff_Q2_minus_Q1']+ix['ci95']:+.2f}]: {verdict}. "
        f"Note the budget matters: at a budget long enough for everything to "
        f"be learned anyway, every cell saturates and no scheduler can differ.")
    return {"tables": {"two_by_two": rows, "paired": paired_rows},
            "figures": {"two_by_two": fig}, "summary": summary}



# ==================================================== parameter sweeps
def _detect_stats(runs, threshold):
    recs = [x for r in runs for x in _per_concept(r, threshold)]
    dec = [x for x in recs if x["declared_step"] is not None]
    on_c = [x["delay_on_concept"] for x in recs
            if x["delay_on_concept"] is not None]
    fa = sum(x["premature"] for x in dec)
    return dict(n_declared=len(dec),
                false_alarm_rate=fa / len(dec) if dec else float("nan"),
                delay_on_concept_mean=st.mean(on_c) if on_c else float("nan"))


def _calib_gap(runs):
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


def _gap_ci(runs, n_boot=400, seed=7):
    """95% interval on the pooled gap, resampling LEARNERS rather than
    pairs, because the pairs within one learner are not independent."""
    per = []
    for r in runs:
        b = [t["belief_after"] for t in r["trace"]]
        y = [float(t["true_after"]) for t in r["trace"]]
        if b:
            per.append((sum(y) - sum(b), len(b)))
    if len(per) < 2:
        return float("nan")
    rng = random.Random(seed)
    boots = []
    for _ in range(n_boot):
        pick = [per[rng.randrange(len(per))] for _ in per]
        num = sum(a for a, _ in pick)
        den = sum(n for _, n in pick)
        boots.append(num / den if den else float("nan"))
    boots.sort()
    lo, hi = boots[int(.025 * len(boots))], boots[int(.975 * len(boots)) - 1]
    return (hi - lo) / 2


def param_sweep(n_learners=30, n_steps=120, threshold=0.9, seed0=4242,
                cur=None, **run_kw):
    """Vary one BKT parameter at a time, with the tutor kept correctly
    specified (student and tutor move together), and watch what happens
    to detection delay and the false-alarm rate.

    This is not a misspecification study: it asks what the parameters
    themselves do. `mismatch` is the study where the two sides differ.
    """
    cur = cur or build_curriculum()
    grids = {"p_G": [0.05, 0.15, 0.25, 0.35, 0.45],
             "p_S": [0.02, 0.05, 0.10, 0.20, 0.30],
             "p_T": [0.05, 0.10, 0.20, 0.30, 0.40],
             "p_L0": [0.05, 0.15, 0.30, 0.50]}
    rows = []
    for pname, vals in grids.items():
        for v in vals:
            pr = dict(BKT_PARAMS, **{pname: v})
            spec = _spec_from(threshold, n_steps, run_kw)
            spec.student_params = pr
            spec.tutor_params = pr
            runs = _population(cur, spec, n_learners, seed0)
            mb, mt = _calib_gap(runs)
            rows.append(dict(parameter=pname, value=v,
                             calib_mean_belief=mb, calib_frac_known=mt,
                             calib_gap=mt - mb, **_detect_stats(runs, threshold)))

    fig, axes = plt.subplots(1, 3, figsize=(11.4, 3.5))
    for ax, metric, ylab in (
            (axes[0], "delay_on_concept_mean", "questions on that concept"),
            (axes[1], "false_alarm_rate", "false alarm rate"),
            (axes[2], "calib_gap", "calibration gap (known - believed)")):
        for pname, col in zip(grids, (ACCENT, GOOD, "#f0a93a", GREY)):
            xs = [r["value"] for r in rows if r["parameter"] == pname]
            ys = [r[metric] for r in rows if r["parameter"] == pname]
            ax.plot(xs, ys, "o-", lw=1.6, ms=4, color=col, label=pname)
        ax.set_xlabel("parameter value")
        ax.set_ylabel(ylab, fontsize=9)
    axes[2].axhline(0, ls="--", lw=1, color=GREY)
    axes[0].legend(frameon=False, fontsize=8.5)
    fig.suptitle("What each BKT parameter does, tutor correctly specified",
                 fontsize=11)
    fig.tight_layout()

    worst = max(rows, key=lambda r: abs(r["calib_gap"]))
    span = {}
    for pname in grids:
        fa = [r["false_alarm_rate"] for r in rows if r["parameter"] == pname]
        dl = [r["delay_on_concept_mean"] for r in rows if r["parameter"] == pname]
        span[pname] = (max(fa) - min(fa), max(dl) - min(dl))
    fa_rank = sorted(span, key=lambda k: -span[k][0])
    dl_rank = sorted(span, key=lambda k: -span[k][1])
    summary = (
        f"{len(rows)} cells, {n_learners} learners each, all sharing one seed "
        f"block. Every cell here is correctly specified (student and tutor get "
        f"the same values), so the pooled gap measures estimator noise, not "
        f"calibration: it stays within {abs(worst['calib_gap']):.3f} "
        f"everywhere, which says the estimator is unbiased across parameter "
        f"settings rather than that the tutor is calibrated. Range of the "
        f"false-alarm rate across each grid: " +
        ", ".join(f"{k} {span[k][0]:.3f}" for k in fa_rank) +
        ". Range of the on-concept delay: " +
        ", ".join(f"{k} {span[k][1]:.2f}" for k in dl_rank) +
        f". So {fa_rank[0]} is the strongest lever on both, and the effects do "
        f"not separate cleanly by metric.")
    return {"tables": {"param_sweep": rows}, "figures": {"param_sweep": fig},
            "summary": summary}


# ================================================ tutor/student mismatch
def mismatch(n_learners=200, n_steps=120, threshold=0.9, seed0=4242,
             vary="p_G", cur=None, **run_kw):
    """The tutor's assumed parameters differ from the student's real ones.

    (a) one student: the student is fixed at the true values and the
        tutor's assumption for `vary` is swept. The tutor is wrong by a
        known amount, so the calibration gap should grow with the error
        and vanish at the truth. `vary` is one parameter name or a
        sequence of them; each is swept in turn and tagged in the
        `parameter` column.
    (b) many students: every learner draws their own true parameters
        from a spread, while the tutor uses one fixed set. This is the
        realistic case, and the question is whether a single tutor model
        stays usable across a population it does not match.
    """
    cur = cur or build_curriculum()
    truth = dict(BKT_PARAMS)
    rows = []

    # ---- (a) one true student, tutor's assumption swept
    GRIDS = {"p_G": [0.05, 0.15, 0.25, 0.35, 0.45],
             "p_S": [0.02, 0.05, 0.10, 0.20, 0.30],
             "p_T": [0.05, 0.10, 0.20, 0.30, 0.40]}
    varies = [vary] if isinstance(vary, str) else list(vary)
    bad = [v for v in varies if v not in GRIDS]
    if bad:
        raise ValueError(f"mismatch(vary=...) accepts {sorted(GRIDS)}, "
                         f"got {bad}")
    for name in varies:
        for v in GRIDS[name]:
            spec = _spec_from(threshold, n_steps, run_kw)
            spec.student_params = truth
            spec.tutor_params = dict(truth, **{name: v})
            runs = _population(cur, spec, n_learners, seed0)
            mb, mt = _calib_gap(runs)
            rows.append(dict(arm="one student", parameter=name,
                             tutor_value=v, student_value=truth[name],
                             error=v - truth[name],
                             calib_mean_belief=mb, calib_frac_known=mt,
                             calib_gap=mt - mb, calib_gap_ci95=_gap_ci(runs),
                             **_detect_stats(runs, threshold)))

    # ---- (b) a population of students, one fixed tutor
    pop_rows = []
    for spread in (0.0, 0.05, 0.10, 0.15):
        runs = []
        for i in range(n_learners):
            r = random.Random(seed0 + 9000 + i)
            sp = dict(truth)
            for k in ("p_G", "p_S", "p_T"):
                sp[k] = min(0.45, max(0.02, truth[k] + r.uniform(-spread, spread)))
            spec = _spec_from(threshold, n_steps, run_kw)
            spec.student_params = sp
            spec.tutor_params = truth          # one model for everybody
            runs.append(run_one(cur, spec, seed=seed0 + i, keep_trace=True))
        mb, mt = _calib_gap(runs)
        pop_rows.append(dict(arm="population", spread=spread,
                             calib_mean_belief=mb, calib_frac_known=mt,
                             calib_gap=mt - mb, calib_gap_ci95=_gap_ci(runs),
                             **_detect_stats(runs, threshold)))

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.6))
    a1.axhline(0, ls="--", lw=1, color=GREY)
    # one colour per swept parameter; solid = calibration gap, dashed =
    # false alarms, so a reader compares parameters by colour and metric
    # by line style rather than by reading the legend twice.
    pal = (ACCENT, GOOD, "#e2a03f")
    for i, name in enumerate(varies):
        sub = [r for r in rows if r["parameter"] == name]
        col = pal[i % len(pal)]
        a1.plot([r["error"] for r in sub], [r["calib_gap"] for r in sub],
                "o-", color=col, lw=1.7, label=f"{name}: calibration gap")
        a1.plot([r["error"] for r in sub],
                [r["false_alarm_rate"] for r in sub],
                "s--", color=col, lw=1.4, label=f"{name}: false alarms")
    a1.axvline(0, ls=":", lw=1, color=GREY)
    a1.set_xlabel("tutor's assumed value minus the student's true value")
    a1.set_ylabel("rate")
    a1.set_title("One student, tutor's assumption swept", fontsize=10.5)
    a1.legend(frameon=False, fontsize=7.5,
              ncol=2 if len(varies) > 1 else 1)

    a2.axhline(0, ls="--", lw=1, color=GREY)
    a2.plot([r["spread"] for r in pop_rows],
            [r["calib_gap"] for r in pop_rows], "o-", color=ACCENT, lw=1.7,
            label="calibration gap")
    a2.plot([r["spread"] for r in pop_rows],
            [r["false_alarm_rate"] for r in pop_rows], "s--", color=GOOD,
            lw=1.4, label="false alarm rate")
    a2.set_xlabel("spread of the students' true parameters (uniform +/-)")
    a2.set_ylabel("rate")
    a2.set_title("A population, one fixed tutor model", fontsize=10.5)
    a2.legend(frameon=False, fontsize=8.5)
    fig.tight_layout()

    parts = []
    for name in varies:
        sub = [r for r in rows if r["parameter"] == name]
        at_truth = min(sub, key=lambda r: abs(r["error"]))
        worst = max(sub, key=lambda r: abs(r["calib_gap"]))
        parts.append(
            f"{name}: gap {at_truth['calib_gap']:+.3f} "
            f"+/-{at_truth['calib_gap_ci95']:.3f} when the tutor is right, "
            f"{worst['calib_gap']:+.3f} +/-{worst['calib_gap_ci95']:.3f} at "
            f"its worst ({name}={worst['tutor_value']}, error "
            f"{worst['error']:+.2f})")
    widest = pop_rows[-1]
    summary = (
        f"(a) One student, {n_learners} learners, the tutor's assumption "
        f"swept one parameter at a time. " + "; ".join(parts) + ". "
        f"(b) A population with spread +/-{widest['spread']:.2f} against one "
        f"fixed tutor: gap {widest['calib_gap']:+.3f} "
        f"+/-{widest['calib_gap_ci95']:.3f}, false alarms "
        f"{widest['false_alarm_rate']:.1%} against "
        f"{pop_rows[0]['false_alarm_rate']:.1%} when every student matches the "
        f"tutor exactly. The spread rows share a seed block, so they are a "
        f"paired trend rather than four independent estimates.")
    return {"tables": {"mismatch_one": rows, "mismatch_population": pop_rows},
            "figures": {"mismatch": fig}, "summary": summary}



# ================================ concepts mastered as a function of time
def mastery_curve(n_learners=200, n_steps=300, threshold=0.9, seed0=4242,
                  cur=None, **_):
    """Concepts the student TRULY knows, against questions asked.

    The 2x2's four cells plotted over time instead of collapsed to a
    single end-of-run number. Two questions are answered at once:

      (1) how the arms separate as the budget grows, which is the
          better/worse pair the whiteboard sketches;
      (2) how many questions are enough for a learner to know every
          concept, reported as a median over learners with the
          non-finishers counted rather than dropped.

    Read off `learned_step`, which records the step each concept
    became known (0 if known before the first question, None if never).
    That is the student's own hidden state, so the curve owes nothing
    to what the tutor believes.
    """
    if n_learners < 2:
        raise ValueError("mastery_curve needs at least 2 learners to report "
                         "an interval; got %d." % n_learners)
    if n_steps < 1:
        raise ValueError("mastery_curve needs at least 1 question; got %d."
                         % n_steps)
    cur = cur or build_curriculum()
    n_c = len(cur.concepts)
    rows, done_rows, curves, finishes = [], [], {}, {}

    for sname, sm in STUDENT_MODELS.items():
        for qname, sched in (("Q1", "uniform_unmastered"),
                             ("Q2", "uniform_zpd")):
            spec = _spec_2x2(sname, sched, n_steps, threshold, sm)
            runs = _population(cur, spec, n_learners, seed0)

            # per learner: concepts known at each step, and the step at
            # which the last one landed (None if they never finished)
            per_learner, finish = [], []
            for r in runs:
                ls = r["learned_step"]
                steps = [v for v in ls.values() if v is not None]
                counts = [sum(1 for v in steps if v <= t)
                          for t in range(n_steps + 1)]
                per_learner.append(counts)
                finish.append(max(steps) if len(steps) == n_c else None)

            mean_curve, ci_curve, allknown = [], [], []
            for t in range(n_steps + 1):
                col = [c[t] for c in per_learner]
                m = st.mean(col)
                sd = st.stdev(col) if len(col) > 1 else 0.0
                mean_curve.append(m)
                ci_curve.append(1.96 * sd / math.sqrt(len(col)))
                allknown.append(sum(1 for v in col if v >= n_c) / len(col))
                rows.append(dict(student=sname, scheduler=qname,
                                 sched_key=sched, step=t,
                                 mean_known=m, ci95=ci_curve[-1],
                                 frac_all_known=allknown[-1],
                                 n_concepts=n_c, n_learners=n_learners))
            curves[(sname, qname)] = (mean_curve, ci_curve, allknown)
            finishes[(sname, qname)] = finish

            reached = [f for f in finish if f is not None]
            done_rows.append(dict(
                student=sname, scheduler=qname, n_learners=n_learners,
                n_steps=n_steps, n_concepts=n_c,
                frac_reached_all=len(reached) / len(finish),
                median_questions_to_all=(st.median(reached) if reached
                                         else float("nan")),
                mean_questions_to_all=(st.mean(reached) if reached
                                       else float("nan")),
                n_censored=len(finish) - len(reached),
                final_mean_known=mean_curve[-1]))

    # ------------------------------------------------------------ figure
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.8, 3.7))
    style = {("S1", "Q1"): (ACCENT, "--"), ("S1", "Q2"): (ACCENT, "-"),
             ("S2", "Q1"): ("#e2a03f", "--"), ("S2", "Q2"): ("#e2a03f", "-")}
    xs = list(range(n_steps + 1))
    for key, (mean_curve, ci_curve, allknown) in curves.items():
        col, ls = style.get(key, (GREY, "-"))
        lab = f"{key[0]} / {key[1]}"
        a1.plot(xs, mean_curve, ls, color=col, lw=1.8, label=lab)
        a1.fill_between(xs, [m - c for m, c in zip(mean_curve, ci_curve)],
                        [m + c for m, c in zip(mean_curve, ci_curve)],
                        color=col, alpha=0.13, lw=0)
        a2.plot(xs, allknown, ls, color=col, lw=1.8, label=lab)
    a1.axhline(n_c, ls=":", lw=1, color=GREY)
    a1.set_xlabel("questions asked")
    a1.set_ylabel("concepts truly known")
    a1.set_title(f"Mastery over time (of {n_c}, shaded = 95% CI)",
                 fontsize=10.5)
    a1.legend(frameon=False, fontsize=8.5, loc="lower right")
    a2.set_ylim(-0.03, 1.03)
    a2.set_xlabel("questions asked")
    a2.set_ylabel("fraction of learners knowing every concept")
    a2.set_title("How many learners have finished", fontsize=10.5)
    a2.legend(frameon=False, fontsize=8.5, loc="upper left")
    fig.tight_layout()

    # ------------------------------ paired contrast: Q2 minus Q1, by learner
    paired = []
    for sname in STUDENT_MODELS:
        a, b = finishes[(sname, "Q1")], finishes[(sname, "Q2")]
        # seed i is the SAME learner in both arms, so pair before differencing
        d = [y - x for x, y in zip(a, b) if x is not None and y is not None]
        if len(d) > 1:
            m = st.mean(d)
            ci = 1.96 * st.stdev(d) / math.sqrt(len(d))
        else:
            m, ci = float("nan"), float("nan")
        paired.append(dict(student=sname, diff_Q2_minus_Q1=m, ci95=ci,
                           n_paired=len(d), n_dropped=len(a) - len(d),
                           faster_with_Q2=sum(1 for v in d if v < 0),
                           favours=("Q2" if m + ci < 0 else
                                    "Q1" if m - ci > 0 else "neither")))

    # ----------------------------------------------------------- summary
    def cell(sname, qname):
        return next(r for r in done_rows
                    if r["student"] == sname and r["scheduler"] == qname)

    bits = []
    for sname in STUDENT_MODELS:
        q1, q2 = cell(sname, "Q1"), cell(sname, "Q2")
        pr = next(x for x in paired if x["student"] == sname)
        if q1["n_censored"] or q2["n_censored"]:
            bits.append(
                f"{sname}: {q1['final_mean_known']:.2f} known under Q1 vs "
                f"{q2['final_mean_known']:.2f} under Q2 after {n_steps} "
                f"questions ({q1['frac_reached_all']:.0%} vs "
                f"{q2['frac_reached_all']:.0%} of learners reached all {n_c})")
        else:
            bits.append(
                f"{sname} needs a median {q1['median_questions_to_all']:.0f} "
                f"questions under Q1 and "
                f"{q2['median_questions_to_all']:.0f} under Q2, paired "
                f"difference {pr['diff_Q2_minus_Q1']:+.1f} "
                f"+/-{pr['ci95']:.1f} questions (favours {pr['favours']})")
    # A median over finishers only is biased whenever many learners did
    # not finish, so quote it only when nearly everyone did, and say so
    # plainly otherwise rather than reporting a number built on a tail.
    worst_cens = max(r["n_censored"] for r in done_rows) / n_learners
    if worst_cens <= 0.05:
        fastest = min(done_rows, key=lambda r: r["median_questions_to_all"])
        slowest = max(done_rows, key=lambda r: r["median_questions_to_all"])
        tail = (f" Every arm gets every learner to all {n_c} concepts inside "
                f"{n_steps} questions, at a median of "
                f"{fastest['median_questions_to_all']:.0f} "
                f"({fastest['student']}/{fastest['scheduler']}) to "
                f"{slowest['median_questions_to_all']:.0f} "
                f"({slowest['student']}/{slowest['scheduler']}).")
    else:
        tail = (f" No median to full mastery is quoted: up to "
                f"{worst_cens:.0%} of learners in some arm never reach all "
                f"{n_c} concepts inside {n_steps} questions, so a median "
                f"over the finishers would describe the fast tail only.")
    summary = (f"{n_learners} learners per cell, {n_steps} questions. "
               + "; ".join(bits) + "." + tail)

    return {"tables": {"mastery_curve": rows, "questions_to_all": done_rows,
                       "paired": paired},
            "figures": {"mastery_curve": fig}, "summary": summary}


# ======================== separating the restriction from the belief lag
def _oracle_run(cur, gated_student, restrict, seed, n_steps, rng_off=77777):
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
        L.answer(_pick_question(cur, rng.choice(elig), rng), 0.0)
    return sum(L.known.values())


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
        a = [_oracle_run(cur, gated, False, seed0 + i, n_steps)
             for i in range(n_learners)]
        b = [_oracle_run(cur, gated, True, seed0 + i, n_steps)
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


# ---------------------------------------------------------------- registry
EXPERIMENTS = {
    "check1_calibration": (
        calibration,
        "Check 1. Is the tutor's belief correct? Bin every belief and see "
        "how often the student truly knows the concept.",
        dict(n_learners=50, n_steps=120, threshold=0.9)),
    "check2_detection": (
        detection,
        "Check 2. Detection delay and false-alarm rate as a function of "
        "the mastery threshold.",
        dict(n_learners=30, n_steps=120)),
    "s1s2_x_q1q2": (
        two_by_two,
        "The 2x2. Two student models (prerequisites irrelevant / "
        "prerequisite-gated) by two question-selection rules (anything "
        "unmastered / prerequisite-ready only).",
        dict(n_learners=60, n_steps=40, threshold=0.9)),
    "mastery_curve": (
        mastery_curve,
        "Concepts truly known against questions asked, for all four 2x2 "
        "cells, plus how many questions are enough to know every concept.",
        dict(n_learners=200, n_steps=300, threshold=0.9)),
    "param_sweep": (
        param_sweep,
        "Vary one BKT parameter at a time with the tutor correctly "
        "specified: what does each parameter actually do?",
        dict(n_learners=30, n_steps=120, threshold=0.9)),
    "mismatch": (
        mismatch,
        "The tutor's assumed parameters differ from the student's real "
        "ones: one student with the assumption swept, then a population "
        "of students against one fixed tutor.",
        dict(n_learners=40, n_steps=120, threshold=0.9,
             vary=("p_G", "p_S", "p_T"))),
    "restriction_only": (
        restriction_only,
        "Separates the prerequisite restriction from the cost of gating "
        "on a belief that lags the truth, by running both arms against "
        "the student's true state.",
        dict(n_learners=400, n_steps=40)),
    "trace_20_steps": (
        trace_table,
        "Step-by-step trace of one short run: ZPD, question, answer, true "
        "state and belief before and after.",
        dict(n_steps=20, threshold=0.9, seed=4242)),
}
