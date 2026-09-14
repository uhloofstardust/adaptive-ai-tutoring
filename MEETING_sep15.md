# Points for Tuesday's meeting with Surya

Branch: `plain-bkt` on `uhloofstardust/adaptive-ai-tutoring`. `main` is untouched.

Everything below runs from three commands:

```
streamlit run app.py        # the viewer
python3 make_sanity.py      # every plot and table below -> sanity_outputs/
python3 test_sanity.py      # 21 checks; the original 55 still pass too
```

---

## 1. What we built, in one paragraph

A student who *is* a BKT process: each concept is a coin, known or not, with the four
standard parameters. No forgetting, no difficulty, no prerequisite effect. The tutor is
the BKT belief we already had, reading the **same four numbers from the same file**
(`cursim/params.py`), so "same parameters" is enforced by the code rather than by
memory. The scheduler is uniform random over the ZPD, no bandit (registered as
`uniform_zpd`). On top of that: both checks from the mail, the 20-step trace, and a
viewer where you can watch a single run one question at a time.

---

## 2. Check 1: is the belief calibrated?  (yes)

Every time the tutor updates a belief we record (belief, true state) for that concept,
then bin by belief. Both values are read at the same instant: after the tutor's update
and after the student's transition, i.e. the state going into the next question.

100 learners × 400 questions = 40,000 pairs. All nine populated bins:

| tutor believes | student truly knows | gap | 95% CI | n |
|---:|---:|---:|---:|---:|
| 0.143 | 0.147 | +0.004 | ±0.006 | 15,305 |
| 0.214 | 0.212 | −0.002 | ±0.013 | 3,762 |
| 0.383 | 0.344 | −0.038 | ±0.034 | 755 |
| 0.449 | 0.443 | −0.006 | ±0.012 | 7,046 |
| 0.549 | 0.522 | −0.027 | ±0.024 | 1,704 |
| 0.666 | 0.617 | −0.050 | ±0.069 | 193 |
| 0.772 | 0.756 | −0.016 | ±0.013 | 4,224 |
| 0.841 | 0.836 | −0.005 | ±0.022 | 1,107 |
| 0.953 | 0.950 | −0.003 | ±0.006 | 5,904 |

Overall: mean belief 0.433, fraction truly known 0.429.

Honest reading: all gaps are under 0.05, most are within their CI, and three sit just
outside it on the low side. To see whether that is noise we reran at 400 learners
(160,000 pairs, committed as `check1_calibration_400learners.csv`): every gap shrinks
to under 0.02 and the overall numbers are 0.434 vs 0.433. The sign of the small
mid-bin gaps also flips across seeds. **The tutor's belief is correct.**

One caveat on the CIs: successive pairs on the same concept are dependent (the belief
after one ask is the belief before the next), so the per-bin CIs are nominal. The
overall comparison (0.433 vs 0.429) does not have that problem and is the robust one.

*Plots:* `sanity_outputs/check1_calibration.png`, `check1_calibration_400learners.png`

**Design choice to confirm:** we count a "moment" only when the concept was just asked.
Beliefs on concepts not being asked do not change (no decay), so counting them every
step would repeat the same pair many times.

---

## 3. Check 2: does mastery detection work?  (yes, with the expected trade-off)

For each (learner, concept) we know the exact step the student learned it, and the
first step the tutor's belief crossed the threshold.

- **Delay, on that concept** = questions asked *on that concept* between the true
  learning step and the declaration. This is the headline: it is what the detector
  actually sees.
- **Delay, overall** = questions asked *to anyone* in that window. Reported only for
  concepts learned *during* the run. For concepts the student knew before question 1
  this number would measure how long the ZPD took to reach them, which is a curriculum
  property, not detection. (A first draft of these notes mixed the two; the mixed
  figure was up to 3× too high.)
- **False alarm** = a declaration made before the student had learned it. Reported as a
  share of all declarations, which is the tutor-user's question: when it says
  "mastered", how often is it wrong?

One population of 30 learners *per threshold*, because the threshold also defines the
ZPD and therefore changes what gets asked.

| threshold | delay on concept | delay overall | false alarms, measured | predicted by calibration | of those, never learned | unresolved at end |
|---:|---:|---:|---:|---:|---:|---:|
| 0.50 | 1.9 | 10.7 | 28.3% | 27.7% | 137 / 340 | 0 |
| 0.60 | 2.2 | 13.0 | 22.9% | 21.4% | 105 / 275 | 0 |
| 0.70 | 2.2 | 13.3 | 23.2% | 21.2% | 116 / 278 | 0 |
| 0.80 | 3.0 | 17.8 | 10.0% | 9.1% | 78 / 119 | 0 |
| 0.90 | 3.2 | 20.4 | 7.3% | 6.2% | 67 / 84 | 12 |
| 0.95 | 4.3 | 28.6 | 2.6% | 2.4% | 27 / 28 | 42 |
| 0.99 | 5.7 | 42.1 | 0.4% | 0.5% | 4 / 4 | 80 |

Raising the threshold buys fewer false alarms at the price of longer delay. That is the
shape it must have if the code is right.

*Plot:* `sanity_outputs/check2_detection.png`

**Four things worth saying out loud:**

- **The two checks agree, and this is the strongest evidence we have.** If the belief
  is calibrated, the false-alarm rate at any threshold must equal 1 − (mean belief at
  the moment of declaration). The "predicted" column is that quantity; the "measured"
  column counts actual premature declarations. They match at every threshold. To be
  precise about what this is: the same trajectories scored two ways, not two
  independent experiments. It is still a strong internal-consistency check that a
  buggy update would fail.
- **Thresholds 0.6 and 0.7 are the same operating point.** With these parameters the
  belief after consecutive correct answers goes 0.15 → 0.46 → 0.79 → 0.94, so any
  threshold between 0.46 and 0.79 is crossed on the same answer. The effective
  threshold is the belief at declaration, which is why we report it.
- **A false alarm is permanent under this scheduler.** Once declared, the concept
  leaves the ZPD and is never asked again; the student can only learn on an ask. So
  the "never learned" column: at θ = 0.9, 67 of the 84 false alarms are concepts the
  student *never* learns in 400 questions. This is a real property of ZPD gating with
  no review step, and worth a sentence in any write-up. A review rule would fix it and
  is a natural scheduler variant later.
- **"Unresolved at end" is not a miss rate.** We decomposed every one: at 0.99, the 80
  are 47 learned in the last 50 questions (no time to detect) + 28 known from the
  start but never reached by the ZPD + 5 asked but not yet over the bar. A 400-question
  run simply ends. The mail did not ask for a miss rate and we are not claiming one.

---

## 4. The 20-step trace

`sanity_outputs/trace_20.md` (table) and `trace_20.png` (rendered). Per row: the ZPD
before the question, the concept asked, the answer, true state before → after, belief
before → after, and whether mastery was declared.

Three moments worth pointing at:

- **Steps 9 and 11:** the student learns on a *wrong* answer. BKT transitions after
  answering, so this is correct, and it is exactly why the belief must be compared to
  the *post-transition* state.
- **Step 7:** "Colors" is already known (from p(L0)) but the tutor believes 0.15. It
  cannot know yet. Calibration is about being right on average, not every time.
- **Step 15 → 16:** "Numbers 1-5" crosses 0.9 and is declared. On the next row it has
  left the ZPD and "Numbers 6-10" and "Time words" have entered. Prerequisite gating,
  visibly working.

---

## 5. The viewer

`streamlit run app.py`. Sidebar: student simulator, KT model, scheduler, threshold,
questions, seed. Two tabs:

- **Dry run.** Press Run, then drag the step slider. For that step: the ZPD (picked
  concept highlighted), the question, the answer, true state before → after, belief
  before → after, declared or not. Below: the tutor's belief on every ZPD concept, and
  belief-vs-truth over time for the asked concept. Then the trace table so far. Save
  the run (config incl. the BKT parameters, trace CSV, plots) or download the CSV. If
  you change a setting without pressing Run, it says so and disables saving, so a
  saved bundle always matches the run it came from.
- **Experiments.** Pick check 1, check 2, or the trace; adjust parameters; run; save.
  All three honour the sidebar's student / model / scheduler.

**It is reusable without editing.** Every dropdown is populated from a registry in the
package: `LEARNERS`, `MASTERY_MODELS`, `SCHEDULERS`, `EXPERIMENTS`. A new scheduler
class added to `SCHEDULERS` appears in the menu; a new experiment function added to
`EXPERIMENTS` gets its parameters turned into inputs.

---

## 6. Decisions we made where the mail was open

To confirm, not to relitigate:

| Decision | What we chose | Why |
|---|---|---|
| Parameter values | `p(L0)=0.15, p(T)=0.12, p(G)=0.25, p(S)=0.10` | cursim's defaults; guess 0.25 for a 4-option question |
| "Uniformly at random from the ZPD" | uniform over ZPD *concepts*, then uniform over that concept's questions | concepts are the unit the ZPD is defined on |
| "Declares mastery" | first crossing of the threshold; a premature crossing counts even if belief later drops back | one number per concept; matches the latch |
| Check 1 "moments" | when the concept was just asked | see section 2 |
| Delay, overall | only for concepts learned during the run | see section 3 |
| False-alarm rate | premature ÷ all declarations | the tutor-user's question |
| Empty ZPD | fall back to uniform over all concepts | keeps a fixed question budget |
| Concepts known at step 0 | learned step = 0; count toward on-concept delay and false alarms, not overall delay | see section 3 |
| Which branch | `plain-bkt` new; `main` untouched | mail says keep the current simulator |

---

## 7. What the next step will need

"Give each concept its own p(T), depending on whether prerequisites are learned."

The student side is already there behind one flag: `prereq_gated_pT=True` on
`BKTLearner` uses `p(T)` when all prerequisites are truly known and `pT_low` (0.02)
otherwise. Off for everything above; the checkbox is in the sidebar.

The question it raises: **what does the tutor use?** The student's p(T) depends on the
*true* state of prerequisites, which the tutor cannot see. Options: (a) tutor keeps a
constant p(T), so it becomes mildly misspecified; (b) tutor picks p(T) from its own
*belief* about the prerequisites. (b) is closer to "same parameters". Neither tutor
side is implemented yet; it is a few lines once chosen.

---

## 8. What we did not do, and limits

- One curriculum (the 40-concept language graph). The addition graph from the
  CurriculumTutor paper is not built.
- Check 2 uses 30 learners per threshold. Enough for the shape; not for error bars.
- 400 questions per run, which is where "unresolved at end" comes from.
- The `binary` and `bkt_forget` tutors in the dropdown use their own parameters
  (`binary` has p(T)=0.06); the sidebar says so when you pick them. The mail's checks
  are for `bkt` / `bkt`.

---

## 9. Questions for Surya

1. Is "moments when the concept was just asked" the right population for check 1?
2. False-alarm rate is premature ÷ all declarations. Would you rather see it ÷ all
   concepts, or ÷ concepts not known at the start?
3. One population per threshold (ZPD moves with θ) versus one fixed trajectory scored
   at every θ. We did the former because it measures the real system. Happy to add the
   latter; in on-concept units they should agree.
4. For the next step: tutor-side p(T), constant or gated on the tutor's own belief?
5. Is the "permanent false alarm" property (section 3) something you want addressed
   now with a review rule, or noted and left for the scheduler work?

---

*Revision note.* A first draft of these notes reported an overall delay that mixed in
concepts known before the run, showed 7 of the 9 calibration bins, and labelled
horizon censoring as a "miss rate". All three were caught in an independent review pass
before this version and are corrected above; the underlying code was right, the
reporting was not.
