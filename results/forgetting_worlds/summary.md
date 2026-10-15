# forgetting_worlds

30 learners on layered_40. learner forgets: best is CT + forgetting model (31.2); learner does not forget: best is CT + binary (40.0).

## conditions

| experiment | condition | n_learners | final_mastery | final_learned | retained_mastery | retained_usable | coverage | sd_retained_usable |
|---|---|---|---|---|---|---|---|---|
| 2_learner_forgets | CT + binary | 30 | 0.6108 | 4.5 | 0.5153 | 21.87 | 39.97 | 3.61 |
| 2_learner_forgets | CT + forgetting model | 30 | 0.6645 | 17.67 | 0.5664 | 31.23 | 34.5 | 1.41 |
| 2_learner_forgets | adaptive review | 30 | 0.6223 | 22.07 | 0.5314 | 28.33 | 33.33 | 1.27 |
| 2_learner_does_not_forget | CT + binary | 30 | 0.9913 | 40 | 0.9913 | 40 | 40 | 0 |
| 2_learner_does_not_forget | CT + forgetting model | 30 | 0.9444 | 37.23 | 0.9444 | 38.53 | 39.17 | 0.9 |
| 2_learner_does_not_forget | adaptive review | 30 | 0.8242 | 31.9 | 0.8242 | 32.9 | 35.47 | 1.18 |

## paired

| world | comparison | metric | mean_diff | sd | wins | losses | n | p_sign |
|---|---|---|---|---|---|---|---|---|
| learner forgets | CT + forgetting model - CT + binary | retained_usable | 9.367 | 3.801 | 30 | 0 | 30 | 1.863e-09 |
| learner forgets | adaptive review - CT + binary | retained_usable | 6.467 | 3.748 | 30 | 0 | 30 | 1.863e-09 |
| learner does not forget | CT + forgetting model - CT + binary | retained_usable | -1.467 | 0.8996 | 0 | 27 | 30 | 1.49e-08 |
| learner does not forget | adaptive review - CT + binary | retained_usable | -7.1 | 1.185 | 0 | 30 | 30 | 1.863e-09 |
