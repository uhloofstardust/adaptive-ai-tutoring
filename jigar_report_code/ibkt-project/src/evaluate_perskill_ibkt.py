"""Per-skill AUC of plain BKT and individualized BKT on the future
portion (the skill-averaged convention, matching evaluate_perskill.py
of the classical project). Writes results/auc_per_skill_ibkt.csv."""
import numpy as np
import pandas as pd
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


by_skill = {}
for (user, skill), (pa, fu) in pairs.items():
    if len(fu) == 0 or skill not in params.index:
        continue
    r = params.loc[skill]
    m = mult.loc[user] if user in mult.index else None
    mL0 = float(m["mL0"]) if m is not None else 1.0
    mT = float(m["mT"]) if m is not None else 1.0
    d = by_skill.setdefault(skill, {"y": [], "pb": [], "pi": []})
    d["y"].append(fu)
    d["pb"].append(run_pair(pa, fu, r.pL0, r.pT, r.pS, r.pG))
    d["pi"].append(run_pair(pa, fu,
                            float(np.clip(mL0 * r.pL0, 0.01, 0.99)),
                            float(np.clip(mT * r.pT, 0.005, 0.95)),
                            r.pS, r.pG))

rows, single_class = [], 0
for skill, d in sorted(by_skill.items()):
    y = np.concatenate(d["y"])
    if len(np.unique(y)) < 2:
        single_class += 1
        continue
    pb = np.concatenate(d["pb"]); pi = np.concatenate(d["pi"])
    rows.append({"skill_id": skill, "n_future_rows": len(y),
                 "auc_plain": roc_auc_score(y, pb),
                 "auc_ibkt": roc_auc_score(y, pi)})
out = pd.DataFrame(rows)
out["gain"] = out.auc_ibkt - out.auc_plain
out.to_csv("results/auc_per_skill_ibkt.csv", index=False,
           float_format="%.4f")

w = out.n_future_rows
print(f"skills with per-skill AUC: {len(out)} "
      f"(skipped, single-class future data: {single_class})")
print(f"macro AUC     plain {out.auc_plain.mean():.4f}   "
      f"iBKT {out.auc_ibkt.mean():.4f}   "
      f"gain {out.auc_ibkt.mean()-out.auc_plain.mean():+.4f}")
print(f"weighted AUC  plain {np.average(out.auc_plain, weights=w):.4f}   "
      f"iBKT {np.average(out.auc_ibkt, weights=w):.4f}")
print(f"median per-skill gain: {out.gain.median():+.4f}; "
      f"skills improved: {(out.gain > 0).sum()} / {len(out)}")

big = out[out.n_future_rows >= 200]
print("\nlargest gains (skills with >= 200 future rows):")
for _, r in big.nlargest(5, "gain").iterrows():
    print(f"  skill {int(r.skill_id):4d}  n {int(r.n_future_rows):5d}  "
          f"plain {r.auc_plain:.3f}  iBKT {r.auc_ibkt:.3f}  "
          f"gain {r.gain:+.4f}")
print("largest drops:")
for _, r in big.nsmallest(3, "gain").iterrows():
    print(f"  skill {int(r.skill_id):4d}  n {int(r.n_future_rows):5d}  "
          f"plain {r.auc_plain:.3f}  iBKT {r.auc_ibkt:.3f}  "
          f"gain {r.gain:+.4f}")
