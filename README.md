# cursim — a simulator for adaptive tutoring

A simulated learner who knows, guesses, slips and forgets, taught by
different question-selection strategies, so those strategies can be
compared before any human pilot. The curriculum is a graph of concepts
with prerequisites; the tutor never sees the learner's true state and
must infer it from answers.

The default curriculum is deliberately abstract. Concepts are named by
tier (`A1`, `B2`, `D1`), not by subject, so nothing in the machinery
depends on what is being taught.

## Every number here is checkable

This repo follows one rule: **no number appears in a document unless a
committed artifact produces it.** `sanity_outputs/*.csv` is the source of
truth, `python3 make_sanity.py` regenerates all of it from scratch, and
the tables in `docs/simulator.tex` and `sanity_outputs/summary.md` are
written from those CSVs rather than typed.

```
streamlit run app.py         # step or play through a single run
python3 make_sanity.py       # every plot and table -> sanity_outputs/
python3 test_sanity.py       # 101 checks on the plain-BKT setup
python3 test_simulator.py    # 55 checks on the original simulator
```

Both suites pass. Several checks are not unit tests but guards on claims
that turned out to be wrong earlier and would otherwise creep back: that
a scoring rule which cancels cannot be used to argue two tutors are
equivalent, and that an interval covering zero is never printed as
though it meant no effect.

## The two student models and the two schedulers

The central comparison is a 2x2.

Concepts truly known after 40 questions, 400 learners, paired by learner
(`sanity_outputs/two_by_two_paired.csv`):

| | Q1: ask anything not believed mastered | Q2: ask only prerequisite-ready | Q2 − Q1 |
|---|---:|---:|---|
| **S1** prerequisites do not affect learning | 6.15 | 6.00 | −0.15 ± 0.14, slightly favours Q1 |
| **S2** p(T) drops to `pT_low` until prerequisites are truly known | 4.39 | 5.86 | +1.47 ± 0.18, favours Q2 |

The interaction, +1.62 ± 0.16, is the claim: the scheduler is worth
about one and a half concepts to S2 and slightly negative to S1.

The S1 cell is deliberately not written as "no effect". It is small and
budget-dependent: resolved and slightly costly to Q2 at 40 questions,
indistinguishable from zero at 120, and still unsettled across six
independent blocks scored on time to full mastery (+0.37 ± 0.57, blocks
disagreeing in sign). `seed_blocks` is the experiment that checks this,
and it exists because an earlier draft asserted a sign the data did not
support.

S2 is selected by choosing the `bkt_prereq` student. There is exactly one
S2 in the repo and its `pT_low` lives in `data/params.json`, so no code
path can quietly run a different one.

## Curricula and parameters are data

Anything named `data/curriculum_<name>.json` is loadable by `<name>` and
appears in the interface automatically, so adding a curriculum is a new
file and never a code edit.

| File | What it is |
|---|---|
| `data/curriculum_abstract.json` | 8 concepts, the default. A symmetric 2-3-2-1 diamond over 4 tiers, small enough that the ZPD stays readable |
| `data/curriculum_language.json` | the original 40-concept graph, frozen so earlier results stay reproducible |
| `data/params.json` | the shared BKT parameters, S2's `pT_low`, and the interface defaults |

`build_curriculum()` loads the default; `build_curriculum("language")`
loads the original. `python3 -m cursim.curriculum` lists what is
available with its size and depth.

## The experiments

All ten are in the `EXPERIMENTS` registry, so they appear in the
interface with their parameters as controls, with no edit to `app.py`.

| Name | What it asks |
|---|---|
| `check1_calibration` | when the tutor believes p, is the concept truly known with frequency p? |
| `check2_detection` | how long until the tutor notices mastery, and how often does it declare too early? |
| `s1s2_x_q1q2` | the 2x2: does the question-selection rule matter, and does that depend on the student model? |
| `mastery_curve` | concepts truly known against questions asked, all four cells, and how many questions are enough to know every concept |
| `param_sweep` | what each BKT parameter does, with the tutor correctly specified |
| `mismatch` | the tutor's assumed parameters differ from the student's real ones, one parameter at a time or across a population |
| `tutor_choice` | students differ in one parameter: which single fixed assumption should the tutor use, and how much would a perfectly adapting tutor buy over it? |
| `seed_blocks` | re-runs the mastery contrast on independent seed blocks, so a sign a single run cannot resolve can still be checked |
| `restriction_only` | separates the prerequisite restriction from the cost of gating on a belief that lags the truth |
| `trace_20_steps` | one run, 20 rows, every column |

`tutor_choice` includes an **oracle** arm handed each learner's own true
parameters. It is not a proposal, because no tutor can see a student's
parameters. It is the upper bound that makes "should the tutor adapt"
answerable at all.

## Three scores, and why only one is used

`tutor_choice` is scored on the Brier score. The other two stay in the
CSV as diagnostics, because each fails in an instructive way:

- the **pooled signed calibration gap** cancels. A tutor overconfident
  about half its students and underconfident about the other half scores
  zero, and under a symmetric spread that is exactly the error an
  adapting tutor would remove.
- **mean |belief - truth|** is not a proper scoring rule. It is minimised
  by the median, so while most concepts are still unknown it rewards a
  tutor that simply stays pessimistic.
- **Brier** is proper, and at the 120-question horizon these studies run
  at it recovers the true parameter for both parameters that were swept,
  p(S) and p(guess). p(T) is offered by the experiment but is not in the
  committed run, so nothing here is claimed about it. At a 40-question
  horizon the Brier curve is nearly flat and does not identify the
  parameter reliably either, which is why the horizon is stated rather
  than assumed.

## Code

| File | Role |
|---|---|
| `cursim/params.py` | reads the shared BKT parameters from `data/params.json` |
| `cursim/curriculum.py` | loads any curriculum from `data/`, plus a tier layout for drawing |
| `cursim/learner.py` | the simulated students: `BKTLearner` (S1 and S2) and the continuous learner, in the `LEARNERS` registry (3 entries) |
| `cursim/mastery.py` | what the tutor believes, in `MASTERY_MODELS` (5 entries) |
| `cursim/schedulers.py` | question selection, in `SCHEDULERS` (10 entries), plus the `zpd()` helper |
| `cursim/simulation.py` | the run loop, the per-step trace, and the metrics |
| `cursim/sanity.py` | the ten experiments, their figures, and the `EXPERIMENTS` registry |
| `cursim/plots.py` | the six figure functions used by `run_experiments.py` |
| `cursim/viewer_data.py` | packages one run into the JSON the viewer plays |
| `cursim/viewer.py` | renders the viewer as one self-contained HTML string |
| `viewer/viewer.html` | the viewer: curriculum graph, belief charts, transport |
| `viewer/vendor/` | Chart.js, vendored so it works with no network |
| `app.py` | the interface; everything selectable comes from a registry or from `data/` |
| `run_experiments.py` | the four original experiments, `data/results.csv`, and `--selftest` |
| `test_sanity.py`, `test_simulator.py` | the two suites |

## The dry run

Press Run, then Play or drag the slider. The graph shows every concept
coloured by what the tutor believes, with the concept being asked filled
solid and a ring on the ones the student truly knows. Beside it, one
small chart per concept, all advancing together, so you never have to
wait for a concept to come round again to see it move. Chips choose which
charts to show.

## Written descriptions

Three documents in `docs/`, all with tables generated from the CSVs by
`make_tables.py`:

| File | What it covers |
|---|---|
| `jigar.tex` / `.pdf` | the tutor's four BKT parameters: what each does, what happens when the tutor's values are wrong for one student and for a mixed group, and which single set a tutor should use |
| `sanved.tex` / `.pdf` | whether the order of questions matters: the two student models, the two question-selection rules, the 2x2 between them, and the checks that separate the restriction from the belief lag |
| `simulator.tex` / `.pdf` | the full reference: models, update rules, what is measured against what, and everything established so far |

The first two are short and plain-language. The third is the complete
version and assumes more.

## Branches

`plain-bkt` carries the BKT students, the sanity checks and the
interface. `main` keeps the original simulator untouched.
