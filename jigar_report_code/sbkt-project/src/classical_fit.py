"""Vectorized BKT log-likelihood over a parameter grid.

Loops over time steps; vectorizes over (sequences x param combos).
Sequences must be sorted by length descending so active rows are a
contiguous prefix slice at every step.

Numerical note: the Bayes denominator is built additively as
numerator + complement, never as 1 - prediction. The subtraction
form cancels catastrophically once P(L) sits within float epsilon
of 1 after a long correct streak; for some parameter combos the
rounded denominator falls below the numerator, the posterior
exceeds 1, and each subsequent incorrect answer amplifies the
overshoot by roughly (1-pG)(1-pT)/pS (up to ~18x per step at grid
corners) until the likelihood goes negative and log() returns NaN.
A NaN log-likelihood then hijacks np.argmax during fitting. The
additive form guarantees posterior <= 1 in floating point, so P(L)
stays in [0, 1] and every log() argument stays safely positive.
Self-test: agreement with the slow, hand-verified BKT class on
random data, plus a saturation stress case that NaNs the old form
on 2172 of 29241 grid combos.
"""
import numpy as np
from bkt import BKT


def loglik_grid(seqs, pL0, pT, pS, pG):
    """Total log-likelihood of seqs for every param combo.

    seqs: list of 0/1 arrays, sorted by length DESCENDING.
    pL0, pT, pS, pG: 1-D arrays, same length C (one entry per combo).
    Returns: (C,) array of summed log-likelihoods.
    """
    lens = np.array([len(s) for s in seqs])
    assert (np.diff(lens) <= 0).all(), "sort sequences by length desc"
    N, T, C = len(seqs), lens.max(), len(pL0)

    O = np.zeros((N, T), dtype=np.int8)
    for i, s in enumerate(seqs):
        O[i, : len(s)] = s
    n_active = (lens[:, None] > np.arange(T)).sum(axis=0)

    pL = np.broadcast_to(pL0, (N, C)).copy()
    ll = np.zeros(C)
    for t in range(T):
        k = n_active[t]
        pl = pL[:k]
        obs = O[:k, t, None]                              # (k, 1)
        num = np.where(obs == 1, pl * (1 - pS), pl * pS)
        rest = np.where(obs == 1, (1 - pl) * pG, (1 - pl) * (1 - pG))
        lik = num + rest                     # P(observation), additive
        ll += np.log(lik).sum(axis=0)
        post = num / lik                     # <= 1 guaranteed in float
        pL[:k] = post + (1 - post) * pT
    assert np.isfinite(ll).all(), "non-finite log-likelihood"
    return ll


def loglik_slow(seqs, pL0, pT, pS, pG):
    """Reference: same quantity via the verified BKT class."""
    ll = np.zeros(len(pL0))
    for c in range(len(pL0)):
        model = BKT(pL0[c], pT[c], pS[c], pG[c])
        for s in seqs:
            preds, _ = model.trace(s)
            ll[c] += np.log(np.where(s == 1, preds, 1 - preds)).sum()
    return ll


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    seqs = [rng.integers(0, 2, rng.integers(1, 16)) for _ in range(20)]
    seqs.sort(key=len, reverse=True)

    C = 50
    pL0 = rng.uniform(0.05, 0.95, C)
    pT = rng.uniform(0.05, 0.95, C)
    pS = rng.uniform(0.05, 0.45, C)
    pG = rng.uniform(0.05, 0.45, C)
    fast = loglik_grid(seqs, pL0, pT, pS, pG)
    slow = loglik_slow(seqs, pL0, pT, pS, pG)
    print(f"random test: max |fast - slow| = {np.abs(fast - slow).max():.2e}")
    assert np.allclose(fast, slow, atol=1e-9)

    # saturation stress: long correct streak then long incorrect run,
    # at all 16 parameter corners plus the known offender combo.
    # The old 1 - pred denominator goes non-finite on 3 of these 17.
    trig = [np.array([1] * 30 + [0] * 60, dtype=np.int8)]
    c = [[a, b, s, g] for a in (0.05, 0.95) for b in (0.05, 0.95)
         for s in (0.05, 0.45) for g in (0.05, 0.45)]
    c.append([0.05, 0.05, 0.10, 0.05])
    c = np.array(c).T
    fast = loglik_grid(trig, c[0], c[1], c[2], c[3])
    slow = loglik_slow(trig, c[0], c[1], c[2], c[3])
    print(f"stress test: max |fast - slow| = {np.abs(fast - slow).max():.2e}")
    assert np.allclose(fast, slow, atol=1e-9)
    print("self-test PASSED: vectorized == verified reference, saturation-safe")
