# representation

30 learners on layered_40. Concepts still usable after the break: binary (permanent) 21.9, continuous 27.4, continuous + forgetting 31.2. Continuous + forgetting minus binary: +9.37, better for 30/30 learners (sign p 0.0000).

## conditions

| experiment | condition | n_learners | final_mastery | final_learned | retained_mastery | retained_usable | coverage | sd_retained_usable |
|---|---|---|---|---|---|---|---|---|
| 1_representation | binary (permanent) | 30 | 0.6108 | 4.5 | 0.5153 | 21.87 | 39.97 | 3.61 |
| 1_representation | continuous | 30 | 0.652 | 4.7 | 0.5519 | 27.37 | 40 | 3.15 |
| 1_representation | continuous + forgetting | 30 | 0.6645 | 17.67 | 0.5664 | 31.23 | 34.5 | 1.41 |

## paired

| comparison | metric | mean_diff | sd | wins | losses | n | p_sign |
|---|---|---|---|---|---|---|---|
| continuous + forgetting - binary (permanent) | final_learned | 13.17 | 3.13 | 30 | 0 | 30 | 1.863e-09 |
| continuous + forgetting - binary (permanent) | retained_usable | 9.367 | 3.801 | 30 | 0 | 30 | 1.863e-09 |
| continuous + forgetting - binary (permanent) | retained_mastery | 0.05106 | 0.01993 | 30 | 0 | 30 | 1.863e-09 |
