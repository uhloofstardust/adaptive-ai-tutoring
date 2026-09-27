# Adaptive AI Tutoring — Marathi→Bengali Curriculum Simulator

This repo extends CurriculumTutor (see `CurriculumTutor.pdf`) into a
simulator for adaptive language tutoring: a fake learner that knows,
forgets, and guesses, taught by different question-selection strategies,
so those strategies can be compared before any human pilot.

## Read these in order

1. **`simulator_expln.md`** — what the simulator is, how every part of
   it works, and why each design choice was made. Read this first; it
   is the reference for everything below.
2. **`experiment_plans.md`** — the experiments planned on top of the
   simulator described in (1). Read this second; it assumes the
   concepts from `simulator_expln.md`.

## Code in this repo

| File | Role | Depends on |
|---|---|---|
| `cursim/curriculum.py` | Defines the curriculum data model: the concept graph and its question bank (see `simulator_expln.md`, Part 3). No dependency on any other file here. | — |
| `cursim/learner.py` | The simulated student: hidden continuous mastery, prerequisite-gated learning, exponential forgetting (Part 4). | `curriculum.py` |
| `cursim/mastery.py` | What the tutor believes: binary-permanent, continuous, continuous-with-forgetting (Part 5). | — |
| `cursim/schedulers.py` | The four question-selection strategies (Part 6). | `curriculum.py`, `mastery.py` |
| `cursim/simulation.py` | The run loop, metrics, paired comparison and sign test (Part 7). | all of the above |
| `cursim/plots.py` | The six figure functions (Part 8.6). | `simulation.py` |
| `run_experiments.py` | Experiment definitions, `data/results.csv`, and `--selftest`. | all of the above |
| `test_simulator.py` | Test suite for the simulator (see `simulator_expln.md`, Part 8). | all `cursim` modules |

**Current state:** all modules described in `simulator_expln.md` Part 8
are present. `test_simulator.py` passes all 55 checks.

## The `plain-bkt` branch

Adds a plain BKT student, the two sanity checks, and an interface for
watching a single run unfold. `main` keeps the original simulator untouched.

```
streamlit run app.py         # step or play through a run; run the checks
python3 make_sanity.py       # every plot and table -> sanity_outputs/
python3 test_sanity.py       # 29 checks on the plain-BKT setup
python3 test_simulator.py    # the original 55 checks
```

### Curricula are data

Every curriculum lives in `data/` as JSON, so adding one is a new file and
never a code edit. Anything named `curriculum_<name>.json` is loadable by
`<name>` and appears in the interface automatically.

| File | What it is |
|---|---|
| `data/curriculum_abstract.json` | 8 concepts, the default. Subject-free: ids are `<tier letter><index>`, so `A1` has no prerequisites and `D1` is the capstone. A symmetric 2-3-2-1 diamond, small enough that the ZPD stays readable |
| `data/curriculum_language.json` | the original 40-concept graph, frozen, so the earlier experiments and their committed results stay reproducible |
| `data/params.json` | the shared BKT parameters and the interface defaults |

`build_curriculum()` loads the default; `build_curriculum("language")` loads
the original. The older experiment scripts are pinned to `"language"`.

### Code

| File | What it adds |
|---|---|
| `cursim/params.py` | reads the shared BKT parameters from `data/params.json` |
| `cursim/curriculum.py` | loads any curriculum from `data/`, plus a tier layout for drawing |
| `cursim/learner.py` | `BKTLearner` and the `LEARNERS` registry |
| `cursim/mastery.py` | the `"bkt"` model and the `MASTERY_MODELS` registry |
| `cursim/schedulers.py` | `zpd()` helper so the run loop can record the ZPD |
| `cursim/simulation.py` | `learner`, `threshold`, `bkt_params` on `RunSpec`; `keep_trace` |
| `cursim/sanity.py` | check 1, check 2, the trace, and the `EXPERIMENTS` registry |
| `cursim/viewer_data.py` | packages one run into the JSON the viewer plays |
| `cursim/viewer.py` | renders the viewer as one self-contained HTML string |
| `viewer/viewer.html` | the viewer: curriculum graph, belief charts, transport |
| `viewer/vendor/` | Chart.js, vendored so it works with no network |
| `app.py` | the interface. Everything selectable comes from a registry or from `data/` |

### The experiments

| Name | What it asks |
|---|---|
| `check1_calibration` | when the tutor believes p, is the student known with frequency p? |
| `check2_detection` | how long until the tutor notices, and how often does it declare too early? |
| `s1s2_x_q1q2` | the 2x2: does the question-selection rule matter, and does that depend on the student model? |
| `param_sweep` | what does each BKT parameter actually do, with the tutor correctly specified? |
| `mismatch` | the tutor's assumed parameters differ from the student's real ones |
| `trace_20_steps` | one run, 20 rows, every column |

`docs/simulator.tex` (and its PDF) is the written description: the models,
the update rules, what is measured against what, and what has been established.

### The dry run

Press Run, then Play or drag the slider. The graph shows every concept
coloured by what the tutor believes, with the concept being asked filled
solid and a ring on the ones the student truly knows. Beside it, one small
chart per concept, all advancing together, so you never have to wait for a
concept to come round again to see it move. Chips choose which charts to show.

## Running it

```
python -m cursim.curriculum      # builds the curriculum, writes data/curriculum.json
python test_simulator.py         # 55 checks
python run_experiments.py --selftest
python run_experiments.py        # all four experiments -> data/results.csv, figures/
```
