# knob_sweep

selection: 50 learners (seeds 9000+), evaluation: 100 fresh learners (seeds 12000+), layered_40. half-life 14d: published CT loses on average 17.38 topics (worst 19.16) against the best (revision, depth) per break; best single pair 3.4 (worst 10.29); half-life 7d: published CT loses on average 11.18 topics (worst 16.94) against the best (revision, depth) per break; best single pair 2.55 (worst 4.85); half-life 28d: published CT loses on average 6.05 topics (worst 16.97) against the best (revision, depth) per break; best single pair 1.56 (worst 12.71).

## fixed_settings

| half_life_days | setting | revision | depth_h | correct_in_row | mean_loss | worst_loss | breaks_within_1_of_best | n_breaks |
|---|---|---|---|---|---|---|---|---|
| 14 | published CurriculumTutor | 0 | 7.82 | 7 | 17.38 | 19.16 | 0 | 8 |
| 14 | best single revision budget | 0.3 | 7.82 | 7 | 8.08 | 10.75 | 0 | 8 |
| 14 | best single study depth | 0 | 7.82 | 7 | 17.38 | 19.16 | 0 | 8 |
| 14 | best single pair of both | 0.5 | 2 | 2 | 3.4 | 10.29 | 3 | 8 |
| 7 | published CurriculumTutor | 0 | 7.82 | 7 | 11.18 | 16.94 | 0 | 6 |
| 7 | best single revision budget | 0.5 | 7.82 | 7 | 2.62 | 5.92 | 2 | 6 |
| 7 | best single study depth | 0 | 12 | 10 | 11.03 | 17.23 | 0 | 6 |
| 7 | best single pair of both | 0.5 | 6 | 5 | 2.55 | 4.85 | 2 | 6 |
| 28 | published CurriculumTutor | 0 | 7.82 | 7 | 6.05 | 16.97 | 0 | 10 |
| 28 | best single revision budget | 0 | 7.82 | 7 | 6.05 | 16.97 | 0 | 10 |
| 28 | best single study depth | 0 | 6 | 5 | 5.52 | 21.88 | 6 | 10 |
| 28 | best single pair of both | 0.4 | 3 | 3 | 1.56 | 12.71 | 8 | 10 |
