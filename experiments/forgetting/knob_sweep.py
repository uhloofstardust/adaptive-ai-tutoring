"""Two knobs on CurriculumTutor, and how the best setting depends on the
break length.

CurriculumTutor here is the published algorithm (KL-UCB over the ZPD, CUSUM
mastery test; see cursim/schedulers/curriculum_tutor_paper.py). Every tutor
in this experiment is that algorithm with at most two things changed:

  revision budget   the share of questions spent on already-learned topics
                    (0 = the published algorithm)
  study depth       the CUSUM threshold h that says "learned, move on"
                    (the paper's ln(1/0.0004) = the published algorithm).
                    Reported as the number of correct answers in a row
                    that clears it.

Nothing else differs between tutors, and no tutor is told the break length.
Questions the tutor has no use for (the ZPD is empty) are left unasked, as in
the paper: `leftover="idle"`. The variant `leftover="revise"` spends them on
revision instead (suite entry knob_sweep_spare).
The break length is not a knob: it is the situation. For each break length
we ask which knob setting gives the most topics still usable afterwards.

The best setting is chosen on one set of learners (selection seeds) and its
score is read on a different set (evaluation seeds), so the reported numbers
are not flattered by the choosing.
"""

import json
import math
import os
from concurrent.futures import ProcessPoolExecutor

from cursim.curriculum import build_curriculum
from cursim.params import BKT_PARAMS
from cursim.schedulers.curriculum_tutor_paper import PAPER_H
from cursim.simulation import RunSpec, run_condition
from cursim.stats import mean_ci

from ..registry import experiment
from .common import UsableAfter, usable_ci
from .plots import (fig_knob_best, fig_knob_curves, fig_knob_heat,
                    fig_knob_loss)

RHOS = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6)
HS = (1.0, 2.0, 3.0, 4.0, 6.0, PAPER_H, 10.0, 12.0, 15.0, 22.0)
BREAKS = (0, 1, 2, 3, 4, 5, 7, 10, 14, 21, 28)
HALF_LIVES = (14, 7, 28)

_LLR = math.log((1 - BKT_PARAMS["p_S"]) / BKT_PARAMS["p_G"])


def rows_needed(h):
    """Correct answers in a row that clear threshold h from a fresh start."""
    return math.floor(h / _LLR + 1e-9) + 1


CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), ".cache", "knob_sweep")


def _cell(args):
    """Cached on disk, so a long sweep can be run in pieces."""
    key = ("v2_" if args[3] == "revise" else "v3_") + "_".join(str(a) if not isinstance(a, tuple) else
                   "-".join(map(str, a)) for a in args)
    path = os.path.join(CACHE, key + ".json")
    if os.path.exists(path):
        raw = json.load(open(path))
        return (args, {int(d): tuple(v) for d, v in raw["out"].items()},
                raw["extra"])
    _, out, extra = _cell_run(args)
    os.makedirs(CACHE, exist_ok=True)
    json.dump({"out": out, "extra": extra}, open(path, "w"))
    return args, out, extra


def _cell_run(args):
    """One (half-life, revision, depth) cell on one seed set: for every
    break, the population mean and 95% half-width of usable topics."""
    hl, rho, h, leftover, seed, n, breaks = args
    cur = build_curriculum("layered_40")
    spec = RunSpec(
        scheduler="curriculum_tutor_paper", mastery_model="binary",
        scheduler_params=dict(depth_h=h, revision=rho, leftover=leftover),
        profile="average", profile_overrides={"forget_half_life_days": hl},
        break_days=breaks, label=f"rho={rho} h={h:.2f}")
    res = run_condition(cur, spec, n_learners=n, base_seed=seed)
    out = {d: usable_ci(UsableAfter(res, d), "v") for d in breaks}
    st = [r["sched_stats"] for r in res.per_learner]
    extra = dict(final_learned=res.mean("final_learned"),
                 coverage=res.mean("coverage"),
                 revision_share=sum(x["revision_share"] for x in st) / len(st),
                 tutor_learned=sum(x["tutor_learned"] for x in st) / len(st),
                 finished=sum(x["finished"] for x in st) / len(st))
    return args, out, extra


@experiment("knob_sweep",
            "Revision budget and study depth as the only changes to the "
            "published CurriculumTutor; best setting at each fixed break "
            "length.",
            defaults=dict(n_select=50, n_eval=100, select_seed=9000,
                          eval_seed=12000, half_lives=HALF_LIVES,
                          break_days=BREAKS),
            curriculum="layered_40")
def knob_sweep(n_select=50, n_eval=100, select_seed=9000, eval_seed=12000,
               half_lives=HALF_LIVES, break_days=BREAKS, warm=None,
               leftover="idle", cur=None, **_):
    """`warm=(rho_index_lo, rho_index_hi)` only fills the on-disk cache for
    those revision values and returns, so a long sweep can be run in pieces
    that each fit a short call. Without it the full sweep runs (instantly,
    if the cache is full)."""
    breaks = tuple(break_days)
    jobs = [(hl, r, h, leftover, seed, n, breaks)
            for hl in half_lives
            for r in (RHOS if warm is None else RHOS[warm[0]:warm[1]])
            for h in HS
            for seed, n in ((select_seed, n_select), (eval_seed, n_eval))]
    with ProcessPoolExecutor() as ex:
        done = list(ex.map(_cell, jobs, chunksize=2))
    if warm is not None:
        return {"tables": {}, "figures": {},
                "summary": f"cache warmed for {len(jobs)} cells"}
    sel, ev, extras = {}, {}, {}
    for (hl, r, h, _lo, seed, n, _), out, extra in done:
        (sel if seed == select_seed else ev)[(hl, r, h)] = out
        if seed == eval_seed:
            extras[(hl, r, h)] = extra

    grid_rows, best_rows, loss_rows, fixed_rows = [], [], [], []
    figures, notes = {}, []
    rho_by_hl, rows_by_hl, breaks_by_hl = {}, {}, {}
    for hl in half_lives:
        def S(r, h, d):
            return sel[(hl, r, h)][d][0]

        def E(r, h, d):
            return ev[(hl, r, h)][d]

        for r in RHOS:
            for h in HS:
                for d in breaks:
                    grid_rows.append(dict(
                        half_life_days=hl, revision=r, depth_h=round(h, 2),
                        correct_in_row=rows_needed(h), break_days=d,
                        select_mean=round(S(r, h, d), 2),
                        eval_mean=round(E(r, h, d)[0], 2),
                        eval_ci95=round(E(r, h, d)[1], 2)))
        ct = (0.0, PAPER_H)
        fam = {
            "revision only": [(r, PAPER_H) for r in RHOS],
            "depth only": [(0.0, h) for h in HS],
            "both": [(r, h) for r in RHOS for h in HS],
        }
        chosen = {}
        for d in breaks:
            for name, cells in fam.items():
                best = max(cells, key=lambda c: (S(c[0], c[1], d), -c[0]))
                chosen[(name, d)] = best
                v, ci = E(best[0], best[1], d)
                best_rows.append(dict(
                    half_life_days=hl, break_days=d, family=name,
                    best_revision=best[0], best_depth_h=round(best[1], 2),
                    best_correct_in_row=rows_needed(best[1]),
                    usable_eval=round(v, 2), ci95=round(ci, 2),
                    published_ct=round(E(*ct, d)[0], 2),
                    gain_over_ct=round(v - E(*ct, d)[0], 2)))
        live = [d for d in breaks
                if E(*chosen[("both", d)][:2], d)[0] >= 1.0]
        both_best = {d: E(*chosen[("both", d)][:2], d)[0] for d in breaks}

        # Fixed settings: one choice used for every break, picked on the
        # selection seeds to do best on average over the live breaks.
        def fixed_best(cells):
            return max(cells, key=lambda c: sum(S(c[0], c[1], d)
                                                for d in live) / len(live))
        fixed = {
            "published CurriculumTutor": ct,
            "best single revision budget": fixed_best(fam["revision only"]),
            "best single study depth": fixed_best(fam["depth only"]),
            "best single pair of both": fixed_best(fam["both"]),
        }
        losses = {}
        for name, c in fixed.items():
            ys = [both_best[d] - E(c[0], c[1], d)[0] for d in breaks]
            losses[name] = ys
            lv = [both_best[d] - E(c[0], c[1], d)[0] for d in live]
            fixed_rows.append(dict(
                half_life_days=hl, setting=name, revision=c[0],
                depth_h=round(c[1], 2), correct_in_row=rows_needed(c[1]),
                mean_loss=round(sum(lv) / len(lv), 2),
                worst_loss=round(max(lv), 2),
                breaks_within_1_of_best=sum(
                    1 for x in lv if x <= 1.0), n_breaks=len(lv)))
            for d, y in zip(breaks, ys):
                loss_rows.append(dict(half_life_days=hl, setting=name,
                                      break_days=d, topics_lost=round(y, 2)))
        # for the "best setting against break length" figure: the best pair,
        # only where it still keeps 5+ topics (below that it is noise)
        shown = [d for d in live if both_best[d] >= 5]
        breaks_by_hl[hl] = list(shown)
        rho_by_hl[hl] = [chosen[("both", d)][0] for d in shown]
        rows_by_hl[hl] = [rows_needed(chosen[("both", d)][1]) for d in shown]
        notes.append(
            f"half-life {hl}d: published CT loses on average "
            f"{fixed_rows[-4]['mean_loss']} topics (worst "
            f"{fixed_rows[-4]['worst_loss']}) against the best "
            f"(revision, depth) per break; best single pair "
            f"{fixed_rows[-1]['mean_loss']} (worst "
            f"{fixed_rows[-1]['worst_loss']})")

        if hl == 14:
            show = [d for d in (0, 1, 3, 5, 7, 10, 14) if d in live]
            depth_rows = [rows_needed(h) for h in HS]
            figures["knob_curves"] = fig_knob_curves(
                list(RHOS), depth_rows,
                {d: [E(r, PAPER_H, d)[0] for r in RHOS] for d in show},
                {d: [E(0.0, h, d)[0] for h in HS] for d in show}, show, hl,
                {d: chosen[("revision only", d)][0] for d in show},
                {d: rows_needed(chosen[("depth only", d)][1]) for d in show})
            hshow = [d for d in (0, 3, 7, 14) if d in live]
            figures["knob_heat"] = fig_knob_heat(
                list(RHOS), depth_rows,
                {d: [[E(r, h, d)[0] for r in RHOS] for h in HS]
                 for d in hshow}, hshow, hl)
            figures["knob_loss"] = fig_knob_loss(
                list(live), {n: [v for d, v in zip(breaks, ys) if d in live]
                             for n, ys in losses.items()}, hl)
    figures["knob_best"] = fig_knob_best(breaks_by_hl, rho_by_hl, rows_by_hl)
    cov = [dict(half_life_days=k[0], revision=k[1], depth_h=round(k[2], 2),
                final_learned=round(v["final_learned"], 2),
                coverage=round(v["coverage"], 2),
                tutor_marked_learned=round(v["tutor_learned"], 2),
                share_finished=round(v["finished"], 2),
                revision_share=round(v["revision_share"], 3))
           for k, v in sorted(extras.items())]
    return {
        "tables": {"grid": grid_rows, "best": best_rows,
                   "fixed_settings": fixed_rows, "loss": loss_rows,
                   "coverage": cov},
        "figures": figures,
        "summary": (f"selection: {n_select} learners (seeds {select_seed}+), "
                    f"evaluation: {n_eval} fresh learners (seeds "
                    f"{eval_seed}+), layered_40. " + "; ".join(notes) + "."),
    }
