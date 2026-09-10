# What I did on Sep 10, explained simply

No jargon. Anything technical gets explained the first time it shows up.

---

## 1. Where we were before today

We have a simulator called **cursim**. It has two halves:

- A **fake student**, who has some hidden knowledge of 40 language concepts,
  learns a bit from every question, and slowly forgets things over time.
- A **tutor**, who cannot see any of that. All the tutor ever sees is right and
  wrong answers, and from those it has to guess what the student knows and pick
  the next question.

The tutor is really two separate pieces, and this matters:

1. **The belief model.** What the tutor *thinks* the student knows.
2. **The scheduler.** Given that belief, which question to actually ask.

Today I added one new belief model and two new schedulers, all taken from
published papers, and checked whether any of them beat what we already had.

---

## 2. The three things I added

### Thing 1: forgetting inside BKT (the `p_F` parameter)

**BKT** stands for Bayesian Knowledge Tracing. It is the standard way a tutor
tracks a student. For each concept it keeps one number: *the probability this
student knows it*. After every answer that number is updated with Bayes' rule.
Right answer, number goes up. Wrong answer, number goes down.

Classic BKT has a quiet assumption: **once you know something, you know it
forever.** The number can go up but never drifts back down on its own.

The HRI 2017 paper (Schodde and colleagues, a robot that teaches language to
children) adds one parameter to fix this, called `p_F`, the **forget
probability**. It says: each time the student practises a skill, there is a
small chance they have lost it since last time.

That is a one-line change to the update rule, and I made it.

### Thing 2: the predictive scheduler

Same paper. Most schedulers pick a question using some rule of thumb. This one
does something smarter: **before asking, it imagines what would happen.**

For every concept the student is ready for, it asks itself:

> "If I posed this question, and the student got it right, where would my belief
> end up? And if they got it wrong, where would it end up? How likely is each?"

It averages those two outcomes, weighted by how likely each is, and picks the
concept where its belief would move the most. Moving the belief a lot means
learning a lot about the student, which usually means the question was neither
too easy nor too hard.

This is called **one-step lookahead**. Look one move ahead, pick the best one.

### Thing 3: MAPLE

From the other paper (Segal and colleagues, 2018), which I reproduced
separately earlier.

Picture each concept as a slot machine. You do not know which pays best, so you
try them and learn. That setup is called a **multi-armed bandit**. MAPLE's twist
is that the machines do not all start equal: **easy concepts start with a higher
chance of being picked**, because we already know roughly which concepts are
easy. Then after every answer it shifts the weights, making harder concepts more
likely after a success and less likely after a failure.

I also built **Naive MAPLE**: exactly the same bandit, but the starting weights
are random. This is the control. MAPLE and Naive MAPLE differ in one single
thing, so if MAPLE wins, the difficulty ranking has to be the reason.

---

## 3. One small plumbing fix I had to make first

MAPLE needs to know whether the student got the last question right, so it can
shift its weights.

But cursim's scheduler was never told. It was only ever asked "which question
next?" and the answer went off to the belief model, not to the scheduler.

So I added one line: after each answer, the scheduler is now told what happened.
Every older scheduler simply ignores it, so nothing else changed. I re-ran the
project's own 55 automated checks and all 55 still pass.

---

## 4. How I tested them

Six versions of the tutor, run over the same 30 fake students.

**Same students, same random numbers, every time.** Student number 12 is the
identical person in all six runs. This matters more than it sounds. If you use
different students in each run, a difference might just mean one group happened
to be better. Using the same people removes that entirely. It is called a
**paired** comparison.

I measured two things:

- **Learned**: how many of the 40 concepts the student really knows at the end.
- **Usable after a break**: how many are still usable 3 days later with no
  practice. This is the honest one, because anything measured right after
  practice flatters every method equally.

---

## 5. What happened

| Tutor version | Learned | Usable after break |
|---|---|---|
| The original (no forgetting at all) | 4.50 | 21.87 |
| **What we already had (time decay)** | **18.63** | **30.33** |
| New: BKT forget (`p_F`) | 5.50 | 24.83 |
| New: Predictive scheduler | 5.53 | 24.67 |
| New: MAPLE | 3.50 | 24.10 |
| New: Naive MAPLE | 3.40 | 23.97 |

**None of the new things won.** Our existing time-decay model is still well
ahead of everything.

---

## 6. Why `p_F` lost, which is the interesting bit

Look at those two forgetting models side by side.

**`p_F` (the new one):** every time a concept is *practised*, there is a 5%
chance the student has lost it. The belief drops **only when a question is
asked**.

**Time decay (what we had):** the belief slowly fades as *days pass*, whether or
not anything is asked.

Now think about what actually happens in a session. The student practises for a
while, the tutor becomes confident, so it stops asking about that concept and
moves on. Then 24 hours pass. The student forgets.

With time decay, the tutor's confidence quietly drops overnight, so the concept
comes back up for review. It notices.

With `p_F`, **nothing happens at all**, because nothing is being asked. The
belief just sits there, frozen and wrong, forever.

So `p_F` has the exact same blind spot as the original no-forgetting tutor, the
blind spot we were trying to fix in the first place. That is why it only reached
24.83, barely above the original's 21.87, while time decay reached 30.33 and won
for **all 30 out of 30 students**.

> **In one sentence: `p_F` models forgetting caused by practice. We need
> forgetting caused by time passing. They are different things, and only one of
> them fixes the problem.**

This is worth writing in the thesis, because `p_F` is the standard textbook way
to put forgetting into BKT. Now we have a measured reason for not using it,
instead of just an opinion.

## 7. Why the predictive scheduler changed nothing

It scored 24.67 against 24.83. Better for 10 students out of 30, which is a coin
flip.

The reason is simple. Both schedulers are choosing from the same small handful
of concepts the student is currently ready for, and within that handful all the
options look about equally useful. Looking one move ahead only helps if the
moves actually differ from each other. Here they mostly do not.

## 8. Why MAPLE's ranking did not help

MAPLE beat Naive MAPLE for 14 students out of 30. That is exactly noise.

But this does **not** mean MAPLE is wrong, and here is why. In my separate
experiment on MAPLE's own simulator, the ranking clearly *did* help. The
difference is how fine-grained the ranking was:

- **There:** a ranking over 100 individual questions. Very detailed.
- **Here:** a ranking over concepts by tier, and we only have 7 tiers. Very
  coarse.

A ranking that only sorts things into 7 buckets does not tell the bandit much.
So the fair conclusion is: **a coarse ranking is not worth much**, not "the
paper is wrong".

---

## 9. One more thing worth noticing

Look at the last column of the results table in the report: how many of the 40
concepts each tutor actually touched.

- Time decay (the winner): **33.3** concepts
- Everything else: **40.0** concepts

The winner covered **fewer** concepts. It kept going back to the same 33 and
drilling them properly, instead of spreading itself thinly over all 40.

That is the same pattern we found in the earlier experiments: **depth beats
breadth** on this measure. Nice to see it turn up independently again.

---

## 10. The honest summary

- I added three published ideas properly, and they are all in the code and
  tested.
- None of them improved anything.
- The most useful outcome is knowing **why** the standard BKT forgetting
  parameter does not solve our problem, which is a real result and not just a
  failed attempt.
- If we want to give MAPLE a fair second chance here, it needs a per-question
  difficulty ranking rather than a per-tier one.

## 11. What is limited about this

One curriculum. 30 students. One value of `p_F` (5%) and one bandit step size,
neither of which I tuned. A tuned version might do better. And these are
simulated students, not real ones, so everything here is a statement about the
model, not about people.

---

## 12. The files

| File | What it is |
|---|---|
| `cursim/mastery.py` | now has `p_F` and the one-step-lookahead calculation |
| `cursim/schedulers.py` | now has `predictive`, `maple`, `naive_maple` |
| `cursim/simulation.py` | one new line: tell the scheduler what happened |
| `exp_sep10.py` | the experiment, takes about 1 second |
| `results_sep10.csv` | the numbers |
| `sep10_out.txt` | the raw output |
| `sep10_report.md` | the short write-up |

Run it with `python3 exp_sep10.py`. Seeds are fixed, so you will get exactly
these numbers.
