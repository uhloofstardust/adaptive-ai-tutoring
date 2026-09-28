"""Checks for the plain-BKT sanity setup. Run: python3 test_sanity.py"""
from cursim.curriculum import build_curriculum
from cursim.simulation import RunSpec, run_one
from cursim.sanity import calibration, detection, trace_table
import statistics as st

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

print("7. the 20-step trace has every required column")
out = trace_table(n_steps=20, cur=cur)
cols = set(out["tables"]["trace"][0])
need = {"step", "zpd", "asked", "answer", "true_before", "true_after",
        "belief_before", "belief_after"}
check(need <= cols, f"trace has {sorted(need)}")
check(len(out["tables"]["trace"]) == 20, "exactly 20 rows")

print("8. Q1 reaches outside the ZPD, Q2 never does")
from cursim.schedulers import SCHEDULERS
r1 = run_one(cur, spec(scheduler="uniform_unmastered"), seed=11, keep_trace=True)
r2 = run_one(cur, spec(scheduler="uniform_zpd"), seed=11, keep_trace=True)
out1 = sum(1 for t in r1["trace"] if t["zpd"] and t["concept"] not in t["zpd"])
out2 = sum(1 for t in r2["trace"] if t["zpd"] and t["concept"] not in t["zpd"])
check(out1 > 0, f"Q1 asked outside the ZPD {out1} times")
check(out2 == 0, "Q2 never asked outside the ZPD")
check(all(not t["zpd"] or t["concept"] in t["zpd"] for t in r2["trace"]),
      "every Q2 pick was prerequisite-ready")

print("9. S2 learns slower than S1 when prerequisites are unmet")
from cursim.params import STUDENT_MODELS
def s_spec(learner, **kw):
    pr = dict(BKT_PARAMS)
    return RunSpec(scheduler="uniform_unmastered", mastery_model="bkt",
                   learner=learner, threshold=0.9,
                   student_params=pr, tutor_params=pr, n_sessions=1,
                   questions_per_session=60, gap_hours=0.0, retention_days=0.0,
                   **kw)
k1 = [sum(run_one(cur, s_spec("bkt"), seed=900 + i, keep_trace=True)
          ["trace"][-1]["truth"].values()) for i in range(20)]
k2 = [sum(run_one(cur, s_spec("bkt_prereq"), seed=900 + i, keep_trace=True)
          ["trace"][-1]["truth"].values()) for i in range(20)]
check(st.mean(k2) < st.mean(k1),
      f"under Q1, S2 learns less than S1 ({st.mean(k2):.2f} vs {st.mean(k1):.2f})")

print("10. student and tutor parameters can differ")
sp = RunSpec(scheduler="uniform_zpd", mastery_model="bkt", learner="bkt",
             threshold=0.9, n_sessions=1, questions_per_session=40,
             gap_hours=0.0, retention_days=0.0,
             student_params=dict(BKT_PARAMS, p_G=0.25),
             tutor_params=dict(BKT_PARAMS, p_G=0.05))
ra = run_one(cur, sp, seed=5, keep_trace=True)
sp2 = RunSpec(**{**sp.__dict__, "tutor_params": dict(BKT_PARAMS, p_G=0.45)})
rb = run_one(cur, sp2, seed=5, keep_trace=True)
check(ra["trace"][0]["belief_after"] != rb["trace"][0]["belief_after"],
      "changing only the tutor's p_G changes the belief")
# the answer SEQUENCE legitimately differs: a different tutor belief
# gives a different ZPD, so a different question gets asked. What must
# not change is the student itself, so compare their hidden starting state.
init_a = {c for c, v in ra["learned_step"].items() if v == 0}
init_b = {c for c, v in rb["learned_step"].items() if v == 0}
check(init_a == init_b,
      "...and leaves the student's own starting state untouched")

print("11. the 2x2 interaction has the predicted sign")
from cursim.sanity import two_by_two
o = two_by_two(n_learners=40, n_steps=40, cur=cur)
pr = {r["student"]: r for r in o["tables"]["paired"]}
check(pr["S2"]["diff_Q2_minus_Q1"] > 0,
      f"S2 does better with Q2 ({pr['S2']['diff_Q2_minus_Q1']:+.2f})")
check(pr["interaction (S2 minus S1)"]["scheduler_matters"],
      "the scheduler effect depends on the student model")

print("12. the verdict sentence can never contradict its own table")
from cursim.sanity import restriction_only
def verdict_of(out):
    return out["summary"].split(": ", 1)[1].split(". Note")[0] if ": " in out["summary"] else ""
o2 = two_by_two(n_learners=40, n_steps=1, cur=cur)
p2 = {r["student"]: r for r in o2["tables"]["paired"]}
flip = "flips with the student model" in o2["summary"]
both = {p2["S1"]["favours"], p2["S2"]["favours"]} == {"Q1", "Q2"}
check(flip == both,
      f"a sign flip is claimed only when the marginals actually flip "
      f"(n_steps=1: S1 {p2['S1']['favours']}, S2 {p2['S2']['favours']}, "
      f"claimed={flip})")
check(not (o2["tables"]["paired"][2]["scheduler_matters"]
           and "no interaction detected" in o2["summary"]),
      "never denies an interaction its own table reports")

print("13. the restriction alone is neutral for S1")
ro = restriction_only(n_learners=60, n_steps=40, cur=cur)
rr = {r["student"]: r for r in ro["tables"]["restriction_only"]}
check(rr["S1"]["restriction_effect"] == 0.0,
      "truth-gated: the prerequisite restriction costs S1 exactly nothing")
check(rr["S2"]["restriction_effect"] > 0.5,
      f"...and is worth {rr['S2']['restriction_effect']:+.2f} to S2")

print("14. detection refuses a student it cannot measure")
try:
    detection(n_learners=2, n_steps=10, learner="continuous", cur=cur)
    check(False, "detection should refuse the continuous student")
except ValueError as e:
    check("learned_step" in str(e) or "continuous" in str(e),
          "detection refuses the continuous student with a clear message")

print("15. degenerate inputs are refused, not crashed on")
for bad_kw in (dict(n_learners=1), dict(n_learners=0), dict(n_steps=0)):
    try:
        two_by_two(cur=cur, **bad_kw)
        check(False, f"two_by_two should refuse {bad_kw}")
    except ValueError:
        pass
check(True, "two_by_two refuses n_learners<2 and n_steps<1")

print("16. the mastery curve agrees with the 2x2 it summarises")
import matplotlib
matplotlib.use("Agg")
from cursim.sanity import mastery_curve

NL, NS = 40, 40
mc = mastery_curve(n_learners=NL, n_steps=NS, cur=cur)
rows = mc["tables"]["mastery_curve"]

# the curve counts learned_step<=t; two_by_two counts the truth dict at the
# last trace row. Different code paths, same quantity, so they must agree.
x22 = two_by_two(n_learners=NL, n_steps=NS, cur=cur)
end = {(r["student"], r["scheduler"]): r["mean_known"]
       for r in rows if r["step"] == NS}
for r in x22["tables"]["two_by_two"]:
    a, b = end[(r["student"], r["scheduler"])], r["learned_mean"]
    check(abs(a - b) < 1e-9,
          f"{r['student']}/{r['scheduler']}: curve endpoint {a:.4f} "
          f"matches the 2x2's {b:.4f}")

# BKT has no forgetting, so a learner's known-count can never fall
for key in {(r["student"], r["scheduler"]) for r in rows}:
    seq = [r["mean_known"] for r in sorted(
        (r for r in rows if (r["student"], r["scheduler"]) == key),
        key=lambda r: r["step"])]
    check(all(y >= x for x, y in zip(seq, seq[1:])),
          f"{key[0]}/{key[1]}: the curve never goes down")

print("17. the curve reproduces the 2x2 verdict in questions, not counts")
mc2 = mastery_curve(n_learners=400, n_steps=300, cur=cur)
pr = {r["student"]: r for r in mc2["tables"]["paired"]}
check(not pr["S1"]["sign_resolved"]
      and pr["S1"]["favours"] == "unresolved at this n",
      f"S1: Q2 minus Q1 is {pr['S1']['diff_Q2_minus_Q1']:+.1f} "
      f"+/-{pr['S1']['ci95']:.1f} questions, sign not resolved here")
# and the label must not be mistaken for "no effect": across six
# independent 400-learner blocks this contrast came out +1.09, a small
# COST to Q2, which is the direction two_by_two already reports
check("not that the effect is zero" in mc2["summary"],
      "...and the summary says unresolved does not mean zero")
check(pr["S2"]["sign_resolved"] and pr["S2"]["favours"] == "Q2",
      f"S2: Q2 reaches full mastery {-pr['S2']['diff_Q2_minus_Q1']:.1f} "
      f"+/-{pr['S2']['ci95']:.1f} questions sooner")
check(pr["S2"]["median_diff_Q2_minus_Q1"] != pr["S2"]["diff_Q2_minus_Q1"],
      "mean and median paired differences are reported separately")

# a median over finishers only is honest ONLY when nearly all finished
qa = mc2["tables"]["questions_to_all"]
check(all(r["n_censored"] == 0 for r in qa),
      "at 300 questions every learner in every arm reaches all 8 concepts")
check(("No median" in mc2["summary"]) == any(
          r["n_censored"] / r["n_learners"] > 0.05 for r in qa),
      "the summary quotes a median only when almost nobody was censored")

short = mastery_curve(n_learners=20, n_steps=20, cur=cur)
check("No median" in short["summary"],
      "at a budget too short to finish, it refuses to quote a median")

print("18. mastery_curve refuses degenerate inputs")
for bad_kw in (dict(n_learners=1), dict(n_steps=0)):
    try:
        mastery_curve(cur=cur, **bad_kw)
        check(False, f"mastery_curve should refuse {bad_kw}")
    except ValueError:
        pass
check(True, "mastery_curve refuses n_learners<2 and n_steps<1")

print("19. the oracle tutor collapses onto the fixed one when it must")
from cursim.sanity import tutor_choice
from cursim.params import BKT_PARAMS as BP

# At zero spread every student sits exactly at the truth, so a tutor handed
# each student's own parameters IS the fixed tutor at the true value. Same
# students, same seeds, so the two arms must agree exactly, not just closely.
tc0 = tutor_choice(n_learners=12, n_steps=40, vary=("p_S",),
                   spreads=(0.0,), cur=cur)
r0 = tc0["tables"]["tutor_choice"]
oracle = next(r for r in r0 if r["tutor_arm"] == "oracle")
at_truth = next(r for r in r0 if r["tutor_arm"] == "fixed"
                and abs(r["tutor_value"] - BP["p_S"]) < 1e-12)
check(oracle["calib_gap"] == at_truth["calib_gap"],
      "at zero spread the oracle equals the tutor at the truth, exactly")
check(oracle["false_alarm_rate"] == at_truth["false_alarm_rate"],
      "...and declares mastery at exactly the same moments")

# and the verdict row must then say the oracle buys nothing at all
# compare against the AT-TRUTH arm, which is the one the oracle must
# equal by construction; the "best" arm is whichever minimised Brier on
# this run and need not be the same arm at a tiny n
at_t = next(r for r in r0 if r["tutor_arm"] == "fixed"
            and abs(r["tutor_value"] - BP["p_S"]) < 1e-12)
check(oracle["brier"] == at_t["brier"] and oracle["mae"] == at_t["mae"],
      "at zero spread the oracle scores identically to the tutor at the truth")

print("20. tutor_choice keeps the arms paired and refuses bad input")
tc = tutor_choice(n_learners=12, n_steps=40, vary=("p_S",),
                  spreads=(0.10,), cur=cur)
rows = tc["tables"]["tutor_choice"]
check(len({r["tutor_arm"] for r in rows}) == 2
      and sum(1 for r in rows if r["tutor_arm"] == "oracle") == 1,
      "one oracle arm beside the fixed grid")
check(all(r["abs_calib_gap"] == abs(r["calib_gap"]) for r in rows),
      "abs_calib_gap really is the absolute calibration gap")
check("upper bound" in tc["summary"] and "not a proposal" in tc["summary"],
      "the summary says plainly that the oracle cannot be built")

for bad in (dict(n_learners=1), dict(vary=("p_nonsense",))):
    try:
        tutor_choice(cur=cur, n_steps=10, **bad)
        check(False, f"tutor_choice should refuse {bad}")
    except ValueError:
        pass
check(True, "tutor_choice refuses n_learners<2 and an unknown parameter")

print("21. the interval compares the two arms, not each arm to itself")
from cursim.sanity import _gap_ci_paired

# identical arms: every bootstrap draw differences to exactly zero
A = [(0.7, 10), (-1.3, 12), (0.2, 9), (2.1, 11), (-0.4, 10), (1.0, 13)]
check(_gap_ci_paired(A, list(A)) == 0.0,
      "two identical arms get a paired interval of exactly zero")

# a rigid shift in every learner is a difference with no spread, so the
# paired interval collapses even though each arm alone varies a lot
B = [(a + 0.5 * n, n) for a, n in A]
check(_gap_ci_paired(A, B) < 1e-12,
      "a constant per-pair shift gives a paired interval of zero too")
check(_gap_ci_paired(A, A[:3]) != _gap_ci_paired(A, A[:3]),
      "mismatched arm lengths give nan rather than a wrong number")

# and on the real thing: at zero spread the two arms ARE the same tutor,
# so the interval on their difference must be exactly zero
tcz = tutor_choice(n_learners=120, n_steps=120, vary=("p_S",),
                   spreads=(0.0,), cur=cur)
vz = tcz["tables"]["verdict"][0]
check(vz["best_fixed_value"] == vz["at_truth_value"],
      "at zero spread the selected tutor is the one at the truth")
check(vz["ci95"] == 0.0 and vz["brier_ci95"] == 0.0,
      "...so the paired interval against the oracle is exactly zero")
check(vz["ci95_marginal"] > 0.0,
      f"...while each arm's own interval is still +/-{vz['ci95_marginal']:.3f}, "
      f"which is why the marginal one is the wrong comparison")

print("22. the signed gap cancels, which is why it is not the score")
from cursim.sanity import _gap_contrib, _loss_contrib, _pooled

# One tutor, badly wrong about both concepts in opposite directions:
# certain of one it does not know, dismissive of one it does.
cancelling = [{"trace": [{"belief_after": 0.9, "true_after": False},
                         {"belief_after": 0.1, "true_after": True}]}]
check(abs(_pooled(_gap_contrib(cancelling))) < 1e-12,
      "the pooled signed gap scores a maximally wrong tutor as perfect")
check(abs(_pooled(_loss_contrib(cancelling, "abs")) - 0.9) < 1e-12,
      "...while mean |belief - truth| correctly calls it 0.9 off per pair")
check(abs(_pooled(_loss_contrib(cancelling, "sq")) - 0.81) < 1e-12,
      "...and Brier calls it 0.81")

# this is not a contrived edge case: it is what a fixed tutor facing a
# symmetric spread of students does, over- and under-shooting in equal
# measure, so the signed gap is blind to exactly what adapting fixes
tc = tutor_choice(n_learners=40, n_steps=40, vary=("p_S",),
                  spreads=(0.15,), cur=cur)
fixed = [r for r in tc["tables"]["tutor_choice"] if r["tutor_arm"] == "fixed"]
v = tc["tables"]["verdict"][0]
check(v["best_fixed_value"] == min(fixed, key=lambda r: r["brier"])["tutor_value"],
      "the best fixed tutor is the one that minimises Brier")
check(all(r["mae"] > abs(r["calib_gap"]) for r in fixed),
      "every fixed arm's per-pair error exceeds its signed gap, as it must")
check("cancels" in tc["summary"] and "improper" in tc["summary"]
      and "no equivalence margin" in tc["summary"],
      "the summary names both rejected scores and the missing margin")

# Brier is proper, so at the study's horizon it recovers the true
# parameter; MAE is not, and at a SHORT horizon it picks the wrong one.
# That is why the score was changed, and why the short horizon is
# called out as a limit rather than quietly used.
zf = [r for r in tcz["tables"]["tutor_choice"] if r["tutor_arm"] == "fixed"]
check(abs(min(zf, key=lambda r: r["brier"])["tutor_value"] - BP["p_S"]) < 1e-12,
      "at 120 questions, with every student at the truth, Brier picks it")

short = tutor_choice(n_learners=120, n_steps=40, vary=("p_S",),
                     spreads=(0.0,), cur=cur)
sf = [r for r in short["tables"]["tutor_choice"] if r["tutor_arm"] == "fixed"]
check(abs(min(sf, key=lambda r: r["mae"])["tutor_value"] - BP["p_S"]) > 1e-12,
      "at 40 questions MAE picks the wrong p_S, so it is a diagnostic only")
check("nearly flat" in tutor_choice.__doc__
      and "Do not read this study at" in tutor_choice.__doc__,
      "the docstring states the short-horizon limit rather than hiding it")

print("23. no number reaches the document except through a CSV")
import os
import make_tables

# Every data table in docs/simulator.tex is \input from docs/tables/,
# and docs/tables/ is written by make_tables.py from sanity_outputs/.
# If a committed table has drifted from its CSV, or someone typed a
# number straight into the tex, this check is what catches it.
built = make_tables.build()
tex = open("docs/simulator.tex").read()
for name, text in sorted(built.items()):
    path = os.path.join("docs", "tables", f"{name}.tex")
    check(os.path.exists(path) and open(path).read() == text,
          f"docs/tables/{name}.tex matches what the CSVs produce")
    check(f"\\input{{tables/{name}}}" in tex,
          f"...and the document actually includes it")

# and the document must not carry a hand-typed tabular any more
import re
body = re.sub(r"%.*", "", tex)
check("\\begin{tabular}" not in body.split("\\section*{2.")[-1],
      "no hand-typed table survives past the notation section")

print(f"\nALL {passed} CHECKS PASSED")
