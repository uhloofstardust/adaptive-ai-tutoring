"""One real (student, skill) pair traced under the skill's
parameters versus the student's own parameters. Deterministic
example: the student (>= 15 future rows) where the student model
most outperforms the skill model, on their longest pair with at
least 8 past and 4 future answers. Writes
results/pair_trajectory.png."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from temporal import load_split, pair_sequences

skl = pd.read_csv("results/params_temporal.csv").set_index("skill_id")
stu = pd.read_csv("results/params_students.csv").set_index("user_id")
d = pd.read_csv("results/auc_per_student_axes.csv")
d = d[d.n_future_rows >= 15].copy()
d["diff"] = d.auc_student - d.auc_skill
d = d.sort_values(["diff", "user_id"], ascending=[False, True])

df = load_split()
pairs = pair_sequences(df)

chosen = None
for _, row in d.iterrows():
    u = int(row.user_id)
    cands = [(len(pa) + len(fu), skill, pa, fu)
             for (user, skill), (pa, fu) in pairs.items()
             if user == u and skill in skl.index
             and len(pa) >= 8 and len(fu) >= 4]
    if cands:
        cands.sort(key=lambda c: (-c[0], c[1]))
        _, skill, pa, fu = cands[0]
        chosen = (u, int(skill), pa, fu)
        break
u, skill, pa, fu = chosen
r, s = skl.loc[skill], stu.loc[u]
seq = np.concatenate([pa, fu])
print(f"student {u}, skill {skill}: {len(pa)} past + {len(fu)} future")


def beliefs(seq, pL0, pT, pS, pG):
    pL, out = pL0, []
    for obs in seq:
        num = pL * (1 - pS) if obs == 1 else pL * pS
        rest = (1 - pL) * pG if obs == 1 else (1 - pL) * (1 - pG)
        pL = num / (num + rest); pL = pL + (1 - pL) * pT
        out.append(pL)
    return np.array(out)


b_skl = beliefs(seq, r.pL0, r.pT, r.pS, r.pG)
b_stu = beliefs(seq, s.pL0, s.pT, s.pS, s.pG)

xs = np.arange(1, len(seq) + 1)
fig, ax = plt.subplots(figsize=(9, 5))
ax.axvspan(0.5, len(pa) + 0.5, color="#eeeeee", zorder=0)
ax.plot(xs, b_skl, color="#185FA5", lw=1.8, marker="o", ms=4,
        label=f"skill params: L0={r.pL0:.2f} T={r.pT:.2f} "
              f"S={r.pS:.2f} G={r.pG:.2f}")
ax.plot(xs, b_stu, color="#c47f0e", lw=1.8, marker="o", ms=4,
        label=f"student params: L0={s.pL0:.2f} T={s.pT:.2f} "
              f"S={s.pS:.2f} G={s.pG:.2f}")
for x, obs in zip(xs, seq):
    ax.plot(x, 1.005, "o" if obs == 1 else "x", ms=5,
            color="#2e8b57" if obs == 1 else "#c0392b",
            mew=2, clip_on=False)
ax.set_ylim(0, 1.02)
ax.set_xlabel("practice opportunity")
ax.set_ylabel("P(skill mastered)")
ax.set_title(f"Student {u} on skill {skill}: the same answers under "
             "the two axes\n(grey = past, white = future; top markers: "
             "green correct, red wrong)")
ax.legend(loc="lower right", fontsize=8.5)
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig("results/pair_trajectory.png", dpi=150)
print("saved results/pair_trajectory.png")
