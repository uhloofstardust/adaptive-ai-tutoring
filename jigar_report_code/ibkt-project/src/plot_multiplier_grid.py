"""Where the 1,228 personalized students landed on the multiplier
grid: count of students per (mL0, mT) pair. Writes
results/multiplier_grid.png."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

M_L0 = [0.50, 0.70, 0.85, 1.00, 1.15, 1.30, 1.50]
M_T = [0.25, 0.50, 0.75, 1.00, 1.50, 2.50, 4.00]

mult = pd.read_csv("results/student_multipliers.csv")
pers = mult[(mult.mL0 != 1.0) | (mult.mT != 1.0)]

counts = np.zeros((len(M_L0), len(M_T)), dtype=int)
for _, r in pers.iterrows():
    counts[M_L0.index(r.mL0), M_T.index(r.mT)] += 1

fig, ax = plt.subplots(figsize=(7.5, 6))
im = ax.imshow(counts, cmap="Blues", origin="lower")
for i in range(len(M_L0)):
    for j in range(len(M_T)):
        if M_L0[i] == 1.0 and M_T[j] == 1.0:
            ax.text(j, i, "neutral", ha="center", va="center",
                    fontsize=8, color="#666666")
        elif counts[i, j]:
            ax.text(j, i, str(counts[i, j]), ha="center", va="center",
                    fontsize=9,
                    color="white" if counts[i, j] > counts.max() * 0.6
                    else "#1a1a1a")
ax.set_xticks(range(len(M_T)), [f"{v:g}" for v in M_T])
ax.set_yticks(range(len(M_L0)), [f"{v:g}" for v in M_L0])
ax.set_xlabel("learning-rate multiplier mT")
ax.set_ylabel("prior multiplier mL0")
ax.set_title(f"Fitted personal multipliers of {len(pers)} students\n"
             "(students at the neutral cell are not shown; they stay default)")
fig.colorbar(im, ax=ax, label="number of students")
fig.tight_layout()
fig.savefig("results/multiplier_grid.png", dpi=150)
print("saved results/multiplier_grid.png")
print(f"personalized students: {len(pers)}")
