"""The tutoring loop and the metrics.

Sessions, not a flat stream: practice happens in daily sessions with a
gap, so concepts decay between them. Retention is then measured after
a further delay with no practice at all, which is the metric that
separates a tutor that manages forgetting from one that does not.
Final-day mastery flatters every scheduler equally; retention does not.
"""

import dataclasses
import random
import statistics
from dataclasses import dataclass, field
from typing import List, Optional

from .curriculum import Curriculum
from .students import (BKTLearner, LearnerProfile, PROFILES,
                       SimConfig, LEARNERS, learner_kwargs)
from .mastery import make_model
from .schedulers import SCHEDULERS, zpd


@dataclass
class RunSpec:
    """One experimental condition."""
    scheduler: str = "curriculum_tutor"
    scheduler_params: Optional[dict] = None   # keyword arguments for it
    mastery_model: str = "binary"
    learner: str = "continuous"          # key into LEARNERS
    threshold: Optional[float] = None    # mastery threshold for the tutor
    prereq_gated_pT: bool = False        # BKT student only: prereq-gated p(T)
    bkt_params: Optional[dict] = None    # override for BOTH sides at once
    # ...or set the two sides apart, which is what a misspecification
    # study needs. Either overrides bkt_params on its own side.
    student_params: Optional[dict] = None
    tutor_params: Optional[dict] = None
    pT_low: Optional[float] = None       # S2 only: p(T) while prereqs unmet
    profile: str = "average"
    # replace fields of the named profile for this run only, e.g.
    # {"forget_half_life_days": 8}; the shared PROFILES are never touched
    profile_overrides: Optional[dict] = None
    learner_forgets: bool = True
    model_forget_per_day: float = 0.10
    n_sessions: int = 20
    questions_per_session: int = 25
    gap_hours: float = 24.0
    retention_days: float = 3.0
    # extra idle periods (days) at which to measure what is still usable,
    # all from the same run: result["usable_after"][days]
    break_days: tuple = ()
    label: str = ""

    def name(self) -> str:
        return self.label or f"{self.scheduler}/{self.mastery_model}"


@dataclass
class RunResult:
    spec: RunSpec
    per_learner: List[dict] = field(default_factory=list)
    log: List[dict] = field(default_factory=list)

    def mean(self, key: str) -> float:
        return statistics.mean(r[key] for r in self.per_learner)

    def sd(self, key: str) -> float:
        vals = [r[key] for r in self.per_learner]
        return statistics.stdev(vals) if len(vals) > 1 else 0.0


def run_one(cur: Curriculum, spec: RunSpec, seed: int,
            cfg: Optional[SimConfig] = None, keep_log=False,
            keep_trace=False) -> dict:
    """One learner under one condition.

    keep_trace records, for every step, everything the dry-run view and
    the sanity checks need: the ZPD, what was asked, the answer, and the
    tutor's belief and the student's true state before and after.
    """
    cfg = cfg or SimConfig()
    profile: LearnerProfile = PROFILES[spec.profile]
    if spec.profile_overrides:
        profile = dataclasses.replace(profile, **spec.profile_overrides)
    LearnerCls, _, *rest = LEARNERS[spec.learner]
    if LearnerCls is BKTLearner:
        kw = learner_kwargs(spec.learner)      # what the registry says
        if spec.prereq_gated_pT:
            kw["prereq_gated_pT"] = True
        if spec.pT_low is not None:             # the spec may override it
            kw["pT_low"] = spec.pT_low
        kw.pop("params", None)
        learner = LearnerCls(cur, profile, seed=seed, cfg=cfg,
                             params=spec.student_params or spec.bkt_params,
                             **kw)
    else:
        learner = LearnerCls(cur, profile, seed=seed, cfg=cfg,
                             forgetting=spec.learner_forgets)
    mkw = {}
    if spec.mastery_model == "continuous_forget":
        mkw["forget_per_day"] = spec.model_forget_per_day
    if spec.threshold is not None:
        mkw["threshold"] = spec.threshold
    tp = spec.tutor_params or spec.bkt_params
    if tp:
        mkw.update(tp)
    if spec.mastery_model == "oracle":
        mkw["truth"] = learner.true_mastery
    model = make_model(spec.mastery_model, cur.ids(), **mkw)
    sched = SCHEDULERS[spec.scheduler](**(spec.scheduler_params or {}))
    # separate stream so the learner's randomness does not shift when
    # the scheduler changes
    rng = random.Random(seed + 77777)

    now_h, last_qid, log, trace = 0.0, None, [], []
    curve, step = [], 0
    for s in range(spec.n_sessions):
        for _ in range(spec.questions_per_session):
            step += 1
            z = zpd(cur, model, now_h) if keep_trace else None
            q = sched.select(cur, model, now_h, rng, last_qid)
            if q is None:           # the scheduler asks nothing this slot
                now_h += 1.0 / 60.0
                continue
            b_before = model.belief(q.concept_id, now_h)
            res = learner.answer(q, now_h)
            model.observe(q.concept_id, res["correct"], now_h)
            sched.observe(q.concept_id, res["correct"], now_h)
            if keep_log:
                log.append({"session": s, "t_hours": now_h, **res})
            if keep_trace:
                trace.append({
                    "step": step, "session": s, "t_hours": now_h,
                    "zpd": z, "concept": q.concept_id, "qid": q.qid,
                    "correct": res["correct"],
                    "true_before": res.get("state_before",
                                           res["mastery_before"]),
                    "true_after": res.get("state_after",
                                          res["mastery_after"]),
                    "belief_before": b_before,
                    "belief_after": model.belief(q.concept_id, now_h),
                    "mastered_after": model.is_mastered(q.concept_id, now_h),
                    "beliefs": {c: model.belief(c, now_h) for c in cur.ids()},
                    "truth": learner.snapshot(now_h),
                })
            last_qid = q.qid
            now_h += 1.0 / 60.0
        curve.append(learner.mean_mastery(now_h))
        now_h += spec.gap_hours

    end_h = now_h
    final_mastery = learner.mean_mastery(end_h)
    final_learned = learner.n_learned(end_h)
    snapshot_end = learner.snapshot(end_h)      # before any idle decay
    # Idle periods are read in increasing order: the learner applies decay
    # lazily, so asking about an earlier time after a later one would
    # return the later, more decayed state.
    after = {}
    for d in sorted({*spec.break_days, spec.retention_days}):
        t = end_h + d * 24.0
        after[d] = {"mastery": learner.mean_mastery(t),
                    "learned": learner.n_learned(t),
                    "usable": learner.n_learned(t, 0.50)}
    ret = after[spec.retention_days]
    accs = [r["correct"] for r in log] if keep_log else None

    return {
        "seed": seed,
        "final_mastery": final_mastery,
        "final_learned": final_learned,
        "retained_mastery": ret["mastery"],
        "retained_learned": ret["learned"],
        # concepts still usable after the break. Mean mastery rewards
        # spreading thin (many concepts at 0.5); a threshold does not.
        "retained_usable": ret["usable"],
        "usable_after": {d: v["usable"] for d, v in after.items()},
        "coverage": sum(1 for v in learner.exposures.values() if v > 0),
        "max_tier_reached": max(
            (cur.concepts[c].tier
             for c, v in snapshot_end.items()
             if v >= cfg.learned_threshold), default=-1),
        "curve": curve,
        "snapshot_end": snapshot_end,
        "accuracy": statistics.mean(accs) if accs else None,
        "log": log,
        "trace": trace,
        "learned_step": dict(getattr(learner, "learned_step", {})),
        "sched_stats": sched.stats() if hasattr(sched, "stats") else {},
    }


def run_condition(cur: Curriculum, spec: RunSpec, n_learners=30,
                  base_seed=4242, cfg=None, keep_log=False) -> RunResult:
    """Run one condition over a population.

    Every condition uses the same base_seed, so learner i is the same
    person in every condition and comparisons are paired.
    """
    out = RunResult(spec=spec)
    for i in range(n_learners):
        r = run_one(cur, spec, seed=base_seed + i, cfg=cfg,
                    keep_log=keep_log)
        if keep_log:
            out.log.extend({"learner": i, **row} for row in r.pop("log"))
        else:
            r.pop("log")
        out.per_learner.append(r)
    return out
