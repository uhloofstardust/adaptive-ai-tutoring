# Experiment Plans

The simulator described in `simulator_expln.md` is built and tested.
This document sets out the experiments we plan to run on it.

Each plan states the question, the design, what will be measured, and
what we expect to see. Writing the expectation down before running is
deliberate: if the result contradicts it, that is a finding, and if we
had not written it down we could quietly convince ourselves we
expected the outcome all along.

---

## Common protocol for all four experiments

**Population.** 30 simulated learners per condition.

**Practice.** 20 sessions of 25 questions, so 500 questions across 20
simulated days, with a 24-hour gap between sessions.

**Curriculum.** 40 concepts, 290 questions, prerequisite graph, 7
tiers.

**Retention test.** After the last session the clock advances 3 days
with no practice at all, then we measure what is left. This is the
primary measurement. Testing immediately after practice flatters every
strategy equally, because everything was just rehearsed.

**Paired design.** Every condition uses the same learner seeds, so
learner 7 is the same simulated person in every condition: same
starting knowledge, same learning rate, same memory. We therefore
compare learner by learner, not just average against average.

**Statistics.** For each comparison we report the mean difference, how
many learners improved, and a two-sided sign test. "Better for 28 of
30 learners" is much stronger evidence than "the average was higher",
because an average can be moved by one or two extreme cases.

**Primary metrics.**

| Metric | Meaning |
|---|---|
| concepts learned | of 40, how many reached mastery 0.80 at the end |
| usable after break | of 40, how many are still above 0.50 three days later |

Mean mastery will be reported for completeness but not used to draw
conclusions. It is a poor primary metric here: when there is not
enough time to cover the whole curriculum, it rewards spreading thin,
because forty concepts at 0.5 score the same as twenty at 1.0 even
though the second learner can actually use twenty of them.

---

## Experiment 1: Does continuous mastery beat binary mastery?

### The question

CurriculumTutor assumes mastery is binary and permanent: a concept is
either mastered or not, and once mastered it stays mastered. We want
to know what that assumption costs.

### Design

**Hold the question-selection rule fixed** at CurriculumTutor's own
rule, and change only what the tutor believes:

| Condition | The tutor's representation |
|---|---|
| A | binary, permanent (the original assumption) |
| B | continuous, no forgetting |
| C | continuous, with forgetting |

The simulated learner is identical in all three: continuous mastery,
real forgetting, same seeds.

### Why the design is this way

Binary mastery is a claim about the tutor's model, not about the
person. A real learner does not have binary knowledge. So the correct
comparison changes the tutor and holds the learner fixed. If we made
the learner binary in one arm, we would be comparing two different
universes rather than two tutoring strategies.

Holding the scheduler fixed matters just as much. If both the
representation and the policy changed at once, any difference would be
uninterpretable. With the policy fixed, whatever difference appears is
attributable to the representation alone.

### What we expect

Condition C to beat condition A, and the mechanism to be visible in
which concepts each tutor abandons. A permanent latch cannot be
revoked, so once the tutor decides a concept is mastered it stops
teaching it; if the learner then forgets it, the tutor has no way to
find out. Condition B should recover part of the gap, because a belief
that can move down at least responds to wrong answers, but only C
should recover all of it, because only C notices fading in the absence
of any answers at all.

We also expect the mean-mastery metric to show a much smaller
difference than the threshold metrics, for the reason given in the
common protocol. If that happens it is worth reporting explicitly as a
caution about metric choice.

### Figures

Bar chart across the three conditions on both primary metrics, and
mean mastery trajectories over the 20 sessions.

---

## Experiment 2: Does modelling forgetting help, and what does it cost?

### The question

Experiment 1 asks whether modelling forgetting helps a learner who
forgets. This one also asks the harder question: what happens when the
tutor models forgetting and the learner does not actually forget?

Most papers only run the first half. Running both is what turns
"our extension is better" into "our extension is better under these
conditions and worse under those".

### Design

Two worlds, three tutoring conditions in each:

| | Learner forgets | Learner never forgets |
|---|---|---|
| CT + binary | run | run |
| CT + forgetting model | run | run |
| adaptive review | run | run |

The learner's forgetting is switched off entirely in the second world.
Everything else is identical.

### What we expect

**World A (learner forgets).** The forgetting-aware tutor should beat
the binary one clearly. The adaptive review scheduler adds spaced
revision on top; whether it adds much beyond the forgetting model
itself is genuinely unclear to us, and worth finding out.

**World B (learner never forgets).** We expect the forgetting-aware
tutor to be *worse*. It will schedule revision that is not needed, and
that time comes out of teaching new material. We expect adaptive
review to be worse still, because it is the more aggressive version of
the same behaviour.

If that prediction holds, the honest conclusion is that modelling
forgetting is a trade-off rather than a free improvement, and its
value depends on an empirical property of the learner. We would rather
report that than a one-sided result.

### Figures

Two side-by-side panels, one per world, with the same three
conditions, so the reversal is visible at a glance.

---

## Experiment 3: Does the best strategy depend on the learner?

### The question

A tutoring system serves a mixed population. Is there one strategy
that is best for everyone, or does the ranking change from learner to
learner?

### Design

Four learner profiles crossed with three tutoring conditions.

| Profile | Learning rate | Memory half-life |
|---|---|---|
| fast | 1.35 | 18 days |
| average | 1.00 | 14 days |
| slow | 0.70 | 12 days |
| forgetful | 1.10 | 6 days |

The forgetful profile is deliberately not a slow learner: it learns at
close to normal speed but loses knowledge quickly. Keeping ability and
memory as separate dials is what lets us attribute any effect to the
right cause.

### What we expect

We expect the ranking to change across profiles. Specifically, we
expect the extra machinery to earn its keep for learners who forget
quickly, and to be unnecessary or actively wasteful for learners with
strong memory, where the simplest strategy has nothing to fix and
loses nothing to revision overhead.

If no single strategy dominates, that is an argument for adapting the
policy to the estimated learner and not only to the estimated mastery,
which is a natural direction for later work.

### Figures

Grouped bars: learner profile on the x axis, one bar per tutoring
condition.

---

## Experiment 4: How forgetful must a learner be before this matters?

### The question

Experiment 3 uses four discrete profiles. This one turns memory into a
continuous dial and asks where the crossover points are. This is the
experiment most likely to produce a single quotable sentence.

### Design

Sweep the learner's memory half-life across roughly 5 to 22 days,
holding everything else fixed, and run all three tutoring conditions
at each point.

### What we expect

Three regimes, and the transitions between them are the result:

- **Very forgetful learners.** Everything struggles, but revision-heavy
  scheduling should do best, because knowledge that is not refreshed
  is gone before the session ends.
- **Middle range.** The forgetting-aware tutor should be best: it
  notices fading without spending as much of the budget on revision.
- **Strong memory.** The original binary tutor should overtake
  everything, because there is nothing to forget and every revision
  question is a question not spent on new material.

If the crossovers appear, the headline is that the value of modelling
forgetting is not a constant but a function of the learner's memory,
and we will be able to state roughly where the boundaries sit.

### Figures

Line chart: memory half-life on the x axis, concepts retained on the y
axis, one line per condition. The crossing points are the result.

---

## Threats to validity we will report

**Regime dependence.** With a much larger question budget, learners
approach full mastery and the differences between strategies vanish
into the ceiling. Every headline number must be quoted with the
settings that produced it, and experiment 4 exists partly to show what
happens outside the default regime.

**Assumed parameters.** Learning gain, memory half-life and
prerequisite sensitivity are currently chosen by us, not estimated
from data. Every result is therefore a statement about the model. The
plan below addresses this.

**Simulator design choices.** The learner is deliberately not a BKT
model. If it were, then a BKT-based tutor could recover the truth
exactly and any extension would look pointless by construction. Using
a differently-shaped learner keeps the comparison meaningful, but it
does mean results are partly a function of that shape.

**One curriculum.** All four experiments use the same 40-concept
graph. A denser or shallower curriculum might change the conclusions,
and repeating the sweep on a second graph would be a useful robustness
check.

---

## After these four

1. **Fit the learner to real data.** The pilot app logs student,
   question, concept, correct, and timestamp, which is exactly what is
   needed to estimate learning and forgetting parameters from real
   learners. Replacing assumed parameters with fitted ones is the
   single change that would move these experiments from illustrative
   to evidential.
2. **Bandit schedulers.** The adaptive review scheduler is a
   hand-tuned index policy. Because concepts decay whether or not they
   are practised, this is formally a restless bandit problem, which is
   where the multi-armed bandit work plugs in. The `Scheduler`
   interface is the seam and needs no other change.
3. **Separate the scheduling model from the evaluated model.** At the
   moment the scheduler consults the same mastery model that
   experiment 1 is studying. Separating the two would allow a full 2x2
   of representation against policy.
4. **Validate against the pilot.** Compare the adaptive and
   non-adaptive arms of the live app and check whether the direction
   of the simulated effect appears in real data.
