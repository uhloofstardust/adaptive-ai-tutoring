# two_by_two_120

400 learners x 120 questions on abstract, 8 concepts. S1: Q2 minus Q1 = -0.00 [-0.02, +0.01] (favours neither). S2: +0.21 [+0.12, +0.31] (favours Q2). Interaction +0.21 [+0.12, +0.31]: the size, not the sign, of the scheduler effect depends on the student (S1 favours neither, S2 favours Q2). Note the budget matters: at a budget long enough for everything to be learned anyway, every cell saturates and no scheduler can differ.

## two_by_two

| student | scheduler | sched_key | n_learners | n_steps | n_concepts | learned_mean | learned_sd | learned_frac | asked_outside_zpd |
|---|---|---|---|---|---|---|---|---|---|
| S1 | Q1 | uniform_unmastered | 400 | 120 | 8 | 7.99 | 0.09962 | 0.9988 | 29.59 |
| S1 | Q2 | uniform_zpd | 400 | 120 | 8 | 7.987 | 0.1112 | 0.9984 | 0 |
| S2 | Q1 | uniform_unmastered | 400 | 120 | 8 | 7.685 | 0.8108 | 0.9606 | 41.54 |
| S2 | Q2 | uniform_zpd | 400 | 120 | 8 | 7.897 | 0.4718 | 0.9872 | 0 |

## paired

| student | diff_Q2_minus_Q1 | ci95 | better_with_Q2 | n | favours | scheduler_matters | corr_S1_S2 | ci95_if_unpaired |
|---|---|---|---|---|---|---|---|---|
| S1 | -0.0025 | 0.01472 | 4 | 400 | neither | False |  |  |
| S2 | 0.2125 | 0.09372 | 65 | 400 | Q2 | True |  |  |
| interaction (S2 minus S1) | 0.215 | 0.09276 | -1 | 400 | - | True | 0.1433 | 0.09487 |
