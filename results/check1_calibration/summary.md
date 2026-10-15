# check1_calibration

12000 (belief, truth) pairs from 100 learners x 120 questions. Overall: mean belief 0.7713, fraction truly known 0.7728. Largest per-bin gap with n>=20: 0.047. Note: successive pairs on one concept are dependent, so per-bin CIs are nominal; the overall comparison is the robust one.

## calibration

| belief_lo | belief_hi | mean_belief | n | frac_truly_known | ci95 | gap |
|---|---|---|---|---|---|---|
| 0 | 0.1 |  | 0 |  | 0 |  |
| 0.1 | 0.2 |  | 0 |  | 0 |  |
| 0.2 | 0.3 | 0.2347 | 2131 | 0.2332 | 0.01795 | -0.001481 |
| 0.3 | 0.4 | 0.3411 | 394 | 0.3883 | 0.04812 | 0.04727 |
| 0.4 | 0.5 | 0.4232 | 70 | 0.4286 | 0.1159 | 0.005405 |
| 0.5 | 0.6 | 0.5293 | 452 | 0.5221 | 0.04605 | -0.007182 |
| 0.6 | 0.7 | 0.6215 | 928 | 0.625 | 0.03115 | 0.003484 |
| 0.7 | 0.8 | 0.7317 | 233 | 0.7468 | 0.05584 | 0.01512 |
| 0.8 | 0.9 | 0.8646 | 942 | 0.8631 | 0.02195 | -0.001532 |
| 0.9 | 1 | 0.9913 | 6850 | 0.9914 | 0.002188 | 9.733e-05 |
