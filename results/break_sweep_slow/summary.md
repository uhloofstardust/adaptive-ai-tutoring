# break_sweep_slow

30 average learners (half-life 28d) on layered_40. Best real tutor changes: CT + binary -> CT + forgetting model between 7d and 14d; CT + forgetting model -> adaptive review between 18d and 21d. Best oracle reference minus the best real tutor ranges -9.1 to 6.2 concepts.

## curves

| break_days | CT + binary | CT + forgetting model | adaptive review | oracle belief + CT | oracle belief + adaptive review |
|---|---|---|---|---|---|
| 0 | 40 | 35.07 | 30.77 | 40 | 39.87 |
| 3 | 40 | 34.9 | 30.6 | 40 | 39.87 |
| 7 | 39.73 | 34.53 | 30.13 | 40 | 39.83 |
| 14 | 32.4 | 33.23 | 29.3 | 39.17 | 39.47 |
| 18 | 17.13 | 29.9 | 27.93 | 27.67 | 29.47 |
| 21 | 5.63 | 20.7 | 21.77 | 12.63 | 11.9 |
| 23 | 1.5 | 10.67 | 13.37 | 5.4 | 3.87 |
| 25 | 0.23 | 2.9 | 4.87 | 1.2 | 0.23 |
| 28 | 0 | 0 | 0 | 0 | 0 |

## paired_vs_ct_binary

| break_days | comparison | metric | mean_diff | sd | wins | losses | n | p_sign |
|---|---|---|---|---|---|---|---|---|
| 0 | CT + forgetting model - CT + binary | v | -4.933 | 1.143 | 0 | 30 | 30 | 1.863e-09 |
| 0 | adaptive review - CT + binary | v | -9.233 | 1.223 | 0 | 30 | 30 | 1.863e-09 |
| 0 | oracle belief + CT - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |
| 0 | oracle belief + adaptive review - CT + binary | v | -0.1333 | 0.3457 | 0 | 4 | 30 | 0.125 |
| 3 | CT + forgetting model - CT + binary | v | -5.1 | 1.062 | 0 | 30 | 30 | 1.863e-09 |
| 3 | adaptive review - CT + binary | v | -9.4 | 1.221 | 0 | 30 | 30 | 1.863e-09 |
| 3 | oracle belief + CT - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |
| 3 | oracle belief + adaptive review - CT + binary | v | -0.1333 | 0.3457 | 0 | 4 | 30 | 0.125 |
| 7 | CT + forgetting model - CT + binary | v | -5.2 | 1.186 | 0 | 30 | 30 | 1.863e-09 |
| 7 | adaptive review - CT + binary | v | -9.6 | 1.248 | 0 | 30 | 30 | 1.863e-09 |
| 7 | oracle belief + CT - CT + binary | v | 0.2667 | 0.5208 | 7 | 0 | 30 | 0.01562 |
| 7 | oracle belief + adaptive review - CT + binary | v | 0.1 | 0.6618 | 6 | 4 | 30 | 0.7539 |
| 14 | CT + forgetting model - CT + binary | v | 0.8333 | 2.73 | 17 | 8 | 30 | 0.1078 |
| 14 | adaptive review - CT + binary | v | -3.1 | 2.44 | 2 | 23 | 30 | 1.943e-05 |
| 14 | oracle belief + CT - CT + binary | v | 6.767 | 2.738 | 30 | 0 | 30 | 1.863e-09 |
| 14 | oracle belief + adaptive review - CT + binary | v | 7.067 | 2.49 | 30 | 0 | 30 | 1.863e-09 |
| 18 | CT + forgetting model - CT + binary | v | 12.77 | 3.441 | 30 | 0 | 30 | 1.863e-09 |
| 18 | adaptive review - CT + binary | v | 10.8 | 3.347 | 30 | 0 | 30 | 1.863e-09 |
| 18 | oracle belief + CT - CT + binary | v | 10.53 | 3.794 | 30 | 0 | 30 | 1.863e-09 |
| 18 | oracle belief + adaptive review - CT + binary | v | 12.33 | 2.963 | 30 | 0 | 30 | 1.863e-09 |
| 21 | CT + forgetting model - CT + binary | v | 15.07 | 2.912 | 30 | 0 | 30 | 1.863e-09 |
| 21 | adaptive review - CT + binary | v | 16.13 | 3.159 | 30 | 0 | 30 | 1.863e-09 |
| 21 | oracle belief + CT - CT + binary | v | 7 | 3.414 | 29 | 0 | 30 | 3.725e-09 |
| 21 | oracle belief + adaptive review - CT + binary | v | 6.267 | 3.513 | 29 | 0 | 30 | 3.725e-09 |
| 23 | CT + forgetting model - CT + binary | v | 9.167 | 2.245 | 30 | 0 | 30 | 1.863e-09 |
| 23 | adaptive review - CT + binary | v | 11.87 | 1.756 | 30 | 0 | 30 | 1.863e-09 |
| 23 | oracle belief + CT - CT + binary | v | 3.9 | 1.826 | 28 | 0 | 30 | 7.451e-09 |
| 23 | oracle belief + adaptive review - CT + binary | v | 2.367 | 1.974 | 26 | 2 | 30 | 3.032e-06 |
| 25 | CT + forgetting model - CT + binary | v | 2.667 | 1.398 | 28 | 2 | 30 | 8.68e-07 |
| 25 | adaptive review - CT + binary | v | 4.633 | 0.8087 | 30 | 0 | 30 | 1.863e-09 |
| 25 | oracle belief + CT - CT + binary | v | 0.9667 | 0.9643 | 17 | 0 | 30 | 1.526e-05 |
| 25 | oracle belief + adaptive review - CT + binary | v | 0 | 0.7878 | 4 | 5 | 30 | 1 |
| 28 | CT + forgetting model - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |
| 28 | adaptive review - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |
| 28 | oracle belief + CT - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |
| 28 | oracle belief + adaptive review - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |

## leader

| break_days | best_real_tutor | best_oracle_minus_best |
|---|---|---|
| 0 | CT + binary | 0 |
| 3 | CT + binary | 0 |
| 7 | CT + binary | 0.27 |
| 14 | CT + forgetting model | 6.23 |
| 18 | CT + forgetting model | -0.43 |
| 21 | adaptive review | -9.13 |
| 23 | adaptive review | -7.97 |
| 25 | adaptive review | -3.67 |
| 28 | none left | 0 |
