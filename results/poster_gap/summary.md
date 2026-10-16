# poster_gap

50 fresh learners (seeds from 9000) on layered_40, belief decay 0.05/day. half-life 7d: 2 of 5 settings are best at some break; half-life 14d: 4 of 5 settings are best at some break; half-life 28d: 4 of 5 settings are best at some break.

## curves

| half_life_days | break_days | best_possible | CT as published (binary) | CT + decay belief, mastered at 0.7 | CT + decay belief, mastered at 0.8 | CT + decay belief, mastered at 0.9 | adaptive review + decay belief |
|---|---|---|---|---|---|---|---|
| 7 | 0 | 25.98 | 8.96 | 15.32 | 23.26 | 25.22 | 25.98 |
| 7 | 1 | 22.9 | 6.82 | 9.42 | 17.3 | 22.9 | 20.66 |
| 7 | 2 | 18.8 | 4.76 | 5.22 | 10.78 | 18.8 | 13.08 |
| 7 | 3 | 13.12 | 2.44 | 2.2 | 4.86 | 13.12 | 6.02 |
| 7 | 4 | 5.52 | 0.28 | 0.6 | 1.48 | 5.52 | 1.64 |
| 7 | 5 | 0.9 | 0 | 0.06 | 0.2 | 0.9 | 0.08 |
| 7 | 6 | 0 | 0 | 0 | 0 | 0 | 0 |
| 7 | 7 | 0 | 0 | 0 | 0 | 0 | 0 |
| 7 | 8 | 0 | 0 | 0 | 0 | 0 | 0 |
| 7 | 10 | 0 | 0 | 0 | 0 | 0 | 0 |
| 7 | 12 | 0 | 0 | 0 | 0 | 0 | 0 |
| 7 | 14 | 0 | 0 | 0 | 0 | 0 | 0 |
| 7 | 18 | 0 | 0 | 0 | 0 | 0 | 0 |
| 7 | 21 | 0 | 0 | 0 | 0 | 0 | 0 |
| 7 | 25 | 0 | 0 | 0 | 0 | 0 | 0 |
| 7 | 28 | 0 | 0 | 0 | 0 | 0 | 0 |
| 14 | 0 | 39.18 | 29.8 | 39.18 | 38.94 | 31.74 | 35.78 |
| 14 | 1 | 38.7 | 27.8 | 38.12 | 38.7 | 31.54 | 35.58 |
| 14 | 2 | 38.24 | 25.34 | 36.6 | 38.24 | 31.36 | 35.44 |
| 14 | 3 | 36.98 | 22.74 | 34.18 | 36.98 | 31.02 | 35.08 |
| 14 | 4 | 34.62 | 19.7 | 30.88 | 34.62 | 30.48 | 34.48 |
| 14 | 5 | 33 | 16.46 | 26.56 | 30.52 | 29.84 | 33 |
| 14 | 6 | 29.64 | 12.14 | 20.9 | 24.44 | 28.68 | 29.64 |
| 14 | 7 | 26.92 | 7.7 | 15.56 | 18.22 | 26.92 | 23.68 |
| 14 | 8 | 22.9 | 3.66 | 10.18 | 11.68 | 22.9 | 16.5 |
| 14 | 10 | 9.7 | 0.28 | 2.78 | 2.44 | 9.7 | 4.32 |
| 14 | 12 | 0.4 | 0.04 | 0.2 | 0.22 | 0.4 | 0.04 |
| 14 | 14 | 0 | 0 | 0 | 0 | 0 | 0 |
| 14 | 18 | 0 | 0 | 0 | 0 | 0 | 0 |
| 14 | 21 | 0 | 0 | 0 | 0 | 0 | 0 |
| 14 | 25 | 0 | 0 | 0 | 0 | 0 | 0 |
| 14 | 28 | 0 | 0 | 0 | 0 | 0 | 0 |
| 28 | 0 | 40 | 40 | 40 | 40 | 34.54 | 38.94 |
| 28 | 1 | 40 | 40 | 40 | 40 | 34.54 | 38.92 |
| 28 | 2 | 40 | 40 | 40 | 40 | 34.5 | 38.9 |
| 28 | 3 | 40 | 40 | 39.98 | 40 | 34.48 | 38.88 |
| 28 | 4 | 40 | 40 | 39.94 | 40 | 34.38 | 38.82 |
| 28 | 5 | 40 | 39.86 | 39.94 | 40 | 34.28 | 38.82 |
| 28 | 6 | 40 | 39.8 | 39.92 | 40 | 34.2 | 38.76 |
| 28 | 7 | 40 | 39.62 | 39.84 | 40 | 34.12 | 38.66 |
| 28 | 8 | 39.94 | 39.16 | 39.74 | 39.94 | 34.04 | 38.54 |
| 28 | 10 | 39.78 | 37.74 | 39.18 | 39.78 | 33.84 | 38.26 |
| 28 | 12 | 39.34 | 35.3 | 38.12 | 39.34 | 33.56 | 37.88 |
| 28 | 14 | 37.84 | 32.48 | 36 | 37.84 | 33.26 | 36.86 |
| 28 | 18 | 30.32 | 17.24 | 25.02 | 27.84 | 30.32 | 29.2 |
| 28 | 21 | 20.16 | 5.5 | 12.66 | 13.42 | 20.16 | 15.16 |
| 28 | 25 | 3.34 | 0.42 | 1.52 | 1.28 | 3.34 | 0.94 |
| 28 | 28 | 0 | 0 | 0 | 0 | 0 | 0 |

## winners

| half_life_days | break_days | best_setting | best_concepts |
|---|---|---|---|
| 7 | 0 | adaptive review + decay belief | 25.98 |
| 7 | 1 | CT + decay belief, mastered at 0.9 | 22.9 |
| 7 | 2 | CT + decay belief, mastered at 0.9 | 18.8 |
| 7 | 3 | CT + decay belief, mastered at 0.9 | 13.12 |
| 7 | 4 | CT + decay belief, mastered at 0.9 | 5.52 |
| 14 | 0 | CT + decay belief, mastered at 0.7 | 39.18 |
| 14 | 1 | CT + decay belief, mastered at 0.8 | 38.7 |
| 14 | 2 | CT + decay belief, mastered at 0.8 | 38.24 |
| 14 | 3 | CT + decay belief, mastered at 0.8 | 36.98 |
| 14 | 4 | CT + decay belief, mastered at 0.8 | 34.62 |
| 14 | 5 | adaptive review + decay belief | 33 |
| 14 | 6 | adaptive review + decay belief | 29.64 |
| 14 | 7 | CT + decay belief, mastered at 0.9 | 26.92 |
| 14 | 8 | CT + decay belief, mastered at 0.9 | 22.9 |
| 14 | 10 | CT + decay belief, mastered at 0.9 | 9.7 |
| 28 | 0 | CT as published (binary) = CT + decay belief, mastered at 0.7 = CT + decay belief, mastered at 0.8 | 40 |
| 28 | 1 | CT as published (binary) = CT + decay belief, mastered at 0.7 = CT + decay belief, mastered at 0.8 | 40 |
| 28 | 2 | CT as published (binary) = CT + decay belief, mastered at 0.7 = CT + decay belief, mastered at 0.8 | 40 |
| 28 | 3 | CT as published (binary) = CT + decay belief, mastered at 0.7 = CT + decay belief, mastered at 0.8 | 40 |
| 28 | 4 | CT as published (binary) = CT + decay belief, mastered at 0.8 | 40 |
| 28 | 5 | CT + decay belief, mastered at 0.8 | 40 |
| 28 | 6 | CT + decay belief, mastered at 0.8 | 40 |
| 28 | 7 | CT + decay belief, mastered at 0.8 | 40 |
| 28 | 8 | CT + decay belief, mastered at 0.8 | 39.94 |
| 28 | 10 | CT + decay belief, mastered at 0.8 | 39.78 |
| 28 | 12 | CT + decay belief, mastered at 0.8 | 39.34 |
| 28 | 14 | CT + decay belief, mastered at 0.8 | 37.84 |
| 28 | 18 | CT + decay belief, mastered at 0.9 | 30.32 |
| 28 | 21 | CT + decay belief, mastered at 0.9 | 20.16 |
| 28 | 25 | CT + decay belief, mastered at 0.9 | 3.34 |

## gaps

| half_life_days | setting | worst_gap | mean_gap | breaks_where_best |
|---|---|---|---|---|
| 7 | CT as published (binary) | 17.02 | 12.61 | 0 |
| 7 | CT + decay belief, mastered at 0.7 | 13.58 | 10.71 | 0 |
| 7 | CT + decay belief, mastered at 0.8 | 8.26 | 5.73 | 0 |
| 7 | CT + decay belief, mastered at 0.9 | 0.76 | 0.15 | 4 |
| 7 | adaptive review + decay belief | 7.1 | 3.79 | 1 |
| 14 | CT as published (binary) | 19.24 | 14.43 | 0 |
| 14 | CT + decay belief, mastered at 0.7 | 12.72 | 5.49 | 1 |
| 14 | CT + decay belief, mastered at 0.8 | 11.22 | 3.51 | 4 |
| 14 | CT + decay belief, mastered at 0.9 | 7.44 | 3.57 | 3 |
| 14 | adaptive review + decay belief | 6.4 | 2.64 | 2 |
| 28 | CT as published (binary) | 14.66 | 2.91 | 5 |
| 28 | CT + decay belief, mastered at 0.7 | 7.5 | 1.26 | 3 |
| 28 | CT + decay belief, mastered at 0.8 | 6.74 | 0.75 | 12 |
| 28 | CT + decay belief, mastered at 0.9 | 5.94 | 4.48 | 3 |
| 28 | adaptive review + decay belief | 5 | 1.55 | 0 |
