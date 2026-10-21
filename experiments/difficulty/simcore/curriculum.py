"""cursim.curriculum -- the curriculum data model.

A curriculum is a directed acyclic graph of subject-free concepts, each
holding a bank of questions that differ only in difficulty. Nothing in
the simulator depends on what is being taught.

Curricula are DATA, not code. Every graph lives as JSON under
`data/curricula/<name>.json`, so adding one is a new file, never an edit
here. `available()` lists what is present and `build_curriculum(name)`
loads one by name. `generate_layered()` makes a new dummy graph from a
seed, for robustness checks on other shapes.

Shipped graphs:

    abstract    8 concepts, a 2-3-2-1 diamond. Small enough to read, but a
                run saturates quickly, so it is for validation.
    layered_40  40 concepts, 290 questions, 5 roots, 7 tiers. Large
                enough that a question budget does not cover everything,
                so scheduling decisions matter. The graph used by the
                forgetting experiments.

Ids are `<tier letter><index>` (A = no prerequisites), so an id states
its own depth.
"""

import json
import os
import random
import string
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Sequence

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "curricula")
DEFAULT = "abstract"


def available() -> List[str]:
    """Every curriculum name present in data/curricula/."""
    if not os.path.isdir(DATA_DIR):
        return []
    return sorted(f[:-len(".json")] for f in os.listdir(DATA_DIR)
                  if f.endswith(".json"))


@dataclass
class Question:
    """One practice item belonging to a single concept. The simulator
    only ever uses the concept it belongs to and its difficulty."""
    qid: str
    concept_id: str
    difficulty: float          # 0 easy .. 1 hard


@dataclass
class Concept:
    """One node in the curriculum graph: its id, display name, tier
    (depth in the prerequisite DAG, tier 0 = no prerequisites), the
    ids of the concepts it depends on, and its bank of Questions."""
    cid: str
    name: str
    tier: int
    prereqs: List[str]
    questions: List[Question] = field(default_factory=list)


class Curriculum:
    """The whole curriculum: a dict of Concepts keyed by id, checked to
    be acyclic on construction. Provides read-only structural queries
    (roots, edges, topo_order, all_questions, layout) plus JSON
    save/load."""

    def __init__(self, concepts: Dict[str, Concept], name: str = "",
                 title: str = ""):
        self.concepts = concepts
        self.name = name
        self.title = title
        assert self.is_dag(), "curriculum graph must be acyclic"

    # -- structure ----------------------------------------------------
    def ids(self) -> List[str]:
        """All concept ids, in dict-insertion order."""
        return list(self.concepts)

    def roots(self) -> List[str]:
        """Concepts with no prerequisites -- the curriculum's entry
        points, i.e. the concepts a learner can start with."""
        return [c.cid for c in self.concepts.values() if not c.prereqs]

    def edges(self) -> List[tuple]:
        """(prerequisite, dependant) pairs, for drawing the graph."""
        return [(p, c.cid) for c in self.concepts.values() for p in c.prereqs]

    def is_dag(self) -> bool:
        """True iff the prerequisite graph has no cycles. Standard
        depth-first traversal with a 3-colour visited set (0 = unseen,
        1 = on the current path, 2 = fully explored); finding a node
        that is still on the current path means a cycle."""
        color = {c: 0 for c in self.concepts}

        def visit(c):
            if color[c] == 1:
                return False
            if color[c] == 2:
                return True
            color[c] = 1
            for p in self.concepts[c].prereqs:
                if p not in self.concepts or not visit(p):
                    return False
            color[c] = 2
            return True

        return all(visit(c) for c in self.concepts)

    def topo_order(self) -> List[str]:
        """Tier first, then id: a fixed curriculum order that any
        non-adaptive baseline can follow."""
        return [c.cid for c in sorted(self.concepts.values(),
                                      key=lambda c: (c.tier, c.cid))]

    def all_questions(self) -> List[Question]:
        """Every Question across every concept, flattened into one
        list (order not meaningful)."""
        return [q for c in self.concepts.values() for q in c.questions]

    def layout(self) -> Dict[str, Dict[str, float]]:
        """Node positions for drawing: one row per tier, evenly spread
        and centred. Computed here rather than in the viewer so every
        picture of this graph agrees. x and y are both in [0, 1]."""
        by_tier: Dict[int, List[str]] = {}
        for c in sorted(self.concepts.values(), key=lambda c: (c.tier, c.cid)):
            by_tier.setdefault(c.tier, []).append(c.cid)
        tiers = sorted(by_tier)
        pos = {}
        for t in tiers:
            row = by_tier[t]
            y = tiers.index(t) / max(1, len(tiers) - 1)
            for i, cid in enumerate(row):
                pos[cid] = {"x": round((i + 1) / (len(row) + 1), 4),
                            "y": round(y, 4), "tier": t}
        return pos

    # -- persistence --------------------------------------------------
    def to_json(self, path: str):
        """Write this curriculum to `path` as JSON."""
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        blob = {
            "name": self.name, "title": self.title,
            "concepts": [
                {"cid": c.cid, "name": c.name, "tier": c.tier,
                 "prereqs": c.prereqs,
                 "questions": [asdict(q) for q in c.questions]}
                for c in self.concepts.values()],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(blob, f, indent=1)

    @staticmethod
    def from_json(path: str) -> "Curriculum":
        """Load a curriculum from a JSON file written by to_json()."""
        with open(path, encoding="utf-8") as f:
            blob = json.load(f)
        concepts = {}
        for c in blob["concepts"]:
            qs = [Question(q["qid"], q["concept_id"], q["difficulty"])
                  for q in c["questions"]]
            concepts[c["cid"]] = Concept(c["cid"], c["name"], c["tier"],
                                         c["prereqs"], qs)
        return Curriculum(concepts, blob.get("name", ""), blob.get("title", ""))


def build_curriculum(name: str = DEFAULT) -> Curriculum:
    """Load a curriculum by name from data/curricula/."""
    path = os.path.join(DATA_DIR, f"{name}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"no curriculum named {name!r} in {DATA_DIR}. "
            f"Available: {', '.join(available()) or 'none'}")
    return Curriculum.from_json(path)


def generate_layered(tier_sizes: Sequence[int] = (4, 5, 5, 4, 3, 2),
                     max_prereqs: int = 2,
                     questions: Sequence[int] = (5, 9),
                     seed: int = 0, name: str = "") -> Curriculum:
    """A seeded dummy curriculum: `tier_sizes[t]` concepts in tier t.

    Every concept below tier 0 takes between 1 and `max_prereqs`
    prerequisites from the tier directly above it, so tiers are exactly
    the depth in the graph and the result is acyclic by construction.
    Each concept gets a random number of questions in the inclusive range
    `questions`, with difficulty drawn around 0.20 + 0.11 * tier. The
    same arguments always give the same curriculum.
    """
    if not tier_sizes or min(tier_sizes) < 1:
        raise ValueError("tier_sizes must be non-empty and all >= 1")
    if len(tier_sizes) > len(string.ascii_uppercase):
        raise ValueError("at most 26 tiers")
    if max_prereqs < 1:
        raise ValueError("max_prereqs must be >= 1")
    lo, hi = questions
    if not 1 <= lo <= hi:
        raise ValueError("questions must be a range with 1 <= lo <= hi")
    rng = random.Random(seed)
    ids = [[f"{string.ascii_uppercase[t]}{i + 1:02d}" for i in range(n)]
           for t, n in enumerate(tier_sizes)]
    concepts: Dict[str, Concept] = {}
    for t, row in enumerate(ids):
        for cid in row:
            if t == 0:
                prereqs = []
            else:
                k = min(len(ids[t - 1]), rng.randint(1, max_prereqs))
                prereqs = sorted(rng.sample(ids[t - 1], k))
            qs = []
            for j in range(rng.randint(lo, hi)):
                d = min(0.95, max(0.05, rng.gauss(0.20 + 0.11 * t, 0.12)))
                qs.append(Question(f"{cid}.q{j + 1}", cid, round(d, 3)))
            concepts[cid] = Concept(cid, cid, t, prereqs, qs)
    return Curriculum(concepts, name or f"layered_seed{seed}",
                      f"generated, tiers {list(tier_sizes)}, seed {seed}")


if __name__ == "__main__":
    for n in available():
        c = build_curriculum(n)
        tiers = len({x.tier for x in c.concepts.values()})
        print(f"{n:12s} {len(c.concepts):3d} concepts  "
              f"{len(c.all_questions()):4d} questions  {tiers} tiers  "
              f"roots: {', '.join(c.roots())}")
