"""The symmetric result: each axis dominates the aggregation that
removes its rival's signal. Writes results/axes_macro.png."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

panels = [
    ("Within-skill ranking\n(macro over 92 skills)",
     ["student-mean\nbaseline", "skill-based\nBKT", "student-based\nBKT"],
     [0.6533, 0.6486, 0.6718]),
    ("Within-student ranking\n(macro over 1,606 students)",
     ["skill-mean\nbaseline", "skill-based\nBKT", "student-based\nBKT"],
     [0.5937, 0.5853, 0.5741]),
]
fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharey=False)
for ax, (title, names, vals) in zip(axes, panels):
    colors = ["#999999", "#185FA5", "#c47f0e"]
    bars = ax.bar(names, vals, color=colors)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.001, f"{v:.4f}",
                ha="center", fontsize=9)
    ax.set_title(title, fontsize=10)
    ax.set_ylim(min(vals) - 0.02, max(vals) + 0.015)
    ax.grid(alpha=0.25, axis="y")
axes[0].set_ylabel("macro AUC")
fig.suptitle("Each axis wins where the other's signal is removed",
             fontsize=12)
fig.tight_layout()
fig.savefig("results/axes_macro.png", dpi=150)
print("saved results/axes_macro.png")
