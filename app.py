"""cursim dry-run and experiment viewer.

    streamlit run app.py

Everything in the dropdowns comes from registries in the package
(LEARNERS, MASTERY_MODELS, SCHEDULERS, EXPERIMENTS). Add an entry there
and it appears here; this file never needs editing for a new method.
"""
import csv
import io
import json
import os
import time

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
plt.rcParams.update({"font.size": 8.5, "figure.dpi": 100})

from cursim.curriculum import build_curriculum
from cursim.learner import LEARNERS
from cursim.mastery import MASTERY_MODELS
from cursim.schedulers import SCHEDULERS
from cursim.sanity import EXPERIMENTS
from cursim.simulation import RunSpec, run_one
from cursim.params import BKT_PARAMS

st.set_page_config(page_title="cursim", page_icon="◎", layout="wide")

st.markdown("""
<style>
  html, body, [class*="css"] { font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; }
  h1 { font-weight: 600; letter-spacing: -.01em; margin-bottom: .2rem; }
  .sub { color: #6b7280; margin-top: 0; }
  .chip { display:inline-block; padding: 3px 10px; margin: 3px 4px 3px 0; border-radius: 999px;
          background:#eef1f4; color:#374151; font-size: 13px; }
  .chip.pick { background:#b5541c; color:white; font-weight:600; }
  .kv { font-size: 13px; color:#6b7280; margin:0; }
  .big { font-size: 26px; font-weight: 600; margin: 0; letter-spacing:-.01em; }
  .ok { color:#2f855a; } .bad { color:#b5541c; }
  .card { background:#f8f9fb; border:1px solid #e5e7eb; border-radius:8px; padding:14px 16px; }
  div[data-testid="stMetricValue"] { font-size: 22px; }
</style>
""", unsafe_allow_html=True)

ACCENT, GREY, INK = "#b5541c", "#9aa0a6", "#1f2937"
OUT = "runs"


# ---------------------------------------------------------------- helpers
def show_fig(fig, width, close=True):
    """Render at a fixed pixel width; st.pyplot upscales unpredictably.
    close=False for figures the caller still needs (e.g. to save later)."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight")
    if close:
        plt.close(fig)
    st.image(buf.getvalue(), width=width)


def save_bundle(name, config, tables, figures, summary=""):
    """Write config, tables, figures and summary to runs/<name>_<time>/."""
    stamp = time.strftime("%Y%m%d_%H%M%S")
    d = os.path.join(OUT, f"{name}_{stamp}")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "config.json"), "w") as f:
        json.dump({**config, "bkt_params": dict(BKT_PARAMS)}, f, indent=1, default=str)
    for tn, rows in tables.items():
        if rows:
            pd.DataFrame(rows).to_csv(os.path.join(d, f"{tn}.csv"), index=False)
    for fn, fig in figures.items():
        fig.savefig(os.path.join(d, f"{fn}.png"), dpi=160, bbox_inches="tight")
        plt.close(fig)
    if summary:
        with open(os.path.join(d, "summary.txt"), "w") as f:
            f.write(summary + "\n")
    return d


def belief_fig(trace, step, cur, threshold):
    """Belief for every concept in the ZPD at this step, asked one
    highlighted, true state marked."""
    t = trace[step - 1]
    ids = list(t["zpd"]) or cur.ids()
    if t["concept"] not in ids:
        ids.append(t["concept"])
    b = [t["beliefs"][c] for c in ids]
    truth = [t["truth"][c] for c in ids]
    fig, ax = plt.subplots(figsize=(max(4.0, 0.5 * len(ids) + 1.2), 2.5), dpi=100)
    cols = [ACCENT if c == t["concept"] else "#c7ccd3" for c in ids]
    ax.bar(range(len(ids)), b, color=cols, width=0.62)
    for i, (y, tr) in enumerate(zip(b, truth)):
        ax.text(i, y + 0.03, "known" if tr >= 0.999 else ("" if tr <= 0.001 else f"{tr:.2f}"),
                ha="center", fontsize=7.5, color="#2f855a" if tr >= 0.999 else GREY)
    ax.set_xticks(range(len(ids)))
    ax.set_xticklabels([cur.concepts[c].name for c in ids], rotation=30, ha="right", fontsize=8)
    ax.set_ylim(0, 1.12); ax.set_ylabel("tutor's belief", fontsize=9)
    ax.axhline(threshold, ls="--", lw=1, color=GREY)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("What the tutor believes about the ZPD right now", fontsize=9, loc="left")
    fig.tight_layout()
    return fig


def history_fig(trace, step, concept, cur, threshold):
    """Belief vs true state over time for one concept."""
    xs = [t["step"] for t in trace[:step]]
    bs = [t["beliefs"][concept] for t in trace[:step]]
    tr = [t["truth"][concept] for t in trace[:step]]
    asked = [t["step"] for t in trace[:step] if t["concept"] == concept]
    fig, ax = plt.subplots(figsize=(6.0, 2.3), dpi=100)
    ax.fill_between(xs, 0, tr, step="post", color="#2f855a", alpha=0.12, lw=0,
                    label="student truly knows it")
    ax.plot(xs, bs, color=ACCENT, lw=1.8, label="tutor's belief")
    for a in asked:
        ax.axvline(a, color=GREY, lw=0.6, alpha=0.5)
    ax.axhline(threshold, ls="--", lw=1, color=GREY)
    ax.set_ylim(0, 1.05); ax.set_xlim(1, max(step, 2))
    ax.set_xlabel("question number", fontsize=9)
    ax.set_title(f"{cur.concepts[concept].name}: belief vs truth "
                 f"(thin lines = times it was asked)", fontsize=9, loc="left")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


def trace_rows(trace):
    return [dict(step=t["step"], zpd=", ".join(t["zpd"]), asked=t["concept"],
                 question=t["qid"],
                 pick_in_zpd=(t["concept"] in t["zpd"]) if t["zpd"] else None,
                 answer="right" if t["correct"] else "wrong",
                 true_before=fmt_true(t["true_before"]),
                 true_after=fmt_true(t["true_after"]),
                 belief_before=round(t["belief_before"], 3),
                 belief_after=round(t["belief_after"], 3),
                 declared=bool(t["mastered_after"])) for t in trace]


def fmt_true(v):
    if isinstance(v, bool):
        return "known" if v else "not yet"
    return f"{v:.2f}"


# ---------------------------------------------------------------- sidebar
cur = build_curriculum()
with st.sidebar:
    st.markdown("### Setup")
    learner = st.selectbox("Student simulator", list(LEARNERS),
                           format_func=lambda k: k, help="\n\n".join(
                               f"**{k}**: {v[1]}" for k, v in LEARNERS.items()))
    model = st.selectbox("Tutor's knowledge-tracing model", list(MASTERY_MODELS),
                         help="\n\n".join(f"**{k}**: {v}" for k, v in MASTERY_MODELS.items()))
    keys = list(SCHEDULERS)
    sched = st.selectbox("Scheduler", keys,
                         index=keys.index("uniform_zpd") if "uniform_zpd" in keys else 0,
                         help="uniform_zpd is the mail's scheduler: uniform random over "
                              "the ZPD, no bandit. (curriculum_tutor is the same class.)")
    threshold = st.slider("Mastery threshold", 0.5, 0.99, 0.9, 0.01)
    st.session_state["threshold"] = threshold
    n_steps = st.number_input("Questions in the run", 5, 2000, 40, 5)
    seed = st.number_input("Seed", 0, 10**6, 4242, 1)
    prereq_pT = False
    if learner == "bkt":
        prereq_pT = st.checkbox("p(T) depends on prerequisites (next step)", False,
                                help="Off = the plain student from the mail. On = a "
                                     "concept learns slower until its prerequisites "
                                     "are truly known.")
    st.markdown("---")
    st.markdown("**Shared BKT parameters**")
    st.caption(", ".join(f"{k}={v}" for k, v in BKT_PARAMS.items()))
    if learner == "bkt" and model == "bkt":
        st.caption("Student and tutor both read these from `cursim/params.py`.")
    else:
        st.caption("The bkt student reads these. Other tutors (e.g. binary, "
                   "p_T=0.06) or students use their own; see the tooltips.")

st.markdown("# cursim")
st.markdown('<p class="sub">Watch one run step by step, or run the sanity checks.</p>',
            unsafe_allow_html=True)

tab_run, tab_exp = st.tabs(["Dry run", "Experiments"])

# ================================================================ dry run
with tab_run:
    cfg = dict(learner=learner, mastery_model=model, scheduler=sched,
               threshold=threshold, n_steps=int(n_steps), seed=int(seed),
               prereq_gated_pT=prereq_pT)
    key = json.dumps(cfg, sort_keys=True)
    c1, c2 = st.columns([1, 5])
    if c1.button("Run", type="primary", use_container_width=True) or \
            "run" not in st.session_state:
        spec = RunSpec(scheduler=sched, mastery_model=model, learner=learner,
                       threshold=threshold, prereq_gated_pT=prereq_pT,
                       n_sessions=1, questions_per_session=int(n_steps),
                       gap_hours=0.0, retention_days=0.0)
        st.session_state["run"] = run_one(cur, spec, seed=int(seed), keep_trace=True)
        st.session_state["run_key"] = key
        st.session_state["run_cfg"] = dict(cfg)
    stale = st.session_state.get("run_key") != key
    if stale:
        c2.warning("Settings changed since this run. Press Run to apply them. "
                   "Everything below still shows the previous settings.")

    run = st.session_state.get("run")
    if run:
        rc = st.session_state["run_cfg"]          # the config that made this run
        thr = rc["threshold"]
        trace = run["trace"]
        step = st.slider("Step", 1, len(trace), min(len(trace), 1), 1,
                         help="Drag to walk through the run one question at a time.")
        t = trace[step - 1]

        left, mid, right = st.columns([1.35, 1, 1.15])
        with left:
            st.markdown("**ZPD before this question**")
            st.caption("Not yet believed mastered, and every prerequisite believed mastered.")
            chips = "".join(
                f'<span class="chip{" pick" if c == t["concept"] else ""}">'
                f'{cur.concepts[c].name}</span>' for c in t["zpd"])
            st.markdown(chips or "<em>empty: everything believed mastered</em>",
                        unsafe_allow_html=True)
            if t["zpd"] and t["concept"] not in t["zpd"]:
                st.caption(f"{len(t['zpd'])} concept(s). The `{rc['scheduler']}` "
                           f"scheduler picked **outside** the ZPD this step.")
            else:
                st.caption(f"{len(t['zpd'])} concept(s). Highlighted = the one the "
                           f"scheduler picked.")
        with mid:
            st.markdown("**The tutor asks**")
            st.markdown(f'<p class="big">{cur.concepts[t["concept"]].name}</p>',
                        unsafe_allow_html=True)
            st.markdown(f'<p class="kv">question `{t["qid"]}`</p>', unsafe_allow_html=True)
            st.markdown("**The student answers**")
            st.markdown(
                f'<p class="big {"ok" if t["correct"] else "bad"}">'
                f'{"right" if t["correct"] else "wrong"}</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="kv">true state: <b>{fmt_true(t["true_before"])}</b> '
                        f'&rarr; <b>{fmt_true(t["true_after"])}</b></p>',
                        unsafe_allow_html=True)
        with right:
            st.markdown("**The tutor updates**")
            d = t["belief_after"] - t["belief_before"]
            st.metric("belief this concept is known",
                      f"{t['belief_after']:.3f}", f"{d:+.3f}")
            st.markdown(f'<p class="kv">before: {t["belief_before"]:.3f} &nbsp;·&nbsp; '
                        f'threshold {thr:.2f}</p>', unsafe_allow_html=True)
            st.markdown("**declared mastered**" if t["mastered_after"]
                        else "not yet declared mastered")

        g1, g2 = st.columns([1, 1])
        with g1:
            show_fig(belief_fig(trace, step, cur, thr), 520)
        with g2:
            show_fig(history_fig(trace, step, t["concept"], cur, thr), 560)

        st.markdown("**Trace so far**")
        rows = trace_rows(trace[:step])
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                     height=min(420, 38 + 35 * len(rows)))

        b1, b2, _ = st.columns([1, 1, 4])
        if b1.button("Save this run", use_container_width=True, disabled=stale):
            figs = {"beliefs_at_step": belief_fig(trace, step, cur, thr),
                    "history": history_fig(trace, step, t["concept"], cur, thr)}
            d = save_bundle("dryrun", rc, {"trace": trace_rows(trace)}, figs,
                            f"{len(trace)} questions; learned_step: "
                            f"{json.dumps(run['learned_step'])}")
            st.success(f"Saved to `{d}`")
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=list(trace_rows(trace)[0]))
        w.writeheader(); w.writerows(trace_rows(trace))
        b2.download_button("Download trace CSV", buf.getvalue(),
                           "trace.csv", "text/csv", use_container_width=True,
                           disabled=stale)

# ============================================================ experiments
with tab_exp:
    name = st.selectbox("Experiment", list(EXPERIMENTS),
                        format_func=lambda k: f"{k}  —  {EXPERIMENTS[k][1]}")
    fn, desc, defaults = EXPERIMENTS[name]
    st.caption(desc)
    with st.expander("Parameters", expanded=True):
        params = {}
        cols = st.columns(min(4, max(1, len(defaults))))
        for i, (k, v) in enumerate(defaults.items()):
            with cols[i % len(cols)]:
                if isinstance(v, bool):
                    params[k] = st.checkbox(k, v)
                elif isinstance(v, int):
                    params[k] = st.number_input(k, value=v, step=1)
                elif isinstance(v, float):
                    params[k] = st.number_input(k, value=v, step=0.01, format="%.2f")
                else:
                    params[k] = v
        params.update(scheduler=sched, mastery_model=model, learner=learner,
                      prereq_gated_pT=prereq_pT)
        st.caption(f"Runs with the sidebar's student = `{learner}`, tutor = `{model}`, "
                   f"scheduler = `{sched}`. The mail's checks assume `bkt` / `bkt` / "
                   f"`uniform_zpd`; with the `continuous` student the 'true state' is a "
                   f"continuous mastery, so check 1 is not a calibration test there.")

    if st.button("Run experiment", type="primary"):
        with st.spinner("Running..."):
            t0 = time.time()
            out = fn(cur=cur, **params)
            out["secs"] = time.time() - t0
        st.session_state["exp"] = (name, dict(params), out)

    if st.session_state.get("exp") and st.session_state["exp"][0] == name:
        _, ran_params, out = st.session_state["exp"]
        if ran_params != params:
            st.warning("Parameters changed since this result. Run again to apply them.")
        st.info(out["summary"] + f"  ({out['secs']:.1f}s)")
        for fn_, fig in out["figures"].items():
            show_fig(fig, 760, close=False)
        for tn, rows in out["tables"].items():
            st.markdown(f"**{tn}**")
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        if st.button("Save results and plots", disabled=(ran_params != params)):
            d = save_bundle(name, {"experiment": name, **ran_params},
                            out["tables"], out["figures"], out["summary"])
            st.success(f"Saved to `{d}`")
