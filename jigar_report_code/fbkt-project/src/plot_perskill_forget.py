"""Per-skill test AUC: classical vs forgetting. Skills that chose
pF = 0 sit exactly on the diagonal (identical parameters), which
visually confirms the nesting. Writes results/perskill_forget.png."""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

d = pd.read_csv("results/auc_per_skill_forget.csv")
zero = d[d.pF == 0]
pos = d[d.pF > 0]

fig, ax = plt.subplots(figsize=(6.5, 6.5))
ax.plot([0.3, 1.0], [0.3, 1.0], "--", color="#888888", lw=1)
ax.scatter(zero.auc_classical, zero.auc_forget, s=22, color="#185FA5",
           label=f"pF = 0 ({len(zero)} skills, unchanged)", zorder=3)
ax.scatter(pos.auc_classical, pos.auc_forget, s=26, color="#c47f0e",
           label=f"pF > 0 ({len(pos)} skills)", zorder=3)
for sk in [375, 11, 307]:
    r = d[d.skill_id == sk]
    if len(r):
        r = r.iloc[0]
        ax.annotate(f"skill {sk}", (r.auc_classical, r.auc_forget),
                    textcoords="offset points", xytext=(6, 4),
                    fontsize=8)
ax.set_xlabel("test AUC, classical BKT")
ax.set_ylabel("test AUC, forgetting BKT")
ax.set_title("Per-skill test AUC: above the diagonal = forgetting helps")
ax.legend(loc="upper left", fontsize=9)
ax.grid(alpha=0.25)
ax.set_xlim(0.3, 1.0); ax.set_ylim(0.3, 1.0)
fig.tight_layout()
fig.savefig("results/perskill_forget.png", dpi=150)
print("saved results/perskill_forget.png")
