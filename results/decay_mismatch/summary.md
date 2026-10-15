# decay_mismatch

30 learners per cell on layered_40. hl 7d curriculum_tutor: beats the baseline at 6/10 assumed rates; hl 7d adaptive_review: beats the baseline at 6/10 assumed rates; hl 14d curriculum_tutor: beats the baseline at 9/10 assumed rates; hl 14d adaptive_review: beats the baseline at 7/10 assumed rates; hl 28d curriculum_tutor: beats the baseline at 0/10 assumed rates; hl 28d adaptive_review: beats the baseline at 0/10 assumed rates.

## sweep

| comparison | metric | mean_diff | sd | wins | losses | n | p_sign | true_half_life_days | scheduler | assumed_rate | true_rate | usable | ci95 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| curriculum_tutor @ 0.0 - CT + binary | retained_usable | -0.8667 | 1.408 | 5 | 20 | 30 | 0.004077 | 7 | curriculum_tutor | 0 | 0.0943 | 1.7 | 0.43 |
| curriculum_tutor @ 0.01 - CT + binary | retained_usable | -0.7333 | 1.76 | 7 | 19 | 30 | 0.02896 | 7 | curriculum_tutor | 0.01 | 0.0943 | 1.83 | 0.5 |
| curriculum_tutor @ 0.02 - CT + binary | retained_usable | -0.6667 | 1.539 | 8 | 17 | 30 | 0.1078 | 7 | curriculum_tutor | 0.02 | 0.0943 | 1.9 | 0.57 |
| curriculum_tutor @ 0.03 - CT + binary | retained_usable | 0.03333 | 1.691 | 15 | 9 | 30 | 0.3075 | 7 | curriculum_tutor | 0.03 | 0.0943 | 2.6 | 0.48 |
| curriculum_tutor @ 0.05 - CT + binary | retained_usable | 2.867 | 2.03 | 27 | 2 | 30 | 1.624e-06 | 7 | curriculum_tutor | 0.05 | 0.0943 | 5.43 | 0.61 |
| curriculum_tutor @ 0.075 - CT + binary | retained_usable | 6.467 | 2.776 | 28 | 0 | 30 | 7.451e-09 | 7 | curriculum_tutor | 0.075 | 0.0943 | 9.03 | 0.82 |
| curriculum_tutor @ 0.1 - CT + binary | retained_usable | 9.7 | 2.003 | 30 | 0 | 30 | 1.863e-09 | 7 | curriculum_tutor | 0.1 | 0.0943 | 12.27 | 0.62 |
| curriculum_tutor @ 0.15 - CT + binary | retained_usable | 12.3 | 2.136 | 30 | 0 | 30 | 1.863e-09 | 7 | curriculum_tutor | 0.15 | 0.0943 | 14.87 | 0.65 |
| curriculum_tutor @ 0.2 - CT + binary | retained_usable | 12.73 | 1.617 | 30 | 0 | 30 | 1.863e-09 | 7 | curriculum_tutor | 0.2 | 0.0943 | 15.3 | 0.48 |
| curriculum_tutor @ 0.3 - CT + binary | retained_usable | 12.27 | 1.552 | 30 | 0 | 30 | 1.863e-09 | 7 | curriculum_tutor | 0.3 | 0.0943 | 14.83 | 0.44 |
| adaptive_review @ 0.0 - CT + binary | retained_usable | -0.8333 | 1.895 | 8 | 19 | 30 | 0.05224 | 7 | adaptive_review | 0 | 0.0943 | 1.73 | 0.48 |
| adaptive_review @ 0.01 - CT + binary | retained_usable | -0.7333 | 1.461 | 7 | 17 | 30 | 0.06391 | 7 | adaptive_review | 0.01 | 0.0943 | 1.83 | 0.36 |
| adaptive_review @ 0.02 - CT + binary | retained_usable | -0.2667 | 2.258 | 9 | 15 | 30 | 0.3075 | 7 | adaptive_review | 0.02 | 0.0943 | 2.3 | 0.64 |
| adaptive_review @ 0.03 - CT + binary | retained_usable | 0.6333 | 1.938 | 16 | 14 | 30 | 0.8555 | 7 | adaptive_review | 0.03 | 0.0943 | 3.2 | 0.57 |
| adaptive_review @ 0.05 - CT + binary | retained_usable | 2.7 | 1.841 | 26 | 3 | 30 | 1.524e-05 | 7 | adaptive_review | 0.05 | 0.0943 | 5.27 | 0.63 |
| adaptive_review @ 0.075 - CT + binary | retained_usable | 8.567 | 1.813 | 30 | 0 | 30 | 1.863e-09 | 7 | adaptive_review | 0.075 | 0.0943 | 11.13 | 0.66 |
| adaptive_review @ 0.1 - CT + binary | retained_usable | 12.17 | 1.802 | 30 | 0 | 30 | 1.863e-09 | 7 | adaptive_review | 0.1 | 0.0943 | 14.73 | 0.55 |
| adaptive_review @ 0.15 - CT + binary | retained_usable | 14.17 | 2.135 | 30 | 0 | 30 | 1.863e-09 | 7 | adaptive_review | 0.15 | 0.0943 | 16.73 | 0.68 |
| adaptive_review @ 0.2 - CT + binary | retained_usable | 14.07 | 1.311 | 30 | 0 | 30 | 1.863e-09 | 7 | adaptive_review | 0.2 | 0.0943 | 16.63 | 0.37 |
| adaptive_review @ 0.3 - CT + binary | retained_usable | 12.87 | 1.717 | 30 | 0 | 30 | 1.863e-09 | 7 | adaptive_review | 0.3 | 0.0943 | 15.43 | 0.54 |
| curriculum_tutor @ 0.0 - CT + binary | retained_usable | 5.5 | 4.711 | 26 | 2 | 30 | 3.032e-06 | 14 | curriculum_tutor | 0 | 0.0483 | 27.37 | 1.13 |
| curriculum_tutor @ 0.01 - CT + binary | retained_usable | 7.333 | 4.054 | 29 | 1 | 30 | 5.774e-08 | 14 | curriculum_tutor | 0.01 | 0.0483 | 29.2 | 0.81 |
| curriculum_tutor @ 0.02 - CT + binary | retained_usable | 8.8 | 4.097 | 30 | 0 | 30 | 1.863e-09 | 14 | curriculum_tutor | 0.02 | 0.0483 | 30.67 | 0.83 |
| curriculum_tutor @ 0.03 - CT + binary | retained_usable | 11.63 | 3.926 | 30 | 0 | 30 | 1.863e-09 | 14 | curriculum_tutor | 0.03 | 0.0483 | 33.5 | 0.72 |
| curriculum_tutor @ 0.05 - CT + binary | retained_usable | 14.53 | 4.041 | 30 | 0 | 30 | 1.863e-09 | 14 | curriculum_tutor | 0.05 | 0.0483 | 36.4 | 0.53 |
| curriculum_tutor @ 0.075 - CT + binary | retained_usable | 11.6 | 3.802 | 30 | 0 | 30 | 1.863e-09 | 14 | curriculum_tutor | 0.075 | 0.0483 | 33.47 | 0.52 |
| curriculum_tutor @ 0.1 - CT + binary | retained_usable | 9.367 | 3.801 | 30 | 0 | 30 | 1.863e-09 | 14 | curriculum_tutor | 0.1 | 0.0483 | 31.23 | 0.5 |
| curriculum_tutor @ 0.15 - CT + binary | retained_usable | 5.733 | 3.248 | 28 | 0 | 30 | 7.451e-09 | 14 | curriculum_tutor | 0.15 | 0.0483 | 27.6 | 0.42 |
| curriculum_tutor @ 0.2 - CT + binary | retained_usable | 3.167 | 3.514 | 23 | 6 | 30 | 0.002316 | 14 | curriculum_tutor | 0.2 | 0.0483 | 25.03 | 0.48 |
| curriculum_tutor @ 0.3 - CT + binary | retained_usable | 1.933 | 4.152 | 17 | 9 | 30 | 0.1686 | 14 | curriculum_tutor | 0.3 | 0.0483 | 23.8 | 0.45 |
| adaptive_review @ 0.0 - CT + binary | retained_usable | 11.3 | 3.761 | 30 | 0 | 30 | 1.863e-09 | 14 | adaptive_review | 0 | 0.0483 | 33.17 | 1.24 |
| adaptive_review @ 0.01 - CT + binary | retained_usable | 12.07 | 4.631 | 30 | 0 | 30 | 1.863e-09 | 14 | adaptive_review | 0.01 | 0.0483 | 33.93 | 1.31 |
| adaptive_review @ 0.02 - CT + binary | retained_usable | 12.23 | 4.141 | 30 | 0 | 30 | 1.863e-09 | 14 | adaptive_review | 0.02 | 0.0483 | 34.1 | 0.95 |
| adaptive_review @ 0.03 - CT + binary | retained_usable | 14.37 | 3.873 | 30 | 0 | 30 | 1.863e-09 | 14 | adaptive_review | 0.03 | 0.0483 | 36.23 | 0.72 |
| adaptive_review @ 0.05 - CT + binary | retained_usable | 13.03 | 3.7 | 30 | 0 | 30 | 1.863e-09 | 14 | adaptive_review | 0.05 | 0.0483 | 34.9 | 0.45 |
| adaptive_review @ 0.075 - CT + binary | retained_usable | 9.333 | 3.986 | 30 | 0 | 30 | 1.863e-09 | 14 | adaptive_review | 0.075 | 0.0483 | 31.2 | 0.51 |
| adaptive_review @ 0.1 - CT + binary | retained_usable | 6.467 | 3.748 | 30 | 0 | 30 | 1.863e-09 | 14 | adaptive_review | 0.1 | 0.0483 | 28.33 | 0.45 |
| adaptive_review @ 0.15 - CT + binary | retained_usable | 0.2667 | 3.903 | 14 | 11 | 30 | 0.69 | 14 | adaptive_review | 0.15 | 0.0483 | 22.13 | 0.45 |
| adaptive_review @ 0.2 - CT + binary | retained_usable | -1.733 | 3.787 | 7 | 20 | 30 | 0.01916 | 14 | adaptive_review | 0.2 | 0.0483 | 20.13 | 0.38 |
| adaptive_review @ 0.3 - CT + binary | retained_usable | -2.9 | 3.642 | 6 | 21 | 30 | 0.005925 | 14 | adaptive_review | 0.3 | 0.0483 | 18.97 | 0.38 |
| curriculum_tutor @ 0.0 - CT + binary | retained_usable | -0.5 | 0.6823 | 0 | 12 | 30 | 0.0004883 | 28 | curriculum_tutor | 0 | 0.0245 | 39.5 | 0.24 |
| curriculum_tutor @ 0.01 - CT + binary | retained_usable | -0.1333 | 0.3457 | 0 | 4 | 30 | 0.125 | 28 | curriculum_tutor | 0.01 | 0.0245 | 39.87 | 0.12 |
| curriculum_tutor @ 0.02 - CT + binary | retained_usable | -0.03333 | 0.1826 | 0 | 1 | 30 | 1 | 28 | curriculum_tutor | 0.02 | 0.0245 | 39.97 | 0.07 |
| curriculum_tutor @ 0.03 - CT + binary | retained_usable | 0 | 0 | 0 | 0 | 30 | 1 | 28 | curriculum_tutor | 0.03 | 0.0245 | 40 | 0 |
| curriculum_tutor @ 0.05 - CT + binary | retained_usable | 0 | 0 | 0 | 0 | 30 | 1 | 28 | curriculum_tutor | 0.05 | 0.0245 | 40 | 0 |
| curriculum_tutor @ 0.075 - CT + binary | retained_usable | -2.133 | 1.279 | 0 | 28 | 30 | 7.451e-09 | 28 | curriculum_tutor | 0.075 | 0.0245 | 37.87 | 0.46 |
| curriculum_tutor @ 0.1 - CT + binary | retained_usable | -5.1 | 1.062 | 0 | 30 | 30 | 1.863e-09 | 28 | curriculum_tutor | 0.1 | 0.0245 | 34.9 | 0.38 |
| curriculum_tutor @ 0.15 - CT + binary | retained_usable | -9.567 | 1.006 | 0 | 30 | 30 | 1.863e-09 | 28 | curriculum_tutor | 0.15 | 0.0245 | 30.43 | 0.36 |
| curriculum_tutor @ 0.2 - CT + binary | retained_usable | -12 | 1.05 | 0 | 30 | 30 | 1.863e-09 | 28 | curriculum_tutor | 0.2 | 0.0245 | 28 | 0.38 |
| curriculum_tutor @ 0.3 - CT + binary | retained_usable | -12.77 | 1.04 | 0 | 30 | 30 | 1.863e-09 | 28 | curriculum_tutor | 0.3 | 0.0245 | 27.23 | 0.37 |
| adaptive_review @ 0.0 - CT + binary | retained_usable | 0 | 0 | 0 | 0 | 30 | 1 | 28 | adaptive_review | 0 | 0.0245 | 40 | 0 |
| adaptive_review @ 0.01 - CT + binary | retained_usable | 0 | 0 | 0 | 0 | 30 | 1 | 28 | adaptive_review | 0.01 | 0.0245 | 40 | 0 |
| adaptive_review @ 0.02 - CT + binary | retained_usable | 0 | 0 | 0 | 0 | 30 | 1 | 28 | adaptive_review | 0.02 | 0.0245 | 40 | 0 |
| adaptive_review @ 0.03 - CT + binary | retained_usable | 0 | 0 | 0 | 0 | 30 | 1 | 28 | adaptive_review | 0.03 | 0.0245 | 40 | 0 |
| adaptive_review @ 0.05 - CT + binary | retained_usable | -1.4 | 1.102 | 0 | 22 | 30 | 4.768e-07 | 28 | adaptive_review | 0.05 | 0.0245 | 38.6 | 0.39 |
| adaptive_review @ 0.075 - CT + binary | retained_usable | -5.133 | 0.9371 | 0 | 30 | 30 | 1.863e-09 | 28 | adaptive_review | 0.075 | 0.0245 | 34.87 | 0.34 |
| adaptive_review @ 0.1 - CT + binary | retained_usable | -9.4 | 1.221 | 0 | 30 | 30 | 1.863e-09 | 28 | adaptive_review | 0.1 | 0.0245 | 30.6 | 0.44 |
| adaptive_review @ 0.15 - CT + binary | retained_usable | -16.4 | 1.221 | 0 | 30 | 30 | 1.863e-09 | 28 | adaptive_review | 0.15 | 0.0245 | 23.6 | 0.44 |
| adaptive_review @ 0.2 - CT + binary | retained_usable | -18.37 | 1.129 | 0 | 30 | 30 | 1.863e-09 | 28 | adaptive_review | 0.2 | 0.0245 | 21.63 | 0.4 |
| adaptive_review @ 0.3 - CT + binary | retained_usable | -19.17 | 0.8339 | 0 | 30 | 30 | 1.863e-09 | 28 | adaptive_review | 0.3 | 0.0245 | 20.83 | 0.3 |

## reach

| true_half_life_days | scheduler | true_rate | lowest_ok | highest_ok | n_rates_ok | n_rates |
|---|---|---|---|---|---|---|
| 7 | curriculum_tutor | 0.0943 | 0.05 | 0.3 | 6 | 10 |
| 7 | adaptive_review | 0.0943 | 0.05 | 0.3 | 6 | 10 |
| 14 | curriculum_tutor | 0.0483 | 0 | 0.2 | 9 | 10 |
| 14 | adaptive_review | 0.0483 | 0 | 0.1 | 7 | 10 |
| 28 | curriculum_tutor | 0.0245 | None | None | 0 | 10 |
| 28 | adaptive_review | 0.0245 | None | None | 0 | 10 |
