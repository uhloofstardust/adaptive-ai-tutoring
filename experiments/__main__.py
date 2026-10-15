"""Command line.

    python -m experiments list
    python -m experiments run <name> [--set key=value ...] [--out results]
    python -m experiments suite <suite|all> [--out results]

Values given to --set are read as Python literals, so
`--set n_learners=100 --set half_lives="(5,10,20)"` works; anything that
does not parse stays a string. `--set curriculum=layered_40` picks the
curriculum.
"""

import argparse
import ast
import sys

from . import EXPERIMENTS, META
from .runner import DEFAULT_OUT, run_and_save
from .suites import SUITES


def _parse_set(items):
    out = {}
    for item in items or []:
        if "=" not in item:
            sys.exit(f"--set expects key=value, got {item!r}")
        k, v = item.split("=", 1)
        try:
            out[k.strip()] = ast.literal_eval(v)
        except (ValueError, SyntaxError):
            out[k.strip()] = v
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m experiments")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list experiments and suites")
    r = sub.add_parser("run", help="run one experiment")
    r.add_argument("name")
    r.add_argument("--set", action="append", metavar="KEY=VALUE")
    r.add_argument("--out", default=DEFAULT_OUT)
    s = sub.add_parser("suite", help="run a named group of runs")
    s.add_argument("name", help=f"one of {', '.join(SUITES)}, or all")
    s.add_argument("--out", default=DEFAULT_OUT)
    a = ap.parse_args(argv)

    if a.cmd == "list":
        for name, (_, desc, defaults) in sorted(EXPERIMENTS.items()):
            print(f"{name:22s} [{META[name]['group']}, "
                  f"{META[name]['curriculum']}]\n    {desc}\n    "
                  f"defaults: {defaults}")
        print("\nsuites: " + ", ".join(f"{k} ({len(v)} runs)"
                                        for k, v in SUITES.items()))
    elif a.cmd == "run":
        print(run_and_save(a.name, _parse_set(a.set), a.out))
    else:
        names = list(SUITES) if a.name == "all" else [a.name]
        for n in names:
            if n not in SUITES:
                sys.exit(f"no suite {n!r}; have {', '.join(SUITES)}")
            for output_name, exp, params in SUITES[n]:
                print(f"[{n}] {output_name} ...", flush=True)
                run_and_save(exp, params, a.out, output_name)


if __name__ == "__main__":
    main()
