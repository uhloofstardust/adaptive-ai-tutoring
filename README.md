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

## Running it

```
python -m cursim.curriculum      # builds the curriculum, writes data/curriculum.json
python test_simulator.py         # 55 checks
python run_experiments.py --selftest
python run_experiments.py        # all four experiments -> data/results.csv, figures/
```
