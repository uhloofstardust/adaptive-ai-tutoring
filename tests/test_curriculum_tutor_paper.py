"""Does cursim.schedulers.curriculum_tutor_paper do what Algorithm 2 of
Shabana et al. (AIED 2022) says? Each check below is a line of the paper.
Run: python -m tests.test_curriculum_tutor_paper"""
import math
import random

from cursim.curriculum import build_curriculum
from cursim.schedulers.curriculum_tutor_paper import (
    CurriculumTutorPaper, PAPER_H, kl_bern, kl_ucb_index)
from cursim.simulation import RunSpec, run_one

passed = 0


def check(cond, msg):
    global passed
    assert cond, msg
    passed += 1
    print(f"  ok  {msg}")


cur = build_curriculum("layered_40")
rng = random.Random(1)

print("1. CUSUM change-point test (paper eq. 5-8; h = ln(1/0.0004))")
check(abs(PAPER_H - math.log(2500)) < 1e-12, "h = ln(1/0.0004) = 7.824")
s = CurriculumTutorPaper()
c = next(iter(cur.concepts))
right = math.log(0.9 / 0.25)       # log p1(1)/p0(1), p_slip 0.1, p_guess 0.25
wrong = math.log(0.1 / 0.75)       # log p1(0)/p0(0)
check(abs(s.llr_right - right) < 1e-12 and abs(s.llr_wrong - wrong) < 1e-12,
      "per-answer log-likelihood ratios match eq. 7-8")
for _ in range(6):
    s.observe(c, True, 0)
check(c not in s.learned, "6 right answers in a row: not yet learned (6 x 1.28 = 7.69 < 7.82)")
s.observe(c, True, 0)
check(c in s.learned, "7th right answer: change detected, concept learned")
s2 = CurriculumTutorPaper()
for _ in range(6):
    s2.observe(c, True, 0)
s2.observe(c, False, 0)
check(abs(s2.u[c] - max(0.0, 6 * right + wrong)) < 1e-12,
      "a wrong answer subtracts its ratio (recursion, eq. 6)")
s3 = CurriculumTutorPaper()
s3.observe(c, False, 0)
check(s3.u[c] == 0.0, "the statistic never goes below 0")

print("2. ZPD (Algorithm 2, lines 1, 18-20)")
s = CurriculumTutorPaper()
roots = [cid for cid, cc in cur.concepts.items() if not cc.prereqs]
check(sorted(s.zpd(cur)) == sorted(roots),
      "starts as the concepts with no prerequisites")
child = next(cid for cid, cc in cur.concepts.items()
             if cc.prereqs and all(p in roots for p in cc.prereqs))
for p in cur.concepts[child].prereqs:
    s.learned.add(p)
check(child in s.zpd(cur), "a concept joins once all its prerequisites are learned")
partial = [p for p in cur.concepts[child].prereqs]
if len(partial) > 1:
    s.learned.discard(partial[0])
    check(child not in s.zpd(cur), "...and not before")
s.learned.add(roots[0])
check(roots[0] not in s.zpd(cur), "a learned concept leaves the ZPD")

print("3. KL-UCB (section 5)")
check(kl_ucb_index(0.0, 0, 10) == float("inf"), "an untried arm has an infinite index")
u = kl_ucb_index(0.5, 10, 100)
check(abs(10 * kl_bern(0.5, u) - math.log(100)) < 1e-6 and u > 0.5,
      "index solves n * kl(mean, q) = ln t")
check(kl_ucb_index(0.5, 5, 100) > kl_ucb_index(0.5, 50, 100),
      "fewer pulls: larger bonus")
check(kl_ucb_index(0.8, 10, 100) > kl_ucb_index(0.4, 10, 100),
      "higher mean: higher index")
check(kl_ucb_index(1.0, 10, 100) == 1.0, "the index never exceeds 1")
s = CurriculumTutorPaper()
picked = set()
for _ in range(len(roots)):
    q = s.select(cur, None, 0, rng, None)
    s.observe(q.concept_id, True, 0)
    picked.add(q.concept_id)
check(picked <= set(roots), "only ZPD concepts are asked")
check(len(picked) == len(roots),
      "untried arms are pulled before any arm is repeated")

print("4. knobs: defaults are the published algorithm; each knob is one change")
d = CurriculumTutorPaper()
check(d.revision == 0.0 and d.h == PAPER_H, "defaults: no revision, paper's h")
res = run_one(cur, RunSpec(scheduler="curriculum_tutor_paper",
                           mastery_model="binary", n_sessions=2,
                           questions_per_session=100), seed=1, keep_log=True)
sch = CurriculumTutorPaper()
rr = random.Random(5)
bad = 0
for _ in range(300):
    z = sch.zpd(cur)
    q = sch.select(cur, None, 0, rr, None)
    if z and q.concept_id not in z:
        bad += 1
    sch.observe(q.concept_id, rr.random() < 0.8, 0)
check(bad == 0 and len(sch.learned) > 0,
      "revision 0: every question comes from the ZPD while it is non-empty")
for rho in (0.1, 0.25, 0.5):
    sch = CurriculumTutorPaper(revision=rho)
    sch.learned = {"x"}
    sch.last_asked = {"x": 0}
    n_rev = 0
    cur_ids = list(cur.concepts)
    sch.learned = set(cur_ids[:3])           # three learned, plenty left to teach
    for _ in range(1000):
        sch.select(cur, None, 0, rng, None)
        n_rev += sch.revising_now
        sch.observe(cur_ids[0], True, 0)
    check(abs(n_rev / 1000 - rho) < 0.01, f"revision budget {rho}: share of questions spent revising = {n_rev/1000:.3f}")
sch = CurriculumTutorPaper(revision=0.3)
sch.learned = set(list(cur.concepts)[:3])
asked = []
for _ in range(60):
    q = sch.select(cur, None, 0, rng, None)
    if sch.revising_now:
        asked.append(q.concept_id)
    sch.observe(q.concept_id, True, 0)
    sch.learned = set(list(cur.concepts)[:3])   # keep three learned
check(len(set(asked)) == 3, "revision cycles through all learned concepts (least recently asked first)")

print("5. when the ZPD is empty")
s = CurriculumTutorPaper()
s.learned = set(cur.concepts)
check(s.select(cur, None, 0, rng, None) is None,
      "published algorithm: nothing left to teach, no question is asked")
s = CurriculumTutorPaper(revision=0.3)
s.learned = set(cur.concepts)
s.credit = 1.0
check(s.select(cur, None, 0, rng, None) is not None,
      "...unless the revision budget asks for one")
s = CurriculumTutorPaper(leftover="revise")
s.learned = set(cur.concepts)
check(s.select(cur, None, 0, rng, None) is not None,
      "leftover='revise' (a variant): spare questions go to revision")
res = run_one(cur, RunSpec(scheduler="curriculum_tutor_paper",
                           mastery_model="binary",
                           scheduler_params=dict(depth_h=1.0)), seed=3)
check(res["sched_stats"]["finished"] and res["sched_stats"]["revision_share"] == 0.0,
      "with h = 1 the curriculum is finished early and the rest is left idle")

print(f"\n{passed} checks passed")
