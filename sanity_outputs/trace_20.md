# Step-by-step trace, one run, 20 questions

Plain BKT student and BKT tutor, shared parameters {'p_L0': 0.15, 'p_T': 0.2, 'p_G': 0.25, 'p_S': 0.1}, scheduler = uniform random over the ZPD, mastery threshold 0.9, seed 4242.

| step | ZPD before the question | asked | answer | true state | belief | declared |
|---:|---|---|:---:|:---:|:---:|:---:|
| 1 | A1, A2 | **A1** | right | not yet → not yet | 0.150 → 0.511 |  |
| 2 | A1, A2 | **A1** | wrong | not yet → known | 0.511 → 0.298 |  |
| 3 | A1, A2 | **A1** | right | known → known | 0.298 → 0.683 |  |
| 4 | A1, A2 | **A1** | right | known → known | 0.683 → 0.909 | yes |
| 5 | A2, B1 | **A2** | wrong | not yet → known | 0.150 → 0.218 |  |
| 6 | A2, B1 | **B1** | right | known → known | 0.150 → 0.511 |  |
| 7 | A2, B1 | **B1** | right | known → known | 0.511 → 0.832 |  |
| 8 | A2, B1 | **A2** | right | known → known | 0.218 → 0.601 |  |
| 9 | A2, B1 | **A2** | right | known → known | 0.601 → 0.876 |  |
| 10 | A2, B1 | **B1** | right | known → known | 0.832 → 0.957 | yes |
| 11 | A2 | **A2** | wrong | known → known | 0.876 → 0.587 |  |
| 12 | A2 | **A2** | right | known → known | 0.587 → 0.869 |  |
| 13 | A2 | **A2** | right | known → known | 0.869 → 0.968 | yes |
| 14 | B2, B3 | **B2** | right | not yet → not yet | 0.150 → 0.511 |  |
| 15 | B2, B3 | **B3** | wrong | not yet → not yet | 0.150 → 0.218 |  |
| 16 | B2, B3 | **B2** | wrong | not yet → not yet | 0.511 → 0.298 |  |
| 17 | B2, B3 | **B2** | right | not yet → not yet | 0.298 → 0.683 |  |
| 18 | B2, B3 | **B2** | wrong | not yet → not yet | 0.683 → 0.379 |  |
| 19 | B2, B3 | **B3** | wrong | not yet → not yet | 0.218 → 0.229 |  |
| 20 | B2, B3 | **B3** | wrong | not yet → known | 0.229 → 0.230 |  |

20 questions, seed 4242, threshold 0.9. The student learned 3 concept(s) during these steps.
