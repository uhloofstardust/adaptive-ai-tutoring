# break_sweep

30 average learners on layered_40. Best real tutor changes: CT + forgetting model -> adaptive review between 7d and 8d. Best oracle reference minus the best real tutor ranges -2.1 to 4.0 concepts.

## curves

| break_days | CT + binary | CT + forgetting model | adaptive review | oracle belief + CT | oracle belief + adaptive review |
|---|---|---|---|---|---|
| 0 | 28.87 | 32.3 | 29 | 35.8 | 28.33 |
| 1 | 26.73 | 32.07 | 28.77 | 35.63 | 28.3 |
| 2 | 24.7 | 31.77 | 28.63 | 35.4 | 28.3 |
| 3 | 21.87 | 31.23 | 28.33 | 35.13 | 28.27 |
| 5 | 15.87 | 30.23 | 27.73 | 34.2 | 28.1 |
| 7 | 6.93 | 26.77 | 25.87 | 30.57 | 28.07 |
| 8 | 3.47 | 22.4 | 23.5 | 22.07 | 27.27 |
| 9 | 0.9 | 16.5 | 18.1 | 9.67 | 18.93 |
| 10 | 0.17 | 9.33 | 11.73 | 2.13 | 9.67 |
| 11 | 0 | 3.5 | 4.57 | 0 | 2.6 |
| 12 | 0 | 0.5 | 0.77 | 0 | 0 |
| 14 | 0 | 0 | 0 | 0 | 0 |
| 21 | 0 | 0 | 0 | 0 | 0 |

## paired_vs_ct_binary

| break_days | comparison | metric | mean_diff | sd | wins | losses | n | p_sign |
|---|---|---|---|---|---|---|---|---|
| 0 | CT + forgetting model - CT + binary | v | 3.433 | 3.884 | 22 | 6 | 30 | 0.003719 |
| 0 | adaptive review - CT + binary | v | 0.1333 | 3.963 | 15 | 14 | 30 | 1 |
| 0 | oracle belief + CT - CT + binary | v | 6.933 | 3.741 | 28 | 0 | 30 | 7.451e-09 |
| 0 | oracle belief + adaptive review - CT + binary | v | -0.5333 | 3.674 | 15 | 14 | 30 | 1 |
| 1 | CT + forgetting model - CT + binary | v | 5.333 | 3.951 | 25 | 3 | 30 | 2.744e-05 |
| 1 | adaptive review - CT + binary | v | 2.033 | 3.899 | 17 | 10 | 30 | 0.2478 |
| 1 | oracle belief + CT - CT + binary | v | 8.9 | 3.642 | 30 | 0 | 30 | 1.863e-09 |
| 1 | oracle belief + adaptive review - CT + binary | v | 1.567 | 3.645 | 18 | 10 | 30 | 0.1849 |
| 2 | CT + forgetting model - CT + binary | v | 7.067 | 3.886 | 27 | 0 | 30 | 1.49e-08 |
| 2 | adaptive review - CT + binary | v | 3.933 | 3.939 | 23 | 4 | 30 | 0.0003107 |
| 2 | oracle belief + CT - CT + binary | v | 10.7 | 3.669 | 30 | 0 | 30 | 1.863e-09 |
| 2 | oracle belief + adaptive review - CT + binary | v | 3.6 | 3.701 | 24 | 4 | 30 | 0.00018 |
| 3 | CT + forgetting model - CT + binary | v | 9.367 | 3.801 | 30 | 0 | 30 | 1.863e-09 |
| 3 | adaptive review - CT + binary | v | 6.467 | 3.748 | 30 | 0 | 30 | 1.863e-09 |
| 3 | oracle belief + CT - CT + binary | v | 13.27 | 3.562 | 30 | 0 | 30 | 1.863e-09 |
| 3 | oracle belief + adaptive review - CT + binary | v | 6.4 | 3.587 | 29 | 0 | 30 | 3.725e-09 |
| 5 | CT + forgetting model - CT + binary | v | 14.37 | 3.285 | 30 | 0 | 30 | 1.863e-09 |
| 5 | adaptive review - CT + binary | v | 11.87 | 3.17 | 30 | 0 | 30 | 1.863e-09 |
| 5 | oracle belief + CT - CT + binary | v | 18.33 | 3.556 | 30 | 0 | 30 | 1.863e-09 |
| 5 | oracle belief + adaptive review - CT + binary | v | 12.23 | 3.36 | 30 | 0 | 30 | 1.863e-09 |
| 7 | CT + forgetting model - CT + binary | v | 19.83 | 2.588 | 30 | 0 | 30 | 1.863e-09 |
| 7 | adaptive review - CT + binary | v | 18.93 | 2.348 | 30 | 0 | 30 | 1.863e-09 |
| 7 | oracle belief + CT - CT + binary | v | 23.63 | 2.619 | 30 | 0 | 30 | 1.863e-09 |
| 7 | oracle belief + adaptive review - CT + binary | v | 21.13 | 2.129 | 30 | 0 | 30 | 1.863e-09 |
| 8 | CT + forgetting model - CT + binary | v | 18.93 | 2.612 | 30 | 0 | 30 | 1.863e-09 |
| 8 | adaptive review - CT + binary | v | 20.03 | 2.141 | 30 | 0 | 30 | 1.863e-09 |
| 8 | oracle belief + CT - CT + binary | v | 18.6 | 3.158 | 30 | 0 | 30 | 1.863e-09 |
| 8 | oracle belief + adaptive review - CT + binary | v | 23.8 | 2.007 | 30 | 0 | 30 | 1.863e-09 |
| 9 | CT + forgetting model - CT + binary | v | 15.6 | 2.749 | 30 | 0 | 30 | 1.863e-09 |
| 9 | adaptive review - CT + binary | v | 17.2 | 2.295 | 30 | 0 | 30 | 1.863e-09 |
| 9 | oracle belief + CT - CT + binary | v | 8.767 | 2.192 | 30 | 0 | 30 | 1.863e-09 |
| 9 | oracle belief + adaptive review - CT + binary | v | 18.03 | 2.785 | 30 | 0 | 30 | 1.863e-09 |
| 10 | CT + forgetting model - CT + binary | v | 9.167 | 1.367 | 30 | 0 | 30 | 1.863e-09 |
| 10 | adaptive review - CT + binary | v | 11.57 | 1.331 | 30 | 0 | 30 | 1.863e-09 |
| 10 | oracle belief + CT - CT + binary | v | 1.967 | 1.299 | 27 | 1 | 30 | 2.161e-07 |
| 10 | oracle belief + adaptive review - CT + binary | v | 9.5 | 1.697 | 30 | 0 | 30 | 1.863e-09 |
| 11 | CT + forgetting model - CT + binary | v | 3.5 | 1.106 | 30 | 0 | 30 | 1.863e-09 |
| 11 | adaptive review - CT + binary | v | 4.567 | 1.223 | 30 | 0 | 30 | 1.863e-09 |
| 11 | oracle belief + CT - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |
| 11 | oracle belief + adaptive review - CT + binary | v | 2.6 | 1.192 | 28 | 0 | 30 | 7.451e-09 |
| 12 | CT + forgetting model - CT + binary | v | 0.5 | 0.6823 | 12 | 0 | 30 | 0.0004883 |
| 12 | adaptive review - CT + binary | v | 0.7667 | 0.7279 | 18 | 0 | 30 | 7.629e-06 |
| 12 | oracle belief + CT - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |
| 12 | oracle belief + adaptive review - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |
| 14 | CT + forgetting model - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |
| 14 | adaptive review - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |
| 14 | oracle belief + CT - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |
| 14 | oracle belief + adaptive review - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |
| 21 | CT + forgetting model - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |
| 21 | adaptive review - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |
| 21 | oracle belief + CT - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |
| 21 | oracle belief + adaptive review - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |

## leader

| break_days | best_real_tutor | best_oracle_minus_best |
|---|---|---|
| 0 | CT + forgetting model | 3.5 |
| 1 | CT + forgetting model | 3.57 |
| 2 | CT + forgetting model | 3.63 |
| 3 | CT + forgetting model | 3.9 |
| 5 | CT + forgetting model | 3.97 |
| 7 | CT + forgetting model | 3.8 |
| 8 | adaptive review | 3.77 |
| 9 | adaptive review | 0.83 |
| 10 | adaptive review | -2.07 |
| 11 | adaptive review | -1.97 |
| 12 | none left | -0.77 |
| 14 | none left | 0 |
| 21 | none left | 0 |
