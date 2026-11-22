"""The same answer sequence under the fitted parameters of nine
students (the nine most active), mirroring the classical project's
nine-skill grid. Writes results/student_grid.png."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEQ = [0, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1]
stu = pd.read_csv("results/params_students.csv")
top = stu.sort_values(["n_past_rows", "user_id"],
                      ascending=[False, True]).head(9)

fig, axes = plt.subplots(3, 3, figsize=(11, 8.6), sharex=True,
                         sharey=True)
xs = list(range(1, len(SEQ) + 1))
for ax, (_, s) in zip(axes.flat, top.iterrows()):
    pL, ys = s.pL0, []
    for obs in SEQ:
        num = pL * (1 - s.pS) if obs == 1 else pL * s.pS
        rest = (1 - pL) * s.pG if obs == 1 else (1 - pL) * (1 - s.pG)
        pL = num / (num + rest); pL = pL + (1 - pL) * s.pT
        ys.append(pL)
    ax.plot(xs, ys, color="#22303f", lw=1.6, zorder=2)
    for x, obs, yv in zip(xs, SEQ, ys):
        ax.plot(x, yv, "o" if obs == 1 else "x", ms=5 if obs else 6,
                color="#2e8b57" if obs == 1 else "#c0392b",
                mew=2, zorder=3)
    ax.set_title(f"student {int(s.user_id)}   n={int(s.n_past_rows)}\n"
                 f"L0={s.pL0:.2f}  T={s.pT:.2f}  "
                 f"S={s.pS:.2f}  G={s.pG:.2f}", fontsize=8.5)
    ax.set_ylim(0, 1.02)
    ax.grid(alpha=0.25)
for ax in axes[-1, :]:
    ax.set_xlabel("practice opportunity", fontsize=8.5)
for ax in axes[:, 0]:
    ax.set_ylabel("P(mastered)", fontsize=8.5)
fig.suptitle("Same answer sequence under the fitted parameters of "
             "the nine most active students "
             "(mirror of the classical nine-skill grid)", fontsize=11)
fig.tight_layout()
fig.savefig("results/student_grid.png", dpi=150)
print("saved results/student_grid.png")
