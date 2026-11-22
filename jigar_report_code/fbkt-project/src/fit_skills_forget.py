"""Fit forgetting BKT per skill by exhaustive grid search on the
classical seed-42 student split (identical protocol to the
classical project, so results are directly comparable).

Grid: the classical 19 x 19 x 9 x 9 for (pL0, pT, pS, pG) crossed
with pF in {0.00, 0.05, 0.10, 0.15, 0.20, 0.25} = 175,446
combinations per skill. Because pF = 0 is inside the grid,
classical BKT is nested in the search: the best pF = 0 combination
IS the classical fit, recomputed. That slice is written out
separately and, if the classical project's params.csv is found at
../bkt-project/results/params.csv, compared against it.

The run is RESUMABLE: results are saved after every skill, and a
rerun skips skills already fitted. A full run takes a few minutes.
Optional environment variable FIT_BUDGET_S stops cleanly after
that many seconds (rerun to continue).

Writes results/params_forget.csv and results/params_pf0.csv.
"""
import os
import time
import numpy as np
import pandas as pd
from fit_forget import loglik_grid5
from sequences import load_df, split_students, build_sequences

MIN_STUDENTS = 50
CHUNK = 2048
BUDGET = float(os.environ.get("FIT_BUDGET_S", "1e18"))
F_OUT = "results/params_forget.csv"
Z_OUT = "results/params_pf0.csv"

vals_LT = np.round(np.arange(0.05, 0.951, 0.05), 2)
vals_SG = np.round(np.arange(0.05, 0.451, 0.05), 2)
vals_F = np.round(np.arange(0.00, 0.251, 0.05), 2)
GRID = np.array([[a, b, s, g, f]
                 for a in vals_LT for b in vals_LT
                 for s in vals_SG for g in vals_SG for f in vals_F])
PF0 = GRID[:, 4] == 0.0
print(f"grid: {len(GRID)} combinations "
      f"({int(PF0.sum())} of them classical, pF = 0)")

df = load_df()
test_users = split_students(df)
train = df[~df["user_id"].isin(test_users)]
seqs_all = build_sequences(train)

todo = sorted(((k, list(v.values())) for k, v in seqs_all.items()
               if len(v) >= MIN_STUDENTS),
              key=lambda kv: -sum(len(s) for s in kv[1]))

rows_f = (pd.read_csv(F_OUT).to_dict("records")
          if os.path.exists(F_OUT) else [])
rows_0 = (pd.read_csv(Z_OUT).to_dict("records")
          if os.path.exists(Z_OUT) else [])
done = {r["skill_id"] for r in rows_f}
print(f"skills to fit: {len(todo)} (already done: {len(done)})")

t0 = time.time()
for skill, seqs in todo:
    if skill in done:
        continue
    if time.time() - t0 > BUDGET:
        print(f"time budget reached after {time.time()-t0:.0f}s; "
              f"{len(done)}/{len(todo)} done. Rerun to continue.")
        break
    seqs = sorted(seqs, key=len, reverse=True)
    best_ll, best = -np.inf, None
    best_ll0, best0 = -np.inf, None
    for c0 in range(0, len(GRID), CHUNK):
        g = GRID[c0:c0 + CHUNK]
        ll = loglik_grid5(seqs, g[:, 0], g[:, 1], g[:, 2], g[:, 3],
                          g[:, 4])
        j = int(np.argmax(ll))
        if ll[j] > best_ll:
            best_ll, best = float(ll[j]), g[j]
        z = PF0[c0:c0 + CHUNK]
        if z.any():
            llz = np.where(z, ll, -np.inf)
            j0 = int(np.argmax(llz))
            if llz[j0] > best_ll0:
                best_ll0, best0 = float(llz[j0]), g[j0]
    n_rows = int(sum(len(s) for s in seqs))
    rows_f.append({"skill_id": skill, "pL0": best[0], "pT": best[1],
                   "pS": best[2], "pG": best[3], "pF": best[4],
                   "loglik": best_ll, "n_train_seqs": len(seqs),
                   "n_train_rows": n_rows})
    rows_0.append({"skill_id": skill, "pL0": best0[0], "pT": best0[1],
                   "pS": best0[2], "pG": best0[3],
                   "loglik": best_ll0, "n_train_seqs": len(seqs),
                   "n_train_rows": n_rows})
    done.add(skill)
    pd.DataFrame(rows_f).sort_values("skill_id").to_csv(F_OUT, index=False)
    pd.DataFrame(rows_0).sort_values("skill_id").to_csv(Z_OUT, index=False)
    if len(done) % 10 == 0 or len(done) == len(todo):
        print(f"  {len(done)}/{len(todo)} skills fitted "
              f"({time.time() - t0:.0f}s elapsed)")

if len(done) == len(todo):
    pf = pd.DataFrame(rows_f).sort_values("skill_id")
    p0 = pd.DataFrame(rows_0).sort_values("skill_id")
    print("\nfitted pF value counts over the skills:")
    print(pf["pF"].value_counts().sort_index().to_string())
    gain = pf["loglik"].to_numpy() - p0["loglik"].to_numpy()
    print(f"\ntrain log-likelihood gain of forgetting (must be >= 0): "
          f"min {gain.min():.3f}, median {np.median(gain):.3f}, "
          f"max {gain.max():.3f}")
    classical = "../bkt-project/results/params.csv"
    if os.path.exists(classical):
        cp = pd.read_csv(classical).sort_values("skill_id")
        m = p0.merge(cp, on="skill_id", suffixes=("_pf0", "_cls"))
        dll = (m["loglik_pf0"] - m["loglik_cls"]).abs().max()
        same = ((m["pL0_pf0"] == m["pL0_cls"])
                & (m["pT_pf0"] == m["pT_cls"])
                & (m["pS_pf0"] == m["pS_cls"])
                & (m["pG_pf0"] == m["pG_cls"])).sum()
        print(f"\ncross-check vs classical params.csv: "
              f"max |loglik diff| = {dll:.2e}; "
              f"identical parameter rows: {same}/{len(m)}")
    else:
        print("\n(classical params.csv not found; cross-check skipped)")
