# seed_blocks

6 independent blocks of 400 learners, 300 questions. S1: +0.37 +/-0.57 across 6 blocks (a cost to Q2), individual blocks from -0.93 to +1.08, sign the same in all blocks: no; S2: -23.08 +/-1.36 across 6 blocks (Q2 sooner), individual blocks from -25.61 to -20.66, sign the same in all blocks: yes. A sign that holds in every block is evidence a single block's interval cannot give.

## seed_blocks

| block | seed0 | student | diff_Q2_minus_Q1 | ci95_within_block | sign_resolved_in_block | n_learners | n_steps |
|---|---|---|---|---|---|---|---|
| 0 | 4242 | S1 | 0.2675 | 2.258 | False | 400 | 300 |
| 0 | 4242 | S2 | -22.43 | 4.316 | True | 400 | 300 |
| 1 | 104242 | S1 | 0.9575 | 2.575 | False | 400 | 300 |
| 1 | 104242 | S2 | -22.56 | 3.869 | True | 400 | 300 |
| 2 | 204242 | S1 | 0.3525 | 2.377 | False | 400 | 300 |
| 2 | 204242 | S2 | -22.93 | 4.148 | True | 400 | 300 |
| 3 | 304242 | S1 | 0.4625 | 2.233 | False | 400 | 300 |
| 3 | 304242 | S2 | -25.61 | 3.877 | True | 400 | 300 |
| 4 | 404242 | S1 | -0.925 | 2.144 | False | 400 | 300 |
| 4 | 404242 | S2 | -24.3 | 4.595 | True | 400 | 300 |
| 5 | 504242 | S1 | 1.077 | 2.163 | False | 400 | 300 |
| 5 | 504242 | S2 | -20.66 | 4.049 | True | 400 | 300 |

## across_blocks

| student | n_blocks | mean_across_blocks | ci95_across_blocks | blocks_favouring_Q2 | blocks_favouring_Q1 | sign_agrees_in_all_blocks | min_block | max_block |
|---|---|---|---|---|---|---|---|---|
| S1 | 6 | 0.3654 | 0.5705 | 1 | 5 | False | -0.925 | 1.077 |
| S2 | 6 | -23.08 | 1.361 | 6 | 0 | True | -25.61 | -20.66 |
