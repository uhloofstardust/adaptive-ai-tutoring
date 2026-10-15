"""Experiments on the simulator, one module each.

    experiments/bkt/         validation of the BKT tutor on the plain student
    experiments/forgetting/  forgetting-aware tutoring on the continuous student

    python -m experiments list
    python -m experiments run <name> [--set key=value ...] [--out results]
    python -m experiments suite <suite> [--out results]

Importing this package registers every experiment (see registry.py).
"""

import importlib
import pkgutil

from .registry import EXPERIMENTS, META, experiment  # noqa: F401


def load_all():
    """Import every experiment module so each registers itself."""
    for group in ("bkt", "forgetting"):
        pkg = importlib.import_module(f"{__name__}.{group}")
        for m in pkgutil.iter_modules(pkg.__path__):
            if m.name != "common":
                importlib.import_module(f"{pkg.__name__}.{m.name}")
    return EXPERIMENTS


load_all()
