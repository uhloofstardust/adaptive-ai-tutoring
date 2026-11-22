"""One real student's belief trajectory on one skill, under the
skill's plain parameters versus the student's personal parameters.
The example is chosen deterministically: the personalized student
with the highest likelihood gain who has a pair with at least 8
past and 4 future answers on a fitted skill. Writes
results/student_trajectory.png."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from temporal import load_split, pair_sequences

params = pd.read_csv("results/params_temporal.csv").set_index("skill_id")
mult = pd.read_csv("results/student_multipliers.csv")
df = load_split()
pairs = pair_sequences(df)

pers = mult[(mult.mL0 != 1.0) | (mult.mT != 1.0)]
pers = pers.sort_values(["ll_gain", "user_id"],
                        ascending=[False, True])

chosen = None
for _, m in pers.iterrows():
    for (user, skill), (pa, fu) in sorted(pairs.items()):
        if (user == m.user_id and skill in params.index
                and len(pa) >= 8 and len(fu) >= 4):
            chosen = (int(user), int(skill), float(m.mL0), float(m.mT),
                      pa, fu)
            break
    if chosen:
        break

user, skill, mL0, mT, pa, fu = chosen
r = params.loc[skill]
seq = np.concatenate([pa, fu])
print(f"student {user}, skill {skill}, mL0 {mL0:g}, mT {mT:g}, "
      f"{len(pa)} past + {len(fu)} future answers")


def beliefs(seq, pL0, pT, pS, pG):
    pL, out = pL0, []
    for obs in seq:
        num = pL * (1 - pS) if obs == 1 else pL * pS
        rest = (1 - pL) * pG if obs == 1 else (1 - pL) * (1 - pG)
        pL = num / (num + rest)
        pL = pL + (1 - pL) * pT
        out.append(pL)
    return np.array(out)


b_plain = beliefs(seq, r.pL0, r.pT, r.pS, r.pG)
b_pers = beliefs(seq, float(np.clip(mL0 * r.pL0, 0.01, 0.99)),
                 float(np.clip(mT * r.pT, 0.005, 0.95)), r.pS, r.pG)

xs = np.arange(1, len(seq) + 1)
fig, ax = plt.subplots(figsize=(9, 5))
ax.axvspan(0.5, len(pa) + 0.5, color="#eeeeee", zorder=0)
ax.text(len(pa) / 2 + 0.5, 0.05, "past (fitting)", ha="center",
        fontsize=9, color="#555555")
ax.text(len(pa) + len(fu) / 2 + 0.5, 0.05, "future (evaluation)",
        ha="center", fontsize=9, color="#555555")
ax.plot(xs, b_plain, color="#185FA5", lw=1.8, marker="o", ms=4,
        label=f"plain: L0={r.pL0:.2f} T={r.pT:.2f}")
ax.plot(xs, b_pers, color="#7d3c98", lw=1.8, marker="o", ms=4,
        label=f"personal: L0={np.clip(mL0*r.pL0,0.01,0.99):.2f} "
              f"T={np.clip(mT*r.pT,0.005,0.95):.2f}")
for x, obs in zip(xs, seq):
    ax.plot(x, 1.005, "o" if obs == 1 else "x", ms=5,
            color="#2e8b57" if obs == 1 else "#c0392b",
            mew=2, clip_on=False)
ax.set_ylim(0, 1.02)
ax.set_xticks(xs[::2])
ax.set_xlabel("practice opportunity")
ax.set_ylabel("P(skill mastered)")
ax.set_title(f"Student {user} on skill {skill}: plain vs personal "
             "parameters\n(top markers: green = correct, red = wrong; "
             "slip and guess identical)")
ax.legend(loc="lower right", fontsize=9)
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig("results/student_trajectory.png", dpi=150)
print("saved results/student_trajectory.png")
