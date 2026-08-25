"""Figures. Consistent styling, no chartjunk, values labelled so a
reader can quote a number without a table.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# most specific substring first: "continuous + forgetting" must not
# be caught by the "continuous" rule
PALETTE = [("binary", "#B4482B"), ("forgetting", "#3D7A5B"),
           ("forget", "#3D7A5B"), ("adaptive", "#E8A020"),
           ("continuous", "#2C5FA8"), ("curriculum", "#B4482B"),
           ("CT +", "#B4482B"), ("random", "#8A8F9A")]
RETENTION_DAYS = 3          # set by run_experiments to match the spec
plt.rcParams.update({
    "figure.dpi": 130, "savefig.dpi": 160,
    "font.size": 10, "axes.titlesize": 11.5, "axes.labelsize": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "legend.frameon": False,
})


def color(name: str) -> str:
    for k, v in PALETTE:
        if k in name:
            return v
    return "#5B6B78"


def _bars(ax, labels, values, errs=None, fmt="{:.1f}", ylabel=""):
    cols = [color(l) for l in labels]
    b = ax.bar(range(len(labels)), values, yerr=errs, color=cols,
               capsize=3, width=0.62)
    for i, (v, bar) in enumerate(zip(values, b)):
        pad = (errs[i] if errs else 0) + max(values) * 0.03
        ax.text(bar.get_x() + bar.get_width() / 2, v + pad, fmt.format(v),
                ha="center", fontsize=9.5, fontweight="bold")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, max(values) * 1.28)


def fig_curriculum(cur, path):
    """The prerequisite DAG, laid out by tier."""
    tiers = {}
    for c in cur.concepts.values():
        tiers.setdefault(c.tier, []).append(c.cid)
    pos = {}
    for t, ids in tiers.items():
        ids.sort()
        for i, cid in enumerate(ids):
            pos[cid] = (t, i - len(ids) / 2.0)
    fig, ax = plt.subplots(figsize=(11, 7))
    for c in cur.concepts.values():
        x1, y1 = pos[c.cid]
        for p in c.prereqs:
            x0, y0 = pos[p]
            ax.annotate("", xy=(x1 - 0.06, y1), xytext=(x0 + 0.06, y0),
                        arrowprops=dict(arrowstyle="-|>", lw=0.7,
                                        color="#B9C2CC",
                                        connectionstyle="arc3,rad=0.08"))
    for cid, (x, y) in pos.items():
        t = cur.concepts[cid].tier
        ax.scatter([x], [y], s=42, zorder=3,
                   color=plt.cm.viridis(t / 5.0), edgecolor="white",
                   linewidth=0.8)
        ax.text(x + 0.07, y, cur.concepts[cid].name, fontsize=7.4,
                va="center")
    ax.set_xticks(sorted(tiers))
    ax.set_xticklabels([f"tier {t}\n({len(tiers[t])} concepts)"
                        for t in sorted(tiers)])
    ax.set_yticks([])
    ax.grid(False)
    ax.set_xlim(-0.4, max(tiers) + 1.15)
    ax.set_title(f"Language curriculum: {len(cur.concepts)} concepts, "
                 f"{len(cur.all_questions())} questions, "
                 f"{len(cur.roots())} independent entry points")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def fig_experiment1(results, path):
    """Binary vs continuous mastery, scheduler held fixed."""
    labels = list(results)
    short = [l.replace(" + ", "\n+ ").replace(" (", "\n(")
             for l in labels]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.3))
    for ax, key, name, fmt in [
            (axes[0], "final_learned", "concepts learned (>= 0.80)", "{:.1f}"),
            (axes[1], "retained_usable",
             f"still usable after {RETENTION_DAYS} idle days (>= 0.50)",
             "{:.1f}"),
            (axes[2], "retained_mastery",
             f"mean mastery after {RETENTION_DAYS} idle days", "{:.3f}")]:
        _bars(ax, short, [results[l].mean(key) for l in labels],
              [results[l].sd(key) for l in labels], fmt=fmt)
        ax.set_title(name)
    axes[0].set_ylabel("concepts (of 40)")
    fig.suptitle("Tutor's mastery representation, scheduling rule held "
                 "fixed (CurriculumTutor gate)", fontsize=12)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def fig_trajectories(curves: dict, path, title):
    """Mean true mastery over sessions."""
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    for name, ys in curves.items():
        ax.plot(range(1, len(ys) + 1), ys, lw=2, label=name,
                color=color(name))
    ax.set_xlabel("session")
    ax.set_ylabel("mean true mastery over all concepts")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def fig_experiment2(rows, path):
    """Forgetting: learner forgets vs not, tutor models it vs not."""
    worlds = ["learner forgets", "learner does not forget"]
    conds = list(rows[worlds[0]])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3), sharey=True)
    for ax, w in zip(axes, worlds):
        _bars(ax, conds, [rows[w][c] for c in conds], fmt="{:.1f}")
        ax.set_title(w)
    axes[0].set_ylabel("concepts usable after the break")
    fig.suptitle("Does modelling forgetting help, and does it cost "
                 "anything when there is none to model?", fontsize=12)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def fig_experiment3(matrix, path):
    """Learner types x scheduler."""
    profiles = list(matrix)
    conds = list(matrix[profiles[0]])
    n = len(conds)
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    width = 0.8 / n
    for i, c in enumerate(conds):
        xs = [j + i * width - 0.4 + width / 2 for j in range(len(profiles))]
        vals = [matrix[p][c] for p in profiles]
        bars = ax.bar(xs, vals, width=width * 0.92, label=c, color=color(c))
        for x, v in zip(xs, vals):
            ax.text(x, v + 0.4, f"{v:.0f}", ha="center", fontsize=8)
    ax.set_xticks(range(len(profiles)))
    ax.set_xticklabels(profiles)
    ax.set_ylabel("concepts usable after the break")
    ax.set_title("Learner type against tutoring condition")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def fig_experiment4(x, series, path):
    """Sweep over the learner's forgetting speed."""
    fig, ax = plt.subplots(figsize=(7.6, 4.7))
    for name, ys in series.items():
        ax.plot(x, ys, marker="o", ms=4.5, lw=2, label=name,
                color=color(name))
    ax.set_xlabel("learner's memory half-life (days) - left is more forgetful")
    ax.set_ylabel("concepts usable after the break")
    ax.set_title("Where modelling forgetting starts to matter")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
