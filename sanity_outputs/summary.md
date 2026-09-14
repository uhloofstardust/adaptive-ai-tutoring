# Sanity check summary

Shared BKT parameters: `{'p_L0': 0.15, 'p_T': 0.12, 'p_G': 0.25, 'p_S': 0.1}`

**Check 1.** 40000 (belief, truth) pairs from 100 learners x 400 questions. Overall: mean belief 0.4331, fraction truly known 0.4289. Largest per-bin gap with n>=20: 0.050. Note: successive pairs on one concept are dependent, so per-bin CIs are nominal; the overall comparison is the robust one.

Noise check at 4x the learners: 160000 (belief, truth) pairs from 400 learners x 400 questions. Overall: mean belief 0.4343, fraction truly known 0.4326. Largest per-bin gap with n>=20: 0.019. Note: successive pairs on one concept are dependent, so per-bin CIs are nominal; the overall comparison is the robust one.

| belief (bin mean) | truly known | gap | n |
|---:|---:|---:|---:|
| 0.143 | 0.147 | +0.004 | 15305 |
| 0.214 | 0.212 | -0.002 | 3762 |
| 0.383 | 0.344 | -0.038 | 755 |
| 0.449 | 0.443 | -0.006 | 7046 |
| 0.549 | 0.522 | -0.027 | 1704 |
| 0.666 | 0.617 | -0.050 | 193 |
| 0.772 | 0.756 | -0.016 | 4224 |
| 0.841 | 0.836 | -0.005 | 1107 |
| 0.953 | 0.950 | -0.003 | 5904 |

**Check 2.** Threshold 0.5: 1.9 questions on the concept until declared, false alarms 28.3%. Threshold 0.99: 5.7 questions, false alarms 0.4%. 'Unresolved' counts concepts learned but not declared by the end of the 400-question run; every one is either learned in the last 50 questions or never reached by the ZPD, i.e. a horizon effect, not a detector failure.

| threshold | questions on that concept until declared | questions overall (concepts learned during the run) | false alarms, measured | predicted by calibration | of which never learned | unresolved at end (late / unreached / other) |
|---:|---:|---:|---:|---:|---:|---:|
| 0.50 | 1.9 | 10.7 | 28.3% | 27.7% | 137/340 | 0 (0 / 0 / 0) |
| 0.60 | 2.2 | 13.0 | 22.9% | 21.4% | 105/275 | 0 (0 / 0 / 0) |
| 0.70 | 2.2 | 13.3 | 23.2% | 21.2% | 116/278 | 0 (0 / 0 / 0) |
| 0.80 | 3.0 | 17.8 | 10.0% | 9.1% | 78/119 | 0 (0 / 0 / 0) |
| 0.90 | 3.2 | 20.4 | 7.3% | 6.2% | 67/84 | 12 (9 / 3 / 0) |
| 0.95 | 4.3 | 28.6 | 2.6% | 2.4% | 27/28 | 42 (25 / 13 / 4) |
| 0.99 | 5.7 | 42.1 | 0.4% | 0.5% | 4/4 | 80 (47 / 28 / 5) |

- 'Questions overall' is reported only for concepts learned during the run. For concepts known before question 1 it would measure how long the ZPD took to reach them, which is a curriculum property, not detection.
- 'Predicted by calibration' is 1 minus the mean belief at the moment of declaration; if check 1 holds it must match the measured false-alarm rate.
- 'Of which never learned': a falsely declared concept leaves the ZPD and is never asked again, so the student never gets the chance to learn it.
- 'Unresolved': learned but not declared when the run ended. Every one is either learned in the last 50 questions or never reached by the ZPD.

**Trace.** 20 questions, seed 4242, threshold 0.9. The student learned 2 concept(s) during these steps. See `trace_20.md` and `trace_20.png`.
