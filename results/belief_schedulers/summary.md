# belief_schedulers

30 learners on layered_40. Best arm: CT + time decay (31.23 concepts usable after the break). Predictive and MAPLE are not run on the time-decay belief, so they are not compared with it like for like.

## arms

| arm | scheduler | mastery | n | learned | usable | usable_ci95 | mean_mastery | covered |
|---|---|---|---|---|---|---|---|---|
| CT + binary (paper's original) | curriculum_tutor | binary | 30 | 4.5 | 21.87 | 1.291 | 0.6108 | 39.97 |
| CT + time decay | curriculum_tutor | continuous_forget | 30 | 17.67 | 31.23 | 0.503 | 0.6645 | 34.5 |
| CT + BKT forget (p_F) | curriculum_tutor | bkt_forget | 30 | 5.7 | 26.43 | 0.89 | 0.6405 | 40 |
| Predictive + BKT forget | predictive | bkt_forget | 30 | 5.467 | 27 | 0.99 | 0.6443 | 40 |
| MAPLE + BKT forget | maple | bkt_forget | 30 | 4.733 | 23.87 | 0.75 | 0.6092 | 40 |
| Naive MAPLE + BKT forget | naive_maple | bkt_forget | 30 | 4.267 | 23.4 | 1.18 | 0.6017 | 40 |

## head_to_head

| comparison | mean_diff | wins | n | p_sign |
|---|---|---|---|---|
| CT + BKT forget (p_F) - CT + time decay | -4.8 | 0 | 30 | 3.725e-09 |
| Predictive + BKT forget - CT + BKT forget (p_F) | 0.5667 | 17 | 30 | 0.4583 |
| MAPLE + BKT forget - Naive MAPLE + BKT forget | 0.4667 | 16 | 30 | 0.5716 |
| MAPLE + BKT forget - CT + BKT forget (p_F) | -2.567 | 3 | 30 | 0.0001565 |
