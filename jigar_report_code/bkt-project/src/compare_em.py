"""EM vs grid-search agreement on the largest fitted skills."""
import numpy as np
import pandas as pd
from sequences import load_df, split_students, build_sequences
from em_bkt import em_fit

N_SKILLS = 10

df = load_df()
test_ids = split_students(df)
seqs = build_sequences(df)
grid = pd.read_csv("results/params.csv").set_index("skill_id")

train_of = {
    sk: [s for u, s in users.items() if u not in test_ids]
    for sk, users in seqs.items()
}
biggest = sorted(
    (sk for sk in grid.index if sk in train_of),
    key=lambda sk: -sum(len(s) for s in train_of[sk]),
)[:N_SKILLS]

rows = []
for sk in biggest:
    g = grid.loc[sk]
    em, _ = em_fit(train_of[sk], n_restarts=5, seed=42)
    rows.append(dict(
        skill_id=sk, n_seq=len(train_of[sk]),
        pL0_grid=g.pL0, pL0_em=round(em["pL0"], 3),
        pT_grid=g.pT, pT_em=round(em["pT"], 3),
        pS_grid=g.pS, pS_em=round(em["pS"], 3),
        pG_grid=g.pG, pG_em=round(em["pG"], 3),
    ))

r = pd.DataFrame(rows)
pd.set_option("display.width", 200, "display.max_columns", 30)
print(r.to_string(index=False))

diffs = np.concatenate([
    (r.pL0_grid - r.pL0_em).abs(), (r.pT_grid - r.pT_em).abs(),
    (r.pS_grid - r.pS_em).abs(), (r.pG_grid - r.pG_em).abs(),
])
print(f"\nmean |grid - EM| across all params: {diffs.mean():.3f}")
print(f"max  |grid - EM|:                   {diffs.max():.3f}")
n_floor = int((r.pT_grid <= 0.051).sum())
print(f"skills at grid T-floor: {n_floor}/{len(r)}; "
      f"their EM pT range: "
      f"[{r.loc[r.pT_grid <= 0.051, 'pT_em'].min():.3f}, "
      f"{r.loc[r.pT_grid <= 0.051, 'pT_em'].max():.3f}]")
r.to_csv("results/em_vs_grid.csv", index=False)
print("\nsaved results/em_vs_grid.csv")
