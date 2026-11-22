"""Estimate per-student multipliers on P(L0) and P(T).

Individualized BKT in the spirit of Yudelson et al. (2013): the
prior and the learning rate get a per-student component while slip
and guess stay per-skill. Here the student component is a pair of
multipliers (mL0, mT) applied to every skill's fitted (pL0, pT):

    pL0'(student, skill) = clip(mL0 * pL0(skill), 0.01, 0.99)
    pT'(student, skill)  = clip(mT  * pT(skill),  0.005, 0.95)

For each student the pair is chosen from a small candidate grid by
maximizing the log-likelihood of that student's OWN PAST answers
across all their fitted skills. A student keeps the neutral pair
(1, 1) unless the best pair beats neutral by at least MARGIN nats
on their past data (a simple guard against fitting noise), and
students with fewer than MIN_ROWS past rows always stay neutral.

Writes results/student_multipliers.csv.
"""
import time
import numpy as np
import pandas as pd
from temporal import load_split, pair_sequences

MIN_ROWS = 20
MARGIN = 1.0

M_L0 = np.array([0.50, 0.70, 0.85, 1.00, 1.15, 1.30, 1.50])
M_T = np.array([0.25, 0.50, 0.75, 1.00, 1.50, 2.50, 4.00])
COMBOS = np.array([[a, b] for a in M_L0 for b in M_T])   # (49, 2)
NEUTRAL = int(np.where((COMBOS[:, 0] == 1.0) &
                       (COMBOS[:, 1] == 1.0))[0][0])


def student_loglik(seq_list, base, mL0s, mTs):
    """Log-likelihood of one student's past sequences for every
    multiplier combo. seq_list: list of 0/1 arrays. base: (n, 4)
    array of the matching skills' (pL0, pT, pS, pG). Vectorized over
    (sequences x combos), looping over time steps only."""
    n, C = len(seq_list), len(mL0s)
    lens = np.array([len(s) for s in seq_list])
    T = lens.max()
    O = np.zeros((n, T), dtype=np.int8)
    for i, s in enumerate(seq_list):
        O[i, :len(s)] = s
    alive = lens[:, None] > np.arange(T)                  # (n, T)

    pL = np.clip(base[:, 0:1] * mL0s[None, :], 0.01, 0.99)   # (n, C)
    pT = np.clip(base[:, 1:2] * mTs[None, :], 0.005, 0.95)
    pS = base[:, 2:3]
    pG = base[:, 3:4]
    ll = np.zeros(C)
    for t in range(T):
        a = alive[:, t]
        if not a.any():
            break
        pl = pL[a]
        obs = O[a, t][:, None]
        num = np.where(obs == 1, pl * (1 - pS[a]), pl * pS[a])
        rest = np.where(obs == 1, (1 - pl) * pG[a],
                        (1 - pl) * (1 - pG[a]))
        lik = num + rest                       # additive, saturation-safe
        ll += np.log(lik).sum(axis=0)
        post = num / lik
        pL[a] = post + (1 - post) * pT[a]
    assert np.isfinite(ll).all()
    return ll


if __name__ == "__main__":
    df = load_split()
    pairs = pair_sequences(df)
    params = pd.read_csv("results/params_temporal.csv").set_index("skill_id")

    by_student = {}
    for (user, skill), (past, fut) in pairs.items():
        if skill in params.index and len(past):
            by_student.setdefault(user, []).append((skill, past))

    rows, t0 = [], time.time()
    n_personal = 0
    for i, (user, lst) in enumerate(sorted(by_student.items()), 1):
        seqs = [p for _, p in lst]
        n_rows = int(sum(len(s) for s in seqs))
        if n_rows < MIN_ROWS:
            rows.append({"user_id": user, "mL0": 1.0, "mT": 1.0,
                         "n_past_rows": n_rows, "ll_gain": 0.0})
            continue
        base = params.loc[[s for s, _ in lst],
                          ["pL0", "pT", "pS", "pG"]].to_numpy()
        ll = student_loglik(seqs, base, COMBOS[:, 0], COMBOS[:, 1])
        j = int(np.argmax(ll))
        gain = float(ll[j] - ll[NEUTRAL])
        if gain >= MARGIN and j != NEUTRAL:
            mL0, mT = COMBOS[j]
            n_personal += 1
        else:
            mL0, mT, gain = 1.0, 1.0, 0.0
        rows.append({"user_id": user, "mL0": mL0, "mT": mT,
                     "n_past_rows": n_rows, "ll_gain": round(gain, 3)})
        if i % 500 == 0:
            print(f"  {i}/{len(by_student)} students "
                  f"({time.time() - t0:.0f}s)")

    out = pd.DataFrame(rows)
    out.to_csv("results/student_multipliers.csv", index=False)
    print(f"\nwrote results/student_multipliers.csv "
          f"({len(out)} students, {time.time() - t0:.0f}s)")
    print(f"students with personal parameters: {n_personal} "
          f"({n_personal/len(out):.1%}); the rest stay neutral")
    pers = out[(out.mL0 != 1.0) | (out.mT != 1.0)]
    if len(pers):
        print("multiplier medians among personalized students: "
              f"mL0 {pers.mL0.median():.2f}, mT {pers.mT.median():.2f}")
