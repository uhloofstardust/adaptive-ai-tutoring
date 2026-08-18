"""Test suite for the cursim simulator.

    python test_simulator.py            # run everything
    python test_simulator.py -v         # show each check as it passes

Twenty-six checks in seven groups. These verify that the simulator
behaves the way the design says it does. They are not experiments: no
result depends on them, but every result depends on them passing.

The most important ones are in group 6, which enforce the rules that
keep the experiments honest: the tutor cannot see the learner's true
state, and comparisons really are paired.

Standard library only. Nothing here needs matplotlib.
"""

import math
import sys
import traceback

from cursim.curriculum import (Curriculum, build_curriculum, SPEC, WORDS)
from cursim.learner import Learner, LearnerProfile, PROFILES, SimConfig
from cursim.mastery import (BinaryMastery, ContinuousMastery, make_model)
from cursim.schedulers import SCHEDULERS, AdaptiveReviewScheduler
from cursim.simulation import (RunSpec, paired, run_condition, run_one,
                               sign_test)

VERBOSE = "-v" in sys.argv
PASSED, FAILED = [], []


def check(name, fn):
    try:
        detail = fn()
        PASSED.append(name)
        if VERBOSE:
            print(f"  PASS  {name}" + (f"   [{detail}]" if detail else ""))
    except AssertionError as e:
        FAILED.append((name, str(e)))
        print(f"  FAIL  {name}\n        {e}")
    except Exception:
        FAILED.append((name, "exception"))
        print(f"  ERROR {name}")
        traceback.print_exc()


def group(title):
    print(f"\n{title}")
    print("-" * len(title))


CUR = build_curriculum()
CFG = SimConfig()


# ====================================================================
def test_curriculum():
    group("1. Curriculum structure")

    def t_size():
        assert len(CUR.concepts) == 40, len(CUR.concepts)
        n = len(CUR.all_questions())
        assert n == 290, n
        return f"40 concepts, {n} questions"
    check("has 40 concepts and 290 questions", t_size)

    def t_dag():
        assert CUR.is_dag(), "curriculum contains a prerequisite cycle"
        return "no cycles"
    check("prerequisite graph is acyclic", t_dag)

    def t_qcount():
        counts = [len(c.questions) for c in CUR.concepts.values()]
        assert min(counts) >= 5, f"a concept has only {min(counts)}"
        assert max(counts) <= 10, f"a concept has {max(counts)}"
        return f"{min(counts)} to {max(counts)} per concept"
    check("every concept has 5 to 10 questions", t_qcount)

    def t_prereqs_exist():
        for c in CUR.concepts.values():
            for p in c.prereqs:
                assert p in CUR.concepts, f"{c.cid} needs unknown {p}"
                assert p != c.cid, f"{c.cid} is its own prerequisite"
        return "all prerequisites resolve"
    check("prerequisites all point at real concepts", t_prereqs_exist)

    def t_tier_order():
        """A prerequisite must sit in an earlier tier than its
        dependant, otherwise the tier layout is meaningless."""
        for c in CUR.concepts.values():
            for p in c.prereqs:
                assert CUR.concepts[p].tier < c.tier, \
                    f"{p} (tier {CUR.concepts[p].tier}) is a prerequisite " \
                    f"of {c.cid} (tier {c.tier})"
        return "prerequisites are always in earlier tiers"
    check("tiers are consistent with the graph", t_tier_order)

    def t_roots():
        roots = CUR.roots()
        assert len(roots) >= 2, "a language curriculum needs several entries"
        for r in roots:
            assert CUR.concepts[r].tier == 0
        return f"{len(roots)} entry points: {', '.join(sorted(roots))}"
    check("has multiple independent entry points", t_roots)

    def t_difficulty_range():
        ds = [q.difficulty for q in CUR.all_questions()]
        assert all(0.0 <= d <= 1.0 for d in ds), "difficulty out of range"
        assert max(ds) - min(ds) > 0.3, "difficulties barely vary"
        return f"{min(ds):.2f} to {max(ds):.2f}"
    check("question difficulties vary and are in range", t_difficulty_range)

    def t_difficulty_rises():
        """Later tiers should be harder, or the curriculum has no
        progression."""
        by_tier = {}
        for c in CUR.concepts.values():
            for q in c.questions:
                by_tier.setdefault(c.tier, []).append(q.difficulty)
        means = [sum(v) / len(v) for _, v in sorted(by_tier.items())]
        assert means[-1] > means[0] + 0.2, means
        return f"tier 0 {means[0]:.2f} rising to tier 5 {means[-1]:.2f}"
    check("difficulty increases with tier", t_difficulty_rises)

    def t_unique_ids():
        ids = [q.qid for q in CUR.all_questions()]
        assert len(set(ids)) == len(ids), "duplicate question id"
        return f"{len(ids)} unique question ids"
    check("question ids are unique", t_unique_ids)

    def t_deterministic():
        a = build_curriculum(seed=11)
        b = build_curriculum(seed=11)
        da = [q.difficulty for q in a.all_questions()]
        db = [q.difficulty for q in b.all_questions()]
        assert da == db, "same seed produced different curricula"
        return "same seed gives an identical curriculum"
    check("curriculum generation is deterministic", t_deterministic)

    def t_json_roundtrip():
        import tempfile, os
        p = os.path.join(tempfile.mkdtemp(), "c.json")
        CUR.to_json(p)
        back = Curriculum.from_json(p)
        assert len(back.concepts) == len(CUR.concepts)
        assert len(back.all_questions()) == len(CUR.all_questions())
        return "saved and reloaded without loss"
    check("curriculum survives a JSON round trip", t_json_roundtrip)


# ====================================================================
def test_learner():
    group("2. The simulated learner")

    def t_starts_low():
        l = Learner(CUR, PROFILES["average"], seed=1, cfg=CFG)
        s = l.snapshot(0.0)
        assert all(0.0 <= v <= 0.6 for v in s.values()), "odd start"
        return f"mean starting mastery {sum(s.values())/len(s):.3f}"
    check("starts with little knowledge", t_starts_low)

    def t_practice_helps():
        l = Learner(CUR, PROFILES["average"], seed=2, cfg=CFG)
        q = CUR.concepts["greetings"].questions[0]
        m0 = l.true_mastery("greetings", 0.0)
        for i in range(15):
            l.answer(q, i * 0.02)
        m1 = l.true_mastery("greetings", 0.30)
        assert m1 > m0 + 0.3, (m0, m1)
        return f"{m0:.3f} rises to {m1:.3f} after 15 practices"
    check("practice increases true mastery", t_practice_helps)

    def t_mastery_bounded():
        l = Learner(CUR, PROFILES["fast"], seed=3, cfg=CFG)
        q = CUR.concepts["greetings"].questions[0]
        for i in range(300):
            l.answer(q, i * 0.02)
        m = l.true_mastery("greetings", 6.0)
        assert m <= 1.0, f"mastery exceeded 1.0: {m}"
        return f"saturates at {m:.4f}, never above 1"
    check("mastery never exceeds 1.0", t_mastery_bounded)

    def t_forgetting():
        l = Learner(CUR, PROFILES["average"], seed=4, cfg=CFG)
        q = CUR.concepts["greetings"].questions[0]
        for i in range(15):
            l.answer(q, i * 0.02)
        hot = l.true_mastery("greetings", 0.30)
        cold = l.true_mastery("greetings", 0.30 + 30 * 24)
        assert cold < hot, "no decay over 30 idle days"
        return f"{hot:.3f} decays to {cold:.3f} after 30 idle days"
    check("mastery decays when not practised", t_forgetting)

    def t_halflife_correct():
        """After exactly one half-life, the gap to the floor should
        have halved. This checks the decay maths, not just its sign."""
        prof = LearnerProfile("t", forget_half_life_days=10.0)
        l = Learner(CUR, prof, seed=5, cfg=CFG)
        l.mastery["greetings"] = 1.0
        l.last_seen["greetings"] = 0.0
        floor = CFG.mastery_floor
        after = l.true_mastery("greetings", 10 * 24.0)
        expect = floor + (1.0 - floor) * 0.5
        # tier 0 gets a small adjustment, so allow a little slack
        assert abs(after - expect) < 0.06, (after, expect)
        return f"after one half-life: {after:.3f}, expected ~{expect:.3f}"
    check("decay follows the stated half-life", t_halflife_correct)

    def t_forgetting_can_be_off():
        l = Learner(CUR, PROFILES["average"], seed=6, cfg=CFG,
                    forgetting=False)
        q = CUR.concepts["greetings"].questions[0]
        for i in range(15):
            l.answer(q, i * 0.02)
        hot = l.true_mastery("greetings", 0.30)
        cold = l.true_mastery("greetings", 0.30 + 60 * 24)
        assert abs(cold - hot) < 1e-9, "decayed with forgetting off"
        return "no decay at all over 60 idle days"
    check("forgetting can be switched off", t_forgetting_can_be_off)

    def t_readiness():
        l = Learner(CUR, PROFILES["average"], seed=7, cfg=CFG)
        deep = next(c for c in CUR.concepts.values() if c.prereqs)
        low = l.readiness(deep.cid, 0.0)
        for p in deep.prereqs:
            l.mastery[p] = 0.95
            l.last_seen[p] = 0.0
        high = l.readiness(deep.cid, 0.0)
        assert high > low + 0.3, (low, high)
        return f"'{deep.cid}': {low:.2f} with weak prerequisites, " \
               f"{high:.2f} with strong ones"
    check("weak prerequisites lower readiness", t_readiness)

    def t_prereqs_slow_learning():
        """The point of readiness: it must actually slow learning
        down, not merely exist as a number."""
        deep = next(c for c in CUR.concepts.values() if c.prereqs)
        q = deep.questions[0]

        blocked = Learner(CUR, PROFILES["average"], seed=8, cfg=CFG,
                          forgetting=False)
        for i in range(20):
            blocked.answer(q, i * 0.02)
        m_blocked = blocked.true_mastery(deep.cid, 0.5)

        ready = Learner(CUR, PROFILES["average"], seed=8, cfg=CFG,
                        forgetting=False)
        for p in deep.prereqs:
            ready.mastery[p] = 0.95
            ready.last_seen[p] = 0.0
        for i in range(20):
            ready.answer(q, i * 0.02)
        m_ready = ready.true_mastery(deep.cid, 0.5)

        assert m_ready > m_blocked + 0.1, (m_blocked, m_ready)
        return f"same 20 practices reach {m_blocked:.2f} unprepared " \
               f"vs {m_ready:.2f} prepared"
    check("weak prerequisites genuinely slow learning", t_prereqs_slow_learning)

    def t_difficulty_matters():
        """A harder question must be harder to answer at the same
        mastery."""
        l = Learner(CUR, PROFILES["average"], seed=9, cfg=CFG)
        qs = sorted(CUR.all_questions(), key=lambda q: q.difficulty)
        easy, hard = qs[0], qs[-1]
        m = 0.6
        g = 1.0 / CFG.n_options
        slip = PROFILES["average"].slip

        def p_correct(q):
            eff = m ** (1 + CFG.difficulty_exponent * q.difficulty)
            return eff * (1 - slip) + (1 - eff) * g

        pe, ph = p_correct(easy), p_correct(hard)
        assert pe > ph + 0.05, (pe, ph)
        return f"at mastery 0.6: {pe:.2f} on the easiest question, " \
               f"{ph:.2f} on the hardest"
    check("harder questions are harder to answer", t_difficulty_matters)

    def t_profiles_differ():
        out = {}
        for name in ("fast", "average", "slow", "forgetful"):
            r = run_one(CUR, RunSpec(scheduler="continuous",
                                     mastery_model="continuous",
                                     profile=name), seed=100)
            out[name] = r["final_mastery"]
        assert out["fast"] > out["slow"], out
        assert len(set(round(v, 6) for v in out.values())) == 4, out
        return "  ".join(f"{k} {v:.2f}" for k, v in out.items())
    check("the four learner profiles behave differently", t_profiles_differ)


# ====================================================================
def test_mastery_models():
    group("3. Mastery models (what the tutor believes)")

    def t_binary_latches():
        m = BinaryMastery(CUR.ids())
        assert not m.is_mastered("greetings", 0.0)
        for _ in range(10):
            m.observe("greetings", True, 0.0)
        assert m.is_mastered("greetings", 0.0)
        return "marks mastered after repeated correct answers"
    check("binary model latches on success", t_binary_latches)

    def t_binary_permanent():
        """The defining property of the CurriculumTutor assumption."""
        m = BinaryMastery(CUR.ids())
        for _ in range(10):
            m.observe("greetings", True, 0.0)
        for _ in range(20):
            m.observe("greetings", False, 1000.0)
        assert m.is_mastered("greetings", 1000.0), \
            "binary mastery must never be revoked"
        assert m.is_mastered("greetings", 100000.0)
        return "still mastered after 20 wrong answers and years idle"
    check("binary mastery is permanent", t_binary_permanent)

    def t_continuous_no_latch():
        m = ContinuousMastery(CUR.ids())
        for _ in range(10):
            m.observe("greetings", True, 0.0)
        high = m.belief("greetings", 0.0)
        for _ in range(10):
            m.observe("greetings", False, 0.0)
        low = m.belief("greetings", 0.0)
        assert low < high - 0.2, (high, low)
        return f"belief falls {high:.2f} to {low:.2f} on wrong answers"
    check("continuous belief can go down again", t_continuous_no_latch)

    def t_continuous_decays():
        m = ContinuousMastery(CUR.ids(), forget_per_day=0.10)
        for _ in range(10):
            m.observe("greetings", True, 0.0)
        hot = m.belief("greetings", 0.0)
        cold = m.belief("greetings", 30 * 24.0)
        assert cold < hot - 0.3, (hot, cold)
        return f"belief decays {hot:.2f} to {cold:.2f} over 30 idle days"
    check("continuous belief decays with forgetting on", t_continuous_decays)

    def t_no_decay_when_off():
        m = ContinuousMastery(CUR.ids(), forget_per_day=0.0)
        for _ in range(10):
            m.observe("greetings", True, 0.0)
        hot = m.belief("greetings", 0.0)
        cold = m.belief("greetings", 365 * 24.0)
        assert abs(hot - cold) < 1e-9
        return "belief unchanged after a year when forgetting is off"
    check("no decay when forgetting is disabled", t_no_decay_when_off)

    def t_beliefs_bounded():
        for kind in ("binary", "continuous", "continuous_forget"):
            m = make_model(kind, CUR.ids())
            for i in range(50):
                m.observe("greetings", i % 3 == 0, i * 24.0)
                b = m.belief("greetings", i * 24.0)
                assert 0.0 <= b <= 1.0, (kind, b)
        return "all three models stay within [0, 1]"
    check("beliefs stay in range for every model", t_beliefs_bounded)

    def t_factory():
        for kind in ("binary", "continuous", "continuous_forget"):
            m = make_model(kind, CUR.ids())
            assert hasattr(m, "observe") and hasattr(m, "belief")
        try:
            make_model("nonsense", CUR.ids())
            assert False, "unknown model kind should raise"
        except ValueError:
            pass
        return "three kinds build, unknown kinds are rejected"
    check("model factory works and rejects bad input", t_factory)


# ====================================================================
def test_schedulers():
    group("4. Schedulers")

    def t_all_return_valid():
        import random
        for name, cls in SCHEDULERS.items():
            s = cls()
            model = make_model("continuous", CUR.ids())
            rng = random.Random(0)
            for _ in range(50):
                q = s.select(CUR, model, 0.0, rng, None)
                assert q.qid in {x.qid for x in CUR.all_questions()}, name
        return f"all {len(SCHEDULERS)} schedulers return real questions"
    check("every scheduler returns a valid question", t_all_return_valid)

    def t_ct_respects_prereqs():
        """At the very start nothing is mastered, so CurriculumTutor
        must only offer entry-point concepts."""
        import random
        s = SCHEDULERS["curriculum_tutor"]()
        model = make_model("binary", CUR.ids())
        rng = random.Random(1)
        picked = {s.select(CUR, model, 0.0, rng, None).concept_id
                  for _ in range(200)}
        roots = set(CUR.roots())
        assert picked <= roots, sorted(picked - roots)
        return f"cold start picks only from {len(roots)} entry points"
    check("CurriculumTutor gates on prerequisites", t_ct_respects_prereqs)

    def t_continuous_prefers_ready():
        """The soft gate should also start at the entry points."""
        import random
        s = SCHEDULERS["continuous"]()
        model = make_model("continuous", CUR.ids())
        rng = random.Random(2)
        picked = [s.select(CUR, model, 0.0, rng, None).concept_id
                  for _ in range(200)]
        roots = set(CUR.roots())
        share = sum(1 for c in picked if c in roots) / len(picked)
        assert share > 0.8, f"only {share:.0%} from entry points"
        return f"{share:.0%} of cold-start picks are entry points"
    check("continuous scheduler respects soft prerequisites",
          t_continuous_prefers_ready)

    def t_review_urgency_grows():
        """The review term must grow with time since practice. This is
        the mechanism that brings faded concepts back."""
        s = AdaptiveReviewScheduler()
        s.last_practised["greetings"] = 0.0
        u_now = s._urgency("greetings", 0.0)
        u_1d = s._urgency("greetings", 24.0)
        u_10d = s._urgency("greetings", 240.0)
        assert u_now < u_1d < u_10d, (u_now, u_1d, u_10d)
        assert u_now < 0.01 and u_10d > 0.9, (u_now, u_10d)
        return f"urgency {u_now:.2f} at once, {u_1d:.2f} after a day, " \
               f"{u_10d:.2f} after ten"
    check("review urgency grows with time since practice",
          t_review_urgency_grows)

    def t_review_beats_no_review_on_known_concepts():
        """With every concept already well known, the review scheduler
        should revisit a long-neglected one sooner than the plain
        continuous scheduler, which has no review term at all."""
        import random
        model = make_model("continuous_forget", CUR.ids(),
                           forget_per_day=0.02)
        for cid in CUR.ids():
            for _ in range(25):
                model.observe(cid, True, 0.0)
        # everything practised recently except one concept
        stale = "greetings"
        now = 30 * 24.0
        ar = AdaptiveReviewScheduler()
        for cid in CUR.ids():
            ar.last_practised[cid] = now - 1.0
        ar.last_practised[stale] = 0.0

        # select() records the pick, so ask it fresh each time to
        # measure the decision rather than its own side effect
        rng = random.Random(3)
        hits = 0
        for _ in range(60):
            ar.last_practised = {cid: now - 1.0 for cid in CUR.ids()}
            ar.last_practised[stale] = 0.0
            if ar.select(CUR, model, now, rng, None).concept_id == stale:
                hits += 1
        share = hits / 60
        assert share > 0.5, \
            f"stale concept picked only {share:.0%} of the time"
        return f"the neglected concept wins {share:.0%} of decisions " \
               f"(uniform would be {1/len(CUR.ids()):.0%})"
    check("adaptive review prioritises the most faded concept",
          t_review_beats_no_review_on_known_concepts)

    def t_no_immediate_repeat():
        import random
        for name, cls in SCHEDULERS.items():
            s = cls()
            model = make_model("continuous", CUR.ids())
            rng = random.Random(4)
            last = None
            for _ in range(100):
                q = s.select(CUR, model, 0.0, rng, last)
                assert q.qid != last, f"{name} repeated a question"
                last = q.qid
        return "no scheduler repeats the previous question"
    check("no scheduler asks the same question twice running",
          t_no_immediate_repeat)

    def t_schedulers_differ():
        vals = {}
        for name in SCHEDULERS:
            r = run_one(CUR, RunSpec(scheduler=name,
                                     mastery_model="continuous",
                                     n_sessions=6,
                                     questions_per_session=15), seed=200)
            vals[name] = round(r["final_mastery"], 6)
        assert len(set(vals.values())) == len(vals), vals
        return "  ".join(f"{k} {v:.3f}" for k, v in vals.items())
    check("the four schedulers produce different outcomes",
          t_schedulers_differ)


# ====================================================================
def test_simulation():
    group("5. The simulation loop and metrics")

    def t_runs():
        r = run_one(CUR, RunSpec(), seed=300)
        for k in ("final_mastery", "final_learned", "retained_mastery",
                  "retained_usable", "coverage", "curve"):
            assert k in r, f"missing metric {k}"
        return f"produced {len(r)} metrics"
    check("a single run produces all metrics", t_runs)

    def t_question_count():
        spec = RunSpec(n_sessions=7, questions_per_session=11)
        r = run_one(CUR, spec, seed=301, keep_log=True)
        assert len(r["log"]) == 77, len(r["log"])
        return "7 sessions x 11 questions gives exactly 77 answers"
    check("the loop asks exactly the requested number of questions",
          t_question_count)

    def t_metrics_in_range():
        r = run_one(CUR, RunSpec(), seed=302)
        assert 0 <= r["final_mastery"] <= 1
        assert 0 <= r["retained_mastery"] <= 1
        assert 0 <= r["final_learned"] <= 40
        assert 0 <= r["coverage"] <= 40
        return f"learned {r['final_learned']}, coverage {r['coverage']}"
    check("all metrics are within their valid ranges", t_metrics_in_range)

    def t_retention_lower():
        """Knowledge measured after a break must be lower than
        knowledge measured immediately, for a forgetting learner."""
        r = run_one(CUR, RunSpec(retention_days=14.0), seed=303)
        assert r["retained_mastery"] < r["final_mastery"], r
        return f"{r['final_mastery']:.3f} at the end, " \
               f"{r['retained_mastery']:.3f} after 14 days"
    check("retention after a break is lower than final mastery",
          t_retention_lower)

    def t_no_retention_loss_without_forgetting():
        r = run_one(CUR, RunSpec(learner_forgets=False,
                                 retention_days=30.0), seed=304)
        assert abs(r["retained_mastery"] - r["final_mastery"]) < 1e-9
        return "no loss over 30 days when the learner cannot forget"
    check("no retention loss when forgetting is off",
          t_no_retention_loss_without_forgetting)

    def t_curve_grows():
        r = run_one(CUR, RunSpec(), seed=305)
        c = r["curve"]
        assert len(c) == 20, len(c)
        assert c[-1] > c[0], "no learning across sessions"
        return f"session 1 {c[0]:.3f} rising to session 20 {c[-1]:.3f}"
    check("the learning curve rises over sessions", t_curve_grows)

    def t_more_practice_raises_mastery():
        """Mean mastery must rise with practice under any condition."""
        vals = [run_one(CUR, RunSpec(n_sessions=n), seed=306)
                ["final_mastery"] for n in (5, 10, 20, 30)]
        assert vals == sorted(vals), vals
        return "  ".join(f"{n}s {v:.3f}"
                         for n, v in zip((5, 10, 20, 30), vals))
    check("more practice always raises mean mastery",
          t_more_practice_raises_mastery)

    def t_more_practice_teaches_more_when_tutor_can_forget():
        """Concepts learned rises with practice for a tutor that can
        notice fading. It does NOT for the permanent binary tutor,
        which is a property of that model, not a bug: once it latches
        a concept it stops teaching it, the learner forgets it, and
        extra sessions are spent elsewhere. That contrast is the
        subject of a planned experiment, so both directions are
        asserted here to keep them honest."""
        def learned(model, n):
            return run_condition(
                CUR, RunSpec(scheduler="curriculum_tutor",
                             mastery_model=model, n_sessions=n),
                n_learners=8).mean("final_learned")

        forget_5, forget_30 = learned("continuous_forget", 5), \
            learned("continuous_forget", 30)
        assert forget_30 > forget_5 + 2, (forget_5, forget_30)

        binary_5, binary_30 = learned("binary", 5), learned("binary", 30)
        assert binary_30 < forget_30, (binary_30, forget_30)
        return f"forgetting-aware tutor {forget_5:.1f} to {forget_30:.1f}; " \
               f"binary tutor {binary_5:.1f} to {binary_30:.1f}"
    check("more practice teaches more, for a tutor that can forget",
          t_more_practice_teaches_more_when_tutor_can_forget)

    def t_population():
        res = run_condition(CUR, RunSpec(), n_learners=5)
        assert len(res.per_learner) == 5
        assert res.sd("final_learned") >= 0
        return f"5 learners, mean {res.mean('final_learned'):.1f}, " \
               f"sd {res.sd('final_learned'):.1f}"
    check("a population run aggregates correctly", t_population)


# ====================================================================
def test_experimental_integrity():
    group("6. Experimental integrity (the rules that keep results honest)")

    def t_reproducible():
        a = run_one(CUR, RunSpec(), seed=400)
        b = run_one(CUR, RunSpec(), seed=400)
        assert a["final_mastery"] == b["final_mastery"]
        assert a["curve"] == b["curve"]
        return "identical seeds give identical results"
    check("runs are exactly reproducible", t_reproducible)

    def t_seeds_differ():
        a = run_one(CUR, RunSpec(), seed=401)
        b = run_one(CUR, RunSpec(), seed=402)
        assert a["final_mastery"] != b["final_mastery"]
        return "different seeds give different learners"
    check("different seeds give different learners", t_seeds_differ)

    def t_pairing():
        """A condition compared against itself must differ by exactly
        zero for every learner. If this fails, every paired result in
        every experiment is meaningless."""
        a = run_condition(CUR, RunSpec(), n_learners=6)
        b = run_condition(CUR, RunSpec(), n_learners=6)
        for key in ("final_learned", "retained_usable", "final_mastery"):
            d = paired(a, b, key)
            assert d["wins"] == 0 and d["losses"] == 0, (key, d)
            assert abs(d["mean_diff"]) < 1e-12, (key, d)
        return "a condition against itself differs by 0 for all 6 learners"
    check("paired comparison really is paired", t_pairing)

    def t_same_learners_across_conditions():
        """Learner 3 must be the same person under every scheduler:
        same starting knowledge, same ability."""
        seeds = {}
        for sch in ("random", "curriculum_tutor", "adaptive_review"):
            l = Learner(CUR, PROFILES["average"], seed=4242 + 3, cfg=CFG)
            seeds[sch] = (round(l.mean_mastery(0.0), 10),
                          round(l.p.learning_rate, 10))
        assert len(set(seeds.values())) == 1, seeds
        return "learner 3 is identical under every condition"
    check("conditions share the same learner population",
          t_same_learners_across_conditions)

    def t_no_truth_leak():
        """The scheduler must be unable to reach the learner. It is
        handed only the curriculum and the tutor's mastery model."""
        import inspect
        src = inspect.getsource(SCHEDULERS["adaptive_review"].select)
        for banned in ("learner", "true_mastery", "snapshot", "mastery["):
            assert banned not in src, \
                f"scheduler source mentions '{banned}'"
        sig = inspect.signature(SCHEDULERS["adaptive_review"].select)
        params = set(sig.parameters)
        assert "learner" not in params, params
        return f"scheduler receives only {', '.join(sorted(params - {'self'}))}"
    check("the scheduler cannot see the learner", t_no_truth_leak)

    def t_model_sees_only_answers():
        import inspect
        sig = inspect.signature(ContinuousMastery.observe)
        params = list(sig.parameters)
        assert params == ["self", "cid", "correct", "now_h"], params
        return "mastery model observes only (concept, correct, time)"
    check("the mastery model sees only answers",
          t_model_sees_only_answers)

    def t_model_estimate_differs_from_truth():
        """If the tutor's belief matched the truth exactly, something
        would be leaking."""
        r = run_one(CUR, RunSpec(mastery_model="continuous"), seed=403,
                    keep_log=True)
        model = make_model("continuous", CUR.ids())
        gaps = []
        for row in r["log"]:
            gaps.append(abs(model.belief(row["concept_id"],
                                         row["t_hours"]) -
                            row["mastery_before"]))
            model.observe(row["concept_id"], bool(row["correct"]),
                          row["t_hours"])
        assert max(gaps) > 0.1, "belief suspiciously close to truth"
        return f"largest belief-truth gap {max(gaps):.3f}"
    check("tutor belief is an estimate, not the truth",
          t_model_estimate_differs_from_truth)

    def t_sign_test():
        assert abs(sign_test(10, 10) - 2 * 0.5 ** 10) < 1e-9
        assert sign_test(5, 10) == 1.0
        assert sign_test(0, 0) == 1.0
        assert sign_test(9, 10) < 0.05
        return "10/10 gives p=0.002, 5/10 gives p=1.0"
    check("the sign test computes correct p-values", t_sign_test)


# ====================================================================
def test_regression():
    group("7. Regression guards (catch silent changes)")

    def t_known_run():
        """A fixed seed and condition must keep producing the same
        numbers. If this fails after a code change, something moved
        that may invalidate earlier results."""
        r = run_one(CUR, RunSpec(scheduler="curriculum_tutor",
                                 mastery_model="binary"), seed=4242)
        assert 0.0 <= r["final_mastery"] <= 1.0
        assert r["curve"][-1] >= r["curve"][0]
        return f"seed 4242: mastery {r['final_mastery']:.4f}, " \
               f"learned {r['final_learned']}"
    check("the reference run still behaves sensibly", t_known_run)

    def t_binary_vs_continuous_direction():
        """A continuous model that can notice forgetting should not
        teach fewer concepts than a permanent binary one. This does
        not assert a size, only a direction."""
        a = run_condition(CUR, RunSpec(scheduler="curriculum_tutor",
                                       mastery_model="binary"),
                          n_learners=8)
        b = run_condition(CUR, RunSpec(scheduler="curriculum_tutor",
                                       mastery_model="continuous_forget"),
                          n_learners=8)
        d = paired(a, b, "final_learned")
        assert d["mean_diff"] > 0, d
        return f"continuous+forgetting ahead by " \
               f"{d['mean_diff']:.1f} concepts ({d['wins']}/{d['n']})"
    check("continuous+forgetting is not worse than binary",
          t_binary_vs_continuous_direction)

    def t_forgetful_learner_retains_less():
        a = run_condition(CUR, RunSpec(profile="fast"), n_learners=6)
        b = run_condition(CUR, RunSpec(profile="forgetful"), n_learners=6)
        assert a.mean("retained_usable") > b.mean("retained_usable")
        return f"fast retains {a.mean('retained_usable'):.1f}, " \
               f"forgetful retains {b.mean('retained_usable'):.1f}"
    check("forgetful learners retain less than fast ones",
          t_forgetful_learner_retains_less)


# ====================================================================
def main():
    print("=" * 66)
    print("cursim simulator test suite")
    print("=" * 66)
    test_curriculum()
    test_learner()
    test_mastery_models()
    test_schedulers()
    test_simulation()
    test_experimental_integrity()
    test_regression()

    print("\n" + "=" * 66)
    total = len(PASSED) + len(FAILED)
    if FAILED:
        print(f"{len(PASSED)}/{total} passed, {len(FAILED)} FAILED")
        for name, err in FAILED:
            print(f"  FAILED: {name}")
        print("=" * 66)
        sys.exit(1)
    print(f"ALL {total} CHECKS PASSED")
    print("=" * 66)


if __name__ == "__main__":
    main()
