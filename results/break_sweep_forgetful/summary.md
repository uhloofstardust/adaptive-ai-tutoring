# break_sweep_forgetful

30 average learners (half-life 7d) on layered_40. Best real tutor changes: CT + forgetting model -> adaptive review between 1d and 2d. Best oracle reference minus the best real tutor ranges -1.4 to 7.1 concepts.

## curves

| break_days | CT + binary | CT + forgetting model | adaptive review | oracle belief + CT | oracle belief + adaptive review |
|---|---|---|---|---|---|
| 0 | 9.03 | 25.33 | 24.07 | 23.97 | 18.47 |
| 1 | 7.37 | 23.03 | 22.7 | 22.37 | 18.47 |
| 2 | 5.17 | 18.63 | 19.63 | 20.17 | 18.47 |
| 3 | 2.57 | 12.27 | 14.73 | 16.67 | 18.1 |
| 4 | 0.53 | 4.53 | 6.3 | 9.07 | 13.43 |
| 5 | 0 | 0.9 | 0.73 | 0 | 3.83 |
| 6 | 0 | 0 | 0 | 0 | 0 |
| 8 | 0 | 0 | 0 | 0 | 0 |

## paired_vs_ct_binary

| break_days | comparison | metric | mean_diff | sd | wins | losses | n | p_sign |
|---|---|---|---|---|---|---|---|---|
| 0 | CT + forgetting model - CT + binary | v | 16.3 | 2.231 | 30 | 0 | 30 | 1.863e-09 |
| 0 | adaptive review - CT + binary | v | 15.03 | 1.829 | 30 | 0 | 30 | 1.863e-09 |
| 0 | oracle belief + CT - CT + binary | v | 14.93 | 1.741 | 30 | 0 | 30 | 1.863e-09 |
| 0 | oracle belief + adaptive review - CT + binary | v | 9.433 | 1.431 | 30 | 0 | 30 | 1.863e-09 |
| 1 | CT + forgetting model - CT + binary | v | 15.67 | 2.339 | 30 | 0 | 30 | 1.863e-09 |
| 1 | adaptive review - CT + binary | v | 15.33 | 1.863 | 30 | 0 | 30 | 1.863e-09 |
| 1 | oracle belief + CT - CT + binary | v | 15 | 1.894 | 30 | 0 | 30 | 1.863e-09 |
| 1 | oracle belief + adaptive review - CT + binary | v | 11.1 | 1.269 | 30 | 0 | 30 | 1.863e-09 |
| 2 | CT + forgetting model - CT + binary | v | 13.47 | 2.776 | 30 | 0 | 30 | 1.863e-09 |
| 2 | adaptive review - CT + binary | v | 14.47 | 2.047 | 30 | 0 | 30 | 1.863e-09 |
| 2 | oracle belief + CT - CT + binary | v | 15 | 1.576 | 30 | 0 | 30 | 1.863e-09 |
| 2 | oracle belief + adaptive review - CT + binary | v | 13.3 | 1.208 | 30 | 0 | 30 | 1.863e-09 |
| 3 | CT + forgetting model - CT + binary | v | 9.7 | 2.003 | 30 | 0 | 30 | 1.863e-09 |
| 3 | adaptive review - CT + binary | v | 12.17 | 1.802 | 30 | 0 | 30 | 1.863e-09 |
| 3 | oracle belief + CT - CT + binary | v | 14.1 | 1.647 | 30 | 0 | 30 | 1.863e-09 |
| 3 | oracle belief + adaptive review - CT + binary | v | 15.53 | 1.167 | 30 | 0 | 30 | 1.863e-09 |
| 4 | CT + forgetting model - CT + binary | v | 4 | 1.742 | 30 | 0 | 30 | 1.863e-09 |
| 4 | adaptive review - CT + binary | v | 5.767 | 1.96 | 30 | 0 | 30 | 1.863e-09 |
| 4 | oracle belief + CT - CT + binary | v | 8.533 | 2.432 | 30 | 0 | 30 | 1.863e-09 |
| 4 | oracle belief + adaptive review - CT + binary | v | 12.9 | 2.249 | 30 | 0 | 30 | 1.863e-09 |
| 5 | CT + forgetting model - CT + binary | v | 0.9 | 1.062 | 16 | 0 | 30 | 3.052e-05 |
| 5 | adaptive review - CT + binary | v | 0.7333 | 0.8683 | 15 | 0 | 30 | 6.104e-05 |
| 5 | oracle belief + CT - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |
| 5 | oracle belief + adaptive review - CT + binary | v | 3.833 | 0.9129 | 30 | 0 | 30 | 1.863e-09 |
| 6 | CT + forgetting model - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |
| 6 | adaptive review - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |
| 6 | oracle belief + CT - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |
| 6 | oracle belief + adaptive review - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |
| 8 | CT + forgetting model - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |
| 8 | adaptive review - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |
| 8 | oracle belief + CT - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |
| 8 | oracle belief + adaptive review - CT + binary | v | 0 | 0 | 0 | 0 | 30 | 1 |

## leader

| break_days | best_real_tutor | best_oracle_minus_best |
|---|---|---|
| 0 | CT + forgetting model | -1.37 |
| 1 | CT + forgetting model | -0.67 |
| 2 | adaptive review | 0.53 |
| 3 | adaptive review | 3.37 |
| 4 | adaptive review | 7.13 |
| 5 | none left | 2.93 |
| 6 | none left | 0 |
| 8 | none left | 0 |
