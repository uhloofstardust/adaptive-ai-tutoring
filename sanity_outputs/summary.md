# Sanity check summary

Shared BKT parameters: `{'p_L0': 0.15, 'p_T': 0.12, 'p_G': 0.25, 'p_S': 0.1}`

**Check 1.** 40000 (belief, truth) pairs from 100 learners x 400 questions. Largest gap from the diagonal in any bin with n>=20: 0.050.

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

**Check 2.** Threshold 0.5: mean delay 32.6 questions, false alarms 28.3%. Threshold 0.99: delay 67.0, false alarms 0.4%.

| threshold | delay (questions) | delay (on that concept) | false alarms, measured | predicted by calibration | miss rate | declared |
|---:|---:|---:|---:|---:|---:|---:|
| 0.50 | 32.6 | 1.9 | 28.3% | 27.7% | 0.0% | 1200/1200 |
| 0.60 | 36.2 | 2.2 | 22.9% | 21.4% | 0.0% | 1200/1200 |
| 0.70 | 36.4 | 2.2 | 23.2% | 21.2% | 0.0% | 1200/1200 |
| 0.80 | 43.2 | 3.0 | 10.0% | 9.1% | 0.0% | 1195/1200 |
| 0.90 | 46.5 | 3.2 | 7.3% | 6.2% | 1.1% | 1152/1200 |
| 0.95 | 53.6 | 4.3 | 2.6% | 2.4% | 3.8% | 1084/1200 |
| 0.99 | 67.0 | 5.7 | 0.4% | 0.5% | 7.7% | 960/1200 |

'Predicted by calibration' is 1 minus the mean belief at the moment of declaration. If check 1 holds, it must match the measured false-alarm rate. It does, at every threshold.

**Trace.** 20 questions, seed 4242, threshold 0.9. The student learned 2 concept(s) during these steps. See `trace_20.md` and `trace_20.png`.
