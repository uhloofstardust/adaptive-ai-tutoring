"""ROC curves of plain BKT and individualized BKT on the future
portion, on one plot. Writes results/roc_compare.png."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, roc_auc_score
from temporal import load_split, pair_sequences

params = pd.read_csv("results/params_temporal.csv").set_index("skill_id")
mult = pd.read_csv("results/student_multipliers.csv").set_index("user_id")
df = load_split()
pairs = pair_sequences(df)


def run_pair(past, fut, pL0, pT, pS, pG):
    pL = pL0
    for obs in past:
        num = pL * (1 - pS) if obs == 1 else pL * pS
        rest = (1 - pL) * pG if obs == 1 else (1 - pL) * (1 - pG)
        pL = num / (num + rest)
        pL = pL + (1 - pL) * pT
    preds = np.empty(len(fut))
    for t, obs in enumerate(fut):
        preds[t] = pL * (1 - pS) + (1 - pL) * pG
        num = pL * (1 - pS) if obs == 1 else pL * pS
        rest = (1 - pL) * pG if obs == 1 else (1 - pL) * (1 - pG)
        pL = num / (num + rest)
        pL = pL + (1 - pL) * pT
    return preds


y, pb, pi = [], [], []
for (user, skill), (pa, fu) in pairs.items():
    if len(fu) == 0 or skill not in params.index:
        continue
    r = params.loc[skill]
    m = mult.loc[user] if user in mult.index else None
    mL0 = float(m["mL0"]) if m is not None else 1.0
    mT = float(m["mT"]) if m is not None else 1.0
    y.append(fu)
    pb.append(run_pair(pa, fu, r.pL0, r.pT, r.pS, r.pG))
    pi.append(run_pair(pa, fu,
                       float(np.clip(mL0 * r.pL0, 0.01, 0.99)),
                       float(np.clip(mT * r.pT, 0.005, 0.95)),
                       r.pS, r.pG))
y = np.concatenate(y); pb = np.concatenate(pb); pi = np.concatenate(pi)

fig, ax = plt.subplots(figsize=(6, 6))
for pred, label, color, ls in [
        (pb, "plain BKT", "#185FA5", "-"),
        (pi, "individualized BKT", "#7d3c98", "-")]:
    fpr, tpr, _ = roc_curve(y, pred)
    ax.plot(fpr, tpr, color=color, lw=2, ls=ls,
            label=f"{label}  (AUC = {roc_auc_score(y, pred):.4f})")
ax.plot([0, 1], [0, 1], "--", color="#888888", lw=1,
        label="random guessing  (AUC = 0.5)")
ax.set_xlabel("false positive rate")
ax.set_ylabel("true positive rate")
ax.set_title("ROC on the future portion: plain vs individualized BKT")
ax.legend(loc="lower right", fontsize=9)
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig("results/roc_compare.png", dpi=150)
print("saved results/roc_compare.png")
print(f"AUC plain {roc_auc_score(y, pb):.4f}  iBKT {roc_auc_score(y, pi):.4f}")
