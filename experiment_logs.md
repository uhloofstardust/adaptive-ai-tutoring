# Experiment logs

The single place for documentation. Entries are dated, oldest first. Add a
new one at the bottom whenever something is run, decided or corrected.

Rules for this file:

- Say what was run (the exact command), what came out, and what it means.
- Quote numbers only from `results/<name>/` (each has a `meta.json` saying
  what produced it). If a number is not in a committed artifact, do not
  put it here.
- Never edit an old entry's results. If one turns out to be wrong, say so
  in a new entry and point back at it.
- The project goal: a question-scheduling algorithm that accounts for
  forgetting, as a replacement for CurriculumTutor
  (`references/CurriculumTutor.pdf`). Everything below is the instrument
  and the evidence about the problem, not yet the algorithm.

Contents: [Model reference](#model-reference-as-of-2026-10-15) ·
[2026-08-18](#2026-08-18--the-simulator-and-the-plan) ·
[2026-08-25](#2026-08-25--modules-and-first-runs) ·
[2026-09-01](#2026-09-01--experiments-1-4) ·
[2026-09-10](#2026-09-10--bkt-forgetting-predictive-maple-ucb) ·
[2026-09-14](#2026-09-14--plain-bkt-testbed) ·
[2026-09-27](#2026-09-27--curricula-as-data) ·
[2026-09-28](#2026-09-28--student-models-s1-s2-and-the-2x2) ·
[2026-10-15](#2026-10-15--restructure-domain-agnostic-codebase-reproduction) ·
[Open threads](#open-threads)

---

## Model reference (as of 2026-10-15)

### Three parts, kept apart

| Part | Sees the truth? | Question it answers |
|---|---|---|
| Student (`cursim/students/`) | it *is* the truth | what does the learner actually know, and how does it change? |
| Mastery model (`cursim/mastery.py`) | no, only (concept, right/wrong, time) | what does the tutor believe? |
| Scheduler (`cursim/schedulers/`) | no | given that belief, which question next? |

Schedulers and mastery models never see the student's true state; the
true state is used only for scoring. Varying one part with the other two
fixed is the only way an effect can be attributed. Learner and scheduler
use separate random streams, so changing the scheduler does not change
the learner's luck.

### Curriculum

A DAG of subject-free concepts (`data/curricula/<name>.json`); each has a
tier, prerequisites and questions that differ only in difficulty.
`abstract` is an 8-concept 2-3-2-1 diamond (small, saturates fast, for
validation). `layered_40` is 40 concepts, 290 questions, 5 roots, 7 tiers,
used for the forgetting experiments. `generate_layered()` makes new seeded
graphs. Ids are `<tier letter><index>`; nothing depends on what is taught.

### Students

**continuous** (`students/continuous.py`). Per-concept mastery m in [0,1].
Answering a question of difficulty d:

    m_eff = m ** (1 + 1.2 d)
    P(correct) = m_eff (1 - slip) + (1 - m_eff) guess          guess = 0.25
    m <- m + learning_rate * readiness * gain * (1 - m)        gain 0.45 right, 0.10 wrong
    readiness = (1 - s) + s * (weakest prerequisite mastery)   s = 0.8

Forgetting is exponential decay toward a floor of 0.02, applied lazily on
read, with half-life `forget_half_life_days` shortened 6% per tier. A
concept decays whether or not it is practised, which makes scheduling a
restless problem. Profiles (learning rate, half-life days, slip): fast
(1.35, 18, 0.05), average (1.00, 14, 0.07), slow (0.70, 12, 0.10),
forgetful (1.10, 6, 0.07). `forgetful` differs by memory, not ability.

**bkt / bkt_prereq** (`students/bkt.py`). Each concept is a hidden known/
unknown coin with p(L0)=0.15, p(T)=0.2, p(G)=0.25, p(S)=0.1 (shared file
`data/params.json`). The student answers from its current state and only
then transitions, so learning shows on the next question. No forgetting,
no difficulty. S1 (`bkt`): prerequisites do not affect learning. S2
(`bkt_prereq`): p(T) drops to 0.05 until all prerequisites are truly known.

### Mastery models (the tutor's belief)

All use the BKT update: after an observation, Bayes' rule on the belief b,
then `b <- b+ + (1 - b+) p(T)`.

- `binary`: latches at belief 0.97 and never unlatches (CurriculumTutor's
  assumption); uses its own p(T)=0.06.
- `continuous`: the belief as is; mastered at 0.80 (BKT variant `bkt`: 0.9).
- `continuous_forget`: belief decays 10 %/day between practices, so a
  concept the tutor stopped asking about can fade back into the ZPD.
- `bkt_forget`: adds p_F inside the update, a chance a known skill is lost
  each time it is *asked*. Does not move while nothing is asked.

### Schedulers

`random`; `curriculum_tutor` (= `uniform_zpd`, Q2: uniform over the ZPD,
concepts not believed mastered whose prerequisites all are); `uniform_unmastered`
(Q1: anything not believed mastered); `continuous` (soft prerequisites,
learning zone 0.15-0.85, difficulty matched to belief); `adaptive_review`
(continuous plus a review term `0.8 * (1 - exp(-days/2.5)) * belief^2`,
hand-tuned, never tuned); `predictive` (one-step lookahead on expected
belief change, Schodde et al. 2017); `maple` and `naive_maple` (Segal et
al. 2018, tier-ranked or random initial weights); `ucb` (UCB1 over ready
concepts). Add one by subclassing `Scheduler` and decorating with
`@register_scheduler("name")`.

### Protocol and metrics

Default run: 20 sessions of 25 questions with a 24 h gap, then a 3-day
break with no practice, then measure. Conditions share learner seeds, so
learner i is the same person in every condition and comparisons are read
learner by learner (mean difference, wins, exact two-sided sign test).
Primary metric `retained_usable`: concepts of the curriculum still above
mastery 0.50 after the break. `final_learned`: above 0.80 at the end of
practice. Mean mastery is reported but not used for conclusions: when the
budget cannot cover the curriculum it rewards spreading thin (forty
concepts at 0.5 equal twenty at 1.0).

### Reproducing

    python -m experiments list
    python -m experiments run <name> [--set key=value]
    python -m experiments suite all          # regenerates results/
    python -m tests                          # all checks

### Standing limitations

Every parameter is assumed, not fitted, so every result is a statement
about the model and not about people. Learning gain, half-life and
prerequisite sensitivity are the ones that matter most. The continuous
student is deliberately not a BKT model: if it were, a BKT tutor could
recover the truth exactly and any extension would look pointless by
construction. Headline numbers depend on the regime (with a very large
budget learners saturate and strategies converge), so each is quoted with
its settings.

---

## 2026-08-18 · the simulator and the plan

Built the first version: curriculum, continuous student, mastery models,
four schedulers (random, CurriculumTutor, continuous, adaptive review),
the run loop with sessions and the retention test, paired comparison and
sign test, and a 55-check test suite (since then split into
`tests/test_core.py`).

Design decisions that matter for every later result:

- The learner is always continuous, so "binary vs continuous mastery"
  changes the *tutor's* belief and never the person.
- Prerequisites act on the learner (a weak prerequisite slows learning),
  otherwise respecting the graph could never beat ignoring it.
- Decay is lazy and per concept; later tiers decay slightly faster.
- Retention after a break is the primary measurement, not end-of-practice
  mastery, which flatters every strategy equally.

Predictions written down before running, so a contradicting result counts
as a finding:

1. Experiment 1 (representation, scheduler held fixed): continuous with
   forgetting beats binary-permanent; continuous without forgetting
   recovers part of the gap.
2. Experiment 2 (forgetting in both directions): forgetting-aware beats
   binary when the learner forgets; when the learner never forgets it is
   *worse* (revision costs new material) and adaptive review worse still.
3. Experiment 3 (learner profiles): the ranking changes; extra machinery
   pays off for forgetful learners and is wasted on strong memories.
4. Experiment 4 (half-life sweep): three regimes, with revision-heavy
   best for very forgetful learners, forgetting model in the middle,
   binary best for strong memories.

## 2026-08-25 · modules and first runs

Added the modules and the experiment runner. Fixed a crash when `data/`
did not exist and corrected the tier count in the docs (7 tiers, 0 to 6).
Item text for the grammar concepts was placeholder; the simulation only
ever uses concept membership and difficulty.

## 2026-09-01 · experiments 1-4

Committed the results and figures, then added five half-lives (8, 10, 18,
19, 20) to experiment 4 because the original grid only located the two
crossovers somewhere between 7-9 and 16-22 days. 30 learners per
condition, 40-concept graph. **These numbers were produced with the shared
BKT p(T)=0.12 and are superseded by the 2026-10-15 rerun at p(T)=0.2;
they are kept here because other entries cite them.**

Concepts still usable after the 3-day break (at p(T)=0.12):

| | CT + binary | CT + forgetting | adaptive review |
|---|---:|---:|---:|
| Exp 1, learner forgets | 21.87 | 30.33 (continuous, no forgetting: 27.8) | |
| Exp 2, learner forgets | 21.87 | 30.33 | 22.47 |
| Exp 2, learner never forgets | 40.0 | 37.3 | 29.43 |
| Exp 3 fast | 38.03 | 35.77 | 27.1 |
| Exp 3 slow | 9.4 | 21.33 | 17.53 |
| Exp 3 forgetful | 1.13 | 7.73 | 11.23 |

What it showed:

- Permanent mastery is costly when the learner forgets: modelling
  forgetting gave +8.5 usable concepts, better for all 30 learners.
- It is a trade-off, not a free improvement: with no forgetting to model
  the binary tutor was best (40/40) and adaptive review worst.
- The best tutor depends on the learner: binary for fast learners,
  forgetting model for average and slow, adaptive review only for the
  forgetful profile.
- Experiment 4: the ordering flips from adaptive review to the forgetting
  model near 8 days and from the forgetting model to binary near 18 days;
  a paired sign test reads 10/30 at both, a tie.
- Adaptive review did not do what "revision on top of the forgetting
  model" was hoped to do (22.47 vs 30.33). The winning tutor also covered
  fewer concepts (33.3 of 40 vs 40): depth beat breadth.
- Mean mastery moved much less than the threshold metrics, confirming it
  is a poor primary metric here.

## 2026-09-10 · BKT forgetting, predictive, MAPLE, UCB

Added `p_F` forgetting inside BKT (Schodde et al. 2017), the predictive
one-step-lookahead scheduler (same paper), MAPLE and a naive-weights
control (Segal et al. 2018), and later a plain UCB1 scheduler (no
experiment yet). Plumbing change: the scheduler is now told each answer
(`observe`), which bandits need; older schedulers ignore it. Run with
`python -m experiments run belief_schedulers` (was `exp_sep10.py`).

Recorded then (p(T)=0.12, 30 learners; usable after the break):

| arm | learned | usable | covered |
|---|---:|---:|---:|
| CT + binary | 4.50 | 21.87 | 39.97 |
| CT + time decay | 18.63 | 30.33 | 33.30 |
| CT + BKT forget (p_F) | 5.50 | 24.83 | 40.00 |
| Predictive + BKT forget | 5.53 | 24.67 | 40.00 |
| MAPLE + BKT forget | 3.50 | 24.10 | 40.00 |
| Naive MAPLE + BKT forget | 3.40 | 23.97 | 40.00 |

Findings:

1. **`p_F` is practice-time forgetting; the problem needs calendar-time
   forgetting.** The belief only drops when a concept is asked, but a
   concept the tutor stopped asking about stops changing in its belief
   while the student keeps forgetting overnight. It shares the binary
   latch's blind spot. Time decay beat it for 30 of 30 learners. This is
   the standard textbook way to add forgetting to BKT, and now has a
   measured reason for not using it here.
2. Predictive vs CT (both on `p_F`): 10 of 30, noise. Candidate reason:
   the ready-concept set is small and one-step gains inside it are nearly
   equal.
3. MAPLE vs naive MAPLE: 14 of 30, noise. The tier ranking has only 7
   levels, much coarser than the per-question ranking that helped MAPLE on
   its own paper's simulator, so this is no evidence against MAPLE.

**Flaw in this comparison** (flagged 2026-10-15): Predictive and MAPLE
were run only on the weak `p_F` belief, while the winner used time decay.
The two were never crossed, so "none of the new schedulers won" does not
separate the scheduler from the belief model. See open threads.

## 2026-09-14 · plain-BKT testbed

New branch `plain-bkt`: a student that *is* a BKT process (hidden known/
unknown coin, same four parameters as the tutor, read from one file), the
BKT tutor, uniform-random scheduling over the ZPD, and a step-by-step
viewer. Purpose: for this student the tutor's arithmetic has a known right
answer, so any deviation is a bug, not a finding.

- **Check 1, calibration.** Bin the tutor's belief; within a bin, how often
  is the concept truly known? Both values are read after the tutor's update
  and the student's transition (the state going into the next question);
  reading the state before the transition shifts everything one step and
  makes a correct tracer look badly calibrated.
- **Check 2, detection.** For each (learner, concept) the exact learning
  step is known. Delay is counted in questions asked *on that concept*; the
  false-alarm rate is premature declarations over all declarations, and
  must equal 1 - mean belief at the moment of declaration if check 1 holds.
- Three reporting errors were caught in review and fixed: an overall delay
  that mixed in concepts known before the run, a calibration table showing
  7 of 9 bins, and horizon censoring labelled a "miss rate". The code was
  right; the reporting was not.
- A false "mastered" is permanent under ZPD gating with no review: the
  concept leaves the ZPD and is never asked again, so the student never
  gets the chance to learn it. A review rule would address this and is
  directly relevant to forgetting.

## 2026-09-27 · curricula as data

Curricula moved to JSON (adding one is a new file); the 8-concept abstract
diamond became the default and the original 40-concept graph was frozen for
reproducibility. Interface made dark-themed and viewer-based. Meeting notes
of 15 September were frozen as a dated record because their numbers came
from a configuration the repo no longer runs (40 concepts, 400 questions,
p(T)=0.12 versus 8 concepts, 120 questions, p(T)=0.2); the notes are
removed in the 2026-10-15 cleanup and everything worth keeping is in this
file.

**Side effect, not noticed until 2026-10-15:** this change set the shared
default p(T) to 0.2 in `data/params.json` and `mastery.py` reads it, so
every experiment using a default-parameter belief changed (not `binary`,
which sets 0.06 itself). The results committed on 2026-09-01 and 2026-09-10
no longer reproduced.

## 2026-09-28 · student models S1, S2 and the 2x2

Everything below on `abstract`, p(T)=0.2, current numbers in
`results/`. Two student models (S1, S2) crossed with two rules (Q1, Q2).
Prediction written first: Q1 and Q2 equal against S1; Q2 clearly better
against S2.

- **2x2** (`two_by_two`, 400 learners, 40 questions, concepts truly known
  of 8): S1 Q2-Q1 = -0.15 ±0.14 (marginal, at most a slight cost); S2
  +1.47 ±0.18; interaction +1.62 ±0.16. The scheduler is worth about one
  and a half concepts to S2.
- **Budget:** at 120 questions every cell is near the ceiling; S1 effect
  gone (-0.003), S2 still +0.21 [+0.12, +0.31]. A longer budget shrinks the
  contrast, so any scheduler comparison states its budget.
- **Restriction vs lag** (`restriction_only`): when both arms gate on the
  student's true state, the restriction is exactly neutral under S1 (0 for
  all 400 learners) and worth +1.97 under S2. So the S1 cost in the 2x2 is
  gating on a belief that lags the truth, not the restriction itself.
- **Questions to full mastery** (`mastery_curve`, `seed_blocks`): S2 gets
  there about 22 questions sooner under Q2 (median 55 vs 78); across six
  independent blocks the sign holds in all six (-23.08 ±1.36). S1 is
  +0.37 ±0.57 with blocks disagreeing in sign: too small to give a sign.
- **Calibration at 120 questions:** mean belief 0.7713 vs 0.7728 known
  (100 learners); 0.7769 vs 0.7787 at 400 learners. Detection at θ=0.9:
  3.1 questions on the concept, 6.7 % false alarms, matching the 4.3 %
  predicted by calibration within noise.
- **Misspecified tutor** (`mismatch`): the signed gap is +0.002 when right,
  -0.063 when p_G is under-estimated by 0.20, +0.133 when p_T is
  under-estimated by 0.15. With students spread ±0.15 around the tutor's
  value, gap -0.017 and false alarms 7.5 % vs 4.6 %. p_T errors move the
  belief about twice as much as p_G or p_S errors; p_G and p_T errors push
  false alarms in opposite directions so two mistakes can cancel.
- **What should one tutor assume** (`tutor_choice`, Brier score, oracle
  arm as an upper bound): the best fixed tutor sits at the true centre at
  every spread. Adapting to p_S buys 0.0019 ±0.0013 of Brier at spread
  ±0.15 and is unresolved at ±0.05 and ±0.10; adapting to p_G buys nothing
  detectable at any spread.

Corrections made the same day (do not reintroduce):

- "The scheduler costs S1 nothing" was read off one block whose interval
  covered zero; the six-block study shows it cannot be signed.
- "A fixed tutor is as good as one that adapts" was an artifact of scoring
  on the pooled signed gap (over- and under-confidence cancel) at 60
  learners. Mean absolute error is not proper either (it prefers
  p_S=0.02 to the true 0.10 at short horizons). Brier is proper and
  recovers the true parameter.
- Paired intervals must use the paired statistic: the two per-student
  differences are correlated.
- Sensitivity across parameters partly counts threshold crossings: the
  number k of consecutive correct answers to reach θ moves in integer
  steps, so p_S looks insensitive because k never changes over its grid.

Caveats: one curriculum of 8 concepts, one seed base, θ=0.9 shared by
tracer and scheduler and not swept, tutor p(T) held constant against S2,
and no result checked against real learners. Provenance rule adopted: no
number reaches a document unless a committed artifact produces it.

## 2026-10-15 · restructure, domain-agnostic codebase, reproduction

Branch `forgetting` created from `main` (after fast-forwarding `main` to
`plain-bkt`). All work for the thesis topic (scheduling under forgetting)
happens there.

**What changed**

- Removed every language reference. The 40-concept graph is now
  `layered_40` with ids `A01`..`G01` (tier letter + index, in the original
  order), no word pairs, no prompts or answers. Structure, question counts
  and difficulties are unchanged, which is why old numbers reproduce
  exactly (checked below).
- Library `cursim/`: `students/`, `schedulers/` (one module per family,
  registry decorator), `mastery.py`, `simulation.py`, `stats.py`
  (sign test, paired differences, learner-level bootstraps). Per-run
  profile changes use `RunSpec.profile_overrides` instead of mutating the
  shared profiles (the half-life sweep used to overwrite
  `PROFILES["average"]`).
- `experiments/`: one module per experiment, a registry
  (`@experiment(name, description, defaults, curriculum, theme)`), a
  runner that writes `results/<name>/` (CSVs, PNGs, `summary.md`,
  `meta.json`), named suites (`bkt_validation`, `forgetting`), and a CLI.
  Themes are applied per experiment, so importing one no longer changes
  another's figures.
- `tests/`: `test_core` (55), `test_bkt_validation` (73), `test_framework`
  (37). Dropped the checks that guarded LaTeX tables.
- Removed: LaTeX write-ups and PDFs, generated tables, `MEETING_sep15.md`,
  `simulator_expln.md`, `experiment_plans.md`, the Sep 10 reports,
  `make_sanity.py`, `make_tables.py`, `run_experiments.py`, `exp_sep10.py`,
  the old output folders. Their content is in this file; the files remain
  in git history before this commit.
- The interface (`app.py`, `cursim/viewer*.py`, `viewer/`) is kept and
  reads the same registries; smoke-tested with Streamlit's `AppTest`
  (loads, runs, both tabs, no exception).

**Verification.** The refactor was checked against outputs of the code as
it stood on `main` before any edit (not against the committed CSVs, which
no longer reproduced): all 54 condition rows of experiments 1-4 and the six
Sep 10 arms are equal to 1e-9; all 17 BKT-validation tables are equal to
1e-9 relative. One table (`trace_20_steps`) has no pre-refactor CSV under
the same name and was compared on its first rows only.

**Reruns at the current shared p(T)=0.2** (30 learners, usable after the
break; compare with the 2026-09-01 table, which used p(T)=0.12):

| | CT + binary | CT + forgetting | adaptive review |
|---|---:|---:|---:|
| Exp 1/2, learner forgets | 21.87 | 31.23 | 28.33 |
| Exp 2, learner never forgets | 40.0 | 38.53 | 32.9 |
| Exp 3 fast | 38.03 | 37.3 | 31.93 |
| Exp 3 average | 21.87 | 31.23 | 28.33 |
| Exp 3 slow | 9.4 | 21.83 | 21.33 |
| Exp 3 forgetful | 1.13 | 7.47 | 8.43 |

Changes of substance: adaptive review is much closer to the forgetting
model than recorded on 2026-09-01 (28.33 vs 31.23, not 22.47 vs 30.33),
and the crossovers moved to 9-10 days (adaptive review to forgetting
model) and 18-19 days (forgetting model to binary); paired sign tests at
those points were not recomputed. In the Sep 10 comparison the time-decay
arm is 31.23 against `p_F` 26.43 (0 of 30 learners better, p 4e-09), and
MAPLE is now significantly *worse* than CT on `p_F` (-2.57, p 2e-4)
rather than a tie. The conclusions in the 2026-09-10 entry about `p_F`
hold; the ones about MAPLE and about the size of the adaptive-review gap
do not carry over unchanged.

An unrecorded probe on 2026-10-15 (run on a copy of `main` before the merge,
so at p(T)=0.12, not saved): predictive on the time-decay belief scored 32.3
usable vs 30.3 for CT on time decay, and UCB 28.8. Not at current settings
and not tested for significance; it is the reason scheduler x belief model
needs a proper crossed grid.

**Environment note.** `make_tables.py` used a backslash inside an f-string
expression and only ran on Python 3.12+. It is gone, and the code now runs
on 3.10.

---

## 2026-10-15 (later) · belief x scheduler grid, break length, wrong decay rate

Three experiments, all on `layered_40`, 30 learners each (seeds 4242..4271,
the same learners as every earlier forgetting experiment), primary metric
`retained_usable`, paired sign tests. Outputs: `results/belief_scheduler_grid`,
`results/break_sweep`, `results/break_sweep_slow`,
`results/break_sweep_forgetful`, `results/decay_mismatch`. Regenerate with
`python -m experiments suite forgetting`.

**Code added.** `OracleMastery` in `cursim/mastery.py` (belief = the learner's
true mastery; a reference, no real tutor can do it). `RunSpec.break_days`
measures usable concepts after several idle periods from one training run.
One latent bug fixed: `snapshot_end` and `max_tier_reached` were read after
the break decay, so they described the learner a break later. No experiment
used either field, and every earlier table reproduces byte for byte
(only `meta.json` commit hashes changed).

**Correction to an earlier statement.** The crossovers "near 9-10 days and
18-19 days" (entry 2026-10-15 above and the halflife sweep) are in the
learner's memory half-life, with the break fixed at 3 days. They are not
break lengths. Break length is measured for the first time below.

### 1. Belief x scheduler (`belief_scheduler_grid`)

Concepts usable after a 3-day break, mean over 30 learners:

| belief \ scheduler | curriculum_tutor | continuous | adaptive_review |
|---|---|---|---|
| binary | 21.87 | 24.27 | 30.67 |
| continuous (no decay) | 27.37 | 26.23 | 33.17 |
| continuous_forget (10%/day) | 31.23 | 30.00 | 28.33 |
| oracle | 35.13 | 28.03 | 28.27 |

Random scheduler: 21.43 (no better than CurriculumTutor with the binary belief).
All cells except `binary + continuous` (p 0.12) beat the baseline at
p < 1e-5 (sign test, 26 to 30 of 30 learners).

What it shows:
- Belief and scheduler each matter, and they interact, so "which one is
  responsible" has no single answer. Under CurriculumTutor the belief change
  (binary to time decay) is worth +9.37 (30 wins, 0 losses). Under the binary
  belief the scheduler change (CurriculumTutor to adaptive review) is worth +8.80
  (29/0). Under adaptive review the same belief change is -2.33 (8 wins, 20
  losses, p 0.036), and with the time-decay belief adaptive review is
  below CurriculumTutor by 2.90 (0/28).
- Likely reason, not tested: adaptive review has its own review term, which
  double-counts forgetting once the belief already decays. CurriculumTutor has
  no review term of its own, so a belief that notices forgetting is all it needs.
- Best cell is CurriculumTutor with the oracle belief: 35.13, +13.27 over the
  baseline. Better estimation alone (time decay to oracle) is worth another
  +3.90 (30/0) under CurriculumTutor.
- The oracle is not a ceiling for every scheduler. Adaptive review with a perfect
  belief (28.27) is below adaptive review with the binary belief (30.67). 35.13
  is a reference for these schedulers, not the best possible policy.

### 2. Break length (`break_sweep*`)

Learner fixed, break varied; each length read from the same runs. Average learner
(half-life 14 days), usable concepts:

| break (days) | CT + binary | CT + forgetting | adaptive review | oracle + CT |
|---|---|---|---|---|
| 0 | 28.87 | 32.30 | 29.00 | 35.80 |
| 3 | 21.87 | 31.23 | 28.33 | 35.13 |
| 7 | 6.93 | 26.77 | 25.87 | 30.57 |
| 8 | 3.47 | 22.40 | 23.50 | 22.07 |
| 10 | 0.17 | 9.33 | 11.73 | 2.13 |
| 12 | 0.00 | 0.50 | 0.77 | 0.00 |

- There is a cliff, not a slope. Concepts are learned to about the same level
  and decay together, so almost nothing is usable after about 11 days for any
  tutor. At that point no tutor has an advantage.
- The leader changes once: CT + forgetting model up to 7 days, adaptive review
  from 8 days (the two are close either side). CT + binary never leads.
- The advantage of modelling forgetting grows with the break over the useful
  range: CT + forgetting minus CT + binary is +3.43 at 0 days (22/6, p 0.004),
  +9.37 at 3 days, and about +20 at 7 days.
- The oracle line is above the real tutors up to 7 days and below them from 8 to
  10 days (22.07 vs 22.40 and 23.50 at 8; 2.13 vs 9.33 and 11.73 at 10). A
  tutor that assumes faster forgetting than the truth (10%/day against about
  5%/day) keeps a safety margin, which pays off on long breaks.
- Slower learner (half-life 28 days, `break_sweep_slow`): CT + binary already has
  all 40 concepts usable for breaks up to 7 days, and the forgetting model
  costs 5 concepts there (35.07 vs 40 at 0 days). It wins only from about 14
  days on (33.23 vs 32.40). Modelling forgetting has no value when the break is
  short compared with the learner's memory.
- Forgetful learner (half-life 7 days, `break_sweep_forgetful`): CT + binary
  has 9.03 usable at 0 days and 2.57 at 3, the forgetting model 25.33 and 12.27.
  Everything is gone by 5 to 6 days.

### 3. Wrong forgetting rate (`decay_mismatch`)

The tutor's daily decay rate is swept from 0 to 0.30 for learners with true
half-life 7, 14 and 28 days (true daily rates 0.094, 0.048, 0.024), against
CT + binary on the same learners.

- Half-life 14: every assumed rate from 0 to 0.20 beats CT + binary for
  CurriculumTutor (9 of 10 rates significant; rate 0.30, +1.93, is not). Best is 36.40 at 0.05,
  almost exactly the true rate (0.048); baseline 21.87. The hand-picked 0.10 used
  in all earlier experiments gives 31.23, so the earlier forgetting-model
  numbers understated the benefit by about 5 concepts. Adaptive review is best at
  0.03 (36.23) and drops below the baseline at 0.20 and above.
- Half-life 7: the baseline is 2.56. Rates up to 0.03 do nothing (the tutor
  underestimates the forgetting and behaves like the binary tutor). From 0.05
  upwards it helps, best at 0.15 to 0.20 (15.3 and 16.7), about twice the true
  rate. Too high is cheap, too low is useless.
- Half-life 28: the baseline is already at 40 of 40, so nothing can be gained,
  and assuming a fast rate costs up to 12.7 concepts (0.30). Too high is
  expensive here.
- So the benefit does not depend on knowing the exact rate, but the rate has to
  be within roughly 0.5x to 3x of the truth when forgetting is fast, and the
  cost of overestimating depends on how much forgetting there really is.
- Caveat: the tutor's decay has the same functional form as the simulator's
  (exponential toward a floor). Only the rate is varied here. A different
  shape (for example a power law) is untested.

### Implications

- For the thesis: a scheduler that works with a belief that decays, with the
  decay rate learned per student, is the supported direction. The rate matters
  more than the scheduler's review heuristics.
- Headline numbers should be quoted at the tuned rate, not 0.10: CT with a
  matched decay belief 36.40 vs CT + binary 21.87 on the average learner.
- The earlier remark that adaptive review "wins" came from comparing it with a
  CurriculumTutor that had the wrong belief. With the same belief, adaptive review
  is worse than CurriculumTutor (-2.90).

## 2026-10-15 (evening) · literature on forgetting, and what it means for the algorithm

Guide's suggestion: look at how others have handled forgetting. 13 papers read
(full text or abstract page; the fetch was summarised, so check a figure
against the paper before quoting it). A full write-up with links is in the
shared doc "Forgetting in tutoring: what the literature does and what it
means for our algorithm". The points that matter here:

- **Closest to our problem:** Hunziker et al., NeurIPS 2019, "Teaching
  Multiple Concepts to a Forgetful Learner". Each step picks one concept; the
  greedy policy takes the largest expected gain in average predicted recall,
  with an approximation bound under conditions on the memory model (half-life
  regression, concepts independent). Baselines: random, round robin, lowest
  predicted recall. Simulations favour greedy; in the German vocabulary user
  study it scored 0.572 against 0.487 for lowest-recall (p 0.065, not
  significant).
- **Threshold review:** Lindsey et al. 2014 ask the item whose predicted
  recall is nearest a threshold (0.33 best in their simulation). In a
  179-student classroom study it beat massed review by 16.5% on an exam 28
  days later.
- **Review rate from recall:** Tabibian et al. 2019 (MEMORIZE): rate
  proportional to (1 - recall probability), closed form from optimal control.
- **Others:** Settles and Meeder 2016 (half-life regression, Duolingo),
  Pavlik and Anderson 2008 (retention gain per unit practice time), Reddy et
  al. 2016 (new-item rate against review, Leitner queues), Ye et al. 2022
  (stochastic shortest path, 220M logs), Qiu 2012 (KT-Forget: forgetting tied
  to the calendar day), Nagatani et al. 2019 (DKT-F), Choffin et al. 2019
  (DAS3H, prediction only), Cepeda et al. 2006 and 2008 (best gap grows with
  the test delay, 8% to 43% of it).
- **Agreement with our results:** time decay beat forgetting inside the
  update (Qiu's reason: knowledge tracing over-predicts after a day away); the
  leader depends on the delay (Cepeda); a too-slow assumed rate costs more than
  a too-fast one for fast forgetters (same shape as Cepeda's ridgeline, not the
  same quantity).
- **Gap we can fill, from what I read:** none of the schedulers uses a
  prerequisite graph, and only Reddy et al. looks at introducing new items
  against review. Ours must choose between reviewing a faded concept and
  teaching a ready one, from an estimate of recall.
- **Not searched:** restless-bandit and reinforcement-learning review
  schedulers; FSRS.

**Candidate schedulers to implement from this** (replaces item 3 below as
the first step): lowest predicted recall; recall nearest a threshold r*
(sweep r*); review probability proportional to 1 - recall; greedy expected gain
in average recall, extended to score new ZPD concepts on the same scale.
Design question: Cepeda says the best gap depends on the delay, but the rule
here is not to give a scheduler the break length, so the objective should be
an average over plausible breaks.

## Open threads

1. ~~Cross belief with scheduler~~ done 2026-10-15 (later); the effects
   interact. Not yet crossed: `bkt_forget`, `predictive`, `maple`.
2. ~~Oracle~~ done as an oracle belief. A true oracle scheduler (one that
   plans using the learner's true state) is still open, and is needed to
   say how far the best tutor is from the best possible.
3. **Schedulers that account for forgetting** (first four candidates: see the
   2026-10-15 evening entry): a retention-gain index
   (marginal rise in expected recall at the next session per question; the
   restless-bandit view), recall-threshold review (review when predicted
   recall falls below r*), forgetting-aware predictive (lookahead with the
   belief decayed forward), and a tuned adaptive review (its weight 0.8 and
   decay time 2.5 days were never tuned, and it covers fewer concepts).
4. **Method for new schedulers**: tune on one seed block, report on a fresh
   one; do not give a scheduler the break length as an input; report
   several mastery thresholds, not only 0.50; sweep half-life, budget and
   break length (the winner has changed with each); paired sign tests
   against the best baseline, not only against random.
5. **A BKT-style student that forgets with calendar time**, so calibration
   of a forgetting-aware tutor can be checked against a binary truth. The
   plain BKT student ignores time today.
6. **Fit parameters to real data** (pilot logs: student, question, concept,
   correct, timestamp) and validate the direction of simulated effects
   against the pilot.
7. Per-student estimation of the decay rate (the mismatch result says the
   rate matters most), and a different decay shape in the tutor.
8. A second curriculum shape as a robustness check (`generate_layered`).
