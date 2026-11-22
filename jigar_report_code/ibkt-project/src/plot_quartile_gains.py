"""AUC of plain BKT vs iBKT within quartiles of student past-data
volume. Writes results/quartile_gains.png."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score
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
        pL = num / (num + rest); pL = pL + (1 - pL) * pT
    preds = np.empty(len(fut))
    for t, obs in enumerate(fut):
        preds[t] = pL * (1 - pS) + (1 - pL) * pG
        num = pL * (1 - pS) if obs == 1 else pL * pS
        rest = (1 - pL) * pG if obs == 1 else (1 - pL) * (1 - pG)
        pL = num / (num + rest); pL = pL + (1 - pL) * pT
    return preds


y, pb, pi, past_rows = [], [], [], []
for (user, skill), (pa, fu) in pairs.items():
    if len(fu) == 0 or skill not in params.index:
        continue
    r = params.loc[skill]
    m = mult.loc[user] if user in mult.index else None
    mL0 = float(m["mL0"]) if m is not None else 1.0
    mT = float(m["mT"]) if m is not None else 1.0
    npast = int(m["n_past_rows"]) if m is not None else 0
    y.append(fu)
    pb.append(run_pair(pa, fu, r.pL0, r.pT, r.pS, r.pG))
    pi.append(run_pair(pa, fu,
                       float(np.clip(mL0 * r.pL0, 0.01, 0.99)),
                       float(np.clip(mT * r.pT, 0.005, 0.95)),
                       r.pS, r.pG))
    past_rows.append(np.full(len(fu), npast))
y = np.concatenate(y); pb = np.concatenate(pb)
pi = np.concatenate(pi); past_rows = np.concatenate(past_rows)

qs = np.quantile(past_rows, [0.25, 0.5, 0.75])
edges = [-1, qs[0], qs[1], qs[2], np.inf]
labels = [f"Q1\n(<= {qs[0]:.0f} rows)", f"Q2\n(<= {qs[1]:.0f})",
          f"Q3\n(<= {qs[2]:.0f})", f"Q4\n(> {qs[2]:.0f})"]
a_b, a_i = [], []
for lo, hi in zip(edges[:-1], edges[1:]):
    m = (past_rows > lo) & (past_rows <= hi)
    a_b.append(roc_auc_score(y[m], pb[m]))
    a_i.append(roc_auc_score(y[m], pi[m]))

x = np.arange(4)
fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(x - 0.18, a_b, width=0.36, color="#185FA5", label="plain BKT")
ax.bar(x + 0.18, a_i, width=0.36, color="#7d3c98",
       label="individualized BKT")
for i in range(4):
    ax.text(x[i] - 0.18, a_b[i] + 0.001, f"{a_b[i]:.3f}",
            ha="center", fontsize=8)
    ax.text(x[i] + 0.18, a_i[i] + 0.001, f"{a_i[i]:.3f}",
            ha="center", fontsize=8)
    ax.text(x[i], min(a_b[i], a_i[i]) - 0.006,
            f"+{a_i[i]-a_b[i]:.4f}", ha="center", fontsize=8.5,
            color="#2e8b57", fontweight="bold")
ax.set_xticks(x, labels)
ax.set_ylim(0.68, 0.76)
ax.set_ylabel("AUC on future rows")
ax.set_title("AUC by student past-data volume "
             "(green = gain of iBKT over plain)")
ax.legend(loc="upper right", fontsize=9)
ax.grid(alpha=0.25, axis="y")
fig.tight_layout()
fig.savefig("results/quartile_gains.png", dpi=150)
print("saved results/quartile_gains.png")
for lab, b, i_ in zip(["Q1", "Q2", "Q3", "Q4"], a_b, a_i):
    print(f"  {lab}: plain {b:.4f}  iBKT {i_:.4f}  gain {i_-b:+.4f}")
