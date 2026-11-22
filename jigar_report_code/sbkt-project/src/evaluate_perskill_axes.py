"""Per-skill AUC of both axes on the common subset (mirror of the
classical auc_per_skill.csv). Writes results/auc_per_skill_axes.csv."""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
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


by_skill = {}
for (user, skill), (pa, fu) in pairs.items():
    if len(fu) == 0 or skill not in skl.index or user not in stu.index:
        continue
    r, s = skl.loc[skill], stu.loc[user]
    d = by_skill.setdefault(skill, {"y": [], "ps": [], "pt": []})
    d["y"].append(fu)
    d["ps"].append(run_pair(pa, fu, r.pL0, r.pT, r.pS, r.pG))
    d["pt"].append(run_pair(pa, fu, s.pL0, s.pT, s.pS, s.pG))

rows = []
for skill, d in sorted(by_skill.items()):
    y = np.concatenate(d["y"])
    if len(y) < 30 or len(np.unique(y)) < 2:
        continue
    rows.append({"skill_id": skill, "n_rows": len(y),
                 "auc_skill_bkt": roc_auc_score(y, np.concatenate(d["ps"])),
                 "auc_student_bkt": roc_auc_score(y, np.concatenate(d["pt"]))})
out = pd.DataFrame(rows)
out["diff"] = out.auc_student_bkt - out.auc_skill_bkt
out.to_csv("results/auc_per_skill_axes.csv", index=False,
           float_format="%.4f")
print(f"skills: {len(out)}; macro skill-BKT {out.auc_skill_bkt.mean():.4f}"
      f"  student-BKT {out.auc_student_bkt.mean():.4f}")
print(f"student axis better on {(out['diff'] > 0).sum()} of {len(out)} "
      f"skills (median diff {out['diff'].median():+.4f})")
big = out[out.n_rows >= 200]
print("\nstudent axis wins most (>= 200 rows):")
for _, r in big.nlargest(3, "diff").iterrows():
    print(f"  skill {int(r.skill_id):4d}  n {int(r.n_rows):5d}  "
          f"skill {r.auc_skill_bkt:.3f}  student {r.auc_student_bkt:.3f}")
print("skill axis wins most:")
for _, r in big.nsmallest(3, "diff").iterrows():
    print(f"  skill {int(r.skill_id):4d}  n {int(r.n_rows):5d}  "
          f"skill {r.auc_skill_bkt:.3f}  student {r.auc_student_bkt:.3f}")
