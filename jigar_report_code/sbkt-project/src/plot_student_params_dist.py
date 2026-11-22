"""Distributions of the fitted per-student parameters, with the
per-skill medians marked for contrast. Writes
results/student_params_dist.png."""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

stu = pd.read_csv("results/params_students.csv")
skill_medians = {"pL0": 0.70, "pT": 0.15, "pS": 0.20, "pG": 0.15}

fig, axes = plt.subplots(2, 2, figsize=(9, 7))
for ax, p in zip(axes.flat, ["pL0", "pT", "pS", "pG"]):
    ax.hist(stu[p], bins=19, color="#c47f0e", edgecolor="white")
    ax.axvline(skill_medians[p], color="#185FA5", lw=2, ls="--",
               label=f"per-skill median {skill_medians[p]:.2f}")
    ax.set_title(f"per-student {p}  (median {stu[p].median():.2f})",
                 fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25, axis="y")
fig.suptitle(f"Fitted parameters of {len(stu)} students "
             "(orange) vs the skill axis (blue dashed)", fontsize=11)
fig.tight_layout()
fig.savefig("results/student_params_dist.png", dpi=150)
print("saved results/student_params_dist.png")
