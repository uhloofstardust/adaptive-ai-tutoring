# mastery_margin_fresh

50 learners (seeds from 9000) on layered_40. Best threshold by the robust score (mean over breaks of 0 to 10 days): decaying belief 0.9, perfect belief 0.8.

## margin

| belief | threshold | usable_0d | usable_3d | usable_7d | robust | robust_ci95 | coverage |
|---|---|---|---|---|---|---|---|
| continuous_forget | 0.7 | 39.18 | 34.18 | 15.56 | 23.71 | 0.25 | 40 |
| continuous_forget | 0.8 | 38.94 | 36.98 | 18.22 | 25.56 | 0.2 | 39.7 |
| continuous_forget | 0.9 | 31.74 | 31.02 | 26.92 | 26.44 | 0.25 | 34.1 |
| continuous_forget | 0.95 | 25.82 | 24.78 | 21.46 | 22.24 | 0.23 | 29.2 |
| continuous_forget | 0.98 | 23.74 | 22.58 | 19.66 | 20.54 | 0.31 | 28.2 |
| oracle | 0.7 | 40 | 40 | 17.54 | 26.92 | 0.19 | 40 |
| oracle | 0.8 | 35.44 | 35.14 | 30.82 | 28.15 | 0.18 | 36.8 |
| oracle | 0.9 | 27.08 | 26.1 | 23.08 | 23.76 | 0.18 | 29.5 |
| oracle | 0.95 | 21.36 | 20.4 | 18.22 | 18.87 | 0.21 | 26.6 |
| oracle | 0.98 | 16.24 | 16.02 | 15.08 | 15.22 | 0.14 | 19.1 |
