# cursim: a domain-agnostic simulator for adaptive tutoring

A simulated learner who knows, guesses, slips and forgets, taught by different
question-selection strategies, so strategies can be compared before any human
pilot. The curriculum is a graph of dummy concepts (`A01`, `B02`, ...) with
prerequisites. The tutor never sees the learner's true state.

All documentation lives in **`experiment_logs.md`** (model reference, dated
experiment entries, open threads). The CurriculumTutor paper is in `references/`.

## Run

    python -m tests                                   # all checks
    python -m experiments list                        # available experiments
    python -m experiments run forgetting_worlds --set n_learners=10 --out results
    python -m experiments suite bkt_validation        # or: forgetting | all
    streamlit run app.py                              # interactive viewer

Each run writes `results/<name>/` (CSV, PNG, `summary.md`, `meta.json`).

## Layout

    cursim/          core: curriculum, students/, schedulers/, mastery, simulation, stats
    experiments/     registry + runner; bkt/ (validation) and forgetting/ (main work)
    data/            params.json, curricula/ (abstract 8-concept, layered_40)
    tests/           python -m tests
    results/         generated outputs
    references/      papers

## Adding things

- **Scheduler:** add a function in `cursim/schedulers/` decorated with
  `@register_scheduler("name")`.
- **Student:** register in `cursim/students/` (`LEARNERS`).
- **Experiment:** add a module in `experiments/forgetting/` using
  `@experiment("name", "description", defaults=dict(...), curriculum="layered_40")`
  returning `{"tables": ..., "figures": ..., "summary": ...}`, and import it in
  that package's `__init__`.
- **Curriculum:** drop a JSON in `data/curricula/` or use `generate_layered(...)`.
