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

## Parameter sweep

19 cells, 30 learners each, all sharing one seed block. Every cell here is correctly specified (student and tutor get the same values), so the pooled gap measures estimator noise, not calibration: it stays within 0.011 everywhere, which says the estimator is unbiased across parameter settings rather than that the tutor is calibrated. Range of the false-alarm rate across each grid: p_G 0.092, p_T 0.082, p_S 0.046, p_L0 0.025. Range of the on-concept delay: p_T 2.45, p_G 1.64, p_S 0.78, p_L0 0.71. So p_G is the strongest lever on both, and the effects do not separate cleanly by metric.

## Tutor / student mismatch

(a) One student, tutor's p_G swept, 200 learners: the pooled gap is +0.002 +/-0.006 when the tutor is right and -0.063 +/-0.008 at its worst (p_G=0.05, error -0.20). (b) A population with spread +/-0.15 against one fixed tutor: gap -0.017 +/-0.014, false alarms 7.5% against 4.6% when every student matches the tutor exactly. The spread rows share a seed block, so they are a paired trend rather than four independent estimates.

| tutor's p_G | error | calibration gap | false alarms | delay |
|---:|---:|---:|---:|---:|
| 0.05 | -0.20 | -0.063 | 17.1% | 1.8 |
| 0.15 | -0.10 | -0.025 | 12.4% | 2.1 |
| 0.25 | +0.00 | +0.002 | 4.6% | 3.1 |
| 0.35 | +0.10 | +0.023 | 2.9% | 3.3 |
| 0.45 | +0.20 | +0.049 | 1.2% | 4.3 |

| population spread | calibration gap | false alarms | delay |
|---:|---:|---:|---:|
| +/-0.00 | +0.002 | 4.6% | 3.1 |
| +/-0.05 | +0.001 | 4.1% | 3.1 |
| +/-0.10 | -0.008 | 5.8% | 3.1 |
| +/-0.15 | -0.017 | 7.5% | 3.1 |
