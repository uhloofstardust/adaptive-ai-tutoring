"""Evaluate fitted BKT on held-out students. Pooled AUC, main metric.

Baseline: per-skill mean correct rate from train rows (no sequence
information). BKT must beat it for the student model to mean anything.
"""
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

train_mask = ~df["user_id"].isin(test_ids)
skill_mean = df[train_mask].groupby("skill_id")["correct"].mean()

y_true, y_pred, y_base = [], [], []
n_seq, skipped = 0, 0
for sk, users in seqs.items():
    if sk not in models:
        skipped += sum(len(s) for u, s in users.items() if u in test_ids)
        continue
    m, base = models[sk], skill_mean[sk]
    for u, s in users.items():
        if u not in test_ids:
            continue
        preds, _ = m.trace(s)
        y_true.append(s); y_pred.append(preds)
        y_base.append(np.full(len(s), base))
        n_seq += 1

y_true = np.concatenate(y_true)
y_pred = np.concatenate(y_pred)
y_base = np.concatenate(y_base)

rmse = float(np.sqrt(np.mean((y_pred - y_true) ** 2)))
acc = float(((y_pred >= 0.5) == y_true).mean())
maj = float(max(y_true.mean(), 1 - y_true.mean()))
print(f"test sequences: {n_seq}, rows evaluated: {len(y_true)}, "
      f"rows skipped (unfitted skills): {skipped}")
print(f"AUC  BKT:                  {roc_auc_score(y_true, y_pred):.4f}")
print(f"AUC  per-skill mean base:  {roc_auc_score(y_true, y_base):.4f}")
print(f"RMSE BKT:                  {rmse:.4f}")
print(f"acc  BKT (0.5 threshold):  {acc:.4f}")
print(f"acc  majority class:       {maj:.4f}")
