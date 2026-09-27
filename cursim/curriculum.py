"""cursim.curriculum -- the curriculum data model.

The curriculum is DATA, not code. Every graph lives as JSON under
`data/`, so adding one is a new file, never an edit here:

    data/curriculum_abstract.json   8 concepts, the default
    data/curriculum_language.json   40 concepts, the original, kept so
                                    the earlier experiments and their
                                    committed results stay reproducible

Anything in `data/` named `curriculum_<name>.json` is loadable by
`<name>`, and `available()` lists whatever is actually present, so the
interface picks up a new curriculum with no code change.

Contents:
  * Question, Concept  -- one practice item, one node
  * Curriculum         -- the graph, with structural checks, traversal,
                          a tier layout for drawing, and JSON round-trip
  * build_curriculum() -- load one by name
"""

import json
import os
from dataclasses import dataclass, asdict, field
from typing import Dict, List

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DEFAULT = "abstract"


def available() -> List[str]:
    """Every curriculum name present in data/."""
    if not os.path.isdir(DATA_DIR):
        return []
    return sorted(f[len("curriculum_"):-len(".json")]
                  for f in os.listdir(DATA_DIR)
                  if f.startswith("curriculum_") and f.endswith(".json"))


@dataclass
class Question:
    """One practice item belonging to a single concept."""
    qid: str
    concept_id: str
    prompt: str
    answer: str
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
        """Tier first, then name: a fixed curriculum order that any
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
            json.dump(blob, f, ensure_ascii=False, indent=1)

    @staticmethod
    def from_json(path: str) -> "Curriculum":
        """Load a curriculum from a JSON file written by to_json()."""
        with open(path, encoding="utf-8") as f:
            blob = json.load(f)
        concepts = {}
        for c in blob["concepts"]:
            qs = [Question(**q) for q in c["questions"]]
            concepts[c["cid"]] = Concept(c["cid"], c["name"], c["tier"],
                                         c["prereqs"], qs)
        return Curriculum(concepts, blob.get("name", ""), blob.get("title", ""))


def build_curriculum(name: str = DEFAULT) -> Curriculum:
    """Load a curriculum by name from data/.

    "abstract" (the default) is the small subject-free graph;
    "language" is the original 40-concept one.
    """
    path = os.path.join(DATA_DIR, f"curriculum_{name}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"no curriculum named {name!r} in {DATA_DIR}. "
            f"Available: {', '.join(available()) or 'none'}")
    return Curriculum.from_json(path)


if __name__ == "__main__":
    for n in available():
        c = build_curriculum(n)
        tiers = len({x.tier for x in c.concepts.values()})
        print(f"{n:10s} {len(c.concepts):3d} concepts  "
              f"{len(c.all_questions()):4d} questions  {tiers} tiers  "
              f"roots: {', '.join(c.roots())}")
