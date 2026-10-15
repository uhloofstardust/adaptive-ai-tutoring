# check1_calibration_400learners

48000 (belief, truth) pairs from 400 learners x 120 questions. Overall: mean belief 0.7769, fraction truly known 0.7787. Largest per-bin gap with n>=20: 0.029. Note: successive pairs on one concept are dependent, so per-bin CIs are nominal; the overall comparison is the robust one.

## calibration

| belief_lo | belief_hi | mean_belief | n | frac_truly_known | ci95 | gap |
|---|---|---|---|---|---|---|
| 0 | 0.1 |  | 0 |  | 0 |  |
| 0.1 | 0.2 |  | 0 |  | 0 |  |
| 0.2 | 0.3 | 0.2343 | 8422 | 0.2346 | 0.00905 | 0.0003384 |
| 0.3 | 0.4 | 0.3409 | 1473 | 0.3666 | 0.02461 | 0.02571 |
| 0.4 | 0.5 | 0.4239 | 243 | 0.4527 | 0.06258 | 0.02877 |
| 0.5 | 0.6 | 0.5296 | 1715 | 0.5376 | 0.0236 | 0.00798 |
| 0.6 | 0.7 | 0.6211 | 3642 | 0.6269 | 0.01571 | 0.005749 |
| 0.7 | 0.8 | 0.7308 | 845 | 0.7527 | 0.02909 | 0.02191 |
| 0.8 | 0.9 | 0.8653 | 3699 | 0.8616 | 0.01113 | -0.00373 |
| 0.9 | 1 | 0.9915 | 27961 | 0.9915 | 0.001075 | 1.277e-05 |
