"""Within-skill AUC: removes cross-skill difficulty ranking from the
metric. Skills with a single outcome class in test have undefined AUC
and are skipped (counted)."""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from bkt import BKT
from sequences import load_df, split_students, build_sequences

df = load_df()
test_ids = split_students(df)
seqs = build_sequences(df)
params = pd.read_csv("results/params.csv").set_index("skill_id")
models = {sk: BKT(r.pL0, r.pT, r.pS, r.pG) for sk, r in params.iterrows()}

rows, skipped = [], 0
for sk, users in seqs.items():
    if sk not in models:
        continue
    m = models[sk]
    yt, yp = [], []
    for u, s in users.items():
        if u in test_ids:
            preds, _ = m.trace(s)
            yt.append(s)
            yp.append(preds)
    if not yt:
        continue
    yt, yp = np.concatenate(yt), np.concatenate(yp)
    if yt.min() == yt.max():
        skipped += 1
        continue
    rows.append(dict(skill_id=sk, n=len(yt), auc=roc_auc_score(yt, yp)))

r = pd.DataFrame(rows).sort_values("auc")
print(f"skills with defined AUC: {len(r)} (skipped single-class: {skipped})")
print(f"macro mean within-skill AUC:        {r.auc.mean():.4f}")
print(f"row-weighted mean within-skill AUC: {np.average(r.auc, weights=r.n):.4f}")
print(f"median within-skill AUC:            {r.auc.median():.4f}")
print("\nworst 5:")
print(r.head(5).to_string(index=False))
print("\nbest 5:")
print(r.tail(5).to_string(index=False))
r.to_csv("results/auc_per_skill.csv", index=False)
