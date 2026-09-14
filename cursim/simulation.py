"""The tutoring loop and the metrics.

Sessions, not a flat stream: practice happens in daily sessions with a
gap, so concepts decay between them. Retention is then measured after
a further delay with no practice at all, which is the metric that
separates a tutor that manages forgetting from one that does not.
Final-day mastery flatters every scheduler equally; retention does not.
"""

import random
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .curriculum import Curriculum
from .learner import Learner, LearnerProfile, PROFILES, SimConfig, LEARNERS
from .mastery import make_model
from .schedulers import SCHEDULERS, zpd


@dataclass
class RunSpec:
    """One experimental condition."""
    scheduler: str = "curriculum_tutor"
    mastery_model: str = "binary"
    learner: str = "continuous"          # key into LEARNERS
    threshold: Optional[float] = None    # mastery threshold for the tutor
    prereq_gated_pT: bool = False        # BKT student only: next step in the mail
    bkt_params: Optional[dict] = None    # override params.BKT_PARAMS for BOTH sides
    profile: str = "average"
    learner_forgets: bool = True
    model_forget_per_day: float = 0.10
    n_sessions: int = 20
    questions_per_session: int = 25
    gap_hours: float = 24.0
    retention_days: float = 3.0
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
    LearnerCls = LEARNERS[spec.learner][0]
    if spec.learner == "bkt":
        learner = LearnerCls(cur, profile, seed=seed, cfg=cfg,
                             prereq_gated_pT=spec.prereq_gated_pT,
                             params=spec.bkt_params)
    else:
        learner = LearnerCls(cur, profile, seed=seed, cfg=cfg,
                             forgetting=spec.learner_forgets)
    mkw = {}
    if spec.mastery_model == "continuous_forget":
        mkw["forget_per_day"] = spec.model_forget_per_day
    if spec.threshold is not None:
        mkw["threshold"] = spec.threshold
    if spec.bkt_params:
        mkw.update(spec.bkt_params)
    model = make_model(spec.mastery_model, cur.ids(), **mkw)
    sched = SCHEDULERS[spec.scheduler]()
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
    ret_h = end_h + spec.retention_days * 24.0
    accs = [r["correct"] for r in log] if keep_log else None

    return {
        "seed": seed,
        "final_mastery": learner.mean_mastery(end_h),
        "final_learned": learner.n_learned(end_h),
        "retained_mastery": learner.mean_mastery(ret_h),
        "retained_learned": learner.n_learned(ret_h),
        # concepts still usable after the break. Mean mastery rewards
        # spreading thin (many concepts at 0.5); a threshold does not.
        "retained_usable": learner.n_learned(ret_h, 0.50),
        "coverage": sum(1 for v in learner.exposures.values() if v > 0),
        "max_tier_reached": max(
            (cur.concepts[c].tier
             for c, v in learner.snapshot(end_h).items()
             if v >= cfg.learned_threshold), default=-1),
        "curve": curve,
        "snapshot_end": learner.snapshot(end_h),
        "accuracy": statistics.mean(accs) if accs else None,
        "log": log,
        "trace": trace,
        "learned_step": dict(getattr(learner, "learned_step", {})),
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


def paired(a: RunResult, b: RunResult, key: str) -> dict:
    """b minus a, learner by learner (identical seeds)."""
    diffs = [rb[key] - ra[key]
             for ra, rb in zip(a.per_learner, b.per_learner)]
    wins = sum(1 for d in diffs if d > 0)
    losses = sum(1 for d in diffs if d < 0)
    return {"mean_diff": statistics.mean(diffs),
            "sd": statistics.stdev(diffs) if len(diffs) > 1 else 0.0,
            "wins": wins, "losses": losses, "n": len(diffs),
            "p_sign": sign_test(wins, wins + losses)}


def sign_test(k: int, n: int) -> float:
    """Two-sided sign test, standard library only."""
    import math
    if n == 0:
        return 1.0
    probs = [math.comb(n, i) * 0.5 ** n for i in range(n + 1)]
    obs = probs[k]
    return min(1.0, sum(p for p in probs if p <= obs + 1e-12))


def table(results: Dict[str, RunResult], keys=("final_mastery",
                                               "retained_mastery",
                                               "final_learned",
                                               "retained_learned")):
    head = f"{'condition':28s}" + "".join(f"{k:>18s}" for k in keys)
    print(head)
    print("-" * len(head))
    for name, r in results.items():
        row = f"{name:28s}"
        for k in keys:
            row += f"{r.mean(k):>13.3f} ±{r.sd(k):>3.2f}"
        print(row)
