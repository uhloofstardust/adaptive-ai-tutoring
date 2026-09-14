"""Checks for the plain-BKT sanity setup. Run: python3 test_sanity.py"""
from cursim.curriculum import build_curriculum
from cursim.simulation import RunSpec, run_one
from cursim.sanity import calibration, detection, trace_table
from cursim.params import BKT_PARAMS

cur = build_curriculum()
passed = 0


def check(cond, msg):
    global passed
    assert cond, msg
    passed += 1
    print(f"  ok  {msg}")


def spec(**kw):
    base = dict(scheduler="curriculum_tutor", mastery_model="bkt", learner="bkt",
                threshold=0.9, n_sessions=1, questions_per_session=300,
                gap_hours=0.0, retention_days=0.0)
    base.update(kw)
    return RunSpec(**base)


print("1. no guess, no slip: the answer reveals the state exactly")
p = dict(BKT_PARAMS, p_G=0.0, p_S=0.0)
r = run_one(cur, spec(bkt_params=p), seed=1, keep_trace=True)
check(all(t["true_before"] for t in r["trace"] if t["correct"]),
      "every correct answer came from a concept the student truly knew")
check(all(not t["true_before"] for t in r["trace"] if not t["correct"]),
      "every wrong answer came from a concept the student did not know")
check(all(abs(t["belief_after"] - (1.0 if t["correct"] else p["p_T"])) < 1e-12
          for t in r["trace"]),
      "belief after update is exactly 1 (correct) or p_T (wrong)")

print("2. no guess, no slip, learn for certain: belief equals truth every step")
p = dict(BKT_PARAMS, p_G=0.0, p_S=0.0, p_T=1.0, p_L0=0.0)
r = run_one(cur, spec(bkt_params=p), seed=2, keep_trace=True)
check(all(t["belief_after"] == 1.0 and t["true_after"] is True for t in r["trace"]),
      "after any question the concept is known and the tutor is certain of it")
check(all(t["beliefs"][c] == float(t["truth"][c]) for t in r["trace"]
          for c in t["beliefs"]),
      "tutor belief == true state for every concept at every step")

print("3. learned_step agrees with the trace")
r = run_one(cur, spec(), seed=3, keep_trace=True)
ls = r["learned_step"]
for t in r["trace"]:
    for c, v in t["truth"].items():
        exp = ls[c] is not None and ls[c] <= t["step"]
        assert bool(v) == exp, (c, t["step"], v, ls[c])
check(True, "true state at step t == (learned_step <= t) for all concepts")
check(all(ls[c] == 0 for c in ls if r["trace"][0]["truth"][c] and
          not any(t["concept"] == c for t in r["trace"][:1])),
      "concepts known before any question have learned_step 0")

print("4. the scheduler only asks from the ZPD")
check(all(t["concept"] in t["zpd"] for t in r["trace"] if t["zpd"]),
      "asked concept is in the ZPD whenever the ZPD is non-empty")
check(all(all(t["beliefs"][q] >= 0.9 for q in cur.concepts[c].prereqs)
          for t in r["trace"] for c in t["zpd"]),
      "every ZPD concept has all prerequisites believed mastered")

print("5. check 1 is calibrated with the true model")
out = calibration(n_learners=100, n_steps=400, cur=cur)
big = [x for x in out["tables"]["calibration"] if x["n"] >= 500]
check(all(abs(x["gap"]) < 0.05 for x in big),
      f"|frac known - mean belief| < 0.05 in all {len(big)} bins with n>=500")
allb = [x for x in out["tables"]["calibration"] if x["n"]]
mean_b = sum(x["mean_belief"] * x["n"] for x in allb) / sum(x["n"] for x in allb)
mean_t = sum(x["frac_truly_known"] * x["n"] for x in allb) / sum(x["n"] for x in allb)
check(abs(mean_b - mean_t) < 0.01,
      f"overall: mean belief {mean_b:.4f} vs fraction known {mean_t:.4f}")

print("6. check 2 moves the right way with the threshold")
out = detection(n_learners=15, n_steps=300, thresholds=(0.6, 0.8, 0.95), cur=cur)
rows = out["tables"]["detection"]
check(rows[0]["false_alarm_rate"] > rows[-1]["false_alarm_rate"],
      "false alarms fall as the threshold rises")
check(rows[0]["delay_on_concept_mean"] < rows[-1]["delay_on_concept_mean"],
      "detection delay (on concept) grows as the threshold rises")
check(all(0 <= x["false_alarm_rate"] <= 1 and x["delay_mean"] >= 0 for x in rows),
      "rates in [0,1], delays non-negative")
check(all(abs(x["false_alarm_rate"] - x["predicted_false_alarm_rate"]) < 0.04
          for x in rows),
      "measured false-alarm rate matches what calibration predicts (within 0.04)")
check(all(x["unresolved"] == x["unresolved_learned_late"] +
          x["unresolved_never_reached"] + x["unresolved_asked_not_crossed"]
          for x in rows),
      "unresolved concepts fully decomposed by cause")

print("6b. overall delay excludes concepts known before the run")
from cursim.sanity import _per_concept, sanity_spec, _population
recs = [x for r in _population(cur, sanity_spec(threshold=0.9, n_steps=300), 10)
        for x in _per_concept(r, 0.9)]
check(all(x["delay_questions"] is None for x in recs if x["known_at_start"]),
      "no 'questions overall' delay for concepts with learned_step == 0")
check(any(x["delay_on_concept"] is not None for x in recs if x["known_at_start"]),
      "but 'questions on that concept' still counts them")

print("6c. partial parameter override merges with the shared defaults")
r = run_one(cur, spec(bkt_params={"p_T": 0.5}), seed=9, keep_trace=True)
check(len(r["trace"]) == 300, "run with a partial bkt_params dict does not crash")

print("7. the 20-step trace has every column the mail asks for")
out = trace_table(n_steps=20, cur=cur)
cols = set(out["tables"]["trace"][0])
need = {"step", "zpd", "asked", "answer", "true_before", "true_after",
        "belief_before", "belief_after"}
check(need <= cols, f"trace has {sorted(need)}")
check(len(out["tables"]["trace"]) == 20, "exactly 20 rows")

print(f"\nALL {passed} CHECKS PASSED")
