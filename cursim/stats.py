"""Statistics for paired comparisons between conditions.

Every condition runs the same learner seeds, so learner i is the same
simulated person in every condition and comparisons are read learner by
learner. Standard library only.
"""

import math
import random
import statistics
from typing import List, Sequence, Tuple


def sign_test(k: int, n: int) -> float:
    """Two-sided exact sign test: k wins out of n non-tied comparisons."""
    if n == 0:
        return 1.0
    probs = [math.comb(n, i) * 0.5 ** n for i in range(n + 1)]
    obs = probs[k]
    return min(1.0, sum(p for p in probs if p <= obs + 1e-12))


def paired(a, b, key: str) -> dict:
    """b minus a, learner by learner. `a` and `b` are RunResults (or
    anything with a `per_learner` list of dicts) run on identical seeds."""
    diffs = [rb[key] - ra[key]
             for ra, rb in zip(a.per_learner, b.per_learner)]
    wins = sum(1 for d in diffs if d > 0)
    losses = sum(1 for d in diffs if d < 0)
    return {"mean_diff": statistics.mean(diffs),
            "sd": statistics.stdev(diffs) if len(diffs) > 1 else 0.0,
            "wins": wins, "losses": losses, "n": len(diffs),
            "p_sign": sign_test(wins, wins + losses)}


# -- pooled ratios and learner-level bootstrap ------------------------
# A "contribution" is one learner's (numerator, denominator). The pooled
# statistic is sum(numerators) / sum(denominators), and the unit that is
# resampled is the learner, because observations within one learner are
# not independent.

Contribution = Tuple[float, int]


def pooled(contrib: Sequence[Contribution]) -> float:
    num = sum(a for a, _ in contrib)
    den = sum(n for _, n in contrib)
    return num / den if den else float("nan")


def bootstrap_half_width(contrib: Sequence[Contribution], n_boot=400,
                         seed=7) -> float:
    """Half-width of the 95% interval on the pooled value, resampling
    learners."""
    per = [c for c in contrib if c[1]]
    if len(per) < 2:
        return float("nan")
    rng = random.Random(seed)
    boots: List[float] = []
    for _ in range(n_boot):
        pick = [per[rng.randrange(len(per))] for _ in per]
        num = sum(a for a, _ in pick)
        den = sum(n for _, n in pick)
        boots.append(num / den if den else float("nan"))
    boots.sort()
    lo, hi = boots[int(.025 * len(boots))], boots[int(.975 * len(boots)) - 1]
    return (hi - lo) / 2


def bootstrap_diff_half_width(contrib_a: Sequence[Contribution],
                              contrib_b: Sequence[Contribution],
                              n_boot=400, seed=7) -> float:
    """Half-width of the 95% interval on the DIFFERENCE between two
    arms' pooled values. The arms share their learners, so one bootstrap
    draw resamples learner indices once and applies them to both arms;
    each arm's own marginal interval would throw the pairing away."""
    if len(contrib_a) != len(contrib_b) or len(contrib_a) < 2:
        return float("nan")
    rng = random.Random(seed)
    boots = []
    for _ in range(n_boot):
        idx = [rng.randrange(len(contrib_a)) for _ in contrib_a]
        na = sum(contrib_a[i][0] for i in idx)
        da = sum(contrib_a[i][1] for i in idx)
        nb = sum(contrib_b[i][0] for i in idx)
        db = sum(contrib_b[i][1] for i in idx)
        if da and db:
            boots.append(na / da - nb / db)
    if len(boots) < 2:
        return float("nan")
    boots.sort()
    lo, hi = boots[int(.025 * len(boots))], boots[int(.975 * len(boots)) - 1]
    return (hi - lo) / 2


def mean_ci(values: Sequence[float]) -> Tuple[float, float]:
    """Mean and normal-approximation 95% half-width."""
    m = statistics.mean(values)
    e = (1.96 * statistics.stdev(values) / math.sqrt(len(values))
         if len(values) > 1 else 0.0)
    return m, e
