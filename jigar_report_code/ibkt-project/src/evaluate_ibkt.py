"""Evaluate plain BKT and individualized BKT on the FUTURE portion
of the temporal split, under identical conditions.

For every (student, skill) pair whose skill was fitted, the belief
starts at that pair's prior, runs through the pair's PAST answers
without scoring (the tutor has seen them), and then continues onto
the FUTURE answers, where each prediction is emitted BEFORE the
answer and scored. The only difference between the two models is
the parameters: plain BKT uses the skill's (pL0, pT, pS, pG);
iBKT multiplies pL0 and pT by the student's fitted multipliers.

Reports AUC / RMSE / accuracy for both models, the per-skill mean
baseline, and a breakdown of the AUC gain by how much past data
each student has.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from temporal import load_split, pair_sequences

params = pd.read_csv("results/params_temporal.csv").set_index("skill_id")
mult = pd.read_csv("results/student_multipliers.csv").set_index("user_id")

df = load_split()
pairs = pair_sequences(df)

# per-skill mean correct rate on the past, for the no-sequence baseline
past = df[~df["is_future"]]
skill_mean = past.groupby("skill_id")["correct"].mean()


def run_pair(past_seq, fut_seq, pL0, pT, pS, pG):
    """Belief through the past (unscored), predictions on the future."""
    pL = pL0
    for obs in past_seq:
        num = pL * (1 - pS) if obs == 1 else pL * pS
        rest = (1 - pL) * pG if obs == 1 else (1 - pL) * (1 - pG)
        pL = num / (num + rest)
        pL = pL + (1 - pL) * pT
    preds = np.empty(len(fut_seq))
    for t, obs in enumerate(fut_seq):
        preds[t] = pL * (1 - pS) + (1 - pL) * pG        # predict FIRST
        num = pL * (1 - pS) if obs == 1 else pL * pS
        rest = (1 - pL) * pG if obs == 1 else (1 - pL) * (1 - pG)
        pL = num / (num + rest)
        pL = pL + (1 - pL) * pT
    return preds


y, p_base, p_ibkt, p_mean, past_rows_of = [], [], [], [], []
skipped = 0
for (user, skill), (pa, fu) in pairs.items():
    if len(fu) == 0:
        continue
    if skill not in params.index:
        skipped += len(fu)
        continue
    r = params.loc[skill]
    m = mult.loc[user] if user in mult.index else None
    mL0 = float(m["mL0"]) if m is not None else 1.0
    mT = float(m["mT"]) if m is not None else 1.0
    npast = int(m["n_past_rows"]) if m is not None else 0

    y.append(fu)
    p_base.append(run_pair(pa, fu, r.pL0, r.pT, r.pS, r.pG))
    p_ibkt.append(run_pair(pa, fu,
                           float(np.clip(mL0 * r.pL0, 0.01, 0.99)),
                           float(np.clip(mT * r.pT, 0.005, 0.95)),
                           r.pS, r.pG))
    p_mean.append(np.full(len(fu), skill_mean.get(skill, 0.5)))
    past_rows_of.append(np.full(len(fu), npast))

y = np.concatenate(y)
p_base = np.concatenate(p_base)
p_ibkt = np.concatenate(p_ibkt)
p_mean = np.concatenate(p_mean)
past_rows_of = np.concatenate(past_rows_of)

print(f"future rows evaluated: {len(y)}, skipped (unfitted skills): "
      f"{skipped}, total future rows: {len(y) + skipped}")


def report(name, pred):
    auc = roc_auc_score(y, pred)
    rmse = float(np.sqrt(np.mean((pred - y) ** 2)))
    acc = float(((pred >= 0.5) == y).mean())
    print(f"{name:24s} AUC {auc:.4f}   RMSE {rmse:.4f}   acc {acc:.4f}")
    return auc


print()
auc_mean = report("per-skill mean baseline", p_mean)
auc_base = report("plain BKT", p_base)
auc_ibkt = report("individualized BKT", p_ibkt)
print(f"\nAUC gain of iBKT over plain BKT: {auc_ibkt - auc_base:+.4f}")
print(f"majority-class accuracy: {max(y.mean(), 1 - y.mean()):.4f}")

print("\nAUC by student past-data volume (quartiles of past rows):")
qs = np.quantile(past_rows_of, [0.25, 0.5, 0.75])
edges = [-1, qs[0], qs[1], qs[2], np.inf]
labels = [f"Q1 (<= {qs[0]:.0f})", f"Q2 (<= {qs[1]:.0f})",
          f"Q3 (<= {qs[2]:.0f})", f"Q4 (> {qs[2]:.0f})"]
for lo, hi, lab in zip(edges[:-1], edges[1:], labels):
    m = (past_rows_of > lo) & (past_rows_of <= hi)
    if m.sum() < 100 or len(np.unique(y[m])) < 2:
        continue
    a_b = roc_auc_score(y[m], p_base[m])
    a_i = roc_auc_score(y[m], p_ibkt[m])
    print(f"  {lab:14s} rows {m.sum():6d}   plain {a_b:.4f}   "
          f"iBKT {a_i:.4f}   gain {a_i - a_b:+.4f}")
