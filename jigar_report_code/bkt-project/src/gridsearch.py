"""Grid-search BKT params per skill on train students only.

Grid: pL0, pT in {0.05..0.95 step 0.05}; pS, pG in {0.05..0.45}
(identifiability: slip/guess < 0.5). 29,241 combos per skill,
swept in chunks to bound memory. Skills fitted biggest-first.
Usage: python src/gridsearch.py [limit_n_skills]
"""
import sys
import time
import numpy as np
import pandas as pd
from sequences import load_df, split_students, build_sequences
from fit import loglik_grid

MIN_TRAIN = 50
CHUNK = 2048
OUT = "results/params.csv"


def make_grid():
    v_lt = np.arange(0.05, 0.951, 0.05)          # 19 values
    v_sg = np.arange(0.05, 0.451, 0.05)          # 9 values
    g = np.meshgrid(v_lt, v_lt, v_sg, v_sg, indexing="ij")
    return np.stack([a.ravel() for a in g])      # (4, 29241)


def fit_skill(train_seqs, grid):
    seqs = sorted(train_seqs, key=len, reverse=True)
    C = grid.shape[1]
    ll = np.empty(C)
    for a in range(0, C, CHUNK):
        b = min(a + CHUNK, C)
        ll[a:b] = loglik_grid(seqs, grid[0, a:b], grid[1, a:b],
                              grid[2, a:b], grid[3, a:b])
    i = int(np.argmax(ll))
    return grid[:, i], ll[i]


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    df = load_df()
    test_ids = split_students(df)
    seqs = build_sequences(df)
    grid = make_grid()
    print(f"grid combos: {grid.shape[1]}")

    train_of = {
        sk: [s for u, s in users.items() if u not in test_ids]
        for sk, users in seqs.items()
    }
    eligible = [sk for sk, tr in train_of.items() if len(tr) >= MIN_TRAIN]
    eligible.sort(key=lambda sk: -sum(len(s) for s in train_of[sk]))
    total_rows = sum(len(s) for sk in eligible for s in train_of[sk])
    print(f"eligible skills: {len(eligible)}, total train rows: {total_rows}")

    rows = []
    for done, sk in enumerate(eligible[:limit] if limit else eligible, 1):
        train = train_of[sk]
        n_rows = sum(len(s) for s in train)
        t0 = time.perf_counter()
        (pL0, pT, pS, pG), best_ll = fit_skill(train, grid)
        dt = time.perf_counter() - t0
        rows.append(dict(skill_id=sk, pL0=pL0, pT=pT, pS=pS, pG=pG,
                         loglik=best_ll, n_train_seqs=len(train),
                         n_train_rows=n_rows, seconds=round(dt, 2)))
        print(f"[{done}] skill {sk}: {len(train)} seqs, {n_rows} rows, "
              f"L0={pL0:.2f} T={pT:.2f} S={pS:.2f} G={pG:.2f}, {dt:.1f}s")

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nsaved {OUT} ({len(rows)} skills)")

    if limit:
        rate = sum(r["n_train_rows"] for r in rows) / sum(r["seconds"] for r in rows)
        est = total_rows / rate / 60
        print(f"~{rate:,.0f} rows/s -> full run estimate: ~{est:.0f} min "
              f"(rough; per-skill overhead makes the true time somewhat higher)")
