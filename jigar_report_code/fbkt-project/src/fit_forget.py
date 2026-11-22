"""Vectorized log-likelihood engine for forgetting BKT.

Same structure as the verified classical engine (fit.py of the
classical project): pads sequences into a matrix, loops over time
steps only, vectorizes over (sequences x parameter combinations),
uses the ADDITIVE Bayes denominator (the classical project's bug
fix) and asserts all likelihoods finite. The only change is the
transition line, which gains the forgetting term.

Self-tests:
1. slow reference (FBKT class) vs fast engine on random cases.
2. the pF = 0 slice must equal the verified classical engine.
3. the saturation stress case (30 correct then 60 wrong) stays finite.
"""
import numpy as np
from fbkt import FBKT

MIN_P = 1e-12


def loglik_grid5(seqs, pL0s, pTs, pSs, pGs, pFs):
    """Total log-likelihood of seqs for every parameter combination.
    seqs: list of 0/1 numpy arrays, ideally sorted longest first.
    Returns array of shape (n_combos,)."""
    n = len(seqs)
    C = len(pL0s)
    lens = np.array([len(s) for s in seqs])
    order = np.argsort(-lens, kind="mergesort")
    seqs = [seqs[i] for i in order]
    lens = lens[order]
    T = int(lens[0])
    O = np.zeros((n, T), dtype=np.int8)
    for i, s in enumerate(seqs):
        O[i, :len(s)] = s

    pL = np.broadcast_to(pL0s, (n, C)).copy()
    ll = np.zeros(C)
    alive_n = n
    for t in range(T):
        while alive_n > 0 and lens[alive_n - 1] <= t:
            alive_n -= 1
        if alive_n == 0:
            break
        pl = pL[:alive_n]
        obs = O[:alive_n, t][:, None]
        num = np.where(obs == 1, pl * (1 - pSs), pl * pSs)
        rest = np.where(obs == 1, (1 - pl) * pGs, (1 - pl) * (1 - pGs))
        lik = num + rest                      # additive: saturation-safe
        ll += np.log(np.maximum(lik, MIN_P)).sum(axis=0)
        post = num / np.maximum(lik, MIN_P)
        pL[:alive_n] = post * (1 - pFs) + (1 - post) * pTs
    assert np.isfinite(ll).all()
    return ll


def loglik_slow5(seqs, pL0, pT, pS, pG, pF):
    m = FBKT(pL0, pT, pS, pG, pF)
    total = 0.0
    for s in seqs:
        for p, obs in zip(m.trace(s), s):
            total += np.log(p if obs == 1 else 1 - p)
    return total


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    seqs = [rng.integers(0, 2, rng.integers(1, 30)) for _ in range(40)]

    combos = np.array([[0.3, 0.1, 0.1, 0.2, 0.05],
                       [0.7, 0.15, 0.2, 0.15, 0.0],
                       [0.5, 0.3, 0.3, 0.3, 0.2],
                       [0.9, 0.05, 0.45, 0.45, 0.25]])
    fast = loglik_grid5(seqs, *[combos[:, j] for j in range(5)])
    slow = np.array([loglik_slow5(seqs, *c) for c in combos])
    d1 = np.abs(fast - slow).max()
    print(f"random test vs slow reference: max |fast - slow| = {d1:.2e}")
    assert d1 < 1e-9

    # pF = 0 slice must equal the classical verified engine
    import importlib.util as ilu
    spec = ilu.spec_from_file_location("cfit", "src/classical_fit.py")
    cfit = ilu.module_from_spec(spec)
    spec.loader.exec_module(cfit)
    g = np.array([[0.3, 0.1, 0.1, 0.2], [0.7, 0.15, 0.2, 0.15],
                  [0.05, 0.95, 0.45, 0.05], [0.95, 0.05, 0.05, 0.45]])
    seqs_sorted = sorted(seqs, key=len, reverse=True)
    f5 = loglik_grid5(seqs_sorted, g[:, 0], g[:, 1], g[:, 2], g[:, 3],
                      np.zeros(len(g)))
    f4 = cfit.loglik_grid(seqs_sorted, g[:, 0], g[:, 1], g[:, 2], g[:, 3])
    d2 = np.abs(f5 - f4).max()
    print(f"pF=0 slice vs classical engine: max diff = {d2:.2e}")
    assert d2 < 1e-9

    stress = [np.array([1] * 30 + [0] * 60)]
    ll = loglik_grid5(stress, g[:, 0], g[:, 1], g[:, 2], g[:, 3],
                      np.array([0.0, 0.1, 0.2, 0.25]))
    print(f"saturation stress: all finite = {np.isfinite(ll).all()}")
    print("self-test PASSED: fast == slow, pF=0 == classical, "
          "saturation-safe")
