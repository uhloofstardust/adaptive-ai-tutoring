"""Tracer bake-off: which student model tracks the learner best?

The simulator gives something no real dataset can: the learner's TRUE
mastery at every step. That makes two very different questions
answerable side by side.

    1. Which model predicts the next answer best?
       Measured by AUC and log loss on the observed answers, using the
       predict-before-update rule. This is computable on real data.

    2. Which model's belief is closest to the truth?
       Measured by mean absolute error against hidden mastery. This is
       computable ONLY in simulation.

If the two rankings agree, that is evidence that AUC on real logs is a
trustworthy proxy for tracking the actual learner, which is the
assumption every knowledge-tracing paper makes and almost none can
check. If they disagree, that is worth knowing before trusting AUC.

Method: one interaction log is generated with a selector that does not
consult any model (random, round-robin), so the data is identical for
every tracer. Each tracer is then replayed through that same stream of
observations. Comparisons are therefore exactly paired, per student.

    python tracer_bakeoff.py
"""

import math
import statistics
from typing import Dict, List

from student_simulator import (BKTTracer, SimConfig, StudentModel,
                               _sign_test_p, build_concepts,
                               run_experiment)


# --------------------------------------------------------------------
# Extra tracers to compete against BKT
# --------------------------------------------------------------------
class EmpiricalTracer(StudentModel):
    """Running fraction correct per concept, smoothed toward a prior.

    No hidden state, no dynamics, no forgetting: the floor that any
    real student model must beat to justify its machinery.
    """

    def __init__(self, concept_ids, prior=0.25, strength=2.0):
        self.prior, self.strength = prior, strength
        self.n = {c: 0 for c in concept_ids}
        self.k = {c: 0 for c in concept_ids}

    def observe(self, concept_id, correct, now_h):
        self.n[concept_id] += 1
        self.k[concept_id] += int(correct)

    def estimate(self, concept_id, now_h):
        # mastery implied by the smoothed accuracy, inverting a
        # 4-option MCQ guess rate so the scale is comparable
        p = ((self.k[concept_id] + self.prior * self.strength) /
             (self.n[concept_id] + self.strength))
        return max(0.0, min(1.0, (p - 0.25) / 0.75))

    def predict_correct(self, concept_id, now_h):
        return ((self.k[concept_id] + self.prior * self.strength) /
                (self.n[concept_id] + self.strength))


class ConstantTracer(StudentModel):
    """Predicts the same number always. The absolute floor: any model
    scoring near this one has learned nothing from the answers."""

    def __init__(self, concept_ids, value=0.5):
        self.value = value

    def observe(self, concept_id, correct, now_h):
        pass

    def estimate(self, concept_id, now_h):
        return self.value

    def predict_correct(self, concept_id, now_h):
        return self.value


def predict_correct(tracer, cid, t):
    if hasattr(tracer, "predict_correct"):
        return tracer.predict_correct(cid, t)
    m = tracer.estimate(cid, t)
    return m * (1 - tracer.p_S) + (1 - m) * tracer.p_G


# --------------------------------------------------------------------
# Metrics (standard library only)
# --------------------------------------------------------------------
def auc(y: List[int], p: List[float]) -> float:
    """Rank-based AUC with average ranks for ties: the probability that
    a random correct answer is scored above a random wrong one."""
    n1 = sum(y)
    n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return float("nan")
    pairs = sorted(zip(p, y))
    ranks = [0.0] * len(pairs)
    i = 0
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    s = sum(r for r, (_, yy) in zip(ranks, pairs) if yy == 1)
    return (s - n1 * (n1 + 1) / 2.0) / (n1 * n0)


def log_loss(y: List[int], p: List[float], eps=1e-9) -> float:
    tot = 0.0
    for yy, pp in zip(y, p):
        pp = min(1 - eps, max(eps, pp))
        tot -= math.log(pp) if yy == 1 else math.log(1 - pp)
    return tot / len(y)


# --------------------------------------------------------------------
# Replay
# --------------------------------------------------------------------
def replay(log: List[dict], factory, concept_ids) -> dict:
    """Run one tracer through an existing interaction log.

    The tracer sees only (concept_id, correct, time), exactly as in a
    live run. True mastery from the log is used for scoring only.
    """
    by_student, finals = {}, {}
    for r in log:
        if r.get("_final"):
            finals[r["student_id"]] = r
        else:
            by_student.setdefault(r["student_id"], []).append(r)

    per_student, y_all, p_all = {}, [], []
    for sid, rows in by_student.items():
        tracer = factory(concept_ids)
        y, p, abs_err = [], [], []
        for r in rows:
            cid, t = r["concept_id"], r["t_hours"]
            p.append(predict_correct(tracer, cid, t))
            y.append(r["correct"])
            abs_err.append(abs(tracer.estimate(cid, t) -
                               r["true_mastery_before"]))
            tracer.observe(cid, bool(r["correct"]), t)

        f = finals.get(sid)
        final_mae = float("nan")
        if f:
            tf = f["t_hours"]
            true = f["_final_true"]
            final_mae = statistics.mean(
                abs(tracer.estimate(c, tf) - true[c]) for c in true)

        per_student[sid] = {
            "auc": auc(y, p),
            "log_loss": log_loss(y, p),
            "mae_steps": statistics.mean(abs_err),
            "mae_final": final_mae,
        }
        y_all.extend(y)
        p_all.extend(p)

    return {
        "auc_pooled": auc(y_all, p_all),
        "log_loss": log_loss(y_all, p_all),
        "mae_steps": statistics.mean(v["mae_steps"]
                                     for v in per_student.values()),
        "mae_final": statistics.mean(v["mae_final"]
                                     for v in per_student.values()),
        "per_student": per_student,
    }


def paired(a: dict, b: dict, metric: str, lower_is_better: bool):
    """Per-student difference between two tracers on identical logs."""
    ids = sorted(set(a["per_student"]) & set(b["per_student"]))
    diffs = [b["per_student"][i][metric] - a["per_student"][i][metric]
             for i in ids]
    if lower_is_better:
        wins = sum(1 for d in diffs if d < 0)
        losses = sum(1 for d in diffs if d > 0)
    else:
        wins = sum(1 for d in diffs if d > 0)
        losses = sum(1 for d in diffs if d < 0)
    return {"n": len(diffs), "mean_diff": statistics.mean(diffs),
            "wins": wins, "losses": losses,
            "p_sign": _sign_test_p(wins, wins + losses)}


# --------------------------------------------------------------------
def bakeoff(selector="random", n_students=20, n_sessions=12,
            items_per_session=40, base_seed=2026,
            sweep=(0.0, 0.02, 0.05, 0.10, 0.15, 0.25)):
    cfg = SimConfig()
    concepts = build_concepts()
    cids = list(concepts)

    # The selector must not consult a model, or the log would differ
    # per tracer and the comparison would stop being paired.
    assert selector in ("random", "round_robin"), \
        "use a model-free selector so every tracer sees the same data"
    log = run_experiment(selector, concepts, cfg, n_students=n_students,
                         n_sessions=n_sessions,
                         items_per_session=items_per_session,
                         base_seed=base_seed)

    tracers = {"constant 0.5": lambda c: ConstantTracer(c),
               "empirical mean": lambda c: EmpiricalTracer(c)}
    for f in sweep:
        label = "BKT classical" if f == 0.0 else f"BKT forget f={f:.2f}"
        tracers[label] = (lambda c, f=f: BKTTracer(c, forget_per_day=f))

    results = {name: replay(log, fac, cids)
               for name, fac in tracers.items()}

    print(f"\n=== tracer bake-off on the '{selector}' log "
          f"({n_students} students, "
          f"{n_sessions * items_per_session} answers each) ===")
    print(f"{'tracer':22s} {'AUC':>7s} {'log loss':>9s} "
          f"{'MAE steps':>10s} {'MAE final':>10s}")
    for name, r in results.items():
        print(f"{name:22s} {r['auc_pooled']:>7.4f} {r['log_loss']:>9.4f} "
              f"{r['mae_steps']:>10.4f} {r['mae_final']:>10.4f}")

    best_auc = max(results, key=lambda n: results[n]["auc_pooled"])
    best_mae = min(results, key=lambda n: results[n]["mae_steps"])
    print(f"\n  best by AUC (measurable on real data): {best_auc}")
    print(f"  best by MAE vs hidden truth           : {best_mae}")
    print("  the two rankings "
          f"{'AGREE' if best_auc == best_mae else 'DISAGREE'}")

    # what forgetting rate did the data imply, and what was the truth?
    fs = [f for f in sweep if f > 0]
    if fs:
        labels = {f: f"BKT forget f={f:.2f}" for f in fs}
        best_f = min(fs, key=lambda f: results[labels[f]]["mae_steps"])
        # simulator: half life 6 days at average difficulty (~0.30),
        # scaled by (1.3 - 0.6*difficulty)
        hl_days = cfg.forget_half_life_days * (1.3 - 0.6 * 0.30)
        true_f = 1 - 0.5 ** (1.0 / hl_days)
        print(f"\n  recovered forgetting rate: {best_f:.2f} per day")
        print(f"  simulator's actual rate   : {true_f:.2f} per day "
              f"(half-life {hl_days:.1f} days at average difficulty)")

        cls, fgt = results["BKT classical"], results[labels[best_f]]
        for metric, lower in (("mae_steps", True), ("auc", False)):
            d = paired(cls, fgt, metric, lower)
            print(f"  paired {metric:10s} forgetting vs classical: "
                  f"mean {d['mean_diff']:+.4f}, better for "
                  f"{d['wins']}/{d['n']} students, sign p {d['p_sign']:.3f}")
    return results


if __name__ == "__main__":
    bakeoff("random")
    bakeoff("round_robin")
