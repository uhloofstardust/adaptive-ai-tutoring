"""Plot the real ROC curve from held-out test predictions.

Rebuilds the exact same predictions evaluate.py scores (same model,
same students, same skills), then extracts the full curve instead of
just the summary AUC number.
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, roc_auc_score
from bkt import BKT
from sequences import load_df, split_students, build_sequences

df = load_df()
test_ids = split_students(df)
seqs = build_sequences(df)
params = pd.read_csv("results/params.csv").set_index("skill_id")
models = {sk: BKT(r.pL0, r.pT, r.pS, r.pG) for sk, r in params.iterrows()}

y_true, y_pred = [], []
for sk, users in seqs.items():
    if sk not in models:
        continue
    m = models[sk]
    for u, s in users.items():
        if u not in test_ids:
            continue
        preds, _ = m.trace(s)
        y_true.append(s)
        y_pred.append(preds)

y_true = np.concatenate(y_true)
y_pred = np.concatenate(y_pred)

fpr, tpr, thresholds = roc_curve(y_true, y_pred)
auc = roc_auc_score(y_true, y_pred)

i_half = int(np.argmin(np.abs(thresholds - 0.5)))

fig, ax = plt.subplots(figsize=(6, 6))
ax.fill_between(fpr, tpr, alpha=0.12, color="#378ADD")
ax.plot(fpr, tpr, color="#185FA5", lw=2, label=f"BKT  (AUC = {auc:.3f})")
ax.plot([0, 1], [0, 1], "--", color="#999999", lw=1,
        label="random guessing  (AUC = 0.5)")
ax.scatter([fpr[i_half]], [tpr[i_half]], s=70, color="#D85A30",
           edgecolor="white", linewidth=1.5, zorder=5,
           label=f"threshold = 0.5")

ax.set_xlabel("false positive rate")
ax.set_ylabel("true positive rate")
ax.set_title("ROC curve: BKT on held-out students")
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, 1.02)
ax.set_aspect("equal")
ax.legend(loc="lower right", framealpha=0.95)
ax.grid(alpha=0.2)
fig.tight_layout()
fig.savefig("results/roc_curve.png", dpi=150)

print(f"points evaluated: {len(y_true)}")
print(f"points on ROC curve: {len(fpr)}")
print(f"AUC: {auc:.4f}")
print("saved results/roc_curve.png")
