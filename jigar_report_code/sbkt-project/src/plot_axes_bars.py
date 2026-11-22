"""Pooled AUC of the four predictors on the common subset.
Writes results/axes_bars.png."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

names = ["per-skill\nmean", "per-student\nmean",
         "skill-based\nBKT", "student-based\nBKT"]
aucs = [0.6253, 0.6619, 0.7219, 0.6961]
colors = ["#9db8d2", "#d9b38c", "#185FA5", "#c47f0e"]

fig, ax = plt.subplots(figsize=(7.5, 5))
bars = ax.bar(names, aucs, color=colors)
for b, a in zip(bars, aucs):
    ax.text(b.get_x() + b.get_width() / 2, a + 0.002, f"{a:.4f}",
            ha="center", fontsize=10)
ax.set_ylim(0.55, 0.75)
ax.set_ylabel("pooled AUC on common future rows")
ax.set_title("Which axis carries the signal?\n"
             "(84,850 future rows where both models are defined)")
ax.grid(alpha=0.25, axis="y")
fig.tight_layout()
fig.savefig("results/axes_bars.png", dpi=150)
print("saved results/axes_bars.png")
