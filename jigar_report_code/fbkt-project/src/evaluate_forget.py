"""Evaluate forgetting BKT against classical BKT on the classical
seed-42 held-out students (identical protocol and test rows as the
classical project, so numbers are directly comparable).

Three parameter sets are evaluated with the same tracing code:
1. the classical project's params.csv (if found), as continuity
   check against the published 0.7257,
2. the pF = 0 slice of the new grid (classical refit, ties may be
   broken differently),
3. the full forgetting fit.

Writes results/auc_per_skill_forget.csv.
"""
import os
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from fbkt import FBKT
from sequences import load_df, split_students, build_sequences

df = load_df()
test_users = split_students(df)
test = df[df["user_id"].isin(test_users)]
train = df[~df["user_id"].isin(test_users)]
seqs_test = build_sequences(test)
skill_mean = train.groupby("skill_id")["correct"].mean()

sets = {}
classical = "../bkt-project/results/params.csv"
if os.path.exists(classical):
    sets["classical (params.csv)"] = pd.read_csv(classical)
sets["pF=0 slice (refit)"] = pd.read_csv("results/params_pf0.csv")
sets["forgetting BKT"] = pd.read_csv("results/params_forget.csv")
for k in sets:
    s = sets[k].set_index("skill_id")
    if "pF" not in s.columns:
        s = s.assign(pF=0.0)
    sets[k] = s

fitted = sets["forgetting BKT"].index


def trace_preds(seq, r):
    m = FBKT(r.pL0, r.pT, r.pS, r.pG, r.pF)
    pL, preds = r.pL0, np.empty(len(seq))
    for t, obs in enumerate(seq):
        preds[t] = m.predict_correct(pL)
        pL = m.transition(m.update(pL, obs))
    return preds


y_all, preds_all = [], {k: [] for k in sets}
base_all, skill_of = [], []
skipped = 0
for skill, by_user in seqs_test.items():
    if skill not in fitted:
        skipped += sum(len(s) for s in by_user.values())
        continue
    for user, seq in by_user.items():
        y_all.append(np.asarray(seq))
        skill_of.append(np.full(len(seq), skill))
        base_all.append(np.full(len(seq), skill_mean.get(skill, 0.5)))
        for k, P in sets.items():
            preds_all[k].append(trace_preds(seq, P.loc[skill]))

y = np.concatenate(y_all)
skill_of = np.concatenate(skill_of)
base = np.concatenate(base_all)
print(f"test rows evaluated: {len(y)}, skipped (unfitted skills): "
      f"{skipped}, total: {len(y) + skipped}")

print(f"\n{'per-skill mean baseline':28s} AUC "
      f"{roc_auc_score(y, base):.4f}")
P = {}
for k in sets:
    p = np.concatenate(preds_all[k])
    P[k] = p
    rmse = float(np.sqrt(np.mean((p - y) ** 2)))
    acc = float(((p >= 0.5) == y).mean())
    print(f"{k:28s} AUC {roc_auc_score(y, p):.4f}   "
          f"RMSE {rmse:.4f}   acc {acc:.4f}")

pf_of = sets["forgetting BKT"]["pF"]
mask_f = np.isin(skill_of, pf_of[pf_of > 0].index)
print(f"\nrestricted to the {int((pf_of > 0).sum())} skills that "
      f"chose pF > 0 ({mask_f.sum()} rows):")
for k in ["pF=0 slice (refit)", "forgetting BKT"]:
    print(f"  {k:26s} AUC {roc_auc_score(y[mask_f], P[k][mask_f]):.4f}")

rows = []
for skill in fitted:
    m = skill_of == skill
    if len(np.unique(y[m])) < 2:
        continue
    rows.append({"skill_id": skill, "n_test_rows": int(m.sum()),
                 "pF": float(pf_of.loc[skill]),
                 "auc_classical": roc_auc_score(y[m],
                                                P["pF=0 slice (refit)"][m]),
                 "auc_forget": roc_auc_score(y[m],
                                             P["forgetting BKT"][m])})
out = pd.DataFrame(rows)
out["gain"] = out.auc_forget - out.auc_classical
out.to_csv("results/auc_per_skill_forget.csv", index=False,
           float_format="%.4f")
print(f"\nper-skill macro AUC: classical {out.auc_classical.mean():.4f}"
      f"   forgetting {out.auc_forget.mean():.4f}"
      f"   gain {out.auc_forget.mean() - out.auc_classical.mean():+.4f}")
sub = out[out.pF > 0]
print(f"among the {len(sub)} pF>0 skills: improved {int((sub.gain > 0).sum())},"
      f" worsened {int((sub.gain < 0).sum())},"
      f" median gain {sub.gain.median():+.4f}")
big = sub[sub.n_test_rows >= 200]
print("\nlargest test gains (pF>0 skills, >= 200 test rows):")
for _, r in big.nlargest(4, "gain").iterrows():
    print(f"  skill {int(r.skill_id):4d}  pF {r.pF:.2f}  n {int(r.n_test_rows):5d}"
          f"  classical {r.auc_classical:.3f}  forget {r.auc_forget:.3f}"
          f"  gain {r.gain:+.4f}")
print("largest test drops:")
for _, r in big.nsmallest(4, "gain").iterrows():
    print(f"  skill {int(r.skill_id):4d}  pF {r.pF:.2f}  n {int(r.n_test_rows):5d}"
          f"  classical {r.auc_classical:.3f}  forget {r.auc_forget:.3f}"
          f"  gain {r.gain:+.4f}")
