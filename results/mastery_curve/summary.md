# mastery_curve

400 learners per cell, 300 questions, paired by shared seed and shared initial known-set. S1 reaches all 8 after a median 54 questions under Q1 and 54 under Q2; paired MEAN difference +0.3 +/-2.3, paired MEDIAN difference +0.0 (unresolved at this n); S2 reaches all 8 after a median 78 questions under Q1 and 55 under Q2; paired MEAN difference -22.4 +/-4.3, paired MEDIAN difference -17.5 (Q2). Every arm gets every learner to all 8 concepts inside 300 questions, at a median of 54 (S1/Q1) to 78 (S2/Q1). Every arm asks the same fixed number of questions, so a difference here is time to latent mastery, not effort saved. The mean and median paired differences are both given because they are not interchangeable, and an interval covering zero means this run cannot resolve the sign, not that the effect is zero: the S1 contrast is a small cost to Q2 that needs far more learners than this to separate, and two_by_two and restriction_only are the places it shows up.

## questions_to_all

| student | scheduler | n_learners | n_steps | n_concepts | frac_reached_all | median_questions_to_all | mean_questions_to_all | n_censored | final_mean_known |
|---|---|---|---|---|---|---|---|---|---|
| S1 | Q1 | 400 | 300 | 8 | 1 | 54 | 57.87 | 0 | 8 |
| S1 | Q2 | 400 | 300 | 8 | 1 | 54 | 58.14 | 0 | 8 |
| S2 | Q1 | 400 | 300 | 8 | 1 | 78.5 | 86.1 | 0 | 8 |
| S2 | Q2 | 400 | 300 | 8 | 1 | 55 | 63.67 | 0 | 8 |

## paired

| student | diff_Q2_minus_Q1 | ci95 | median_diff_Q2_minus_Q1 | n_paired | n_dropped | faster_with_Q2 | sign_resolved | favours |
|---|---|---|---|---|---|---|---|---|
| S1 | 0.2675 | 2.258 | 0 | 400 | 0 | 191 | False | unresolved at this n |
| S2 | -22.43 | 4.316 | -17.5 | 400 | 0 | 297 | True | Q2 |
