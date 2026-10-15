"""Figure themes. Every experiment declares one; the registry applies it
while the experiment runs, so figures look the same whether they come
from the command line, the interface, or a test, and no experiment can
change another's look by importing it.

    dark    the interface palette (BKT validation experiments)
    light   white background (forgetting experiments)
"""

import contextlib

import matplotlib
matplotlib.use("Agg")

INK, ACCENT, GREY, GOOD = "#e6e9f0", "#6f8ffb", "#98a1b5", "#3ecf8e"
PAPER = "#12151d"

THEMES = {
    "dark": {
        "font.size": 10, "figure.dpi": 130,
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial",
                            "DejaVu Sans"],
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#3a4253", "axes.labelcolor": INK,
        "text.color": INK, "xtick.color": GREY, "ytick.color": GREY,
        "figure.facecolor": PAPER, "axes.facecolor": PAPER,
        "savefig.facecolor": PAPER, "grid.color": "#252b38",
        "legend.facecolor": PAPER, "legend.edgecolor": "#3a4253",
    },
    "light": {
        "figure.dpi": 130, "savefig.dpi": 160,
        "font.size": 10, "axes.titlesize": 11.5, "axes.labelsize": 10,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.25, "legend.frameon": False,
    },
}

# Light-theme colours, keyed by a substring of the condition label. Most
# specific substring first: "continuous + forgetting" must not be caught
# by the "continuous" rule.
PALETTE = [("binary", "#B4482B"), ("forgetting", "#3D7A5B"),
           ("forget", "#3D7A5B"), ("adaptive", "#E8A020"),
           ("continuous", "#2C5FA8"), ("curriculum", "#B4482B"),
           ("CT +", "#B4482B"), ("random", "#8A8F9A")]


def color(label: str) -> str:
    """Colour for a condition label (light theme)."""
    for key, value in PALETTE:
        if key in label:
            return value
    return "#5B6B78"


@contextlib.contextmanager
def theme(name: str):
    """Apply a named theme for the duration of the block."""
    if name not in THEMES:
        raise ValueError(f"unknown theme {name!r}; have {sorted(THEMES)}")
    with matplotlib.rc_context(THEMES[name]):
        yield
