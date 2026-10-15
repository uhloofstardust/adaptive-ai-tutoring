"""Draw a curriculum's prerequisite graph."""

from ..registry import experiment
from cursim.curriculum import build_curriculum
from .plots import fig_curriculum


@experiment("curriculum_graph", "The prerequisite graph of a curriculum, "
            "laid out by tier.", defaults={}, curriculum="layered_40")
def curriculum_graph(cur=None, **_):
    cur = cur or build_curriculum("layered_40")
    rows = [dict(concept=c.cid, tier=c.tier, n_questions=len(c.questions),
                 prerequisites=" ".join(c.prereqs))
            for c in cur.concepts.values()]
    return {"tables": {"concepts": rows},
            "figures": {"curriculum_graph": fig_curriculum(cur)},
            "summary": f"{cur.name}: {len(cur.concepts)} concepts, "
                       f"{len(cur.all_questions())} questions, "
                       f"{len(cur.roots())} entry points."}
