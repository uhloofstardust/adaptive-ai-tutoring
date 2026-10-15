# two_by_two

400 learners x 40 questions on abstract, 8 concepts. S1: Q2 minus Q1 = -0.15 [-0.29, -0.01] (favours Q1). S2: +1.47 [+1.29, +1.64] (favours Q2). Interaction +1.62 [+1.45, +1.78]: the sign of the scheduler effect flips with the student model. Note the budget matters: at a budget long enough for everything to be learned anyway, every cell saturates and no scheduler can differ.

## two_by_two

| student | scheduler | sched_key | n_learners | n_steps | n_concepts | learned_mean | learned_sd | learned_frac | asked_outside_zpd |
|---|---|---|---|---|---|---|---|---|---|
| S1 | Q1 | uniform_unmastered | 400 | 40 | 8 | 6.152 | 1.385 | 0.7691 | 25.96 |
| S1 | Q2 | uniform_zpd | 400 | 40 | 8 | 6 | 1.354 | 0.75 | 0 |
| S2 | Q1 | uniform_unmastered | 400 | 40 | 8 | 4.395 | 1.773 | 0.5494 | 27.62 |
| S2 | Q2 | uniform_zpd | 400 | 40 | 8 | 5.86 | 1.468 | 0.7325 | 0 |

## paired

| student | diff_Q2_minus_Q1 | ci95 | better_with_Q2 | n | favours | scheduler_matters | corr_S1_S2 | ci95_if_unpaired |
|---|---|---|---|---|---|---|---|---|
| S1 | -0.1525 | 0.1398 | 116 | 400 | Q1 | True |  |  |
| S2 | 1.465 | 0.1788 | 283 | 400 | Q2 | True |  |  |
| interaction (S2 minus S1) | 1.617 | 0.1648 | -1 | 400 | - | True | 0.4868 | 0.2269 |
