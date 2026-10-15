# param_sweep

19 cells, 30 learners each, all sharing one seed block. Every cell here is correctly specified (student and tutor get the same values), so the pooled gap measures estimator noise, not calibration: it stays within 0.011 everywhere, which says the estimator is unbiased across parameter settings rather than that the tutor is calibrated. Range of the false-alarm rate across each grid: p_G 0.092, p_T 0.082, p_S 0.046, p_L0 0.025. Range of the on-concept delay: p_T 2.45, p_G 1.64, p_S 0.78, p_L0 0.71. So p_G is the strongest lever on both, and the effects do not separate cleanly by metric.

## param_sweep

| parameter | value | calib_mean_belief | calib_frac_known | calib_gap | n_declared | false_alarm_rate | delay_on_concept_mean |
|---|---|---|---|---|---|---|---|
| p_G | 0.05 | 0.7876 | 0.7978 | 0.01022 | 240 | 0 | 2.142 |
| p_G | 0.15 | 0.7803 | 0.7886 | 0.008291 | 240 | 0.04167 | 2.213 |
| p_G | 0.25 | 0.7601 | 0.7539 | -0.006199 | 240 | 0.06667 | 3.129 |
| p_G | 0.35 | 0.7731 | 0.7733 | 0.0001869 | 240 | 0.09167 | 3.151 |
| p_G | 0.45 | 0.7712 | 0.7689 | -0.002283 | 240 | 0.05833 | 3.783 |
| p_S | 0.02 | 0.7766 | 0.7836 | 0.006964 | 240 | 0.025 | 2.868 |
| p_S | 0.05 | 0.7636 | 0.7622 | -0.001392 | 240 | 0.05417 | 2.881 |
| p_S | 0.1 | 0.7601 | 0.7539 | -0.006199 | 240 | 0.06667 | 3.129 |
| p_S | 0.2 | 0.782 | 0.7817 | -0.0003042 | 240 | 0.07083 | 3.395 |
| p_S | 0.3 | 0.7866 | 0.7756 | -0.01107 | 240 | 0.07083 | 3.65 |
| p_T | 0.05 | 0.2659 | 0.2581 | -0.007812 | 170 | 0.07647 | 4.261 |
| p_T | 0.1 | 0.5284 | 0.5264 | -0.002051 | 234 | 0.1026 | 3.438 |
| p_T | 0.2 | 0.7601 | 0.7539 | -0.006199 | 240 | 0.06667 | 3.129 |
| p_T | 0.3 | 0.8766 | 0.8878 | 0.0112 | 240 | 0.02083 | 2.179 |
| p_T | 0.4 | 0.921 | 0.92 | -0.0009502 | 240 | 0.04167 | 1.813 |
| p_L0 | 0.05 | 0.7453 | 0.75 | 0.004735 | 240 | 0.05 | 3.101 |
| p_L0 | 0.15 | 0.7601 | 0.7539 | -0.006199 | 240 | 0.06667 | 3.129 |
| p_L0 | 0.3 | 0.8167 | 0.8217 | 0.004968 | 240 | 0.07083 | 2.816 |
| p_L0 | 0.5 | 0.8786 | 0.8806 | 0.001929 | 240 | 0.075 | 2.419 |
