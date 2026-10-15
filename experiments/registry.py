"""The experiment registry.

An experiment is a function returning

    {"tables":  {name: [row dicts]},
     "figures": {name: matplotlib Figure},
     "summary": str}

Register one with the decorator and it is available everywhere (the
command line, the interface, the tests) with no other edit:

    @experiment("my_experiment", "What it asks.",
                defaults=dict(n_learners=30), curriculum="layered_40")
    def my_experiment(n_learners=30, cur=None, **_):
        ...

`defaults` are the parameters the interface offers as controls. A function
takes `cur` (a Curriculum); the runner builds it from the `curriculum`
parameter, whose default is declared here.
"""

import functools
from typing import Callable, Dict, Tuple

from .style import theme as _theme

# name -> (function, description, default parameters). Kept as a tuple so
# the interface can unpack it directly.
EXPERIMENTS: Dict[str, Tuple[Callable, str, dict]] = {}
# name -> {"curriculum": default curriculum name, "theme": ..., "group": ...}
META: Dict[str, dict] = {}


def experiment(name: str, description: str, defaults: dict = None,
               curriculum: str = "abstract", theme: str = "light"):
    def deco(fn):
        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            with _theme(theme):
                return fn(*args, **kwargs)

        if name in EXPERIMENTS:
            raise ValueError(f"experiment {name!r} already registered")
        EXPERIMENTS[name] = (wrapped, description, dict(defaults or {}))
        group = fn.__module__.split(".")[1] if "." in fn.__module__ else ""
        META[name] = {"curriculum": curriculum, "theme": theme,
                      "group": group}
        return wrapped
    return deco
