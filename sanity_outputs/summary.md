# Sanity check summary

Shared BKT parameters: `{'p_L0': 0.15, 'p_T': 0.2, 'p_G': 0.25, 'p_S': 0.1}`

**Check 1.** 12000 (belief, truth) pairs from 100 learners x 120 questions. Overall: mean belief 0.7713, fraction truly known 0.7728. Largest per-bin gap with n>=20: 0.047. Note: successive pairs on one concept are dependent, so per-bin CIs are nominal; the overall comparison is the robust one.

Noise check at 4x the learners: 48000 (belief, truth) pairs from 400 learners x 120 questions. Overall: mean belief 0.7769, fraction truly known 0.7787. Largest per-bin gap with n>=20: 0.029. Note: successive pairs on one concept are dependent, so per-bin CIs are nominal; the overall comparison is the robust one.

| belief (bin mean) | truly known | gap | n |
|---:|---:|---:|---:|
| 0.235 | 0.233 | -0.001 | 2131 |
| 0.341 | 0.388 | +0.047 | 394 |
| 0.423 | 0.429 | +0.005 | 70 |
| 0.529 | 0.522 | -0.007 | 452 |
| 0.622 | 0.625 | +0.003 | 928 |
| 0.732 | 0.747 | +0.015 | 233 |
| 0.865 | 0.863 | -0.002 | 942 |
| 0.991 | 0.991 | +0.000 | 6850 |

**Check 2.** Threshold 0.5: 0.9 questions on the concept until declared, false alarms 42.9%. Threshold 0.99: 4.5 questions, false alarms 0.8%. 'Unresolved' counts concepts learned but not declared by the end of the 120-question run; every one is either learned in the last 50 questions or never reached by the ZPD, i.e. a horizon effect, not a detector failure.

| threshold | questions on that concept until declared | questions overall (concepts learned during the run) | false alarms, measured | predicted by calibration | of which never learned | unresolved at end (late / unreached / other) |
|---:|---:|---:|---:|---:|---:|---:|
| 0.50 | 0.9 | 1.5 | 42.9% | 42.7% | 1/103 | 0 (0 / 0 / 0) |
| 0.60 | 1.2 | 1.5 | 31.7% | 34.3% | 1/76 | 0 (0 / 0 / 0) |
| 0.70 | 1.9 | 3.1 | 17.1% | 15.5% | 0/41 | 0 (0 / 0 / 0) |
| 0.80 | 2.1 | 3.6 | 14.6% | 12.1% | 0/35 | 0 (0 / 0 / 0) |
| 0.90 | 3.1 | 5.1 | 6.7% | 4.3% | 0/16 | 0 (0 / 0 / 0) |
| 0.95 | 3.3 | 5.4 | 2.9% | 2.9% | 0/7 | 0 (0 / 0 / 0) |
| 0.99 | 4.5 | 7.9 | 0.8% | 0.7% | 0/2 | 0 (0 / 0 / 0) |

- 'Questions overall' is reported only for concepts learned during the run. For concepts known before question 1 it would measure how long the ZPD took to reach them, which is a curriculum property, not detection.
- 'Predicted by calibration' is 1 minus the mean belief at the moment of declaration; if check 1 holds it must match the measured false-alarm rate.
- 'Of which never learned': a falsely declared concept leaves the ZPD and is never asked again, so the student never gets the chance to learn it.
- 'Unresolved': learned but not declared when the run ended. Every one is either learned in the last 50 questions or never reached by the ZPD.

**Trace.** 20 questions, seed 4242, threshold 0.9. The student learned 3 concept(s) during these steps. See `trace_20.md` and `trace_20.png`.

## The 2x2: does the question-selection rule matter?

400 learners x 40 questions on abstract, 8 concepts. S1: Q2 minus Q1 = -0.15 [-0.29, -0.01] (favours Q1). S2: +1.47 [+1.29, +1.64] (favours Q2). Interaction +1.62 [+1.45, +1.78]: the sign of the scheduler effect flips with the student model. Note the budget matters: at a budget long enough for everything to be learned anyway, every cell saturates and no scheduler can differ.

| student | scheduler | concepts truly known | asked outside the ZPD |
|---|---|---:|---:|
| S1 | Q1 | 6.15 / 8 | 26.0 |
| S1 | Q2 | 6.00 / 8 | 0.0 |
| S2 | Q1 | 4.39 / 8 | 27.6 |
| S2 | Q2 | 5.86 / 8 | 0.0 |

| contrast | Q2 minus Q1 | 95% CI | favours |
|---|---:|---:|---|
| S1 | -0.15 | +/-0.14 | Q1 |
| S2 | +1.47 | +/-0.18 | Q2 |
| interaction (S2 minus S1) | +1.62 | +/-0.16 | - |

### The restriction alone

Both arms gate on the student's true state, so only the prerequisite restriction differs. S1: +0.000 +/-0.000. S2: +1.968 +/-0.167. The restriction itself is worth nothing to a student whose learning does not depend on prerequisites, and a lot to one whose does. Any effect the real Q1/Q2 pair shows for S1 is therefore the cost of gating on a belief that lags the truth, not the cost of the restriction.

| student | unrestricted | restricted | restriction effect | 95% CI |
|---|---:|---:|---:|---:|
| S1 | 7.480 | 7.480 | +0.000 | +/-0.000 |
| S2 | 5.513 | 7.480 | +1.968 | +/-0.167 |

### At a longer budget

400 learners x 120 questions on abstract, 8 concepts. S1: Q2 minus Q1 = -0.00 [-0.02, +0.01] (favours neither). S2: +0.21 [+0.12, +0.31] (favours Q2). Interaction +0.21 [+0.12, +0.31]: the size, not the sign, of the scheduler effect depends on the student (S1 favours neither, S2 favours Q2). Note the budget matters: at a budget long enough for everything to be learned anyway, every cell saturates and no scheduler can differ.

| student | scheduler | concepts truly known |
|---|---|---:|
| S1 | Q1 | 7.99 / 8 |
| S1 | Q2 | 7.99 / 8 |
| S2 | Q1 | 7.68 / 8 |
| S2 | Q2 | 7.90 / 8 |

## Concepts mastered over time

400 learners per cell, 300 questions, paired by shared seed and shared initial known-set. S1 reaches all 8 after a median 54 questions under Q1 and 54 under Q2; paired MEAN difference +0.3 +/-2.3, paired MEDIAN difference +0.0 (unresolved at this n); S2 reaches all 8 after a median 78 questions under Q1 and 55 under Q2; paired MEAN difference -22.4 +/-4.3, paired MEDIAN difference -17.5 (Q2). Every arm gets every learner to all 8 concepts inside 300 questions, at a median of 54 (S1/Q1) to 78 (S2/Q1). Every arm asks the same fixed number of questions, so a difference here is time to latent mastery, not effort saved. The mean and median paired differences are both given because they are not interchangeable, and an interval covering zero means this run cannot resolve the sign, not that the effect is zero: the S1 contrast is a small cost to Q2 that needs far more learners than this to separate, and two_by_two and restriction_only are the places it shows up.

| student | scheduler | known after the budget | reached all | median questions to all | never finished |
|---|---|---:|---:|---:|---:|
| S1 | Q1 | 8.00 / 8 | 100% | 54 | 0/400 |
| S1 | Q2 | 8.00 / 8 | 100% | 54 | 0/400 |
| S2 | Q1 | 8.00 / 8 | 100% | 78 | 0/400 |
| S2 | Q2 | 8.00 / 8 | 100% | 55 | 0/400 |

| student | Q2 minus Q1, questions to full mastery | 95% CI | faster with Q2 | favours |
|---|---:|---:|---:|---|
| S1 | +0.3 | +/-2.3 | 191/400 | unresolved at this n |
| S2 | -22.4 | +/-4.3 | 297/400 | Q2 |

Seed i is the same learner in both arms, so these are paired differences rather than two independent estimates.

## What should the tutor assume?

600 learners per cell, 120 questions, the same students in every arm so the arms are paired. p_S at spread +/-0.15: best fixed tutor (p_S=0.10) scores Brier 0.0854, the oracle 0.0835, so knowing every student's own p_S buys 0.0019 +/-0.0013 of per-pair error; p_G at spread +/-0.15: best fixed tutor (p_G=0.25) scores Brier 0.0829, the oracle 0.0828, so knowing every student's own p_G changes per-pair error by +0.0001, inside the +/-0.0020 this run can resolve. Scored on the Brier score, which is proper and so is minimised by the true probability. The pooled signed gap cancels per-student over- and underconfidence, exactly the error adapting removes, and mean |belief - truth| is improper and rewards a pessimistic tutor early in a run; both are kept as diagnostics only. The oracle is an upper bound, not a proposal: no tutor can see a student's parameters. An interval covering zero here means this run could not resolve a difference of that size, which is not the same as showing there is none; no equivalence margin was set in advance.

| students vary in | spread | best fixed tutor | its Brier | oracle Brier | oracle buys | 95% CI | resolved? |
|---|---:|---:|---:|---:|---:|---:|---|
| p_S | +/-0.05 | 0.10 | 0.0835 | 0.0834 | +0.0002 | +/-0.0005 | no |
| p_S | +/-0.10 | 0.10 | 0.0836 | 0.0834 | +0.0002 | +/-0.0013 | no |
| p_S | +/-0.15 | 0.10 | 0.0854 | 0.0835 | +0.0019 | +/-0.0013 | yes |
| p_G | +/-0.05 | 0.25 | 0.0826 | 0.0832 | -0.0006 | +/-0.0016 | no |
| p_G | +/-0.10 | 0.25 | 0.0824 | 0.0835 | -0.0011 | +/-0.0018 | no |
| p_G | +/-0.15 | 0.25 | 0.0829 | 0.0828 | +0.0001 | +/-0.0020 | no |

Brier is mean (belief - truth)^2 per pair, a proper scoring rule, so it is minimised by the true probability and it does recover the true parameter at 40, 120 and 300 questions alike. Two other scores are in the CSV and are NOT used: the pooled signed calibration gap cancels per-student over- and underconfidence, which under a symmetric spread is exactly the error adapting removes; and mean |belief - truth| is improper, minimised by the median, so at 40 questions it prefers a tutor assuming p_S=0.02 to the true 0.10. The best fixed value is chosen by minimising Brier on the same run that reports it, so it is optimistic; the CSV also carries the tutor sitting at the true centre. The interval is a paired bootstrap on the DIFFERENCE between two arms that share their learners; each arm's own marginal interval (ci95_marginal) is much wider and answers a different question. 'Resolved' means the difference is larger than the interval. A difference inside the interval means this run could not resolve one of that size, not that there is none: no equivalence margin was set in advance.

## Does the contrast hold across independent samples?

6 independent blocks of 400 learners, 300 questions. S1: +0.37 +/-0.57 across 6 blocks (a cost to Q2), individual blocks from -0.93 to +1.08, sign the same in all blocks: no; S2: -23.08 +/-1.36 across 6 blocks (Q2 sooner), individual blocks from -25.61 to -20.66, sign the same in all blocks: yes. A sign that holds in every block is evidence a single block's interval cannot give.

## Parameter sweep

19 cells, 30 learners each, all sharing one seed block. Every cell here is correctly specified (student and tutor get the same values), so the pooled gap measures estimator noise, not calibration: it stays within 0.011 everywhere, which says the estimator is unbiased across parameter settings rather than that the tutor is calibrated. Range of the false-alarm rate across each grid: p_G 0.092, p_T 0.082, p_S 0.046, p_L0 0.025. Range of the on-concept delay: p_T 2.45, p_G 1.64, p_S 0.78, p_L0 0.71. So p_G is the strongest lever on both, and the effects do not separate cleanly by metric.

## Tutor / student mismatch

(a) One student, 200 learners, the tutor's assumption swept one parameter at a time. p_G: gap +0.002 +/-0.006 when the tutor is right, -0.063 +/-0.008 at its worst (p_G=0.05, error -0.20); p_S: gap +0.002 +/-0.006 when the tutor is right, -0.037 +/-0.008 at its worst (p_S=0.3, error +0.20); p_T: gap +0.002 +/-0.006 when the tutor is right, +0.133 +/-0.005 at its worst (p_T=0.05, error -0.15). (b) A population with spread +/-0.15 against one fixed tutor: gap -0.017 +/-0.014, false alarms 7.5% against 4.6% when every student matches the tutor exactly. The spread rows share a seed block, so they are a paired trend rather than four independent estimates.

| parameter | tutor's value | error | calibration gap | false alarms | delay |
|---|---:|---:|---:|---:|---:|
| p_G | 0.05 | -0.20 | -0.063 | 17.1% | 1.8 |
| p_G | 0.15 | -0.10 | -0.025 | 12.4% | 2.1 |
| p_G | 0.25 | +0.00 | +0.002 | 4.6% | 3.1 |
| p_G | 0.35 | +0.10 | +0.023 | 2.9% | 3.3 |
| p_G | 0.45 | +0.20 | +0.049 | 1.2% | 4.3 |
| p_S | 0.02 | -0.08 | +0.029 | 2.9% | 3.3 |
| p_S | 0.05 | -0.05 | +0.015 | 4.4% | 3.1 |
| p_S | 0.10 | +0.00 | +0.002 | 4.6% | 3.1 |
| p_S | 0.20 | +0.10 | -0.023 | 6.4% | 2.9 |
| p_S | 0.30 | +0.20 | -0.037 | 7.0% | 2.8 |
| p_T | 0.05 | -0.15 | +0.133 | 1.3% | 4.3 |
| p_T | 0.10 | -0.10 | +0.073 | 2.9% | 3.4 |
| p_T | 0.20 | +0.00 | +0.002 | 4.6% | 3.1 |
| p_T | 0.30 | +0.10 | -0.053 | 10.6% | 2.3 |
| p_T | 0.40 | +0.20 | -0.094 | 15.6% | 1.9 |

| population spread | calibration gap | false alarms | delay |
|---:|---:|---:|---:|
| +/-0.00 | +0.002 | 4.6% | 3.1 |
| +/-0.05 | +0.001 | 4.1% | 3.1 |
| +/-0.10 | -0.008 | 5.8% | 3.1 |
| +/-0.15 | -0.017 | 7.5% | 3.1 |
