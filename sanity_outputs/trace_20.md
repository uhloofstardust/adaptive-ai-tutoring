# Step-by-step trace, one run, 20 questions

Plain BKT student and BKT tutor, shared parameters {'p_L0': 0.15, 'p_T': 0.12, 'p_G': 0.25, 'p_S': 0.1}, scheduler = uniform random over the ZPD, mastery threshold 0.9, seed 4242.

| step | ZPD before the question | asked | answer | true state | belief | declared |
|---:|---|---|:---:|:---:|:---:|:---:|
| 1 | A1, A2 | **A1** | right | not yet → not yet | 0.150 → 0.462 |  |
| 2 | A1, A2 | **A1** | wrong | not yet → known | 0.462 → 0.210 |  |
| 3 | A1, A2 | **A1** | right | known → known | 0.210 → 0.551 |  |
| 4 | A1, A2 | **A1** | right | known → known | 0.551 → 0.837 |  |
| 5 | A1, A2 | **A1** | right | known → known | 0.837 → 0.955 | yes |
| 6 | A2, B1 | **A2** | right | not yet → not yet | 0.150 → 0.462 |  |
| 7 | A2, B1 | **A2** | wrong | not yet → not yet | 0.462 → 0.210 |  |
| 8 | A2, B1 | **A2** | right | not yet → not yet | 0.210 → 0.551 |  |
| 9 | A2, B1 | **A2** | wrong | not yet → not yet | 0.551 → 0.244 |  |
| 10 | A2, B1 | **A2** | wrong | not yet → not yet | 0.244 → 0.156 |  |
| 11 | A2, B1 | **A2** | wrong | not yet → not yet | 0.156 → 0.141 |  |
| 12 | A2, B1 | **A2** | wrong | not yet → not yet | 0.141 → 0.139 |  |
| 13 | A2, B1 | **B1** | right | known → known | 0.150 → 0.462 |  |
| 14 | A2, B1 | **A2** | right | not yet → not yet | 0.139 → 0.443 |  |
| 15 | A2, B1 | **A2** | wrong | not yet → not yet | 0.443 → 0.204 |  |
| 16 | A2, B1 | **A2** | wrong | not yet → not yet | 0.204 → 0.149 |  |
| 17 | A2, B1 | **B1** | right | known → known | 0.462 → 0.785 |  |
| 18 | A2, B1 | **B1** | right | known → known | 0.785 → 0.938 | yes |
| 19 | A2 | **A2** | wrong | not yet → not yet | 0.149 → 0.140 |  |
| 20 | A2 | **A2** | wrong | not yet → not yet | 0.140 → 0.139 |  |

20 questions, seed 4242, threshold 0.9. The student learned 1 concept(s) during these steps.
