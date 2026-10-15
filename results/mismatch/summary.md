# mismatch

(a) One student, 200 learners, the tutor's assumption swept one parameter at a time. p_G: gap +0.002 +/-0.006 when the tutor is right, -0.063 +/-0.008 at its worst (p_G=0.05, error -0.20); p_S: gap +0.002 +/-0.006 when the tutor is right, -0.037 +/-0.008 at its worst (p_S=0.3, error +0.20); p_T: gap +0.002 +/-0.006 when the tutor is right, +0.133 +/-0.005 at its worst (p_T=0.05, error -0.15). (b) A population with spread +/-0.15 against one fixed tutor: gap -0.017 +/-0.014, false alarms 7.5% against 4.6% when every student matches the tutor exactly. The spread rows share a seed block, so they are a paired trend rather than four independent estimates.

## mismatch_one

| arm | parameter | tutor_value | student_value | error | calib_mean_belief | calib_frac_known | calib_gap | calib_gap_ci95 | n_declared | false_alarm_rate | delay_on_concept_mean |
|---|---|---|---|---|---|---|---|---|---|---|---|
| one student | p_G | 0.05 | 0.25 | -0.2 | 0.8394 | 0.7769 | -0.06252 | 0.007632 | 1600 | 0.1706 | 1.791 |
| one student | p_G | 0.15 | 0.25 | -0.1 | 0.8006 | 0.7753 | -0.02525 | 0.006681 | 1600 | 0.1237 | 2.105 |
| one student | p_G | 0.25 | 0.25 | 0 | 0.7737 | 0.776 | 0.002323 | 0.00634 | 1600 | 0.04625 | 3.056 |
| one student | p_G | 0.35 | 0.25 | 0.1 | 0.7491 | 0.7725 | 0.02347 | 0.005776 | 1600 | 0.02937 | 3.276 |
| one student | p_G | 0.45 | 0.25 | 0.2 | 0.7337 | 0.783 | 0.04931 | 0.005835 | 1600 | 0.0125 | 4.334 |
| one student | p_S | 0.02 | 0.1 | -0.08 | 0.7441 | 0.7727 | 0.02852 | 0.005649 | 1600 | 0.02937 | 3.276 |
| one student | p_S | 0.05 | 0.1 | -0.05 | 0.7576 | 0.7731 | 0.01548 | 0.005868 | 1600 | 0.04375 | 3.078 |
| one student | p_S | 0.1 | 0.1 | 0 | 0.7737 | 0.776 | 0.002323 | 0.00634 | 1600 | 0.04625 | 3.056 |
| one student | p_S | 0.2 | 0.1 | 0.1 | 0.7934 | 0.7704 | -0.023 | 0.008328 | 1600 | 0.06375 | 2.862 |
| one student | p_S | 0.3 | 0.1 | 0.2 | 0.8128 | 0.7762 | -0.03664 | 0.007745 | 1600 | 0.07 | 2.822 |
| one student | p_T | 0.05 | 0.2 | -0.15 | 0.6434 | 0.7767 | 0.1332 | 0.005235 | 1600 | 0.01312 | 4.335 |
| one student | p_T | 0.1 | 0.2 | -0.1 | 0.7006 | 0.7737 | 0.07316 | 0.005127 | 1600 | 0.02875 | 3.363 |
| one student | p_T | 0.2 | 0.2 | 0 | 0.7737 | 0.776 | 0.002323 | 0.00634 | 1600 | 0.04625 | 3.056 |
| one student | p_T | 0.3 | 0.2 | 0.1 | 0.8266 | 0.774 | -0.05257 | 0.007896 | 1600 | 0.1062 | 2.266 |
| one student | p_T | 0.4 | 0.2 | 0.2 | 0.8662 | 0.7724 | -0.09382 | 0.00952 | 1600 | 0.1556 | 1.879 |

## mismatch_population

| arm | spread | calib_mean_belief | calib_frac_known | calib_gap | calib_gap_ci95 | n_declared | false_alarm_rate | delay_on_concept_mean |
|---|---|---|---|---|---|---|---|---|
| population | 0 | 0.7737 | 0.776 | 0.002323 | 0.00634 | 1600 | 0.04625 | 3.056 |
| population | 0.05 | 0.767 | 0.7682 | 0.001253 | 0.006716 | 1600 | 0.04063 | 3.072 |
| population | 0.1 | 0.7549 | 0.7466 | -0.008344 | 0.01002 | 1600 | 0.05813 | 3.106 |
| population | 0.15 | 0.7453 | 0.7282 | -0.01705 | 0.01397 | 1591 | 0.07542 | 3.126 |
