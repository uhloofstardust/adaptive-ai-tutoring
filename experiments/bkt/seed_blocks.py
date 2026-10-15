"""Re-runs the mastery contrast on several independent seed blocks, so a sign that one block cannot resolve can still be checked.
"""

import math
import statistics as st

import matplotlib.pyplot as plt

from cursim.curriculum import build_curriculum
from cursim.params import STUDENT_MODELS

from ..registry import experiment
from ..style import ACCENT
from ..style import GREY
from .mastery_curve import mastery_curve


@experiment('seed_blocks',
            'Re-runs the mastery contrast on several independent seed blocks, so a sign that one block cannot resolve can still be checked.',
            defaults=dict(n_blocks=6, n_learners=400, n_steps=300, threshold=0.9),
            curriculum='abstract', theme='dark')
def seed_blocks(n_blocks=6, n_learners=400, n_steps=300, threshold=0.9,
                seed0=4242, cur=None, **_):
    """Re-run the mastery contrast on several independent seed blocks.

    One run reports an interval, which says how well THAT sample pins the
    number down. It does not say whether the sign would survive another
    sample, and for a small effect those are different questions: a
    contrast whose interval covers zero can still have a definite sign
    that only appears once several blocks are averaged.

    This exists because of a specific mistake. The S1 contrast was once
    reported from a single block as costless, on an interval that
    covered zero. It is in fact a small cost, and it took independent
    blocks to see that. Anything claimed about across-block behaviour
    should come from here rather than from a one-off script.

    Blocks are separated by 100000 in the seed so their learners cannot
    overlap.
    """
    if n_blocks < 2:
        raise ValueError("seed_blocks needs at least 2 blocks; got %d."
                         % n_blocks)
    cur = cur or build_curriculum()
    rows, per_student = [], {s: [] for s in STUDENT_MODELS}
    for b in range(n_blocks):
        out = mastery_curve(n_learners=n_learners, n_steps=n_steps,
                            threshold=threshold, seed0=seed0 + b * 100000,
                            cur=cur)
        for r in out["tables"]["paired"]:
            per_student[r["student"]].append(r["diff_Q2_minus_Q1"])
            rows.append(dict(block=b, seed0=seed0 + b * 100000,
                             student=r["student"],
                             diff_Q2_minus_Q1=r["diff_Q2_minus_Q1"],
                             ci95_within_block=r["ci95"],
                             sign_resolved_in_block=r["sign_resolved"],
                             n_learners=n_learners, n_steps=n_steps))

    summary_rows = []
    for sname, vals in per_student.items():
        m = st.mean(vals)
        se = st.stdev(vals) / math.sqrt(len(vals)) if len(vals) > 1 else 0.0
        neg = sum(1 for v in vals if v < 0)
        summary_rows.append(dict(
            student=sname, n_blocks=len(vals), mean_across_blocks=m,
            ci95_across_blocks=1.96 * se,
            blocks_favouring_Q2=neg, blocks_favouring_Q1=len(vals) - neg,
            sign_agrees_in_all_blocks=(neg == 0 or neg == len(vals)),
            min_block=min(vals), max_block=max(vals)))

    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    for i, (sname, vals) in enumerate(per_student.items()):
        col = (ACCENT, "#e2a03f")[i % 2]
        ax.scatter(vals, [i] * len(vals), s=42, color=col, zorder=3,
                   label=f"{sname} blocks")
        m = st.mean(vals)
        ax.plot([m, m], [i - .22, i + .22], color=col, lw=2.6, zorder=4)
    ax.axvline(0, ls="--", lw=1, color=GREY)
    ax.set_yticks(range(len(per_student)))
    ax.set_yticklabels(list(per_student))
    ax.set_xlabel("Q2 minus Q1, questions to full mastery (one dot per block)")
    ax.set_title(f"{n_blocks} independent blocks of {n_learners} learners",
                 fontsize=10.5)
    fig.tight_layout()

    bits = []
    for r in summary_rows:
        side = "Q2 sooner" if r["mean_across_blocks"] < 0 else "a cost to Q2"
        bits.append(
            f"{r['student']}: {r['mean_across_blocks']:+.2f} "
            f"+/-{r['ci95_across_blocks']:.2f} across {r['n_blocks']} blocks "
            f"({side}), individual blocks from {r['min_block']:+.2f} to "
            f"{r['max_block']:+.2f}, sign the same in all blocks: "
            f"{'yes' if r['sign_agrees_in_all_blocks'] else 'no'}")
    summary = (f"{n_blocks} independent blocks of {n_learners} learners, "
               f"{n_steps} questions. " + "; ".join(bits) + ". A sign that "
               "holds in every block is evidence a single block's interval "
               "cannot give.")
    return {"tables": {"seed_blocks": rows, "across_blocks": summary_rows},
            "figures": {"seed_blocks": fig}, "summary": summary}
