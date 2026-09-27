# Sanity check summary

Shared BKT parameters: `{'p_L0': 0.15, 'p_T': 0.12, 'p_G': 0.25, 'p_S': 0.1}`

**Check 1.** 12000 (belief, truth) pairs from 100 learners x 120 questions. Overall: mean belief 0.6085, fraction truly known 0.6205. Largest per-bin gap with n>=20: 0.059. Note: successive pairs on one concept are dependent, so per-bin CIs are nominal; the overall comparison is the robust one.

Noise check at 4x the learners: 48000 (belief, truth) pairs from 400 learners x 120 questions. Overall: mean belief 0.5982, fraction truly known 0.6029. Largest per-bin gap with n>=20: 0.032. Note: successive pairs on one concept are dependent, so per-bin CIs are nominal; the overall comparison is the robust one.

| belief (bin mean) | truly known | gap | n |
|---:|---:|---:|---:|
| 0.143 | 0.151 | +0.008 | 3104 |
| 0.215 | 0.250 | +0.034 | 757 |
| 0.378 | 0.437 | +0.059 | 190 |
| 0.448 | 0.468 | +0.020 | 1433 |
| 0.550 | 0.601 | +0.051 | 351 |
| 0.668 | 0.702 | +0.034 | 104 |
| 0.769 | 0.775 | +0.005 | 932 |
| 0.848 | 0.893 | +0.044 | 298 |
| 0.983 | 0.986 | +0.003 | 4831 |

**Check 2.** Threshold 0.5: 1.9 questions on the concept until declared, false alarms 28.7%. Threshold 0.99: 5.7 questions, false alarms 0.4%. 'Unresolved' counts concepts learned but not declared by the end of the 120-question run; every one is either learned in the last 50 questions or never reached by the ZPD, i.e. a horizon effect, not a detector failure.

| threshold | questions on that concept until declared | questions overall (concepts learned during the run) | false alarms, measured | predicted by calibration | of which never learned | unresolved at end (late / unreached / other) |
|---:|---:|---:|---:|---:|---:|---:|
| 0.50 | 1.9 | 3.0 | 28.7% | 28.0% | 9/69 | 0 (0 / 0 / 0) |
| 0.60 | 2.1 | 3.4 | 19.2% | 21.5% | 3/46 | 0 (0 / 0 / 0) |
| 0.70 | 2.2 | 3.4 | 19.2% | 21.1% | 3/46 | 0 (0 / 0 / 0) |
| 0.80 | 3.0 | 4.9 | 11.2% | 9.1% | 6/27 | 0 (0 / 0 / 0) |
| 0.90 | 3.4 | 5.2 | 7.1% | 6.1% | 2/17 | 0 (0 / 0 / 0) |
| 0.95 | 4.1 | 7.0 | 3.3% | 2.5% | 2/8 | 0 (0 / 0 / 0) |
| 0.99 | 5.7 | 10.1 | 0.4% | 0.5% | 0/1 | 4 (3 / 1 / 0) |

- 'Questions overall' is reported only for concepts learned during the run. For concepts known before question 1 it would measure how long the ZPD took to reach them, which is a curriculum property, not detection.
- 'Predicted by calibration' is 1 minus the mean belief at the moment of declaration; if check 1 holds it must match the measured false-alarm rate.
- 'Of which never learned': a falsely declared concept leaves the ZPD and is never asked again, so the student never gets the chance to learn it.
- 'Unresolved': learned but not declared when the run ended. Every one is either learned in the last 50 questions or never reached by the ZPD.

**Trace.** 20 questions, seed 4242, threshold 0.9. The student learned 1 concept(s) during these steps. See `trace_20.md` and `trace_20.png`.
