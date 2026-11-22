"""Per-sequence log-likelihood engine for student-based BKT.

Same verified mathematics as the classical engine (additive Bayes
denominator, predict-before-update, finite assertion), but returns
the log-likelihood of EACH sequence separately, shape
(n_sequences, n_combos), instead of one summed total. This lets one
vectorized pass serve many students at once: sequences from many
students are stacked, and each student's total is the sum of their
own rows.

Self-tests:
1. summed over sequences it equals the verified classical engine,
2. single sequences match the scalar BKT class step by step.
"""
import numpy as np

MIN_P = 1e-12


def loglik_per_seq(seqs, pL0s, pTs, pSs, pGs):
    """seqs: list of 0/1 arrays (any order). Returns array
    (len(seqs), len(pL0s)) of per-sequence log-likelihoods."""
    n, C = len(seqs), len(pL0s)
    lens = np.array([len(s) for s in seqs])
    T = int(lens.max())
    O = np.zeros((n, T), dtype=np.int8)
    for i, s in enumerate(seqs):
        O[i, :len(s)] = s

    pL = np.broadcast_to(pL0s, (n, C)).copy()
    ll_mat = np.zeros((n, C))
    for t in range(T):
        alive = lens > t
        if not alive.any():
            break
        pl = pL[alive]
        obs = O[alive, t][:, None]
        num = np.where(obs == 1, pl * (1 - pSs), pl * pSs)
        rest = np.where(obs == 1, (1 - pl) * pGs, (1 - pl) * (1 - pGs))
        lik = num + rest                       # additive, saturation-safe
        ll_mat[alive] += np.log(np.maximum(lik, MIN_P))
        post = num / np.maximum(lik, MIN_P)
        pL[alive] = post + (1 - post) * pTs
    assert np.isfinite(ll_mat).all()
    return ll_mat


if __name__ == "__main__":
    from bkt import BKT
    import importlib.util as ilu
    spec = ilu.spec_from_file_location("cfit", "src/classical_fit.py")
    cfit = ilu.module_from_spec(spec)
    spec.loader.exec_module(cfit)

    rng = np.random.default_rng(1)
    seqs = [rng.integers(0, 2, rng.integers(1, 25)) for _ in range(50)]
    g = np.array([[0.3, 0.1, 0.1, 0.2], [0.7, 0.15, 0.2, 0.15],
                  [0.05, 0.95, 0.45, 0.05], [0.95, 0.05, 0.05, 0.45],
                  [0.5, 0.3, 0.3, 0.3]])

    ll_mat = loglik_per_seq(seqs, g[:, 0], g[:, 1], g[:, 2], g[:, 3])

    seqs_sorted = sorted(seqs, key=len, reverse=True)
    total_cls = cfit.loglik_grid(seqs_sorted, g[:, 0], g[:, 1],
                                 g[:, 2], g[:, 3])
    d1 = np.abs(ll_mat.sum(axis=0) - total_cls).max()
    print(f"summed vs classical engine: max diff = {d1:.2e}")
    assert d1 < 1e-9

    worst = 0.0
    for c in g:
        m = BKT(*c)
        for i, s in enumerate(seqs[:10]):
            ll = 0.0
            pL = m.p_L0
            for obs in s:
                p = m.predict_correct(pL)
                ll += np.log(p if obs == 1 else 1 - p)
                pL = m.transition(m.update(pL, obs))
            j = int(np.where((g == c).all(axis=1))[0][0])
            worst = max(worst, abs(ll - ll_mat[i, j]))
    print(f"per-sequence vs scalar class: max diff = {worst:.2e}")
    assert worst < 1e-9
    print("self-test PASSED: per-sequence engine matches classical "
          "totals and the scalar reference")
