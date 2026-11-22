"""ROC curves of classical BKT (the pF = 0 slice) and forgetting
BKT on the held-out students, one plot. Writes
results/roc_forget.png."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, roc_auc_score
from fbkt import FBKT
from sequences import load_df, split_students, build_sequences

df = load_df()
test_users = split_students(df)
test = df[df["user_id"].isin(test_users)]
seqs_test = build_sequences(test)

sets = {"classical BKT (pF = 0)":
        pd.read_csv("results/params_pf0.csv").set_index("skill_id")
          .assign(pF=0.0),
        "forgetting BKT":
        pd.read_csv("results/params_forget.csv").set_index("skill_id")}
fitted = sets["forgetting BKT"].index

y_all, preds = [], {k: [] for k in sets}
for skill, by_user in seqs_test.items():
    if skill not in fitted:
        continue
    for user, seq in by_user.items():
        y_all.append(np.asarray(seq))
        for k, P in sets.items():
            r = P.loc[skill]
            m = FBKT(r.pL0, r.pT, r.pS, r.pG, r.pF)
            pL, p = r.pL0, np.empty(len(seq))
            for t, obs in enumerate(seq):
                p[t] = m.predict_correct(pL)
                pL = m.transition(m.update(pL, obs))
            preds[k].append(p)
y = np.concatenate(y_all)

fig, ax = plt.subplots(figsize=(6, 6))
for (k, _), color in zip(sets.items(), ["#185FA5", "#c47f0e"]):
    p = np.concatenate(preds[k])
    fpr, tpr, _ = roc_curve(y, p)
    ax.plot(fpr, tpr, color=color, lw=2,
            label=f"{k}  (AUC = {roc_auc_score(y, p):.4f})")
ax.plot([0, 1], [0, 1], "--", color="#888888", lw=1,
        label="random guessing  (AUC = 0.5)")
ax.set_xlabel("false positive rate")
ax.set_ylabel("true positive rate")
ax.set_title("ROC on held-out students: classical vs forgetting BKT")
ax.legend(loc="lower right", fontsize=9)
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig("results/roc_forget.png", dpi=150)
print("saved results/roc_forget.png")
