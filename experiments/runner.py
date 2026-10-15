"""Run an experiment and write its outputs.

    results/<output_name>/
        <table>.csv        one per table the experiment returns
        <figure>.png       one per figure
        summary.md         the summary sentence and every small table
        meta.json          experiment, parameters, curriculum, commit, date

Everything is seeded, so the same parameters reproduce the same tables.
`meta.json` records exactly what produced a directory.
"""

import csv
import datetime
import json
import math
import os
import platform
import subprocess
import time
from typing import Optional

import matplotlib.pyplot as plt

from cursim.curriculum import build_curriculum

from .registry import EXPERIMENTS, META

DEFAULT_OUT = "results"


def resolve(name: str, overrides: Optional[dict] = None):
    """Return (function, merged parameters, curriculum name)."""
    if name not in EXPERIMENTS:
        raise KeyError(f"no experiment {name!r}. Available: "
                       f"{', '.join(sorted(EXPERIMENTS))}")
    fn, _, defaults = EXPERIMENTS[name]
    params = {**defaults, **(overrides or {})}
    curriculum = params.pop("curriculum", META[name]["curriculum"])
    return fn, params, curriculum


def run(name: str, overrides: Optional[dict] = None) -> dict:
    """Run one experiment and return its result dict (no files written)."""
    fn, params, curriculum = resolve(name, overrides)
    return fn(cur=build_curriculum(curriculum), **params)


def _cell(v):
    if isinstance(v, float) and math.isnan(v):
        return ""
    return v


def write_csv(path: str, rows: list):
    if not rows:
        return
    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: _cell(r.get(k, "")) for k in cols})


def _fmt(v):
    if isinstance(v, float):
        return "" if math.isnan(v) else f"{v:.4g}"
    return str(v)


def _markdown(rows: list) -> str:
    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    out = ["| " + " | ".join(cols) + " |",
           "|" + "|".join("---" for _ in cols) + "|"]
    for r in rows:
        out.append("| " + " | ".join(_fmt(r.get(c, "")) for c in cols) + " |")
    return "\n".join(out)


def _git_commit() -> str:
    try:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sha = subprocess.check_output(
            ["git", "-C", root, "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL, text=True).strip()
        dirty = subprocess.check_output(
            ["git", "-C", root, "status", "--porcelain", "--untracked-files=no"],
            stderr=subprocess.DEVNULL, text=True).strip()
        return sha + ("+uncommitted" if dirty else "")
    except Exception:
        return "unknown"


def save(result: dict, out_dir: str, meta: dict) -> str:
    """Write one result to `out_dir`; return the directory."""
    os.makedirs(out_dir, exist_ok=True)
    md = [f"# {meta['output_name']}", "", result["summary"], ""]
    for tname, rows in result["tables"].items():
        write_csv(os.path.join(out_dir, f"{tname}.csv"), rows)
        if rows and len(rows) <= 60:
            md += [f"## {tname}", "", _markdown(rows), ""]
    for fname, fig in result["figures"].items():
        fig.savefig(os.path.join(out_dir, f"{fname}.png"), dpi=170,
                    bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
    with open(os.path.join(out_dir, "summary.md"), "w") as f:
        f.write("\n".join(md))
    with open(os.path.join(out_dir, "meta.json"), "w") as f:
        json.dump(meta, f, indent=1, default=list)
    return out_dir


def run_and_save(name: str, overrides: Optional[dict] = None,
                 out_root: str = DEFAULT_OUT,
                 output_name: Optional[str] = None) -> str:
    """Run `name` with `overrides` and write results/<output_name>/."""
    output_name = output_name or name
    fn, params, curriculum = resolve(name, overrides)
    t0 = time.time()
    result = fn(cur=build_curriculum(curriculum), **params)
    meta = {"output_name": output_name, "experiment": name,
            "curriculum": curriculum, "parameters": params,
            "commit": _git_commit(),
            "run_at_utc": datetime.datetime.now(datetime.timezone.utc)
            .strftime("%Y-%m-%d %H:%M:%S"),
            "seconds": round(time.time() - t0, 1),
            "python": platform.python_version()}
    return save(result, os.path.join(out_root, output_name), meta)
