# The Simulator: A Complete Guide

This document explains everything about `cursim`, the research
simulator built for extending CurriculumTutor to Indian language
learning. It covers what the simulator is, why each design choice was
made, and what every file and every parameter does.

There are no experiment results in this document. It describes the
instrument, not what we measured with it.

---

## Part 1: What this is and why it exists

### 1.1 The problem

We want to design a tutoring system that decides which question to
ask a language learner next. To know whether one design is better
than another, we need to try them on learners. But real learners are
slow, scarce, and inconsistent: a pilot with twenty students takes
months and still gives noisy answers. Worse, with a real learner we
can never see what they actually know. We only see their answers.

So we build a fake learner instead. A program that behaves roughly
like a student: it knows some things, learns from practice, forgets
over time, guesses sometimes, and slips sometimes. Then we let
different tutoring strategies teach this fake learner and see which
one leaves it knowing more.

### 1.2 The one thing a simulator gives us that reality cannot

With a simulated learner, **we know exactly what it knows**. Its true
knowledge is a number inside the program.

This is the whole point. In a real experiment we can only ask "did
the tutor predict the next answer correctly?" With a simulator we can
ask the far better question: "how much does the learner actually know
at the end, and how much do they still know a week later?"

That distinction is the reason the simulator exists.

### 1.3 What this is not

It is not an app. There is no interface, no login, no database. It is
a set of Python files that run experiments and print numbers.

It is also not a claim about real people. Every number it produces is
a statement about the model we wrote. Before any result is used as
evidence about learners, the model's parameters need to be estimated
from real data.

---

## Part 2: The three parts, and why they are kept apart

The simulator has exactly three moving parts. Keeping them separate
is the most important structural decision in the whole design.

```
     SCHEDULER                LEARNER              MASTERY MODEL
  which question next?   answers correctly?     what does the tutor
                                                    believe?

   sees: the graph,       sees: everything      sees: only the answers
   the tutor's beliefs    (it IS the truth)     (concept, right/wrong,
                                                     time)
```

**The scheduler** picks the next question. This is where a bandit
algorithm would plug in.

**The learner** decides whether the answer is right, using its hidden
true knowledge. This is the simulated student.

**The mastery model** watches the answers and estimates what the
learner knows. This is where an improved BKT would plug in.

### 2.1 The rule that keeps the experiment honest

**The scheduler and the mastery model never see the learner's true
knowledge.**

If the scheduler could see the truth, it would trivially pick the
perfect question every time, and the experiment would mean nothing.
The learner's true state is used for one purpose only: scoring at the
end. This rule is enforced in the code, not just by convention.

### 2.2 Why separation matters for the research

Because the parts are separate, we can change one and hold the others
fixed. If we change the mastery model and the results improve, the
improvement came from the representation, not from a better question
policy. If we change the scheduler and hold the model fixed, the
opposite. Without this separation, every result would be confounded.

---

## Part 3: The curriculum

### 3.1 What a concept is

A concept is one teachable unit: "greetings", "past tense verbs",
"telling the time". There are 40 of them.

Each concept has 5 to 9 questions, for a total of 290 questions. Each
question has its own difficulty between 0 and 1.

### 3.2 The prerequisite graph

Concepts are arranged in a directed acyclic graph. An arrow from A to
B means A should be learned before B.

```
tier 0  greetings, numbers 1-5, colors, pronouns, yes/no
           |
tier 1  family, food, animals, body, household, adjectives,
        numbers 6-10, time words, directions
           |
tier 2  plurals, possessives, present tense verbs, question words,
        places, numbers 11-20, weather, clothing, market, illness
           |
tier 3  negation, past tense, postpositions, simple sentences,
        politeness, telling time, shopping dialogue, describing people
           |
tier 4  future tense, compound sentences, narrating past events,
        asking directions, at the clinic
           |
tier 5  conditionals, formal register, storytelling
```

Five independent entry points, six tiers. This shape is deliberate: a
language curriculum is wide and shallow, unlike an arithmetic
curriculum which is narrow and deep. A learner can start greetings and
numbers on the same day; they cannot start division before addition.

### 3.3 Why questions have different difficulties

The original CurriculumTutor treats all questions within a concept as
interchangeable. We do not. Each question has a difficulty, and
difficulty affects how much mastery is needed to answer it.

This matters because it gives the scheduler a second decision. Not
just "which concept?" but "which question within that concept?" A
learner who is shaky on food vocabulary should get an easy food
question, not the hardest one.

---

## Part 4: The learner

This is the simulated student. Everything here is hidden from the
tutor.

### 4.1 Mastery is a number, not a flag

For every concept, the learner holds a mastery value between 0 and 1.
0.0 means no knowledge, 1.0 means complete knowledge, 0.6 means
partial knowledge.

This is always continuous, for every experiment. When we compare
"binary versus continuous mastery", we are changing what the **tutor
believes**, never what the learner is. A real person does not have
binary knowledge, so making the simulated learner binary would be
comparing two different universes instead of two tutoring strategies.

### 4.2 How the learner answers a question

Three steps.

**Step one: apply forgetting.** Bring mastery up to date based on how
long it has been since this concept was last practised. (Details in
4.4.)

**Step two: work out the chance of a correct answer.**

```
m_eff = mastery ^ (1 + 1.2 x difficulty)
P(correct) = m_eff x (1 - slip) + (1 - m_eff) x guess
```

Read this in plain words. The first line says a hard question needs
more mastery than an easy one: raising a number below 1 to a higher
power makes it smaller, so a difficulty of 0.8 shrinks effective
mastery much more than a difficulty of 0.1. The second line is the
standard two-route idea: you answer correctly either because you know
it and did not slip, or because you do not know it and guessed right.

Guess is 0.25 because the questions are four-option multiple choice.
Slip is around 0.07: even a learner who knows something gets it wrong
occasionally.

**Step three: learn from the attempt.**

```
gain = 0.45 if correct, else 0.10
mastery = mastery + learning_rate x readiness x gain x (1 - mastery)
```

Three things are happening. Correct answers teach more than wrong
ones, but wrong answers still teach a little, because the learner sees
the right answer afterwards. The `(1 - mastery)` term means gains
shrink as you approach full mastery, which is why learning curves
flatten. And `readiness` is the prerequisite effect, explained next.

### 4.3 Prerequisites affect the learner, not just the scheduler

This is the second most important design decision in the simulator.

```
readiness = (1 - sensitivity) + sensitivity x (weakest prerequisite)
```

With sensitivity at 0.8, a concept whose prerequisites are all at 0.9
gets a readiness of about 0.92, so learning proceeds almost at full
speed. A concept whose prerequisites are at 0.1 gets a readiness of
about 0.28, so learning is nearly four times slower.

**Why this had to be built in:** if prerequisites only affected which
questions the scheduler was allowed to ask, then the curriculum graph
would be a rule we imposed rather than a fact about learning. A
scheduler that respected the graph could never outperform one that
ignored it, because ignoring it would cost nothing. By making weak
prerequisites genuinely slow down learning, respecting the graph
becomes a real advantage that a good scheduler can earn.

### 4.4 Forgetting

Mastery decays exponentially toward a small floor:

```
mastery = floor + (mastery - floor) x exp(-rate x hours_elapsed)
```

The rate is set by the learner's memory half-life. A half-life of 14
days means that after 14 days without practice, mastery has dropped
halfway toward the floor.

Two details worth knowing:

**Decay is applied lazily.** Nothing runs in the background. Whenever
mastery is read, the code first works out how long it has been and
applies the decay then. Same result, much simpler.

**Later tiers are more fragile.** Tier 5 concepts decay slightly
faster than tier 0 concepts, reflecting that complex material fades
faster than basic vocabulary.

Because concepts decay whether or not they are practised, a concept
the tutor is ignoring is still changing. This is what makes the
scheduling problem genuinely hard, and it is formally what is called a
"restless" problem.

### 4.5 Learner profiles

Four kinds of simulated learner:

| Profile | Learning rate | Memory half-life | Slip |
|---|---|---|---|
| fast | 1.35 | 18 days | 0.05 |
| average | 1.00 | 14 days | 0.07 |
| slow | 0.70 | 12 days | 0.10 |
| forgetful | 1.10 | 6 days | 0.07 |

The forgetful learner is deliberately not a slow learner. It learns at
close to normal speed but loses knowledge quickly. Keeping "ability"
and "memory" as separate dials lets us ask which one a given tutoring
strategy is actually helping.

---

## Part 5: The mastery model, or what the tutor believes

The tutor cannot see the learner. It sees a stream of answers and
must form its own estimate. There are two kinds.

### 5.1 Binary and permanent, the CurriculumTutor assumption

The tutor keeps a belief internally, and when that belief crosses a
high threshold the concept is marked mastered. **Once marked, it can
never be unmarked.**

The critical consequence: the tutor stops teaching that concept
forever. If the learner then forgets it, the tutor has no mechanism
to find out. The concept was permanently ticked off.

### 5.2 Continuous, with optional forgetting

The tutor's belief stays a number between 0 and 1 and is never
latched. With forgetting switched on, the belief also decays between
practices, exactly as the learner's real mastery does.

This is what allows a tutor to notice fading. If the belief for
"family words" drops from 0.9 to 0.6 because it has not been
practised in two weeks, the concept becomes eligible again.

### 5.3 The Bayesian update underneath

Both models use the same update. After each answer:

```
if correct:  numerator = belief x (1 - slip)
             other     = (1 - belief) x guess
if wrong:    numerator = belief x slip
             other     = (1 - belief) x (1 - guess)

belief = numerator / (numerator + other)
belief = belief + (1 - belief) x learn_rate
```

The first part is Bayes' rule: given what just happened, how should
the belief change? The second part adds a small push upward, because
the learner may have learned something from the attempt itself.

The tutor's guess parameter is 0.25, matching the four options. Its
slip and learn parameters are assumed values for now; the plan is to
estimate them from real pilot data later.

---

## Part 6: The schedulers

Four strategies for choosing the next question.

### 6.1 Random

Picks any question from any concept, uniformly. The floor. If a
strategy cannot beat random, it is doing nothing.

### 6.2 CurriculumTutor

The original paper's rule. A concept is eligible if it is not yet
mastered and all its prerequisites are mastered. Pick uniformly among
eligible concepts, then uniformly among that concept's questions
(consistent with the paper's equal-difficulty assumption).

This is a hard gate: prerequisites are either satisfied or they are
not.

### 6.3 Continuous

Uses the continuous belief instead of a yes/no. Three ingredients:

- **Soft prerequisites.** If the weakest prerequisite belief is below
  0.45, the concept's score is multiplied by 0.30. Discouraged, but
  not forbidden. Real prerequisites are rarely absolute.
- **A learning zone.** Concepts whose belief sits between 0.15 and
  0.85 score highest. Too low means the learner will just guess; too
  high means there is little left to teach.
- **Difficulty matching.** Within the chosen concept, pick the
  question whose difficulty is closest to the current belief.

### 6.4 Adaptive review

Everything the continuous scheduler does, plus a review term:

```
urgency = 1 - exp(-days_since_practised / 2.5)
score  += 0.8 x urgency x belief^2
```

Urgency starts at zero right after practice and grows toward one over
days. It is multiplied by `belief^2`, which is the interesting part:
**a concept is only worth reviewing if the learner probably knows it
and it has had time to fade.** There is no point "reviewing" something
that was never learned; that is just teaching.

This is a hand-built index policy. It is deliberately simple, and
replacing it with a principled bandit algorithm is the obvious next
step.

---

## Part 7: How a run works

### 7.1 Sessions, not one long stream

Practice happens in daily sessions. The default is 20 sessions of 25
questions, so 500 questions over 20 simulated days, with a 24-hour gap
between sessions.

The gaps are the point. Without them, forgetting would have no room to
act and the whole research question would disappear.

### 7.2 The loop

```
for each session:
    for each question in the session:
        scheduler picks a question
        learner answers it (using hidden true mastery)
        mastery model observes only the concept and right/wrong
        clock advances one minute
    clock advances 24 hours
```

### 7.3 The retention test

After the last session, the clock jumps forward three more days with
**no practice at all**, and we measure what the learner still knows.

This is the most important measurement in the simulator. Measuring
knowledge immediately after practice flatters every strategy equally,
because everything was just rehearsed. Measuring after a break is what
separates a tutor that built durable knowledge from one that produced
a temporary peak.

### 7.4 What we measure

| Metric | Meaning |
|---|---|
| concepts learned | how many of 40 reached mastery 0.80 at the end |
| usable after break | how many are still above 0.50 three days later |
| mean mastery | average mastery across all 40 concepts |
| coverage | how many concepts were practised at least once |

**A warning about mean mastery.** It is reported for completeness but
it is a poor primary metric here. When there is not enough time to
cover the whole curriculum, mean mastery *rewards spreading thin*:
forty concepts at 0.5 score exactly the same as twenty concepts at
1.0, even though the second learner can actually use twenty concepts
and the first can use none. The threshold metrics do not have this
flaw. Report the mean, but do not draw conclusions from it.

### 7.5 Paired comparison

Every condition is run with the same set of learner seeds. Learner 7
under strategy A is **the exact same simulated person** as learner 7
under strategy B: same starting knowledge, same learning rate, same
memory.

This means we can compare learner by learner rather than only
comparing averages. Saying "strategy B was better for 28 of 30
learners" is far stronger evidence than "strategy B averaged slightly
higher", because averages can be moved by one or two lucky cases.

A sign test converts this into a p-value: if a strategy is genuinely
no better, wins and losses should split like coin flips, and we can
compute how unlikely the observed split is.

---

## Part 8: Every file, explained

```
cursim/
├── cursim/
│   ├── curriculum.py     the concept graph and question bank
│   ├── learner.py        the simulated student
│   ├── mastery.py        what the tutor believes
│   ├── schedulers.py     which question to ask next
│   ├── simulation.py     the loop and the metrics
│   └── plots.py          figures
├── run_experiments.py    experiment definitions and self-tests
├── test_simulator.py     the test suite
├── data/
│   ├── curriculum.json   the generated curriculum, saved
│   └── results.csv       one row per condition after a run
└── figures/              generated charts
```

### 8.1 `curriculum.py` (236 lines)

Builds the concept graph and question bank.

- `WORDS` — real Marathi/Bengali word pairs for the vocabulary
  concepts.
- `SPEC` — the 40 concepts as `(id, name, tier, prerequisites,
  number of questions)`. **To change the curriculum, edit this list.**
- `Question` — one item: id, concept, prompt, answer, difficulty.
- `Concept` — id, name, tier, prerequisites, and its questions.
- `Curriculum` — the whole graph. `is_dag()` checks there are no
  circular prerequisites, `topo_order()` gives a valid teaching order,
  `to_json()` / `from_json()` save and load.
- `build_curriculum(seed)` — generates everything deterministically.
  Question difficulty is drawn around a tier-dependent base
  (`0.20 + 0.11 x tier`), so later concepts are harder.

A note on content: vocabulary concepts carry real word pairs, grammar
concepts carry pattern descriptions like "Present tense verbs:
production item 3". The simulation only ever uses the concept and the
difficulty, never the text, so placeholder text changes nothing. It
must be replaced before any human uses this.

### 8.2 `learner.py` (151 lines)

The simulated student.

- `LearnerProfile` — learning rate, memory half-life, slip,
  prerequisite sensitivity, starting knowledge.
- `PROFILES` — the four learner types.
- `SimConfig` — shared settings: number of options, learning gains,
  difficulty exponent, mastery floor, the 0.80 learned threshold.
- `Learner` — the class itself:
  - `_decay_rate()` — per-hour forgetting rate from the half-life
  - `_refresh()` — applies forgetting up to the current time
  - `readiness()` — the prerequisite multiplier
  - `answer()` — the three steps from section 4.2, returns whether it
    was correct plus mastery before and after
  - `true_mastery()`, `snapshot()`, `mean_mastery()`, `n_learned()` —
    evaluation access, used only for scoring

### 8.3 `mastery.py` (119 lines)

What the tutor believes.

- `MasteryModel` — the interface: `observe()`, `belief()`,
  `is_mastered()`.
- `_BKTCore` — the shared Bayesian update and optional decay.
- `BinaryMastery` — latches at a 0.97 belief and never unlatches.
  Uses a deliberately conservative learn rate so it does not declare
  mastery after two lucky answers.
- `ContinuousMastery` — belief stays continuous;
  `forget_per_day > 0` makes it decay.
- `make_model(kind, ...)` — factory taking `"binary"`,
  `"continuous"`, or `"continuous_forget"`.

**To add a new student model:** subclass `MasteryModel`, implement the
three methods, add it to `make_model`.

### 8.4 `schedulers.py` (157 lines)

Which question to ask next.

- `Scheduler` — the interface: one method, `select()`.
- `_pick_question()` — chooses within a concept, either at random or
  by difficulty matching, avoiding an immediate repeat.
- `RandomScheduler`, `CurriculumTutorScheduler`,
  `ContinuousScheduler`, `AdaptiveReviewScheduler` — the four
  strategies from Part 6.
- `SCHEDULERS` — the registry.

**To add a bandit scheduler:** subclass `Scheduler`, implement
`select()`, add it to `SCHEDULERS`. Nothing else changes.

### 8.5 `simulation.py` (160 lines)

The loop and the measurement.

- `RunSpec` — one experimental condition: which scheduler, which
  mastery model, which learner profile, whether the learner forgets,
  how many sessions, how long the retention break is.
- `RunResult` — the outcomes, with `mean()` and `sd()` helpers.
- `run_one()` — one learner through one condition.
- `run_condition()` — a population, all sharing base seeds so
  comparisons stay paired.
- `paired()` — learner-by-learner differences between two conditions,
  with wins, losses, and a sign-test p-value.
- `sign_test()` — the exact two-sided test.
- `table()` — formatted output.

### 8.6 `plots.py` (175 lines)

Six figure functions: the curriculum graph, representation
comparison, learning trajectories, forgetting comparison, learner
types, and the forgetting sweep. Consistent colours, values printed on
the bars so a reader can quote a number without a table.

### 8.7 `run_experiments.py` (295 lines)

Defines the experiments, writes `data/results.csv`, and contains a
`--selftest` mode.

```
python run_experiments.py             # everything
python run_experiments.py --exp 1     # one experiment
python run_experiments.py --selftest  # invariant checks
```

---

## Part 9: Reproducibility

Every random choice comes from a seeded generator. Two runs with the
same seed produce byte-identical results, on any machine.

The learner's randomness and the scheduler's randomness use
**separate** streams. This matters more than it sounds: if they shared
a stream, changing the scheduler would also change the learner's luck,
and we could never tell which caused a difference.

---

## Part 10: How to extend it

| Goal | What to change |
|---|---|
| New question-selection algorithm | subclass `Scheduler`, add to `SCHEDULERS` |
| New student model | subclass `MasteryModel`, add to `make_model` |
| Different language pair | replace `WORDS` and `SPEC` in `curriculum.py` |
| Different curriculum shape | edit `SPEC`; `is_dag()` will catch mistakes |
| New learner type | add an entry to `PROFILES` |
| Different session structure | change `RunSpec` fields |
| New metric | add it to the dictionary returned by `run_one()` |

---

## Part 11: Honest limitations

**Not validated against humans.** Every number is a statement about
our model. The parameters that matter most (learning gain, memory
half-life, prerequisite sensitivity) are currently assumed values.

**Results depend on the regime.** With a much larger question budget,
learners approach full mastery and differences between strategies
vanish into the ceiling. Any result must be quoted with the settings
that produced it.

**The learner model is simple by choice.** No time-of-day effects, no
motivation, no interference between similar words, no partial credit.
Adding realism was explicitly not the goal; controllability was.

**Mean mastery is a misleading metric** for the reason in section 7.4.

**Item text is placeholder** for the grammar concepts and must be
replaced before real use.
