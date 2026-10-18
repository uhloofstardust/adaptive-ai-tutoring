# knob_sweep_spare

selection: 50 learners (seeds 9000+), evaluation: 100 fresh learners (seeds 12000+), layered_40. half-life 14d: published CT loses on average 18.05 topics (worst 20.3) against the best (revision, depth) per break; best single pair 2.06 (worst 8.45); half-life 7d: published CT loses on average 11.18 topics (worst 16.94) against the best (revision, depth) per break; best single pair 2.55 (worst 4.85); half-life 28d: published CT loses on average 6.21 topics (worst 18.44) against the best (revision, depth) per break; best single pair 0.44 (worst 4.65).

## fixed_settings

| half_life_days | setting | revision | depth_h | correct_in_row | mean_loss | worst_loss | breaks_within_1_of_best | n_breaks |
|---|---|---|---|---|---|---|---|---|
| 14 | published CurriculumTutor | 0 | 7.82 | 7 | 18.05 | 20.3 | 0 | 8 |
| 14 | best single revision budget | 0.3 | 7.82 | 7 | 8.74 | 11.17 | 0 | 8 |
| 14 | best single study depth | 0 | 2 | 2 | 2.62 | 8.14 | 3 | 8 |
| 14 | best single pair of both | 0.3 | 2 | 2 | 2.06 | 8.45 | 6 | 8 |
| 7 | published CurriculumTutor | 0 | 7.82 | 7 | 11.18 | 16.94 | 0 | 6 |
| 7 | best single revision budget | 0.5 | 7.82 | 7 | 2.62 | 5.92 | 2 | 6 |
| 7 | best single study depth | 0 | 1 | 1 | 8.21 | 9.55 | 0 | 6 |
| 7 | best single pair of both | 0.5 | 6 | 5 | 2.55 | 4.85 | 2 | 6 |
| 28 | published CurriculumTutor | 0 | 7.82 | 7 | 6.21 | 18.44 | 0 | 10 |
| 28 | best single revision budget | 0 | 7.82 | 7 | 6.21 | 18.44 | 0 | 10 |
| 28 | best single study depth | 0 | 2 | 2 | 0.55 | 3.94 | 8 | 10 |
| 28 | best single pair of both | 0.1 | 3 | 3 | 0.44 | 4.65 | 9 | 10 |
