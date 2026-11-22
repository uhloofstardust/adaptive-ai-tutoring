"""Distribution of the fitted forgetting probability over the 94
skills. Writes results/pf_distribution.png."""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

pf = pd.read_csv("results/params_forget.csv")["pF"]
vals = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25]
counts = [int((pf == v).sum()) for v in vals]

fig, ax = plt.subplots(figsize=(7, 4.5))
bars = ax.bar([f"{v:.2f}" for v in vals], counts,
              color=["#185FA5"] + ["#c47f0e"] * 5)
for b, c in zip(bars, counts):
    ax.text(b.get_x() + b.get_width() / 2, c + 0.8, str(c),
            ha="center", fontsize=10)
ax.set_xlabel("fitted P(F)")
ax.set_ylabel("number of skills")
ax.set_title(f"Fitted forgetting probability over {len(pf)} skills\n"
             "(blue = forgetting rejected, orange = forgetting chosen)")
ax.grid(alpha=0.25, axis="y")
fig.tight_layout()
fig.savefig("results/pf_distribution.png", dpi=150)
print("saved results/pf_distribution.png")
