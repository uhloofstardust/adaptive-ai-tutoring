"""The axis head-to-head: skill-based BKT versus student-based BKT
on the future portion of the temporal split, under identical
conditions, on the common subset of rows where both models are
defined (skill fitted with >= 50 past students AND student fitted
with >= 20 past rows).

Four predictors:
1. per-skill past-mean baseline  (knows only skill difficulty)
2. per-student past-mean baseline (knows only student strength)
3. skill-based BKT               (classical, temporal refit)
4. student-based BKT             (this project)

Also reports macro-by-skill and macro-by-student aggregations and
a quartile breakdown, and writes results/auc_per_student_axes.csv.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from temporal import load_split, pair_sequences

skl = pd.read_csv("results/params_temporal.csv").set_index("skill_id")
stu = pd.read_csv("results/params_students.csv").set_index("user_id")
df = load_split()
pairs = pair_sequences(df)

past = df[~df["is_future"]]
skill_mean = past.groupby("skill_id")["correct"].mean()
student_mean = past.groupby("user_id")["correct"].mean()


def run_pair(past_seq, fut_seq, pL0, pT, pS, pG):
    pL = pL0
    for obs in past_seq:
        num = pL * (1 - pS) if obs == 1 else pL * pS
        rest = (1 - pL) * pG if obs == 1 else (1 - pL) * (1 - pG)
        pL = num / (num + rest); pL = pL + (1 - pL) * pT
    preds = np.empty(len(fut_seq))
    for t, obs in enumerate(fut_seq):
        preds[t] = pL * (1 - pS) + (1 - pL) * pG
        num = pL * (1 - pS) if obs == 1 else pL * pS
        rest = (1 - pL) * pG if obs == 1 else (1 - pL) * (1 - pG)
        pL = num / (num + rest); pL = pL + (1 - pL) * pT
    return preds


y, p_skl, p_stu, b_skl, b_stu = [], [], [], [], []
skill_of, user_of, past_rows_of = [], [], []
y_all, p_skl_all = [], []
for (user, skill), (pa, fu) in pairs.items():
    if len(fu) == 0 or skill not in skl.index:
        continue
    r = skl.loc[skill]
    ps = run_pair(pa, fu, r.pL0, r.pT, r.pS, r.pG)
    y_all.append(fu); p_skl_all.append(ps)
    if user not in stu.index:
        continue
    s = stu.loc[user]
    y.append(fu)
    p_skl.append(ps)
    p_stu.append(run_pair(pa, fu, s.pL0, s.pT, s.pS, s.pG))
    b_skl.append(np.full(len(fu), skill_mean.get(skill, 0.5)))
    b_stu.append(np.full(len(fu), student_mean.get(user, 0.5)))
    skill_of.append(np.full(len(fu), skill))
    user_of.append(np.full(len(fu), user))
    past_rows_of.append(np.full(len(fu), int(s.n_past_rows)))

y = np.concatenate(y)
P = {"per-skill mean baseline": np.concatenate(b_skl),
     "per-student mean baseline": np.concatenate(b_stu),
     "skill-based BKT": np.concatenate(p_skl),
     "student-based BKT": np.concatenate(p_stu)}
skill_of = np.concatenate(skill_of)
user_of = np.concatenate(user_of)
past_rows_of = np.concatenate(past_rows_of)

ya = np.concatenate(y_all)
pa_ = np.concatenate(p_skl_all)
print(f"cross-check, skill-BKT on ALL {len(ya)} future rows: "
      f"AUC {roc_auc_score(ya, pa_):.4f} (expected 0.7259)")

print(f"\ncommon subset: {len(y)} future rows, "
      f"{len(np.unique(user_of))} students, "
      f"{len(np.unique(skill_of))} skills\n")
for k, p in P.items():
    rmse = float(np.sqrt(np.mean((p - y) ** 2)))
    acc = float(((p >= 0.5) == y).mean())
    print(f"{k:28s} AUC {roc_auc_score(y, p):.4f}   "
          f"RMSE {rmse:.4f}   acc {acc:.4f}")

def macro(by, models, min_rows, label):
    print(f"\nmacro-by-{label} (units with >= {min_rows} rows and "
          f"both classes):")
    for k in models:
        vals, w = [], []
        for u in np.unique(by):
            m = by == u
            if m.sum() < min_rows or len(np.unique(y[m])) < 2:
                continue
            vals.append(roc_auc_score(y[m], P[k][m]))
            w.append(m.sum())
        print(f"  {k:28s} macro {np.mean(vals):.4f}   "
              f"(over {len(vals)} {label}s)")

macro(skill_of, ["per-student mean baseline", "skill-based BKT",
                 "student-based BKT"], 30, "skill")
macro(user_of, ["per-skill mean baseline", "skill-based BKT",
                "student-based BKT"], 10, "student")

print("\nAUC by student past-data volume (quartiles):")
qs = np.quantile(past_rows_of, [0.25, 0.5, 0.75])
edges = [-1, qs[0], qs[1], qs[2], np.inf]
for lo, hi, lab in zip(edges[:-1], edges[1:],
                       [f"Q1 (<= {qs[0]:.0f})", f"Q2 (<= {qs[1]:.0f})",
                        f"Q3 (<= {qs[2]:.0f})", "Q4"]):
    m = (past_rows_of > lo) & (past_rows_of <= hi)
    if len(np.unique(y[m])) < 2:
        continue
    print(f"  {lab:14s} rows {m.sum():6d}   "
          f"skill {roc_auc_score(y[m], P['skill-based BKT'][m]):.4f}   "
          f"student {roc_auc_score(y[m], P['student-based BKT'][m]):.4f}")

rows = []
for u in np.unique(user_of):
    m = user_of == u
    if m.sum() < 10 or len(np.unique(y[m])) < 2:
        continue
    rows.append({"user_id": int(u), "n_future_rows": int(m.sum()),
                 "auc_skill": roc_auc_score(y[m], P["skill-based BKT"][m]),
                 "auc_student": roc_auc_score(y[m],
                                              P["student-based BKT"][m])})
pd.DataFrame(rows).to_csv("results/auc_per_student_axes.csv",
                          index=False, float_format="%.4f")
print(f"\nwrote results/auc_per_student_axes.csv ({len(rows)} students)")
