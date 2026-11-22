"""Synthetic student simulator for CurriculumTutor experiments.

Purpose
-------
We have no real learners yet, so we generate interaction data with a
controllable synthetic student. The data is used for two separate
research tracks:

    (1) comparing question-SELECTION algorithms (random vs MAB), and
    (2) comparing student MODELS / tracers (BKT and its extensions).

Three components, deliberately kept apart
-----------------------------------------
    QuestionSelector   decides WHICH concept to present next.
                       This is where the MAB algorithm goes.
    StudentSimulator   decides WHETHER the answer is correct, using
                       its hidden true knowledge state.
    StudentModel       estimates knowledge from observed answers only.
                       This is where the improved BKT goes.

The single rule that keeps the experiment honest: the selector and the
student model never see the simulator's true mastery. True mastery is
written to the logs for evaluation and nowhere else. A selector may
consult the student model's ESTIMATES (that is what a deployed tutor
does); it may not consult the simulator.

Two design decisions worth knowing about
----------------------------------------
1. The simulator's dynamics are NOT BKT. BKT has a two-state hidden
   variable and a fixed learn probability; this simulator uses
   continuous mastery, per-concept difficulty, per-student learning
   rate, and continuous-time forgetting. This is on purpose. If the
   generative model were BKT, then testing BKT against it would be
   rigged: the model could recover the truth exactly, and any
   extension would look pointless. A mismatched simulator is the
   standard way to keep model comparison meaningful.

2. Practice happens in SESSIONS separated by a time gap (default one
   day), not in one flat stream. Forgetting therefore has room to act
   between sessions, which is what makes scheduling a real decision
   problem: an item's state changes even when it is not chosen. That
   is the restless-bandit structure the MAB work will target.

Usage
-----
    python student_simulator.py               # demo comparison + CSV
    python student_simulator.py --selftest    # invariant checks

Only the Python standard library is used.
"""

import csv
import math
import random
import statistics
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# --------------------------------------------------------------------
# Configuration. Every tunable number lives here so experiments are
# easy to vary and easy to report.
# --------------------------------------------------------------------
@dataclass
class SimConfig:
    n_options: int = 4              # MCQ options; guess rate is 1/n
    slip: float = 0.05              # P(wrong | fully mastered)
    gain_correct: float = 0.45      # learning increment after a hit
    gain_wrong: float = 0.12        # smaller increment after a miss:
                                    # the learner still sees the answer.
                                    # Set negative for "mistakes hurt".
    forget_half_life_days: float = 6.0   # for an average-difficulty item
    mastery_floor: float = 0.05     # forgetting never goes below this
    init_mastery_mean: float = 0.15  # prior knowledge before practice
    init_mastery_spread: float = 0.10
    learning_rate_mean: float = 1.0  # per-student multiplier on gains
    learning_rate_spread: float = 0.35
    mastery_threshold: float = 0.80  # "learned" for reporting


# --------------------------------------------------------------------
# Learning domain: vocabulary between two Indian languages.
# Replace VOCAB to change the language pair; nothing else depends on it.
# The strings are only labels as far as the simulator is concerned, but
# verify them with native readers before reusing this list with real
# learners.
# --------------------------------------------------------------------
SOURCE_LANG, TARGET_LANG = "Marathi", "Bengali"

# (group, source word, target word, difficulty 0..1)
VOCAB = [
    ("food", "पाणी", "জল", 0.20),
    ("food", "दूध", "দুধ", 0.25),
    ("food", "चहा", "চা", 0.20),
    ("food", "भात", "ভাত", 0.30),
    ("food", "फळ", "ফল", 0.35),
    ("food", "अंडं", "ডিম", 0.40),
    ("food", "मीठ", "নুন", 0.45),
    ("food", "साखर", "চিনি", 0.45),
    ("family", "आई", "মা", 0.15),
    ("family", "वडील", "বাবা", 0.20),
    ("family", "भाऊ", "ভাই", 0.25),
    ("family", "बहीण", "বোন", 0.30),
    ("family", "मुलगा", "ছেলে", 0.40),
    ("family", "मुलगी", "মেয়ে", 0.40),
    ("body", "हात", "হাত", 0.20),
    ("body", "डोळा", "চোখ", 0.35),
    ("body", "डोकं", "মাথা", 0.40),
    ("body", "पाय", "পা", 0.25),
    ("animals", "कुत्रा", "কুকুর", 0.30),
    ("animals", "मांजर", "বিড়াল", 0.40),
    ("animals", "गाय", "গরু", 0.25),
    ("animals", "पक्षी", "পাখি", 0.40),
    ("animals", "मासा", "মাছ", 0.30),
    ("colors", "लाल", "লাল", 0.10),
    ("colors", "निळा", "নীল", 0.30),
    ("colors", "हिरवा", "সবুজ", 0.45),
    ("colors", "पिवळा", "হলুদ", 0.45),
    ("colors", "पांढरा", "সাদা", 0.35),
    ("colors", "काळा", "কালো", 0.20),
    ("numbers", "एक", "এক", 0.10),
    ("numbers", "दोन", "দুই", 0.20),
    ("numbers", "तीन", "তিন", 0.20),
    ("numbers", "चार", "চার", 0.15),
    ("numbers", "पाच", "পাঁচ", 0.25),
    ("time", "दिवस", "দিন", 0.25),
    ("time", "रात्र", "রাত", 0.25),
    ("time", "सकाळ", "সকাল", 0.35),
    ("places", "घर", "বাড়ি", 0.20),
    ("places", "रस्ता", "রাস্তা", 0.30),
    ("places", "शहर", "শহর", 0.30),
    ("places", "गाव", "গ্রাম", 0.40),
    ("places", "शाळा", "স্কুল", 0.20),
    ("places", "दुकान", "দোকান", 0.35),
    ("adjectives", "मोठा", "বড়", 0.30),
    ("adjectives", "लहान", "ছোট", 0.35),
    ("adjectives", "चांगला", "ভালো", 0.30),
    ("adjectives", "नवीन", "নতুন", 0.40),
    ("adjectives", "गरम", "গরম", 0.30),
]


@dataclass
class Concept:
    """One vocabulary item. `difficulty` slows learning and speeds
    forgetting; it is a property of the item, hidden from the selector
    and the student model exactly like true mastery."""
    concept_id: str
    source: str
    target: str
    group: str
    difficulty: float
    distractors: List[str] = field(default_factory=list)


def build_concepts(vocab=VOCAB) -> Dict[str, Concept]:
    """Distractors are filled in automatically from the same semantic
    group (falling back to any other item), so that adding vocabulary
    means adding one row, not hand-writing option lists."""
    concepts = {}
    for i, (group, src, tgt, diff) in enumerate(vocab):
        cid = f"vocab_{i:02d}"
        concepts[cid] = Concept(cid, src, tgt, group, diff)
    for c in concepts.values():
        same = [o.target for o in concepts.values()
                if o.group == c.group and o.concept_id != c.concept_id]
        other = [o.target for o in concepts.values()
                 if o.group != c.group]
        c.distractors = same + other      # plausible ones first
    return concepts


def make_question(concept: Concept, cfg: SimConfig,
                  rng: random.Random) -> dict:
    """Build one MCQ in the agreed interchange format."""
    k = cfg.n_options - 1
    plausible = concept.distractors[:max(k, 6)]
    picked = rng.sample(plausible, k) if len(plausible) >= k \
        else list(plausible)
    options = picked + [concept.target]
    rng.shuffle(options)
    return {
        "concept_id": concept.concept_id,
        "question": (f"What is the {TARGET_LANG} word for "
                     f"'{concept.source}'?"),
        "options": options,
        "correct_option": options.index(concept.target),
    }


# --------------------------------------------------------------------
# 2. The simulated student. Owns the hidden truth.
# --------------------------------------------------------------------
@dataclass
class ConceptState:
    mastery: float
    seen: int = 0
    correct: int = 0
    wrong: int = 0
    last_seen_h: Optional[float] = None   # hours on the virtual clock


class StudentSimulator:
    """A synthetic learner.

    Hidden state per concept: continuous mastery in [0, 1] plus simple
    counters. Nothing here is exposed to the selector or the student
    model; `true_mastery()` exists for logging and evaluation only.
    """

    def __init__(self, concepts: Dict[str, Concept], cfg: SimConfig,
                 seed: int, student_id: int = 0):
        self.cfg = cfg
        self.concepts = concepts
        self.student_id = student_id
        self.rng = random.Random(seed)
        # Per-student ability: the same selector faces easy and hard
        # learners, which is what makes averaged comparisons meaningful.
        self.learning_rate = max(0.25, self.rng.gauss(
            cfg.learning_rate_mean, cfg.learning_rate_spread))
        self.state: Dict[str, ConceptState] = {}
        for cid, c in concepts.items():
            m0 = self.rng.gauss(cfg.init_mastery_mean * (1 - c.difficulty),
                                cfg.init_mastery_spread)
            self.state[cid] = ConceptState(mastery=min(0.6, max(0.0, m0)))

    # -- forgetting ---------------------------------------------------
    def _decay_rate(self, concept: Concept) -> float:
        """Per-hour exponential rate. Harder items are forgotten
        faster; half-life is configured for an average item."""
        half_life_h = self.cfg.forget_half_life_days * 24.0
        half_life_h *= (1.3 - 0.6 * concept.difficulty)
        return math.log(2.0) / half_life_h

    def _apply_forgetting(self, cid: str, now_h: float) -> float:
        st = self.state[cid]
        if st.last_seen_h is None:
            return st.mastery
        dt = max(0.0, now_h - st.last_seen_h)
        if dt == 0.0:
            return st.mastery
        floor = self.cfg.mastery_floor
        decayed = floor + (st.mastery - floor) * math.exp(
            -self._decay_rate(self.concepts[cid]) * dt)
        st.mastery = max(floor, min(1.0, decayed))
        return st.mastery

    # -- answering ----------------------------------------------------
    def answer(self, question: dict, now_h: float) -> dict:
        """Receive an MCQ, return the response. Mastery is brought up
        to date (forgetting), the answer is sampled, and then the
        learning update is applied."""
        cid = question["concept_id"]
        concept = self.concepts[cid]
        st = self.state[cid]
        m_before = self._apply_forgetting(cid, now_h)

        guess = 1.0 / len(question["options"])
        p_correct = m_before * (1 - self.cfg.slip) + (1 - m_before) * guess
        correct = self.rng.random() < p_correct

        if correct:
            selected = question["correct_option"]
        else:
            wrong_idx = [i for i in range(len(question["options"]))
                         if i != question["correct_option"]]
            selected = self.rng.choice(wrong_idx)

        # learning: gains shrink as mastery approaches 1, are scaled by
        # the student's ability and damped by item difficulty
        gain = (self.cfg.gain_correct if correct else self.cfg.gain_wrong)
        alpha = self.learning_rate * (1.0 - 0.6 * concept.difficulty)
        st.mastery = min(1.0, max(0.0,
                                  st.mastery + alpha * gain *
                                  (1.0 - st.mastery)))
        st.seen += 1
        st.correct += int(correct)
        st.wrong += int(not correct)
        st.last_seen_h = now_h

        return {"concept_id": cid, "selected_option": selected,
                "correct": bool(correct),
                # for logging only, never given to selector or model:
                "_true_mastery_before": m_before,
                "_true_mastery_after": st.mastery,
                "_exposures_before": st.seen - 1}

    # -- evaluation access (logs only) --------------------------------
    def true_mastery(self, cid: str, now_h: float) -> float:
        return self._apply_forgetting(cid, now_h)

    def true_mastery_all(self, now_h: float) -> Dict[str, float]:
        return {cid: self.true_mastery(cid, now_h) for cid in self.state}


# --------------------------------------------------------------------
# 3. Student models (tracers). Observe answers, estimate knowledge.
#    Replace BKTTracer with the improved model under study.
# --------------------------------------------------------------------
class StudentModel:
    """Interface: sees only (concept_id, correct, time)."""

    def observe(self, concept_id: str, correct: bool, now_h: float):
        raise NotImplementedError

    def estimate(self, concept_id: str, now_h: float) -> float:
        raise NotImplementedError


class BKTTracer(StudentModel):
    """Classical BKT, one belief per concept, shared parameters.

    Set forget_per_day > 0 to get the forgetting variant: belief decays
    toward a floor between practices. This is the hook for the improved
    student model; parameters can later be replaced by values fitted on
    real logs.
    """

    def __init__(self, concept_ids, p_L0=0.20, p_T=0.15, p_S=0.10,
                 p_G=0.25, forget_per_day=0.0, floor=0.05):
        self.p_L0, self.p_T = p_L0, p_T
        self.p_S, self.p_G = p_S, p_G
        self.forget_per_day, self.floor = forget_per_day, floor
        self.belief = {cid: p_L0 for cid in concept_ids}
        self.updated_h = {cid: None for cid in concept_ids}

    def _decayed(self, cid: str, now_h: float) -> float:
        b = self.belief[cid]
        t0 = self.updated_h[cid]
        if t0 is None or self.forget_per_day <= 0.0:
            return b
        days = max(0.0, (now_h - t0) / 24.0)
        b = self.floor + (b - self.floor) * ((1 - self.forget_per_day) ** days)
        return max(self.floor, min(0.99, b))

    def observe(self, concept_id: str, correct: bool, now_h: float):
        b = self._decayed(concept_id, now_h)
        if correct:
            num, rest = b * (1 - self.p_S), (1 - b) * self.p_G
        else:
            num, rest = b * self.p_S, (1 - b) * (1 - self.p_G)
        post = num / (num + rest)
        self.belief[concept_id] = post + (1 - post) * self.p_T
        self.updated_h[concept_id] = now_h

    def estimate(self, concept_id: str, now_h: float) -> float:
        return self._decayed(concept_id, now_h)


# --------------------------------------------------------------------
# 4. Question selectors. Swap these; nothing else changes.
# --------------------------------------------------------------------
class QuestionSelector:
    """Interface. `select` may use the student model's estimates and
    the observed history. It must never touch the simulator."""
    name = "base"

    def select(self, concept_ids: List[str], model: StudentModel,
               history: List[dict], now_h: float,
               rng: random.Random) -> str:
        raise NotImplementedError


class RandomSelector(QuestionSelector):
    """Required baseline: uniform over concepts, no state at all."""
    name = "random"

    def select(self, concept_ids, model, history, now_h, rng):
        return rng.choice(concept_ids)


class RoundRobinSelector(QuestionSelector):
    """Non-adaptive curriculum order: a second, stronger baseline."""
    name = "round_robin"

    def __init__(self):
        self.i = 0

    def select(self, concept_ids, model, history, now_h, rng):
        cid = concept_ids[self.i % len(concept_ids)]
        self.i += 1
        return cid


class ModelGreedySelector(QuestionSelector):
    """Illustrates how a selector consults the STUDENT MODEL (never the
    simulator): pick the concept whose estimated mastery is lowest,
    with a small random tie-break. A MABQuestionSelector plugs in at
    exactly this seam."""
    name = "model_greedy"

    def select(self, concept_ids, model, history, now_h, rng):
        scored = [(model.estimate(cid, now_h) + rng.uniform(0, 1e-3), cid)
                  for cid in concept_ids]
        scored.sort()
        return scored[0][1]


SELECTORS = {
    "random": RandomSelector,
    "round_robin": RoundRobinSelector,
    "model_greedy": ModelGreedySelector,
}


# --------------------------------------------------------------------
# 5. Experiment loop
# --------------------------------------------------------------------
def run_student(selector: QuestionSelector, concepts, cfg: SimConfig,
                seed: int, student_id: int, n_sessions: int,
                items_per_session: int, gap_hours: float,
                model_factory=None) -> List[dict]:
    """One learner, one selector. Returns the interaction log."""
    sim = StudentSimulator(concepts, cfg, seed=seed, student_id=student_id)
    model = (model_factory(list(concepts)) if model_factory
             else BKTTracer(list(concepts)))
    rng = random.Random(seed + 99991)   # selector/question randomness,
                                        # kept separate from the student's
    cids = list(concepts)
    log, now_h, step = [], 0.0, 0
    # What the selector is allowed to see: exactly what a deployed
    # tutor would have. The evaluation log below carries true mastery
    # and must never be handed to the selector or the student model.
    observed: List[dict] = []

    for session in range(n_sessions):
        for _ in range(items_per_session):
            cid = selector.select(cids, model, observed, now_h, rng)
            q = make_question(concepts[cid], cfg, rng)
            resp = sim.answer(q, now_h)

            est_before = model.estimate(cid, now_h)
            model.observe(cid, resp["correct"], now_h)

            log.append({
                "student_id": student_id,
                "selector": selector.name,
                "timestep": step,
                "session": session,
                "t_hours": round(now_h, 3),
                "concept_id": cid,
                "question": q["question"],
                "options": " | ".join(q["options"]),
                "correct_option": q["correct_option"],
                "selected_option": resp["selected_option"],
                "correct": int(resp["correct"]),
                "exposures_before": resp["_exposures_before"],
                # evaluation only, not visible to selector or model:
                "true_mastery_before": round(resp["_true_mastery_before"], 4),
                "true_mastery_after": round(resp["_true_mastery_after"], 4),
                "est_mastery_before": round(est_before, 4),
            })
            observed.append({"timestep": step, "concept_id": cid,
                             "correct": int(resp["correct"]),
                             "t_hours": now_h})
            step += 1
            now_h += 1.0 / 60.0          # a minute per question
        now_h += gap_hours               # gap before the next session

    # final snapshot for evaluation
    final_true = sim.true_mastery_all(now_h)
    final_est = {cid: model.estimate(cid, now_h) for cid in cids}
    for row in log:
        row["_final"] = False
    log.append({"student_id": student_id, "selector": selector.name,
                "timestep": -1, "session": -1, "t_hours": round(now_h, 3),
                "concept_id": "__final__", "question": "", "options": "",
                "correct_option": -1, "selected_option": -1, "correct": -1,
                "exposures_before": -1,
                "true_mastery_before": -1, "true_mastery_after": -1,
                "est_mastery_before": -1, "_final": True,
                "_final_true": final_true, "_final_est": final_est})
    return log


def run_experiment(selector_name: str, concepts, cfg: SimConfig,
                   n_students=20, n_sessions=12, items_per_session=40,
                   gap_hours=24.0, base_seed=2026,
                   model_factory=None) -> List[dict]:
    """Run one selector over a population of students.

    Every selector is run with the SAME base_seed, so the populations
    are identical across selectors: the comparison is paired, and a
    difference in outcomes is the selector's doing, not luck in who
    was simulated.
    """
    all_logs = []
    for s in range(n_students):
        selector = SELECTORS[selector_name]()      # fresh state per student
        all_logs.extend(run_student(
            selector, concepts, cfg, seed=base_seed + s, student_id=s,
            n_sessions=n_sessions, items_per_session=items_per_session,
            gap_hours=gap_hours, model_factory=model_factory))
    return all_logs


# --------------------------------------------------------------------
# 6. Evaluation
# --------------------------------------------------------------------
def summarize(log: List[dict], cfg: SimConfig) -> dict:
    rows = [r for r in log if not r.get("_final")]
    finals = [r for r in log if r.get("_final")]
    acc = statistics.mean(r["correct"] for r in rows)

    by_session = {}
    for r in rows:
        by_session.setdefault(r["session"], []).append(r["correct"])
    acc_curve = [round(statistics.mean(v), 3)
                 for _, v in sorted(by_session.items())]

    # Per-student values are kept, not just their means. Selectors are
    # run on identical seeded populations, so the honest comparison is
    # the PAIRED difference student by student; a mean alone hides
    # whether a gain is consistent or one lucky learner.
    acc_by_student = {}
    for r in rows:
        acc_by_student.setdefault(r["student_id"], []).append(r["correct"])

    per_student, final_means, learned, mae = {}, [], [], []
    for f in finals:
        true, est = f["_final_true"], f["_final_est"]
        sid = f["student_id"]
        fm = statistics.mean(true.values())
        lr = sum(1 for v in true.values() if v >= cfg.mastery_threshold)
        er = statistics.mean(abs(est[c] - true[c]) for c in true)
        final_means.append(fm)
        learned.append(lr)
        mae.append(er)
        per_student[sid] = {
            "accuracy": statistics.mean(acc_by_student.get(sid, [0])),
            "final_mastery": fm, "learned": lr, "tracer_mae": er}

    # How practice was distributed over concepts. A bandit that starts
    # concentrating shows up here long before it shows up in a mean.
    exposures = {}
    for r in rows:
        exposures[r["concept_id"]] = exposures.get(r["concept_id"], 0) + 1
    n_students = max(1, len(finals))
    exposures = {c: v / n_students for c, v in exposures.items()}

    concept_mastery = {}
    for f in finals:
        for cid, v in f["_final_true"].items():
            concept_mastery.setdefault(cid, []).append(v)
    concept_mastery = {c: statistics.mean(v)
                       for c, v in concept_mastery.items()}

    return {
        "selector": rows[0]["selector"] if rows else "?",
        "n_students": len(finals),
        "n_interactions": len(rows),
        "accuracy": round(acc, 4),
        "accuracy_by_session": acc_curve,
        "final_true_mastery": round(statistics.mean(final_means), 4),
        "concepts_learned": round(statistics.mean(learned), 2),
        "n_concepts": len(concept_mastery),
        "tracer_mae": round(statistics.mean(mae), 4),
        "concept_mastery": concept_mastery,
        "per_student": per_student,
        "exposures": exposures,
    }


def print_summary(s: dict, cfg: SimConfig, show_concepts=False):
    print(f"\n--- {s['selector']} "
          f"({s['n_students']} students, {s['n_interactions']} answers)")
    print(f"  overall accuracy      {s['accuracy']:.3f}")
    print(f"  accuracy by session   {s['accuracy_by_session']}")
    print(f"  final true mastery    {s['final_true_mastery']:.3f}")
    print(f"  concepts >= {cfg.mastery_threshold:.2f}       "
          f"{s['concepts_learned']:.2f} of {s['n_concepts']}")
    print(f"  tracer MAE vs truth   {s['tracer_mae']:.3f}")
    if show_concepts:
        worst = sorted(s["concept_mastery"].items(),
                       key=lambda kv: kv[1])[:5]
        print("  weakest concepts      " +
              ", ".join(f"{c} {v:.2f}" for c, v in worst))


def _sign_test_p(k: int, n: int) -> float:
    """Two-sided sign test: probability of an outcome at least as
    unlikely as k successes in n coin flips. Reported so that a small
    mean difference is not mistaken for a real effect."""
    if n == 0:
        return 1.0
    probs = [math.comb(n, i) * 0.5 ** n for i in range(n + 1)]
    obs = probs[k]
    return min(1.0, sum(p for p in probs if p <= obs + 1e-12))


def paired_differences(results: dict, reference: str = "random",
                       metric: str = "final_mastery") -> List[dict]:
    """Student-by-student difference against a reference selector.

    Valid only because every selector was run on the same seeded
    students: student 7 under the MAB is the same simulated learner as
    student 7 under random.
    """
    ref = results[reference]["per_student"]
    out = []
    for name, s in results.items():
        if name == reference:
            continue
        ids = sorted(set(ref) & set(s["per_student"]))
        diffs = [s["per_student"][i][metric] - ref[i][metric] for i in ids]
        wins = sum(1 for d in diffs if d > 0)
        losses = sum(1 for d in diffs if d < 0)
        out.append({
            "selector": name,
            "n": len(diffs),
            "mean_diff": statistics.mean(diffs) if diffs else 0.0,
            "sd_diff": statistics.stdev(diffs) if len(diffs) > 1 else 0.0,
            "wins": wins, "losses": losses,
            "p_sign": _sign_test_p(wins, wins + losses),
        })
    return out


def print_paired(results, cfg, reference="random",
                 metric="final_mastery"):
    rows = paired_differences(results, reference, metric)
    if not rows:
        return
    print(f"\n=== paired difference in {metric} vs '{reference}' "
          f"(same students) ===")
    print(f"{'selector':14s} {'mean diff':>10s} {'sd':>8s} "
          f"{'better':>8s} {'worse':>7s} {'sign p':>8s}")
    for r in rows:
        print(f"{r['selector']:14s} {r['mean_diff']:>+10.4f} "
              f"{r['sd_diff']:>8.4f} {r['wins']:>8d} {r['losses']:>7d} "
              f"{r['p_sign']:>8.3f}")
    print("  a mean gain with a sign p above ~0.05 is not yet evidence; "
          "raise n_students")


def print_exposures(results: dict, top_k: int = 5, bins: int = 8):
    """Mean exposures per concept per student, with concentration.

    top_k share is the fraction of all questions spent on the k most
    practised concepts: a uniform selector over 48 concepts sits near
    k/48, a concentrating bandit climbs well above it."""
    print("\n=== practice distribution over concepts "
          "(mean exposures per student) ===")
    print(f"{'selector':14s} {'min':>5s} {'median':>7s} {'max':>6s} "
          f"{'top5 share':>11s}   histogram")
    for name, s in results.items():
        vals = sorted(s["exposures"].values())
        total = sum(vals)
        top = sum(sorted(vals, reverse=True)[:top_k]) / total if total else 0
        lo, hi = min(vals), max(vals)
        width = (hi - lo) / bins if hi > lo else 1.0
        counts = [0] * bins
        for v in vals:
            counts[min(bins - 1, int((v - lo) / width))] += 1
        blocks = " .:-=+*#@"
        peak = max(counts) or 1
        hist = "".join(blocks[min(len(blocks) - 1,
                                  int(c / peak * (len(blocks) - 1)))]
                       for c in counts)
        print(f"{name:14s} {lo:>5.1f} {statistics.median(vals):>7.1f} "
              f"{hi:>6.1f} {top:>11.1%}   |{hist}|")
    print(f"  histogram: {bins} bins from each selector's own min to "
          "max, denser = more concepts in that band")


def compare_selectors(names, concepts, cfg, **kw):
    """Paired comparison: identical student populations per selector."""
    results = {}
    for n in names:
        results[n] = summarize(
            run_experiment(n, concepts, cfg, **kw), cfg)
    print("\n=== comparison "
          "(same students, same seeds, different selectors) ===")
    print(f"{'selector':14s} {'accuracy':>9s} {'final mastery':>14s} "
          f"{'concepts learned':>17s} {'tracer MAE':>11s}")
    for n, s in results.items():
        print(f"{n:14s} {s['accuracy']:>9.3f} "
              f"{s['final_true_mastery']:>14.3f} "
              f"{s['concepts_learned']:>17.2f} {s['tracer_mae']:>11.3f}")
    ref = "random" if "random" in results else list(results)[0]
    if len(results) > 1:
        print_paired(results, cfg, reference=ref, metric="final_mastery")
        print_paired(results, cfg, reference=ref, metric="learned")
    print_exposures(results)
    return results


def write_csv(log: List[dict], path: str):
    rows = [r for r in log if not r.get("_final")]
    cols = ["student_id", "selector", "timestep", "session", "t_hours",
            "concept_id", "question", "options", "correct_option",
            "selected_option", "correct", "exposures_before",
            "true_mastery_before", "true_mastery_after",
            "est_mastery_before"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {path} ({len(rows)} interactions)")


# --------------------------------------------------------------------
# 7. Self-test: invariants that must hold before trusting any result
# --------------------------------------------------------------------
def selftest():
    cfg = SimConfig()
    concepts = build_concepts()
    cids = list(concepts)

    # 1. questions are well formed
    rng = random.Random(0)
    q = make_question(concepts[cids[0]], cfg, rng)
    assert len(q["options"]) == cfg.n_options
    assert len(set(q["options"])) == cfg.n_options, "duplicate options"
    assert q["options"][q["correct_option"]] == concepts[cids[0]].target
    print(f"question format PASSED: {cfg.n_options} distinct options, "
          "correct index points at the target word")

    # 2. repeated practice raises true mastery
    sim = StudentSimulator(concepts, cfg, seed=1)
    cid = cids[0]
    m0 = sim.state[cid].mastery
    t = 0.0
    for _ in range(10):
        sim.answer(make_question(concepts[cid], cfg, rng), t)
        t += 0.02
    m1 = sim.state[cid].mastery
    assert m1 > m0, (m0, m1)
    print(f"learning PASSED: mastery {m0:.3f} -> {m1:.3f} "
          "after 10 practices")

    # 3. forgetting lowers mastery across a gap
    m_gap = sim.true_mastery(cid, t + 30 * 24)
    assert m_gap < m1, (m1, m_gap)
    print(f"forgetting PASSED: {m1:.3f} decays to {m_gap:.3f} "
          "after 30 idle days")

    # 4. reproducibility: same seed gives an identical log
    kw = dict(n_students=3, n_sessions=2, items_per_session=8,
              base_seed=7)
    a = run_experiment("random", concepts, cfg, **kw)
    b = run_experiment("random", concepts, cfg, **kw)
    ka = [(r["timestep"], r["concept_id"], r["correct"])
          for r in a if not r.get("_final")]
    kb = [(r["timestep"], r["concept_id"], r["correct"])
          for r in b if not r.get("_final")]
    assert ka == kb and len(ka) == 3 * 2 * 8
    print(f"reproducibility PASSED: two runs of {len(ka)} interactions "
          "are identical")

    # 5. the model's estimate is not the truth (no leakage)
    rows = [r for r in a if not r.get("_final")]
    diffs = [abs(r["est_mastery_before"] - r["true_mastery_before"])
             for r in rows]
    assert max(diffs) > 0.05, "estimates suspiciously equal to truth"
    print(f"separation PASSED: estimate and truth differ "
          f"(max gap {max(diffs):.3f}), so no true state is leaking")

    # 6. selectors are interchangeable and actually differ
    picks = {}
    for n in SELECTORS:
        log = run_experiment(n, concepts, cfg, n_students=2, n_sessions=2,
                             items_per_session=10, base_seed=5)
        picks[n] = [r["concept_id"] for r in log if not r.get("_final")]
    assert picks["random"] != picks["round_robin"] != picks["model_greedy"]
    print("selector swap PASSED: all three selectors run and produce "
          "different question orders")

    # 7. the selector cannot see hidden state, mechanically enforced
    forbidden = ("true_mastery", "mastery", "difficulty", "_true")

    class LeakProbe(QuestionSelector):
        name = "leak_probe"

        def select(self, concept_ids, model, history, now_h, rng):
            for row in history:
                for key in row:
                    assert not any(f in key for f in forbidden), \
                        f"selector can see hidden field: {key}"
            return rng.choice(concept_ids)

    SELECTORS["leak_probe"] = LeakProbe
    run_experiment("leak_probe", concepts, cfg, n_students=2,
                   n_sessions=2, items_per_session=10, base_seed=3)
    del SELECTORS["leak_probe"]
    print("no-leak PASSED: the history given to the selector exposes "
          "only concept_id, correct and time")

    # 8. the pairing is real: a selector against itself must differ by
    # exactly zero for every student, which only holds if the same
    # seeds produce the same learners under each run
    kw2 = dict(n_students=6, n_sessions=3, items_per_session=10,
               base_seed=11)
    r1 = summarize(run_experiment("random", concepts, cfg, **kw2), cfg)
    r2 = summarize(run_experiment("random", concepts, cfg, **kw2), cfg)
    pd = paired_differences({"random": r1, "copy": r2},
                            reference="random")[0]
    assert pd["n"] == 6 and pd["wins"] == 0 and pd["losses"] == 0, pd
    assert abs(pd["mean_diff"]) < 1e-12, pd
    print(f"pairing PASSED: a selector against itself differs by "
          f"{pd['mean_diff']:.1e} for all {pd['n']} students")

    print("\nALL SELF-TESTS PASSED")


# --------------------------------------------------------------------
def main():
    cfg = SimConfig()
    concepts = build_concepts()
    print(f"{SOURCE_LANG} -> {TARGET_LANG}, {len(concepts)} concepts, "
          f"{cfg.n_options}-option MCQ")

    # 12 daily sessions x 40 questions over 48 concepts: enough
    # exposure for mastery to build, little enough that scheduling
    # still matters. Metrics saturate if this is made much larger.
    kw = dict(n_students=20, n_sessions=12, items_per_session=40,
              gap_hours=24.0, base_seed=2026)
    results = compare_selectors(list(SELECTORS), concepts, cfg, **kw)
    for name in SELECTORS:
        print_summary(results[name], cfg, show_concepts=(name == "random"))

    # keep one full log for downstream student-model work
    log = run_experiment("random", concepts, cfg, **kw)
    write_csv(log, "interactions_random.csv")
    print("\nTo test a MAB selector: subclass QuestionSelector, add it "
          "to SELECTORS, rerun.")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        main()
