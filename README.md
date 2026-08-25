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
| `test_simulator.py` | Test suite for the simulator (see `simulator_expln.md`, Part 8). Imports `cursim.curriculum` plus `cursim.learner`, `cursim.mastery`, `cursim.schedulers`, `cursim.simulation`. | `cursim/curriculum.py`, and the other `cursim` modules |

**Current state:** of the modules `simulator_expln.md` describes (Part
8), only `cursim/curriculum.py` is committed so far. `test_simulator.py`
already imports the rest, so running it will fail with an `ImportError`
until `learner.py`, `mastery.py`, `schedulers.py`, and `simulation.py`
are added.

## Running what exists

```
python -m cursim.curriculum   # builds the curriculum and writes data/curriculum.json
```
