"""Student-based BKT: fit the four BKT parameters PER STUDENT,
shared across all that student's skills - the exact mirror of
classical BKT, which fits them per skill shared across students.

The hidden mastery state still lives per (student, skill) pair and
every pair's sequence starts fresh at the student's prior; only the
source of the four numbers changes. The model is skill-blind by
construction: a student's parameters are fitted on ALL their past
answers, whatever the skill.

Fitting: same grid as the classical project (19 x 19 x 9 x 9 =
29,241 combinations, slip and guess below 0.5), maximum likelihood
on each student's PAST portion of the temporal split. Students with
fewer than MIN_ROWS past rows are not fitted (too little data for
four numbers). Batched: sequences of many students are stacked and
the per-sequence engine scores them together; each student's total
is the sum of their own rows.

Resumable: results are saved after every batch, a rerun skips
finished students, and FIT_BUDGET_S stops cleanly after a time
budget. Writes results/params_students.csv.
"""
import os
import time
import numpy as np
import pandas as pd
from fit_perseq import loglik_per_seq
from temporal import load_split, pair_sequences

MIN_ROWS = 20
CHUNK = 2048
BATCH_SEQS = 3000
BUDGET = float(os.environ.get("FIT_BUDGET_S", "1e18"))
OUT = "results/params_students.csv"

vals_LT = np.round(np.arange(0.05, 0.951, 0.05), 2)
vals_SG = np.round(np.arange(0.05, 0.451, 0.05), 2)
GRID = np.array([[a, b, s, g]
                 for a in vals_LT for b in vals_LT
                 for s in vals_SG for g in vals_SG])
print(f"grid: {len(GRID)} combinations")

df = load_split()
pairs = pair_sequences(df)

by_student = {}
for (user, skill), (past, fut) in pairs.items():
    if len(past):
        by_student.setdefault(user, []).append(past)

eligible = {u: v for u, v in by_student.items()
            if sum(len(s) for s in v) >= MIN_ROWS}
print(f"students with past data: {len(by_student)}; "
      f"eligible (>= {MIN_ROWS} past rows): {len(eligible)}")

rows = (pd.read_csv(OUT).to_dict("records")
        if os.path.exists(OUT) else [])
done = {r["user_id"] for r in rows}
todo = [u for u in sorted(eligible) if u not in done]
print(f"remaining to fit: {len(todo)}")

t0 = time.time()
i = 0
while i < len(todo):
    if time.time() - t0 > BUDGET:
        print(f"time budget reached after {time.time()-t0:.0f}s; "
              f"{len(done)}/{len(eligible)} done. Rerun to continue.")
        break
    batch_users, batch_seqs, stu_idx = [], [], []
    while i < len(todo) and len(batch_seqs) < BATCH_SEQS:
        u = todo[i]
        for s in eligible[u]:
            batch_seqs.append(s)
            stu_idx.append(len(batch_users))
        batch_users.append(u)
        i += 1
    stu_idx = np.array(stu_idx)
    nb = len(batch_users)
    best_ll = np.full(nb, -np.inf)
    best = np.zeros((nb, 4))
    for c0 in range(0, len(GRID), CHUNK):
        g = GRID[c0:c0 + CHUNK]
        ll_mat = loglik_per_seq(batch_seqs, g[:, 0], g[:, 1],
                             g[:, 2], g[:, 3])
        stu_ll = np.zeros((nb, len(g)))
        np.add.at(stu_ll, stu_idx, ll_mat)
        j = np.argmax(stu_ll, axis=1)
        v = stu_ll[np.arange(nb), j]
        better = v > best_ll
        best_ll[better] = v[better]
        best[better] = g[j[better]]
    for k, u in enumerate(batch_users):
        n_rows = int(sum(len(s) for s in eligible[u]))
        rows.append({"user_id": u,
                     "pL0": best[k, 0], "pT": best[k, 1],
                     "pS": best[k, 2], "pG": best[k, 3],
                     "loglik": float(best_ll[k]),
                     "n_past_rows": n_rows,
                     "n_past_pairs": len(eligible[u])})
        done.add(u)
    pd.DataFrame(rows).sort_values("user_id").to_csv(OUT, index=False)
    print(f"  {len(done)}/{len(eligible)} students fitted "
          f"({time.time() - t0:.0f}s elapsed)")

if len(done) == len(eligible):
    out = pd.DataFrame(rows)
    print(f"\nwrote {OUT} ({len(out)} students)")
    print(out[["pL0", "pT", "pS", "pG"]].describe()
          .loc[["mean", "50%"]].round(3))
