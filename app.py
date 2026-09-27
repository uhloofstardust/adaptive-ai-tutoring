"""cursim: step through one tutoring run, or run the sanity checks.

    streamlit run app.py

Everything selectable comes from a registry in the package (LEARNERS,
MASTERY_MODELS, SCHEDULERS, EXPERIMENTS) or from data/ (the curricula),
so adding a method or a curriculum needs no edit here.
"""
import io
import json
import os
import time

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import matplotlib.pyplot as plt

from cursim import curriculum as curmod
from cursim.curriculum import build_curriculum
from cursim.learner import LEARNERS
from cursim.mastery import MASTERY_MODELS
from cursim.params import BKT_PARAMS, DEFAULTS
from cursim.sanity import EXPERIMENTS
from cursim.schedulers import SCHEDULERS
from cursim.simulation import RunSpec, run_one
from cursim import viewer

st.set_page_config(page_title="cursim", page_icon="◍", layout="wide")

ACCENT, INK, FAINT = "#6f8ffb", "#e6e9f0", "#6e7688"
OUT = "runs"

st.markdown("""
<style>
  .stApp{
    background:
      radial-gradient(1100px 520px at 10% -6%, #18233d 0%, transparent 58%),
      radial-gradient(900px 460px at 94% 2%, #142a2a 0%, transparent 52%),
      linear-gradient(170deg,#0d1016,#11151e);
  }
  html,body,[class*="css"],button,input,select,textarea{
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Helvetica,Arial,sans-serif!important;
  }
  h1{font-weight:650;letter-spacing:-.02em;margin-bottom:.1rem;color:#e9ecf3}
  .sub{color:#98a1b5;margin-top:0;font-size:14px}
  section[data-testid="stSidebar"]{
    background:rgba(255,255,255,.035);backdrop-filter:blur(16px) saturate(140%);
    border-right:1px solid rgba(255,255,255,.07);
  }
  div[data-testid="stExpander"],div[data-testid="stDataFrame"]{
    background:rgba(255,255,255,.04);backdrop-filter:blur(12px);
    border:1px solid rgba(255,255,255,.08);border-radius:14px;
  }
  .stTabs [data-baseweb="tab-list"]{gap:4px;background:transparent}
  .stTabs [data-baseweb="tab"]{
    border-radius:10px 10px 0 0;padding:6px 16px;font-weight:600;font-size:13.5px}
  .stButton>button{
    border-radius:10px;font-weight:600;border:1px solid rgba(255,255,255,.1);
    background:rgba(255,255,255,.06);color:#e6e9f0;transition:.15s}
  .stButton>button:hover{background:rgba(255,255,255,.12);transform:translateY(-1px)}
  .stDownloadButton>button{border-radius:10px;font-weight:600}
  .kv{font-size:12px;color:#6e7688;margin:0}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------- helpers
def show_fig(fig, width, close=True):
    """Render at a fixed pixel width; st.pyplot upscales unpredictably."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight",
                facecolor="#12151d")
    if close:
        plt.close(fig)
    st.image(buf.getvalue(), width=width)


def save_bundle(name, config, tables, figures, summary=""):
    """Write config, tables, figures and summary to runs/<name>_<time>/."""
    stamp = time.strftime("%Y%m%d_%H%M%S")
    d = os.path.join(OUT, f"{name}_{stamp}")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "config.json"), "w") as f:
        json.dump({**config, "bkt_params": dict(BKT_PARAMS)}, f, indent=1,
                  default=str)
    for tn, rows in tables.items():
        if rows:
            pd.DataFrame(rows).to_csv(os.path.join(d, f"{tn}.csv"), index=False)
    for fn, fig in figures.items():
        fig.savefig(os.path.join(d, f"{fn}.png"), dpi=160, bbox_inches="tight",
                    facecolor="#12151d")
        plt.close(fig)
    if summary:
        with open(os.path.join(d, "summary.txt"), "w") as f:
            f.write(summary + "\n")
    return d


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
with st.sidebar:
    st.markdown("### Setup")
    curricula = curmod.available()
    cur_name = st.selectbox(
        "Curriculum", curricula,
        index=curricula.index(DEFAULTS["curriculum"])
        if DEFAULTS["curriculum"] in curricula else 0,
        help="Loaded from data/. Drop in another curriculum_<name>.json "
             "and it appears here.")
    cur = build_curriculum(cur_name)

    learner = st.selectbox("Student simulator", list(LEARNERS),
                           help="\n\n".join(f"**{k}**: {v[1]}"
                                            for k, v in LEARNERS.items()))
    model = st.selectbox("Tutor's knowledge-tracing model",
                         list(MASTERY_MODELS),
                         help="\n\n".join(f"**{k}**: {v}"
                                          for k, v in MASTERY_MODELS.items()))
    keys = list(SCHEDULERS)
    sched = st.selectbox(
        "Scheduler", keys,
        index=keys.index("uniform_zpd") if "uniform_zpd" in keys else 0,
        help="uniform_zpd picks uniformly at random from the ZPD, no bandit. "
             "curriculum_tutor is the same class under its older name.")
    threshold = st.slider("Mastery threshold", 0.5, 0.99,
                          float(DEFAULTS["threshold"]), 0.01)
    n_steps = st.number_input("Questions in the run", 5, 2000,
                              int(DEFAULTS["n_steps"]), 5)
    seed = st.number_input("Seed", 0, 10**6, int(DEFAULTS["seed"]), 1)
    prereq_pT = False
    if learner == "bkt":
        prereq_pT = st.checkbox(
            "p(T) depends on prerequisites", False,
            help="Off = prerequisites do not affect learning at all. "
                 "On = a concept learns slower until its prerequisites are "
                 "truly known.")

    st.markdown("---")
    st.markdown("**Shared BKT parameters**")
    st.caption(", ".join(f"{k} = {v}" for k, v in BKT_PARAMS.items()))
    if learner == "bkt" and model == "bkt":
        st.caption("Student and tutor both read these from `data/params.json`.")
    else:
        st.caption("The bkt student reads these. Other tutors and students "
                   "use their own; see the tooltips.")

st.markdown("# cursim")
st.markdown('<p class="sub">Watch one run unfold, or run the checks.</p>',
            unsafe_allow_html=True)

tab_run, tab_exp = st.tabs(["Dry run", "Experiments"])

# ================================================================ dry run
with tab_run:
    cfg = dict(curriculum=cur_name, learner=learner, mastery_model=model,
               scheduler=sched, threshold=threshold, n_steps=int(n_steps),
               seed=int(seed), prereq_gated_pT=prereq_pT)
    key = json.dumps(cfg, sort_keys=True)

    c1, c2 = st.columns([1, 5])
    if c1.button("Run", type="primary", use_container_width=True) or \
            "run" not in st.session_state:
        spec = RunSpec(scheduler=sched, mastery_model=model, learner=learner,
                       threshold=threshold, prereq_gated_pT=prereq_pT,
                       n_sessions=1, questions_per_session=int(n_steps),
                       gap_hours=0.0, retention_days=0.0)
        st.session_state["run"] = run_one(cur, spec, seed=int(seed),
                                          keep_trace=True)
        st.session_state["run_spec"] = spec
        st.session_state["run_cur"] = cur
        st.session_state["run_key"] = key
        st.session_state["run_cfg"] = dict(cfg)
    stale = st.session_state.get("run_key") != key
    if stale:
        c2.warning("Settings changed since this run. Press Run to apply them. "
                   "Everything below still shows the previous settings.")

    run = st.session_state.get("run")
    if run:
        rc = st.session_state["run_cfg"]
        rcur = st.session_state["run_cur"]
        components.html(
            viewer.render(rcur, st.session_state["run_spec"], rc["seed"],
                          run=run),
            height=viewer.height_for(len(rcur.concepts)), scrolling=True)

        with st.expander("Full trace", expanded=False):
            rows = trace_rows(run["trace"])
            st.dataframe(pd.DataFrame(rows), use_container_width=True,
                         hide_index=True, height=min(460, 40 + 35 * len(rows)))

        b1, b2, _ = st.columns([1, 1, 4])
        if b1.button("Save this run", use_container_width=True, disabled=stale):
            d = save_bundle("dryrun", rc, {"trace": trace_rows(run["trace"])},
                            {}, f"{len(run['trace'])} questions; learned_step: "
                                f"{json.dumps(run['learned_step'])}")
            with open(os.path.join(d, "trace.json"), "w") as f:
                json.dump(viewer.build_payload_for_save(rcur,
                          st.session_state["run_spec"], rc["seed"], run), f)
            st.success(f"Saved to `{d}`")
        buf = io.StringIO()
        rows = trace_rows(run["trace"])
        pd.DataFrame(rows).to_csv(buf, index=False)
        b2.download_button("Download trace CSV", buf.getvalue(), "trace.csv",
                           "text/csv", use_container_width=True, disabled=stale)

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
                    params[k] = st.number_input(k, value=v, step=0.01,
                                                format="%.2f")
                else:
                    params[k] = v
        params.update(scheduler=sched, mastery_model=model, learner=learner,
                      prereq_gated_pT=prereq_pT)
        st.caption(f"Runs on `{cur_name}` with student = `{learner}`, "
                   f"tutor = `{model}`, scheduler = `{sched}`. The checks "
                   f"assume `bkt` / `bkt` / `uniform_zpd`; with the "
                   f"`continuous` student the true state is a continuous "
                   f"mastery, so check 1 is not a calibration test there.")

    if st.button("Run experiment", type="primary"):
        with st.spinner("Running..."):
            t0 = time.time()
            out = fn(cur=cur, **params)
            out["secs"] = time.time() - t0
        st.session_state["exp"] = (name, dict(params), out)

    if st.session_state.get("exp") and st.session_state["exp"][0] == name:
        _, ran_params, out = st.session_state["exp"]
        if ran_params != params:
            st.warning("Parameters changed since this result. "
                       "Run again to apply them.")
        st.info(out["summary"] + f"  ({out['secs']:.1f}s)")
        for fn_, fig in out["figures"].items():
            show_fig(fig, 760, close=False)
        for tn, rows in out["tables"].items():
            st.markdown(f"**{tn}**")
            st.dataframe(pd.DataFrame(rows), use_container_width=True,
                         hide_index=True)
        if st.button("Save results and plots",
                     disabled=(ran_params != params)):
            d = save_bundle(name, {"experiment": name, "curriculum": cur_name,
                                   **ran_params},
                            out["tables"], out["figures"], out["summary"])
            st.success(f"Saved to `{d}`")
