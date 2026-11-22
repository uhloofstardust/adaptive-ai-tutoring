"""ROC curves of skill-based and student-based BKT on the common
subset, one plot. Writes results/roc_axes.png."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, roc_auc_score
from temporal import load_split, pair_sequences

skl = pd.read_csv("results/params_temporal.csv").set_index("skill_id")
stu = pd.read_csv("results/params_students.csv").set_index("user_id")
df = load_split()
pairs = pair_sequences(df)


def run_pair(pa, fu, pL0, pT, pS, pG):
    pL = pL0
    for obs in pa:
        num = pL * (1 - pS) if obs == 1 else pL * pS
        rest = (1 - pL) * pG if obs == 1 else (1 - pL) * (1 - pG)
        pL = num / (num + rest); pL = pL + (1 - pL) * pT
    preds = np.empty(len(fu))
    for t, obs in enumerate(fu):
        preds[t] = pL * (1 - pS) + (1 - pL) * pG
        num = pL * (1 - pS) if obs == 1 else pL * pS
        rest = (1 - pL) * pG if obs == 1 else (1 - pL) * (1 - pG)
        pL = num / (num + rest); pL = pL + (1 - pL) * pT
    return preds


y, ps, pt = [], [], []
for (user, skill), (pa, fu) in pairs.items():
    if len(fu) == 0 or skill not in skl.index or user not in stu.index:
        continue
    r, s = skl.loc[skill], stu.loc[user]
    y.append(fu)
    ps.append(run_pair(pa, fu, r.pL0, r.pT, r.pS, r.pG))
    pt.append(run_pair(pa, fu, s.pL0, s.pT, s.pS, s.pG))
y = np.concatenate(y); ps = np.concatenate(ps); pt = np.concatenate(pt)

fig, ax = plt.subplots(figsize=(6, 6))
for p, label, color in [(ps, "skill-based BKT", "#185FA5"),
                        (pt, "student-based BKT", "#c47f0e")]:
    fpr, tpr, _ = roc_curve(y, p)
    ax.plot(fpr, tpr, color=color, lw=2,
            label=f"{label}  (AUC = {roc_auc_score(y, p):.4f})")
ax.plot([0, 1], [0, 1], "--", color="#888888", lw=1,
        label="random guessing  (AUC = 0.5)")
ax.set_xlabel("false positive rate")
ax.set_ylabel("true positive rate")
ax.set_title("ROC on the common future rows: skill vs student axis")
ax.legend(loc="lower right", fontsize=9)
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig("results/roc_axes.png", dpi=150)
print("saved results/roc_axes.png")
