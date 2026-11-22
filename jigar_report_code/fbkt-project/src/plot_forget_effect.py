"""The same answer sequence under increasing forgetting, median
fitted parameters otherwise. Writes results/forget_effect.png."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fbkt import FBKT

SEQ = [0, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1]
SETTINGS = [("no forgetting: F=0.00", 0.00, "#185FA5"),
            ("F=0.10", 0.10, "#c47f0e"),
            ("F=0.25", 0.25, "#c0392b")]

fig, ax = plt.subplots(figsize=(9, 5))
for t, obs in enumerate(SEQ, start=1):
    if obs == 0:
        ax.axvspan(t - 0.5, t + 0.5, color="#f2d7d5", zorder=0)
xs = list(range(1, len(SEQ) + 1))
for label, pF, color in SETTINGS:
    m = FBKT(0.70, 0.15, 0.20, 0.15, pF)
    pL, ys = m.pL0, []
    for obs in SEQ:
        pL = m.transition(m.update(pL, obs))
        ys.append(pL)
    ax.plot(xs, ys, marker="o", markersize=4, lw=1.8, color=color,
            label=label)
ax.set_ylim(0, 1.02)
ax.set_xticks(xs)
ax.set_xlabel("practice opportunity")
ax.set_ylabel("P(skill mastered)")
ax.set_title("Effect of the forgetting probability "
             "(L0=0.70, T=0.15, S=0.20, G=0.15; shaded = wrong answers)")
ax.legend(loc="lower right", fontsize=9)
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig("results/forget_effect.png", dpi=150)
print("saved results/forget_effect.png")
