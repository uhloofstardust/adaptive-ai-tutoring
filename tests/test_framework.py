"""Checks for the plumbing: curricula, registries, the experiment runner.
Run: python -m tests.test_framework"""
import csv
import json
import os
import tempfile

from cursim.curriculum import (DATA_DIR, available, build_curriculum,
                               generate_layered)
from cursim.schedulers import SCHEDULERS, Scheduler, register_scheduler
from cursim.simulation import RunSpec, run_one
from cursim.students import PROFILES
from cursim.stats import paired, sign_test

import experiments
from experiments import EXPERIMENTS, META
from experiments.registry import experiment
from experiments.runner import run, run_and_save
from experiments.suites import SUITES

passed = 0


def check(cond, msg):
    global passed
    assert cond, msg
    passed += 1
    print(f"  ok  {msg}")


print("1. curricula are subject-free data")
check({"abstract", "layered_40"} <= set(available()), "both shipped curricula are found")
for name in available():
    raw = open(os.path.join(DATA_DIR, name + ".json"), encoding="utf-8").read()
    blob = json.loads(raw)
    check(raw.isascii(), f"{name}: ASCII only, so no language content can hide in it")
    check(all(set(q) == {"qid", "concept_id", "difficulty"}
              for c in blob["concepts"] for q in c["questions"]),
          f"{name}: questions carry an id and a difficulty and nothing else")
    check(all(c["name"] == c["cid"] for c in blob["concepts"]),
          f"{name}: concepts are named by their id")
c40 = build_curriculum("layered_40")
check(len(c40.concepts) == 40 and len(c40.all_questions()) == 290, "layered_40 has 40 concepts and 290 questions")

print("2. generated curricula")
a = generate_layered(seed=3)
b = generate_layered(seed=3)
c = generate_layered(seed=4)
diff = lambda x: [(q.qid, q.difficulty) for q in x.all_questions()]
check(diff(a) == diff(b) and [k.prereqs for k in a.concepts.values()] ==
      [k.prereqs for k in b.concepts.values()], "same seed gives the same curriculum")
check(diff(a) != diff(c), "a different seed gives a different one")
check(a.is_dag() and all(a.concepts[p].tier == k.tier - 1
                         for k in a.concepts.values() for p in k.prereqs),
      "acyclic, and every prerequisite sits exactly one tier above")
check(all(k.prereqs for k in a.concepts.values() if k.tier > 0), "every non-root has a prerequisite")
check([sum(1 for k in a.concepts.values() if k.tier == t) for t in range(6)] == [4, 5, 5, 4, 3, 2],
      "tier sizes are respected")
for bad in (dict(tier_sizes=()), dict(tier_sizes=(2, 0)), dict(max_prereqs=0),
            dict(questions=(0, 3)), dict(questions=(6, 5))):
    try:
        generate_layered(**bad)
    except ValueError:
        pass
    else:
        raise AssertionError(f"accepted {bad}")
check(True, "degenerate arguments are refused")
p = os.path.join(tempfile.mkdtemp(), "g.json")
a.to_json(p)
from cursim.curriculum import Curriculum
check(diff(Curriculum.from_json(p)) == diff(a), "a generated curriculum survives a JSON round trip")

print("3. schedulers")
expected = {"random", "curriculum_tutor", "uniform_zpd", "uniform_unmastered",
            "continuous", "adaptive_review", "predictive", "maple",
            "naive_maple", "ucb"}
check(set(SCHEDULERS) == expected, "the registry holds exactly the ten known names")
check(SCHEDULERS["uniform_zpd"] is SCHEDULERS["curriculum_tutor"], "uniform_zpd is an alias of curriculum_tutor")
cur = build_curriculum()
for name in sorted(SCHEDULERS):
    r = run_one(cur, RunSpec(scheduler=name, mastery_model="continuous_forget",
                             n_sessions=2, questions_per_session=10), seed=5)
    assert 0 <= r["final_mastery"] <= 1, name
check(True, "every registered scheduler completes a short run")
try:
    register_scheduler("random")(type("X", (Scheduler,), {}))
except ValueError:
    check(True, "registering a taken name is refused")
else:
    raise AssertionError("duplicate scheduler name accepted")

print("4. profile overrides")
before = PROFILES["average"].forget_half_life_days
base = RunSpec(n_sessions=3, questions_per_session=15, retention_days=3)
r0 = run_one(cur, base, seed=8)
r1 = run_one(cur, RunSpec(**{**base.__dict__, "profile_overrides": {"forget_half_life_days": 2.0}}), seed=8)
check(PROFILES["average"].forget_half_life_days == before, "the shared profile is never modified")
check(r1["retained_mastery"] < r0["retained_mastery"], "a shorter half-life leaves less after the break")

print("5. statistics")
check(abs(sign_test(10, 10) - 2 * 0.5 ** 10) < 1e-12 and sign_test(0, 0) == 1.0, "sign test")
class R:
    def __init__(self, v): self.per_learner = [{"k": x} for x in v]
d = paired(R([1, 2, 3]), R([2, 2, 5]), "k")
check((d["wins"], d["losses"], d["n"]) == (2, 0, 3) and abs(d["mean_diff"] - 1.0) < 1e-12, "paired differences are b minus a")

print("6. experiment registry")
check(len(EXPERIMENTS) >= 16, f"{len(EXPERIMENTS)} experiments registered")
check(all(isinstance(v[1], str) and v[1] and isinstance(v[2], dict) for v in EXPERIMENTS.values()), "each has a description and default parameters")
check(all(META[n]["curriculum"] in available() for n in EXPERIMENTS), "each declares a curriculum that exists")
check(all(e in EXPERIMENTS for entries in SUITES.values() for _, e, _ in entries), "every suite entry names a registered experiment")
check(len({o for entries in SUITES.values() for o, _, _ in entries}) == sum(len(v) for v in SUITES.values()), "suite output names are unique")
try:
    experiment("check1_calibration", "dup")(lambda **k: None)
except ValueError:
    check(True, "registering a taken experiment name is refused")
else:
    raise AssertionError("duplicate experiment name accepted")

print("7. the runner writes a complete, reproducible record")
out = tempfile.mkdtemp()
d1 = run_and_save("check1_calibration", dict(n_learners=4, n_steps=30), out_root=out, output_name="t1")
files = set(os.listdir(d1))
check({"calibration.csv", "calibration.png", "summary.md", "meta.json"} <= files, f"writes {sorted(files)}")
meta = json.load(open(os.path.join(d1, "meta.json")))
check(meta["experiment"] == "check1_calibration" and meta["parameters"]["n_learners"] == 4
      and meta["curriculum"] == "abstract" and "commit" in meta, "meta.json records what produced it")
d2 = run_and_save("check1_calibration", dict(n_learners=4, n_steps=30), out_root=out, output_name="t2")
check(open(os.path.join(d1, "calibration.csv")).read() == open(os.path.join(d2, "calibration.csv")).read(),
      "same parameters give a byte-identical table")
d3 = run_and_save("check1_calibration", dict(n_learners=4, n_steps=30, curriculum="layered_40"), out_root=out, output_name="t3")
check(json.load(open(os.path.join(d3, "meta.json")))["curriculum"] == "layered_40", "curriculum can be chosen per run")
rows = list(csv.DictReader(open(os.path.join(d1, "calibration.csv"))))
check(len(rows) == 10, "one row per calibration bin")
try:
    run("no_such_experiment")
except KeyError:
    check(True, "an unknown experiment name is refused")

print("8. forgetting experiments run end to end on a tiny budget")
res = run("representation", dict(n_learners=3))
check({"conditions", "paired"} <= set(res["tables"]) and len(res["tables"]["conditions"]) == 3, "representation")
res = run("halflife_sweep", dict(n_learners=2, half_lives=(5, 20)))
check(len(res["tables"]["best_by_half_life"]) == 2, "halflife_sweep honours its half_lives parameter")

print(f"\nALL {passed} CHECKS PASSED")
