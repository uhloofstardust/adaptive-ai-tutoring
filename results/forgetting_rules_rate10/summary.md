# forgetting_rules_rate10

50 fresh learners on layered_40, tutor assumes 0.1/day. Best real tutor by the robust score: CT + decay belief (26.92 usable, mean over breaks of 0 to 10 days; CT + binary 15.15).

## summary

| arm | usable_3d | ci95_3d | robust | ci95_robust | robust_vs_ct_decay | p_vs_ct_decay | robust_vs_ct_binary | p_vs_ct_binary |
|---|---|---|---|---|---|---|---|---|
| CT + binary | 22.74 | 1.19 | 15.15 | 0.65 | -11.77 | 9.059e-14 |  |  |
| CT + decay belief | 31.82 | 0.41 | 26.92 | 0.26 |  |  | 11.77 | 9.059e-14 |
| adaptive review + decay belief | 28.52 | 0.34 | 25.29 | 0.21 | -1.63 | 1.776e-13 | 10.14 | 9.059e-14 |
| lowest recall + decay belief | 31.12 | 0.36 | 26.49 | 0.21 | -0.43 | 0.02129 | 11.34 | 9.059e-14 |
| recall threshold + decay belief | 31.32 | 0.44 | 26.31 | 0.2 | -0.6 | 2.49e-05 | 11.17 | 9.059e-14 |
| proportional review + decay belief | 30.98 | 0.42 | 26.27 | 0.24 | -0.65 | 9.264e-06 | 11.12 | 9.059e-14 |
| CT + oracle belief | 35.14 | 0.3 | 28.15 | 0.18 | 1.23 | 3.708e-11 | 13 | 9.059e-14 |
| lowest recall + oracle belief | 34.72 | 0.3 | 27.81 | 0.2 | 0.89 | 2.386e-05 | 12.66 | 9.059e-14 |
| recall threshold + oracle belief | 34.74 | 0.24 | 27.79 | 0.17 | 0.87 | 1.071e-06 | 12.64 | 9.059e-14 |
| proportional review + oracle belief | 34.72 | 0.3 | 27.81 | 0.2 | 0.89 | 2.386e-05 | 12.66 | 9.059e-14 |

## curves

| break_days | CT + binary | CT + decay belief | adaptive review + decay belief | lowest recall + decay belief | recall threshold + decay belief | proportional review + decay belief | CT + oracle belief | lowest recall + oracle belief | recall threshold + oracle belief | proportional review + oracle belief |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 29.8 | 32.48 | 29.22 | 31.94 | 32.26 | 32.1 | 35.44 | 35.12 | 35.08 | 35.12 |
| 1 | 27.8 | 32.32 | 29.1 | 31.74 | 31.96 | 31.68 | 35.36 | 35 | 34.98 | 35 |
| 2 | 25.34 | 32.18 | 28.82 | 31.5 | 31.74 | 31.38 | 35.22 | 34.88 | 34.84 | 34.88 |
| 3 | 22.74 | 31.82 | 28.52 | 31.12 | 31.32 | 30.98 | 35.14 | 34.72 | 34.74 | 34.72 |
| 4 | 19.7 | 31.26 | 28.18 | 30.64 | 30.9 | 30.48 | 34.86 | 34.52 | 34.42 | 34.52 |
| 5 | 16.46 | 30.56 | 27.62 | 29.9 | 30.42 | 29.82 | 34.34 | 34.04 | 34.16 | 34.04 |
| 6 | 12.14 | 29.4 | 26.84 | 28.98 | 29.32 | 28.58 | 33.52 | 33.16 | 33.04 | 33.16 |
| 7 | 7.7 | 26.9 | 25.74 | 26.94 | 26.54 | 26.2 | 30.82 | 30.7 | 30.36 | 30.7 |
| 8 | 3.66 | 22.7 | 23.44 | 22.52 | 21.74 | 21.9 | 23.12 | 22.22 | 22.68 | 22.22 |
| 9 | 1.02 | 16.62 | 19 | 16.46 | 14.98 | 16.1 | 9.84 | 9.7 | 9.7 | 9.7 |
| 10 | 0.28 | 9.86 | 11.74 | 9.64 | 8.28 | 9.74 | 2 | 1.82 | 1.72 | 1.82 |
| 11 | 0.18 | 3.9 | 4.72 | 3.4 | 3.42 | 4 | 0.04 | 0.02 | 0.04 | 0.02 |
| 12 | 0.04 | 0.54 | 0.66 | 0.46 | 0.38 | 0.48 | 0 | 0 | 0 | 0 |

## estimation_cost

| rule | usable_3d_estimated | usable_3d_oracle | gain_3d | p_3d | gain_robust | p_robust |
|---|---|---|---|---|---|---|
| lowest recall | 31.12 | 34.72 | 3.6 | 9.059e-14 | 1.32 | 1.776e-13 |
| recall threshold | 31.32 | 34.74 | 3.42 | 9.059e-14 | 1.48 | 3.482e-13 |
| proportional review | 30.98 | 34.72 | 3.74 | 9.059e-14 | 1.54 | 9.059e-14 |
| CurriculumTutor | 31.82 | 35.14 | 3.32 | 1.776e-13 |  |  |
