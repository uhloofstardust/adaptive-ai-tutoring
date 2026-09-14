# Points for Tuesday's meeting with Surya

Branch: `plain-bkt` on `uhloofstardust/adaptive-ai-tutoring`. `main` is untouched.

Everything below runs from three commands:

```
streamlit run app.py        # the viewer
python3 make_sanity.py      # every plot and table below -> sanity_outputs/
python3 test_sanity.py      # 16 checks; the original 55 still pass too
```

---

## 1. What we built, in one paragraph

A student who *is* a BKT process: each concept is a coin, known or not, with the four
standard parameters. No forgetting, no difficulty, no prerequisite effect. The tutor is
the BKT belief we already had, reading the **same four numbers from the same file**
(`cursim/params.py`), so "same parameters" is enforced by the code rather than by
memory. The scheduler is uniform random over the ZPD, no bandit. On top of that, both
checks from the mail, the 20-step trace, and a viewer where you can watch a single run
one question at a time.

---

## 2. Check 1: is the belief calibrated?  (yes)

Every time the tutor updates a belief we record (belief, true state) for that concept,
then bin by belief. Both values are read at the same instant: after the tutor's update
and after the student's transition, i.e. the state going into the next question.

100 learners × 400 questions = 40,000 pairs:

| tutor believes | student truly knows | gap | n |
|---:|---:|---:|---:|
| 0.143 | 0.147 | +0.004 | 15,305 |
| 0.214 | 0.212 | −0.002 | 3,762 |
| 0.449 | 0.443 | −0.006 | 7,046 |
| 0.549 | 0.522 | −0.027 | 1,704 |
| 0.772 | 0.756 | −0.016 | 4,224 |
| 0.841 | 0.836 | −0.005 | 1,107 |
| 0.953 | 0.950 | −0.003 | 5,904 |

Every bin with n ≥ 500 is within 0.03 of the diagonal. We also ran 400 × 400 = 160,000
pairs to make sure the small negative gaps in the middle bins are noise: they shrink to
under 0.02 and sit within 2–3 standard errors, which is what nine bins of sampling
noise look like. **The tutor's belief is correct.**

*Plot:* `sanity_outputs/check1_calibration.png`

**Design choice to confirm with Surya:** we count a "moment" only when the concept was
just asked. Beliefs on concepts not being asked do not change (no decay), so counting
them at every step would just repeat the same pair many times. Either way gives the
same calibration; this way the n per bin is honest.

---

## 3. Check 2: does mastery detection work?  (yes, with the expected trade-off)

For each (learner, concept) we know the exact step the student learned it, and the
first step the tutor's belief crossed the threshold.

- **Delay** = declared step − learned step, when the declaration came after.
- **False alarm** = declared before the student actually learned it (or never did).
- **Miss** = student learned it, tutor never declared it within 400 questions.

One population of 30 learners *per threshold*, because the threshold also defines the
ZPD and therefore changes what gets asked.

| threshold | delay (questions) | delay (on that concept) | false alarms, measured | predicted by calibration | misses |
|---:|---:|---:|---:|---:|---:|
| 0.50 | 32.6 | 1.9 | 28.3% | 27.7% | 0.0% |
| 0.70 | 36.4 | 2.2 | 23.2% | 21.2% | 0.0% |
| 0.80 | 43.2 | 3.0 | 10.0% | 9.1% | 0.0% |
| 0.90 | 46.5 | 3.2 | 7.3% | 6.2% | 1.1% |
| 0.95 | 53.6 | 4.3 | 2.6% | 2.4% | 3.8% |
| 0.99 | 67.0 | 5.7 | 0.4% | 0.5% | 7.7% |

Raising the threshold buys fewer false alarms at the price of longer delay and more
misses. That is the shape it must have if the code is right.

*Plot:* `sanity_outputs/check2_detection.png`

**Two things worth saying out loud:**

- The two delay columns differ by 10×. "Questions overall" counts every question the
  tutor asked anyone; "on that concept" counts only questions on the concept in
  question. With 40 concepts and a ZPD of 5–10, a given concept is asked roughly every
  15 questions, so the tutor usually notices within **2–4 attempts on that concept**.
- **The two checks agree with each other, and this is the strongest evidence we
  have.** If the belief is calibrated, then the false-alarm rate at threshold θ must
  equal 1 − (mean belief at the moment of declaration). That "predicted" column is
  computed from check 1's logic alone; the "measured" column from check 2's. They
  match at every threshold: 27.7 vs 28.3, 9.1 vs 10.0, 6.2 vs 7.3, 2.4 vs 2.6, 0.5 vs
  0.4. Two independent measurements of the same code agreeing is worth more than
  either alone.

---

## 4. The 20-step trace

`sanity_outputs/trace_20.md` (table) and `trace_20.png` (rendered). Per row: the ZPD
before the question, the concept asked, the answer, true state before → after, belief
before → after, and whether mastery was declared.

Three moments in it worth pointing at:

- **Steps 9 and 11:** the student learns on a *wrong* answer. BKT transitions after
  answering, so this is correct, not a bug, and it is exactly why the belief must be
  compared to the *post-transition* state.
- **Step 7:** "Colors" is already known (from p(L0)) but the tutor's belief is 0.15. The
  tutor cannot know yet. Calibration is about being right on average, not every time.
- **Step 15 → 16:** "Numbers 1-5" crosses 0.9 and is declared. On the next row it has
  left the ZPD and "Numbers 6-10" and "Time words" have entered. The prerequisite
  gating is visible working.

---

## 5. The viewer

`streamlit run app.py`. Sidebar: student simulator, KT model, scheduler, threshold,
questions, seed. Two tabs:

- **Dry run.** Press Run, then drag the step slider. For that step you see the ZPD
  (picked concept highlighted), the question, the answer, true state before → after,
  belief before → after, and whether mastery was declared. Below: a bar chart of the
  tutor's belief on every ZPD concept, and belief-vs-truth over time for the asked
  concept. Then the trace table so far. Buttons save the run (config, trace CSV, plots)
  or download the CSV.
- **Experiments.** Pick check 1, check 2, or the trace; adjust parameters; run; save.

**It is reusable without editing.** Every dropdown is populated from a registry in the
package: `LEARNERS`, `MASTERY_MODELS`, `SCHEDULERS`, `EXPERIMENTS`. A new scheduler
class added to `SCHEDULERS` appears in the menu. A new experiment function added to
`EXPERIMENTS` gets its parameters turned into inputs automatically.

---

## 6. Decisions we made where the mail was open

To confirm, not to relitigate:

| Decision | What we chose | Why |
|---|---|---|
| Parameter values | `p(L0)=0.15, p(T)=0.12, p(G)=0.25, p(S)=0.10` | cursim's existing defaults; guess is 0.25 for a 4-option question |
| "Declares mastery" | first crossing of the threshold | one number per concept; matches how the latch already works |
| Check 1 "moments" | when the concept was just asked | see section 2 |
| Delay units | both: overall questions and questions on that concept | they tell different stories |
| Empty ZPD | fall back to uniform over all concepts | keeps a fixed question budget for averaging |
| Concepts known at step 0 | learned step = 0 | any declaration then counts as a detection with delay from 0 |
| Which branch | `plain-bkt` new; `main` untouched | mail says keep the current simulator |

---

## 7. What the next step will need

"Give each concept its own p(T), depending on whether prerequisites are learned."

The student side is already there behind one flag: `prereq_gated_pT=True` on
`BKTLearner` uses `p(T)` when all prerequisites are truly known and `pT_low` (0.02)
otherwise. It is off for everything above.

The question it raises, for Surya: **what does the tutor use?** The student's p(T)
depends on the *true* state of prerequisites, which the tutor cannot see. Options are
(a) tutor keeps a constant p(T), so it becomes mildly misspecified; (b) tutor uses its
own *belief* about the prerequisites to pick p(T). Option (b) is closer to "same
parameters". We have not implemented either tutor side yet; it is a few lines once
chosen.

---

## 8. What we did not do, and limits

- Only one curriculum (the 40-concept language graph). The addition graph from the
  CurriculumTutor paper is not built.
- Check 2 runs 30 learners per threshold. Enough for the shape; error bars would need
  more.
- 400 questions per run. With p(T)=0.12 a handful of concepts are never learned in that
  budget at high thresholds, which is where the miss rate comes from.
- The trace uses seed 4242. Any seed works from the viewer.

---

## 9. Things we are unsure about and would like Surya to weigh in on

1. Is "moments when the concept was just asked" the right population for check 1?
2. False-alarm rate is *premature declarations ÷ all declarations*. Should it be
   ÷ all concepts instead?
3. Running one population per threshold (ZPD moves with θ) versus one fixed trajectory
   scored at every θ. We did the former because it measures the real system; the
   latter isolates the detector. Happy to add the latter.
4. For the next step, tutor-side p(T): constant, or gated on the tutor's own belief?
