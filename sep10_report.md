# Sep 10 report: two new schedulers and a new forgetting model

Jigar Shaikh (DA25M014) · cursim

I added three things from two papers and tested them against what we already had.
Short version: **none of them beat what we already had**, and the reason why is
the interesting part.

---

## What I added

| Thing | From | What it is |
|---|---|---|
| **BKT forget `p_F`** | Schodde et al., HRI 2017 | a known skill can be *lost* each time it is practised, not just gained |
| **Predictive scheduler** | Schodde et al., HRI 2017 | look one step ahead, pick the question that would move the belief the most |
| **MAPLE scheduler** | Segal et al., 2018 | bandit over concepts, easy ones start heavier, weights shift after each answer |
| **Naive MAPLE** | (control arm) | same bandit, random starting weights, no difficulty ranking |

I also added one line to `simulation.py`: the scheduler is now told whether the
answer was right. Without that, no bandit can work. Every old scheduler ignores
it, so nothing broke. **All 55 existing checks still pass.**

---

## Results

30 learners, same seeds in every arm, so every comparison is the same person
against themselves.

| Arm | Learned (of 40) | Usable after 3-day break | Concepts covered |
|---|---|---|---|
| CT + binary (the original) | 4.50 | 21.87 | 39.97 |
| **CT + time decay** | **18.63** | **30.33** | 33.30 |
| CT + BKT forget (`p_F`) | 5.50 | 24.83 | 40.00 |
| Predictive + BKT forget | 5.53 | 24.67 | 40.00 |
| MAPLE + BKT forget | 3.50 | 24.10 | 40.00 |
| Naive MAPLE + BKT forget | 3.40 | 23.97 | 40.00 |

Head to head, learner by learner:

| Comparison | Difference | Better for | Verdict |
|---|---|---|---|
| BKT forget vs time decay | **−5.50** | 0 / 30 | time decay wins, clearly |
| Predictive vs CT | −0.17 | 10 / 30 | no difference |
| MAPLE vs Naive MAPLE | +0.13 | 14 / 30 | no difference |
| MAPLE vs CT | −0.73 | 8 / 30 | no difference |

---

## Finding 1: BKT's `p_F` cannot model the kind of forgetting we care about

This is the important one.

`p_F` says: *every time the student practises a skill, there is a 5% chance
they have lost it.* So the belief only drops **when a question is asked**.

But our learner forgets **on the calendar**, over the 24-hour gaps between
sessions, when nothing is being asked at all.

So `p_F` has exactly the same blind spot as the binary latch we were trying to
fix: once the tutor stops asking about a concept, it stops learning anything
about it, forever. That is why it lands at 24.83, barely above the binary
model's 21.87, while our time-decay model gets 30.33 and wins for **30 out of
30 learners**.

**`p_F` is practice-time forgetting. Our thesis needs calendar-time
forgetting. They are not the same mechanism, and only one of them solves the
problem.**

That is a genuinely useful thing to be able to say, because `p_F` is the
standard textbook way to put forgetting into BKT, and now we have a measured
reason for not using it.

## Finding 2: looking one step ahead changes nothing

The predictive scheduler scored 24.67 against CT's 24.83. Better for 10 of 30
learners. That is a coin flip.

The reason is that both policies are choosing from the *same* small set of
concepts the student is currently ready for, and inside that set the expected
one-step gains are nearly identical. Looking ahead one step only helps if the
options actually differ, and here they mostly do not.

## Finding 3: the difficulty ranking did not help either

MAPLE beat Naive MAPLE for 14 of 30 learners. That is exactly noise.

This is worth flagging because in my separate MAPLE reproduction, on that
paper's own simulator, the ranking **did** help. The difference is that here I
ranked whole *concepts* by their tier, and our curriculum only has 7 tiers, so
the ranking is very coarse. In the other experiment the ranking was over 100
individual questions and much finer.

**So this is not evidence against MAPLE. It is evidence that a coarse ranking
is not worth much.**

---

## What I would take from this

- Keep the time-decay mastery model. It is still the best thing we have, and
  now we know it beats the standard BKT alternative rather than just assuming so.
- `p_F` is worth keeping in the code as a documented dead end, and worth one
  sentence in the thesis.
- If MAPLE is worth another try here, give it a per-question difficulty ranking
  instead of a per-tier one.

## Limits

One curriculum, 30 learners, one setting of `p_F` (0.05) and one bandit step
size. I did not tune anything. Coverage tells a side story worth noting: the
time-decay arm touches only 33 of 40 concepts while every new arm touches all
40, so time decay is winning by going deep rather than broad, the same trade-off
we saw in the earlier experiments.

---

**Files:** `exp_sep10.py` (run it, ~1 second), `results_sep10.csv`,
`sep10_out.txt` (raw output), `sep_10_expln.md` (plain-language walkthrough).
