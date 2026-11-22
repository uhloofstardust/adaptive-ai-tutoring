"""Refit per-skill BKT parameters on the PAST portion of the
temporal split, using the same verified vectorized engine and the
same grid as the classical project (19 x 19 x 9 x 9 = 29,241
combinations; slip and guess capped below 0.5 for identifiability).

Writes results/params_temporal.csv.
"""
import time
import numpy as np
import pandas as pd
from fit import loglik_grid
from temporal import load_split, past_skill_sequences

MIN_STUDENTS = 50
CHUNK = 2048

vals_LT = np.round(np.arange(0.05, 0.951, 0.05), 2)   # 19 values
vals_SG = np.round(np.arange(0.05, 0.451, 0.05), 2)   # 9 values
GRID = np.array([[a, b, s, g]
                 for a in vals_LT for b in vals_LT
                 for s in vals_SG for g in vals_SG])
print(f"grid: {len(GRID)} combinations")

df = load_split()
skill_seqs = past_skill_sequences(df)

rows = []
t0 = time.time()
todo = sorted(((k, v) for k, v in skill_seqs.items()
               if len(v) >= MIN_STUDENTS),
              key=lambda kv: -sum(len(s) for s in kv[1]))
for i, (skill, seqs) in enumerate(todo, 1):
    seqs = sorted(seqs, key=len, reverse=True)
    best_ll, best = -np.inf, None
    for c0 in range(0, len(GRID), CHUNK):
        g = GRID[c0:c0 + CHUNK]
        ll = loglik_grid(seqs, g[:, 0], g[:, 1], g[:, 2], g[:, 3])
        j = int(np.argmax(ll))
        if ll[j] > best_ll:
            best_ll, best = float(ll[j]), g[j]
    rows.append({"skill_id": skill,
                 "pL0": best[0], "pT": best[1],
                 "pS": best[2], "pG": best[3],
                 "loglik": best_ll,
                 "n_train_seqs": len(seqs),
                 "n_train_rows": int(sum(len(s) for s in seqs))})
    if i % 10 == 0 or i == len(todo):
        print(f"  {i}/{len(todo)} skills fitted "
              f"({time.time() - t0:.0f}s elapsed)")

out = pd.DataFrame(rows).sort_values("skill_id")
out.to_csv("results/params_temporal.csv", index=False)
print(f"\nwrote results/params_temporal.csv "
      f"({len(out)} skills, {time.time() - t0:.0f}s total)")
print(out[["pL0", "pT", "pS", "pG"]].describe().loc[["mean", "50%"]])
