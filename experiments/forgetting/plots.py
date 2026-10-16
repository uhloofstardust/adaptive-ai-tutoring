"""Figures for the forgetting experiments. Each function returns a
matplotlib Figure; saving is the runner's job. Colours come from the
condition label (style.color) so a condition looks the same everywhere."""

import matplotlib.pyplot as plt

from ..style import color


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


def fig_curriculum(cur):
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
    ax.set_title(f"Curriculum: {len(cur.concepts)} concepts, "
                 f"{len(cur.all_questions())} questions, "
                 f"{len(cur.roots())} independent entry points")
    fig.tight_layout()
    return fig


def fig_representation(results, retention_days=3):
    """Binary vs continuous mastery, scheduler held fixed."""
    labels = list(results)
    short = [l.replace(" + ", "\n+ ").replace(" (", "\n(")
             for l in labels]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.3))
    for ax, key, name, fmt in [
            (axes[0], "final_learned", "concepts learned (>= 0.80)", "{:.1f}"),
            (axes[1], "retained_usable",
             f"still usable after {retention_days} idle days (>= 0.50)",
             "{:.1f}"),
            (axes[2], "retained_mastery",
             f"mean mastery after {retention_days} idle days", "{:.3f}")]:
        _bars(ax, short, [results[l].mean(key) for l in labels],
              [results[l].sd(key) for l in labels], fmt=fmt)
        ax.set_title(name)
    axes[0].set_ylabel("concepts (of 40)")
    fig.suptitle("Tutor's mastery representation, scheduling rule held "
                 "fixed (CurriculumTutor gate)", fontsize=12)
    fig.tight_layout()
    return fig


def fig_trajectories(curves: dict, title):
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
    return fig


def fig_worlds(rows):
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
    return fig


def fig_learner_types(matrix):
    """Learner types x scheduler."""
    profiles = list(matrix)
    conds = list(matrix[profiles[0]])
    n = len(conds)
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    width = 0.8 / n
    for i, c in enumerate(conds):
        xs = [j + i * width - 0.4 + width / 2 for j in range(len(profiles))]
        vals = [matrix[p][c] for p in profiles]
        ax.bar(xs, vals, width=width * 0.92, label=c, color=color(c))
        for x, v in zip(xs, vals):
            ax.text(x, v + 0.4, f"{v:.0f}", ha="center", fontsize=8)
    ax.set_xticks(range(len(profiles)))
    ax.set_xticklabels(profiles)
    ax.set_ylabel("concepts usable after the break")
    ax.set_title("Learner type against tutoring condition")
    ax.legend(fontsize=9)
    fig.tight_layout()
    return fig


def fig_halflife_sweep(x, series):
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
    return fig


def fig_grid(beliefs, scheds, cell, baseline):
    """Heatmap: tutor's belief model (rows) x scheduler (columns).
    `cell[(belief, sched)]` is the mean number of concepts usable."""
    import numpy as np
    z = np.array([[cell[(b, s)] for s in scheds] for b in beliefs])
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    im = ax.imshow(z, cmap="YlGn", aspect="auto")
    for i in range(len(beliefs)):
        for j in range(len(scheds)):
            ax.text(j, i, f"{z[i, j]:.1f}", ha="center", va="center",
                    fontsize=11, fontweight="bold")
    ax.set_xticks(range(len(scheds)))
    ax.set_xticklabels(scheds)
    ax.set_yticks(range(len(beliefs)))
    ax.set_yticklabels(beliefs)
    ax.set_xlabel("question-selection rule")
    ax.set_ylabel("what the tutor believes")
    ax.grid(False)
    ax.set_title(f"Concepts usable after the break "
                 f"(CurriculumTutor baseline {baseline:.1f})")
    fig.colorbar(im, ax=ax, fraction=0.04)
    fig.tight_layout()
    return fig


def fig_break_sweep(days, series, cis, title):
    """Concepts still usable against the length of the break."""
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for name, ys in series.items():
        ls = ("-" if "oracle" not in name
              else "--" if name.endswith("CT") else ":")
        ax.plot(days, ys, marker="o", ms=4, lw=2, ls=ls, label=name,
                color=color(name))
        lo = [y - e for y, e in zip(ys, cis[name])]
        hi = [y + e for y, e in zip(ys, cis[name])]
        ax.fill_between(days, lo, hi, color=color(name), alpha=0.12, lw=0)
    ax.set_xlabel("days of break after the last session")
    ax.set_ylabel("concepts still usable (mastery >= 0.50)")
    ax.set_title(title)
    ax.legend(fontsize=9)
    fig.tight_layout()
    return fig


def fig_mismatch(panels, baselines, matched):
    """Tutor's assumed forgetting rate against concepts usable, one panel
    per true learner half-life. `panels[hl][scheduler]` is
    [(rate, mean, ci), ...]."""
    hls = list(panels)
    fig, axes = plt.subplots(1, len(hls), figsize=(4.6 * len(hls), 4.4),
                             sharey=True, squeeze=False)
    axes = axes[0]
    for ax, hl in zip(axes, hls):
        for sched, pts in panels[hl].items():
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            name = {"curriculum_tutor": "CT + forgetting model",
                    "adaptive_review": "adaptive review"}.get(sched, sched)
            ax.errorbar(xs, ys, yerr=[p[2] for p in pts], marker="o", ms=4,
                        lw=2, capsize=2, label=name, color=color(name))
        ax.axhline(baselines[hl], color=color("CT + binary"), ls="--",
                   lw=1.5, label="CT + binary")
        ax.axvline(matched[hl], color="#6B4FA0", ls=":", lw=1.5,
                   label="true rate")
        ax.set_xscale("symlog", linthresh=0.01)
        ax.set_xlim(left=0)
        ax.set_title(f"true half-life {hl} days")
        ax.set_xlabel("forgetting rate the tutor assumes (per day)")
    axes[0].set_ylabel("concepts usable after the break")
    axes[0].legend(fontsize=8)
    fig.suptitle("A tutor with the wrong forgetting speed", fontsize=12)
    fig.tight_layout()
    return fig


def fig_estimation_cost(rules, estimated, oracle, errs):
    """Per rule: usable concepts with the tutor's own belief against the
    same rule with a perfect belief. The gap is what better estimation
    could buy that rule."""
    import numpy as np
    x = np.arange(len(rules))
    fig, ax = plt.subplots(figsize=(8, 4.4))
    ax.bar(x - 0.2, estimated, 0.38, yerr=errs, capsize=3,
           color=[color(r) for r in rules], label="tutor's decaying belief")
    ax.bar(x + 0.2, oracle, 0.38, color=[color(r) for r in rules],
           alpha=0.45, hatch="//", edgecolor="white",
           label="perfect belief (reference)")
    for xi, a, b in zip(x, estimated, oracle):
        ax.text(xi - 0.2, a + 0.5, f"{a:.1f}", ha="center", fontsize=8.5)
        ax.text(xi + 0.2, b + 0.5, f"{b:.1f}", ha="center", fontsize=8.5)
    ax.set_xticks(x)
    ax.set_xticklabels(rules, fontsize=9)
    ax.set_ylabel("concepts usable after the break")
    ax.set_title("What a perfect belief would add to each rule")
    ax.legend(fontsize=9, loc="lower right")
    fig.tight_layout()
    return fig


def fig_review_tuning(rules, rates, r_review, rows):
    """Robust score against the fade threshold, a panel per belief decay
    rate and a line per review rule."""
    fig, axes = plt.subplots(1, len(rates), figsize=(5.2 * len(rates), 4.2),
                             sharey=True, squeeze=False)
    for ax, rate in zip(axes[0], rates):
        for rule in rules:
            ys = [next(x["robust"] for x in rows
                       if x["rule"] == rule and x["r_review"] == r
                       and x["belief_decay_per_day"] == rate)
                  for r in r_review]
            name = rule.replace("_", " ")
            ax.plot(r_review, ys, marker="o", lw=2, label=name,
                    color=color(name))
        ax.set_title(f"belief decays {rate} per day")
        ax.set_xlabel("fade threshold r_review")
    axes[0][0].set_ylabel("usable concepts, mean over breaks of 0-10 days")
    axes[0][0].legend(fontsize=8.5)
    fig.tight_layout()
    return fig


def fig_margin(days, panels, title):
    """Break curves for several mastery thresholds, one panel per belief.
    `panels[name][threshold]` is the list of usable concepts by break."""
    fig, axes = plt.subplots(1, len(panels), figsize=(5.6 * len(panels), 4.4),
                             sharey=True, squeeze=False)
    for ax, (name, by_thr) in zip(axes[0], panels.items()):
        n = len(by_thr)
        for i, (thr, ys) in enumerate(by_thr.items()):
            ax.plot(days, ys, lw=2, marker="o", ms=3.5,
                    color=plt.cm.viridis(i / max(1, n - 1)),
                    label=f"mastered at {thr}")
        ax.set_title(name)
        ax.set_xlabel("days of break")
    axes[0][0].set_ylabel("concepts usable (mastery >= 0.50)")
    axes[0][0].legend(fontsize=8.5)
    fig.suptitle(title, fontsize=11.5)
    fig.tight_layout()
    return fig


_GAP_COLORS = {"CT as published (binary)": "#B4482B",
               "CT + decay belief, mastered at 0.7": "#9FC5A8",
               "CT + decay belief, mastered at 0.8": "#3D7A5B",
               "CT + decay belief, mastered at 0.9": "#1C4A33",
               "adaptive review + decay belief": "#E8A020"}


def fig_poster_gap(days, panels):
    """Top row: concepts usable against break length for every setting, with
    the best-in-hindsight envelope. Bottom row: each setting's gap to it.
    `panels[half_life] = (series, cis, best)`."""
    n = len(panels)
    fig, axes = plt.subplots(2, n, figsize=(5.2 * n, 8), squeeze=False,
                             sharex="col")
    for j, (hl, (series, cis, best)) in enumerate(panels.items()):
        top, bot = axes[0][j], axes[1][j]
        for name, ys in series.items():
            c = _GAP_COLORS.get(name, "#5B6B78")
            top.plot(days, ys, marker="o", ms=3, lw=1.8, color=c, label=name)
            bot.plot(days, [b - y for b, y in zip(best, ys)], marker="o",
                     ms=3, lw=1.8, color=c)
        top.plot(days, best, color="black", ls="--", lw=1.4,
                 label="best possible (best setting at each break)")
        top.set_title(f"learners with a {hl}-day memory half-life")
        bot.set_xlabel("days of break")
        bot.axhline(0, color="black", lw=0.8)
        live = [d for d, b in zip(days, best) if b >= 1.0]
        top.set_xlim(-0.5, max(live) + 2)
    axes[0][0].set_ylabel("concepts still usable")
    axes[1][0].set_ylabel("concepts lost versus the best setting")
    axes[0][0].legend(fontsize=7.5)
    fig.tight_layout()
    return fig
