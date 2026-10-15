# forgetting_rules

50 fresh learners on layered_40, tutor assumes 0.05/day. Best real tutor by the robust score: adaptive review + decay belief (26.59 usable, mean over breaks of 0 to 10 days; CT + binary 15.15).

## summary

| arm | usable_3d | ci95_3d | robust | ci95_robust | robust_vs_ct_decay | p_vs_ct_decay | robust_vs_ct_binary | p_vs_ct_binary |
|---|---|---|---|---|---|---|---|---|
| CT + binary | 22.74 | 1.19 | 15.15 | 0.65 | -10.41 | 9.059e-14 |  |  |
| CT + decay belief | 36.98 | 0.47 | 25.56 | 0.2 |  |  | 10.41 | 9.059e-14 |
| adaptive review + decay belief | 35.08 | 0.46 | 26.59 | 0.2 | 1.04 | 2.465e-10 | 11.45 | 9.059e-14 |
| lowest recall + decay belief | 36.66 | 0.54 | 25.49 | 0.2 | -0.06 | 0.3916 | 10.35 | 9.059e-14 |
| recall threshold + decay belief | 36.46 | 0.45 | 25.55 | 0.21 | -0.01 | 1 | 10.4 | 9.059e-14 |
| proportional review + decay belief | 36.86 | 0.49 | 25.7 | 0.2 | 0.15 | 0.3222 | 10.55 | 9.059e-14 |
| CT + oracle belief | 35.14 | 0.3 | 28.15 | 0.18 | 2.59 | 9.059e-14 | 13 | 9.059e-14 |
| lowest recall + oracle belief | 34.72 | 0.3 | 27.81 | 0.2 | 2.25 | 9.059e-14 | 12.66 | 9.059e-14 |
| recall threshold + oracle belief | 34.74 | 0.24 | 27.79 | 0.17 | 2.24 | 9.059e-14 | 12.64 | 9.059e-14 |
| proportional review + oracle belief | 34.72 | 0.3 | 27.81 | 0.2 | 2.25 | 9.059e-14 | 12.66 | 9.059e-14 |

## curves

| break_days | CT + binary | CT + decay belief | adaptive review + decay belief | lowest recall + decay belief | recall threshold + decay belief | proportional review + decay belief | CT + oracle belief | lowest recall + oracle belief | recall threshold + oracle belief | proportional review + oracle belief |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 29.8 | 38.94 | 35.78 | 38.48 | 38.14 | 38.28 | 35.44 | 35.12 | 35.08 | 35.12 |
| 1 | 27.8 | 38.7 | 35.58 | 38.3 | 38 | 37.98 | 35.36 | 35 | 34.98 | 35 |
| 2 | 25.34 | 38.24 | 35.44 | 37.66 | 37.54 | 37.52 | 35.22 | 34.88 | 34.84 | 34.88 |
| 3 | 22.74 | 36.98 | 35.08 | 36.66 | 36.46 | 36.86 | 35.14 | 34.72 | 34.74 | 34.72 |
| 4 | 19.7 | 34.62 | 34.48 | 34.34 | 34.56 | 34.46 | 34.86 | 34.52 | 34.42 | 34.52 |
| 5 | 16.46 | 30.52 | 33 | 30.56 | 31.2 | 30.94 | 34.34 | 34.04 | 34.16 | 34.04 |
| 6 | 12.14 | 24.44 | 29.64 | 25.02 | 25.74 | 25.8 | 33.52 | 33.16 | 33.04 | 33.16 |
| 7 | 7.7 | 18.22 | 23.68 | 18.3 | 18.56 | 19.22 | 30.82 | 30.7 | 30.36 | 30.7 |
| 8 | 3.66 | 11.68 | 16.5 | 12.24 | 11.52 | 12.46 | 23.12 | 22.22 | 22.68 | 22.22 |
| 9 | 1.02 | 6.34 | 9.04 | 6.4 | 6.44 | 6.68 | 9.84 | 9.7 | 9.7 | 9.7 |
| 10 | 0.28 | 2.44 | 4.32 | 2.48 | 2.84 | 2.52 | 2 | 1.82 | 1.72 | 1.82 |
| 11 | 0.18 | 0.82 | 0.92 | 0.76 | 0.8 | 0.74 | 0.04 | 0.02 | 0.04 | 0.02 |
| 12 | 0.04 | 0.22 | 0.04 | 0.1 | 0.12 | 0.18 | 0 | 0 | 0 | 0 |

## estimation_cost

| rule | usable_3d_estimated | usable_3d_oracle | gain_3d | p_3d | gain_robust | p_robust |
|---|---|---|---|---|---|---|
| lowest recall | 36.66 | 34.72 | -1.94 | 4.434e-07 | 2.31 | 9.059e-14 |
| recall threshold | 36.46 | 34.74 | -1.72 | 5.653e-08 | 2.25 | 9.059e-14 |
| proportional review | 36.86 | 34.72 | -2.14 | 5.116e-12 | 2.11 | 9.059e-14 |
| CurriculumTutor | 36.98 | 35.14 | -1.84 | 2.458e-08 |  |  |
