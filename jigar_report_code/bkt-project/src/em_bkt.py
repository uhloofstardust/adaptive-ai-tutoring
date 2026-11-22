"""From-scratch EM (Baum-Welch) for classical BKT.

Independent second optimizer to validate the brute-force grid search.
Hidden state 0=not mastered, 1=mastered; no forgetting (transition
1->0 fixed at 0). Slip/guess capped below 0.5 to match the grid's
identifiability constraint. Scaled forward-backward for numerical
stability. Self-test recovers known synthetic parameters.
"""
import numpy as np


def _fb_one(seq, pi, T, E):
    n = len(seq)
    a = np.zeros((n, 2))
    c = np.zeros(n)
    a[0] = pi * E[:, seq[0]]
    c[0] = a[0].sum()
    a[0] /= c[0]
    for t in range(1, n):
        a[t] = (a[t - 1] @ T) * E[:, seq[t]]
        c[t] = a[t].sum()
        a[t] /= c[t]
    b = np.zeros((n, 2))
    b[-1] = 1.0
    for t in range(n - 2, -1, -1):
        b[t] = (T @ (E[:, seq[t + 1]] * b[t + 1])) / c[t + 1]
    gamma = a * b
    gamma /= gamma.sum(axis=1, keepdims=True)
    xi = np.zeros((2, 2))
    for t in range(n - 1):
        num = (a[t][:, None] * T) * (E[:, seq[t + 1]] * b[t + 1])[None, :]
        xi += num / c[t + 1]
    return gamma, xi, np.log(c).sum()


def em_fit(seqs, n_restarts=8, max_iter=200, tol=1e-6, seed=0):
    rng = np.random.default_rng(seed)
    best = None
    for _ in range(n_restarts):
        pL0 = rng.uniform(0.1, 0.9)
        pT = rng.uniform(0.05, 0.6)
        pS = rng.uniform(0.05, 0.4)
        pG = rng.uniform(0.05, 0.4)
        prev = -np.inf
        for _ in range(max_iter):
            T = np.array([[1 - pT, pT], [0.0, 1.0]])
            E = np.array([[1 - pG, pG], [pS, 1 - pS]])
            pi = np.array([1 - pL0, pL0])
            g0 = np.zeros(2)
            trans = np.zeros((2, 2))
            gsum = np.zeros(2)
            em = np.zeros((2, 2))
            gtot = np.zeros(2)
            ll = 0.0
            for s in seqs:
                gamma, xi, sll = _fb_one(s, pi, T, E)
                ll += sll
                g0 += gamma[0]
                trans += xi
                gsum += gamma[:-1].sum(axis=0)
                for obs in (0, 1):
                    em[:, obs] += gamma[s == obs].sum(axis=0)
                gtot += gamma.sum(axis=0)
            pL0 = g0[1] / g0.sum()
            pT = trans[0, 1] / max(gsum[0], 1e-12)
            pG = em[0, 1] / max(gtot[0], 1e-12)
            pS = em[1, 0] / max(gtot[1], 1e-12)
            pT = min(max(pT, 1e-4), 0.999)
            pG = min(max(pG, 1e-4), 0.499)
            pS = min(max(pS, 1e-4), 0.499)
            pL0 = min(max(pL0, 1e-4), 0.999)
            if ll - prev < tol:
                break
            prev = ll
        if best is None or ll > best[1]:
            best = (dict(pL0=pL0, pT=pT, pS=pS, pG=pG), ll)
    return best


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    true = dict(pL0=0.30, pT=0.20, pS=0.10, pG=0.25)
    seqs = []
    for _ in range(400):
        know = rng.random() < true["pL0"]
        s = []
        for _ in range(int(rng.integers(3, 15))):
            p = (1 - true["pS"]) if know else true["pG"]
            s.append(int(rng.random() < p))
            if not know and rng.random() < true["pT"]:
                know = True
        seqs.append(np.array(s, dtype=np.int8))
    params, ll = em_fit(seqs, seed=1)
    got = {k: round(v, 3) for k, v in params.items()}
    print("recovered:", got, "\ntrue:     ", true)
    assert abs(got["pT"] - 0.20) < 0.06 and abs(got["pS"] - 0.10) < 0.06
    print("EM self-test PASSED: recovers known synthetic params")
