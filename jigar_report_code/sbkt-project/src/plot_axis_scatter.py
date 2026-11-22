"""Per-student AUC: skill-based vs student-based model. Above the
diagonal = the student's own model predicts them better than the
skill model does. Writes results/axis_scatter.png."""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

d = pd.read_csv("results/auc_per_student_axes.csv")
win = (d.auc_student > d.auc_skill).mean()

fig, ax = plt.subplots(figsize=(6.5, 6.5))
ax.plot([0, 1], [0, 1], "--", color="#888888", lw=1)
ax.scatter(d.auc_skill, d.auc_student, s=10, alpha=0.35,
           color="#c47f0e")
ax.set_xlabel("per-student AUC, skill-based BKT")
ax.set_ylabel("per-student AUC, student-based BKT")
ax.set_title(f"Per-student head-to-head ({len(d)} students, "
             f">= 10 future rows)\nstudent model wins for "
             f"{win:.0%} of students")
ax.grid(alpha=0.25)
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
fig.tight_layout()
fig.savefig("results/axis_scatter.png", dpi=150)
print("saved results/axis_scatter.png")
