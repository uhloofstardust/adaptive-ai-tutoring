"""Curriculum: a prerequisite DAG of concepts, each with a bank of
questions carrying their own difficulty.

Two departures from CurriculumTutor, both deliberate:

  * questions within a concept are NOT equally difficult. Each has a
    difficulty in [0, 1] which affects how much mastery it takes to
    answer, so difficulty-aware item selection becomes possible.
  * the graph is a language curriculum, not an arithmetic one, so it
    is wider and shallower with several independent roots.

Item text is illustrative. The simulation consumes only concept
membership and difficulty; replace the strings before any human
pilot. Vocabulary concepts carry real Marathi/Bengali pairs where
available, grammar concepts carry pattern descriptions.
"""

import json
import random
from dataclasses import dataclass, asdict, field
from typing import Dict, List

SOURCE_LANG, TARGET_LANG = "Marathi", "Bengali"

# Real word pairs for the vocabulary concepts. Where a concept needs
# more questions than there are pairs, extra items are generated as
# clearly-labelled recall variants.
WORDS = {
    "greetings": [("नमस्कार", "নমস্কার"), ("धन्यवाद", "ধন্যবাদ"),
                  ("होय", "হ্যাঁ"), ("नाही", "না"),
                  ("क्षमा करा", "ক্ষমা করবেন"), ("शुभ रात्री", "শুভ রাত্রি")],
    "numbers_1_5": [("एक", "এক"), ("दोन", "দুই"), ("तीन", "তিন"),
                    ("चार", "চার"), ("पाच", "পাঁচ")],
    "numbers_6_10": [("सहा", "ছয়"), ("सात", "সাত"), ("आठ", "আট"),
                     ("नऊ", "নয়"), ("दहा", "দশ")],
    "colors": [("लाल", "লাল"), ("निळा", "নীল"), ("हिरवा", "সবুজ"),
               ("पिवळा", "হলুদ"), ("पांढरा", "সাদা"), ("काळा", "কালো")],
    "pronouns": [("मी", "আমি"), ("तू", "তুমি"), ("तो", "সে"),
                 ("आम्ही", "আমরা"), ("ते", "তারা")],
    "family": [("आई", "মা"), ("वडील", "বাবা"), ("भाऊ", "ভাই"),
               ("बहीण", "বোন"), ("मुलगा", "ছেলে"), ("मुलगी", "মেয়ে")],
    "food": [("पाणी", "জল"), ("दूध", "দুধ"), ("भात", "ভাত"),
             ("फळ", "ফল"), ("चहा", "চা"), ("मीठ", "নুন")],
    "animals": [("कुत्रा", "কুকুর"), ("मांजर", "বিড়াল"), ("गाय", "গরু"),
                ("पक्षी", "পাখি"), ("मासा", "মাছ")],
    "body": [("हात", "হাত"), ("डोळा", "চোখ"), ("पाय", "পা"),
             ("डोकं", "মাথা"), ("कान", "কান")],
    "household": [("घर", "বাড়ি"), ("दार", "দরজা"), ("खिडकी", "জানালা"),
                  ("पुस्तक", "বই"), ("खुर्ची", "চেয়ার")],
    "time_basic": [("दिवस", "দিন"), ("रात्र", "রাত"), ("सकाळ", "সকাল"),
                   ("आज", "আজ"), ("उद्या", "আগামীকাল")],
    "places": [("शाळा", "স্কুল"), ("दुकान", "দোকান"), ("शहर", "শহর"),
               ("गाव", "গ্রাম"), ("रस्ता", "রাস্তা")],
    "adjectives_basic": [("मोठा", "বড়"), ("लहान", "ছোট"),
                         ("चांगला", "ভালো"), ("नवीन", "নতুন"),
                         ("गरम", "গরম")],
}

# (concept_id, display name, tier, prerequisites, n_questions)
SPEC = [
    # tier 0: independent roots
    ("greetings", "Greetings", 0, [], 8),
    ("numbers_1_5", "Numbers 1-5", 0, [], 7),
    ("colors", "Colors", 0, [], 7),
    ("pronouns", "Pronouns", 0, [], 6),
    ("yes_no", "Yes / no answers", 0, [], 5),
    # tier 1
    ("numbers_6_10", "Numbers 6-10", 1, ["numbers_1_5"], 7),
    ("family", "Family words", 1, ["greetings"], 8),
    ("food", "Food and drink", 1, ["greetings"], 8),
    ("animals", "Animals", 1, ["greetings"], 6),
    ("body", "Body parts", 1, ["greetings"], 6),
    ("household", "Household objects", 1, ["greetings"], 7),
    ("adjectives_basic", "Basic adjectives", 1, ["colors"], 7),
    ("time_basic", "Time words", 1, ["numbers_1_5"], 6),
    ("directions", "Direction words", 1, ["pronouns"], 6),
    # tier 2
    ("plurals", "Plural forms", 2, ["family", "food"], 7),
    ("possessives", "Possessives", 2, ["pronouns", "family"], 7),
    ("verbs_present", "Present tense verbs", 2, ["pronouns"], 9),
    ("question_words", "Question words", 2, ["yes_no", "pronouns"], 7),
    ("places", "Places", 2, ["directions"], 6),
    ("numbers_teens", "Numbers 11-20", 2, ["numbers_6_10"], 7),
    ("weather", "Weather", 2, ["adjectives_basic"], 6),
    ("clothing", "Clothing", 2, ["colors", "household"], 6),
    ("market", "Market words", 2, ["food", "numbers_6_10"], 7),
    ("ailments", "Talking about illness", 2, ["body"], 6),
    # tier 3
    ("negation", "Negation", 3, ["verbs_present", "yes_no"], 7),
    ("verbs_past", "Past tense verbs", 3, ["verbs_present"], 9),
    ("postpositions", "Postpositions", 3, ["places", "possessives"], 8),
    ("simple_sentences", "Simple sentences", 3,
     ["verbs_present", "plurals"], 9),
    ("politeness", "Polite forms", 3, ["greetings", "verbs_present"], 7),
    ("telling_time", "Telling the time", 3,
     ["time_basic", "numbers_teens"], 7),
    ("shopping_talk", "Shopping dialogue", 3,
     ["market", "question_words"], 8),
    ("describing", "Describing people", 3,
     ["adjectives_basic", "body"], 7),
    # tier 4
    ("verbs_future", "Future tense verbs", 4, ["verbs_past"], 8),
    ("compound_sentences", "Compound sentences", 4,
     ["simple_sentences", "negation"], 9),
    ("narration_past", "Narrating past events", 4,
     ["verbs_past", "simple_sentences"], 9),
    ("directions_talk", "Asking for directions", 4,
     ["postpositions", "question_words"], 8),
    ("clinic_talk", "At the clinic", 4, ["ailments", "politeness"], 7),
    # tier 5
    ("conditionals", "Conditional sentences", 5,
     ["compound_sentences"], 8),
    ("formal_register", "Formal register", 5,
     ["politeness", "compound_sentences"], 8),
    # tier 6: depends on a tier-5 concept, so it needs its own level
    ("storytelling", "Storytelling", 6,
     ["narration_past", "conditionals"], 9),
]


@dataclass
class Question:
    qid: str
    concept_id: str
    prompt: str
    answer: str
    difficulty: float          # 0 easy .. 1 hard


@dataclass
class Concept:
    cid: str
    name: str
    tier: int
    prereqs: List[str]
    questions: List[Question] = field(default_factory=list)


class Curriculum:
    def __init__(self, concepts: Dict[str, Concept]):
        self.concepts = concepts
        assert self.is_dag(), "curriculum graph must be acyclic"

    # -- structure ----------------------------------------------------
    def ids(self) -> List[str]:
        return list(self.concepts)

    def roots(self) -> List[str]:
        return [c.cid for c in self.concepts.values() if not c.prereqs]

    def is_dag(self) -> bool:
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
        return [q for c in self.concepts.values() for q in c.questions]

    # -- persistence --------------------------------------------------
    def to_json(self, path: str):
        blob = {
            "source_lang": SOURCE_LANG, "target_lang": TARGET_LANG,
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
        with open(path, encoding="utf-8") as f:
            blob = json.load(f)
        concepts = {}
        for c in blob["concepts"]:
            qs = [Question(**q) for q in c["questions"]]
            concepts[c["cid"]] = Concept(c["cid"], c["name"], c["tier"],
                                         c["prereqs"], qs)
        return Curriculum(concepts)


def build_curriculum(seed: int = 11) -> Curriculum:
    """Generate the curriculum deterministically.

    Question difficulty rises with tier (later concepts are harder)
    and varies within a concept, so that item selection has something
    to choose between.
    """
    rng = random.Random(seed)
    concepts = {}
    for cid, name, tier, prereqs, nq in SPEC:
        base = 0.20 + 0.11 * tier              # tier 0 easy, tier 5 hard
        pairs = WORDS.get(cid, [])
        qs = []
        for i in range(nq):
            d = min(0.95, max(0.05, rng.gauss(base, 0.12)))
            if i < len(pairs):
                src, tgt = pairs[i]
                prompt = f"{TARGET_LANG} for '{src}'?"
                answer = tgt
            else:
                prompt = f"{name}: production item {i + 1}"
                answer = f"<{cid}_{i + 1}>"
            qs.append(Question(f"{cid}_q{i + 1}", cid, prompt, answer,
                               round(d, 3)))
        concepts[cid] = Concept(cid, name, tier, list(prereqs), qs)
    return Curriculum(concepts)


if __name__ == "__main__":
    cur = build_curriculum()
    n_q = len(cur.all_questions())
    print(f"{len(cur.concepts)} concepts, {n_q} questions, "
          f"{len(cur.roots())} roots, "
          f"max tier {max(c.tier for c in cur.concepts.values())}")
    cur.to_json("data/curriculum.json")
    print("wrote data/curriculum.json")
