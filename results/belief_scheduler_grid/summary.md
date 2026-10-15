# belief_scheduler_grid

30 learners on layered_40. Baseline (CurriculumTutor, binary belief) 21.87 usable. Best cell ('oracle', 'curriculum_tutor') at 35.13. Swapping only the belief to time decay under CurriculumTutor: +9.37; swapping only the scheduler to adaptive review under the binary belief: +8.80.

## grid

| belief | scheduler | usable | ci95 | vs_baseline | wins | losses | p_sign |
|---|---|---|---|---|---|---|---|
| binary | curriculum_tutor | 21.87 | 1.29 | 0 | 0 | 0 | 1 |
| binary | continuous | 24.27 | 1.11 | 2.4 | 18 | 9 | 0.1221 |
| binary | adaptive_review | 30.67 | 1.09 | 8.8 | 29 | 0 | 3.725e-09 |
| continuous | curriculum_tutor | 27.37 | 1.13 | 5.5 | 26 | 2 | 3.032e-06 |
| continuous | continuous | 26.23 | 1.1 | 4.367 | 26 | 2 | 3.032e-06 |
| continuous | adaptive_review | 33.17 | 1.24 | 11.3 | 30 | 0 | 1.863e-09 |
| continuous_forget | curriculum_tutor | 31.23 | 0.5 | 9.367 | 30 | 0 | 1.863e-09 |
| continuous_forget | continuous | 30 | 0.65 | 8.133 | 30 | 0 | 1.863e-09 |
| continuous_forget | adaptive_review | 28.33 | 0.45 | 6.467 | 30 | 0 | 1.863e-09 |
| oracle | curriculum_tutor | 35.13 | 0.38 | 13.27 | 30 | 0 | 1.863e-09 |
| oracle | continuous | 28.03 | 0.29 | 6.167 | 28 | 0 | 7.451e-09 |
| oracle | adaptive_review | 28.27 | 0.31 | 6.4 | 29 | 0 | 3.725e-09 |
| (ignored) | random | 21.43 | 0.93 | -0.4333 | 14 | 14 | 1 |

## effects

| varied | held | comparison | metric | mean_diff | sd | wins | losses | n | p_sign |
|---|---|---|---|---|---|---|---|---|---|
| belief | curriculum_tutor | curriculum_tutor + continuous_forget - curriculum_tutor + binary | retained_usable | 9.367 | 3.801 | 30 | 0 | 30 | 1.863e-09 |
| belief | curriculum_tutor | curriculum_tutor + oracle - curriculum_tutor + continuous_forget | retained_usable | 3.9 | 1.242 | 30 | 0 | 30 | 1.863e-09 |
| belief | continuous | continuous + continuous_forget - continuous + binary | retained_usable | 5.733 | 3.629 | 27 | 2 | 30 | 1.624e-06 |
| belief | continuous | continuous + oracle - continuous + continuous_forget | retained_usable | -1.967 | 1.65 | 3 | 25 | 30 | 2.744e-05 |
| belief | adaptive_review | adaptive_review + continuous_forget - adaptive_review + binary | retained_usable | -2.333 | 2.881 | 8 | 20 | 30 | 0.0357 |
| belief | adaptive_review | adaptive_review + oracle - adaptive_review + continuous_forget | retained_usable | -0.06667 | 1.172 | 10 | 9 | 30 | 1 |
| scheduler | binary | continuous + binary - curriculum_tutor + binary | retained_usable | 2.4 | 4.782 | 18 | 9 | 30 | 0.1221 |
| scheduler | binary | adaptive_review + binary - curriculum_tutor + binary | retained_usable | 8.8 | 4.213 | 29 | 0 | 30 | 3.725e-09 |
| scheduler | continuous | continuous + continuous - curriculum_tutor + continuous | retained_usable | -1.133 | 4.1 | 10 | 16 | 30 | 0.3269 |
| scheduler | continuous | adaptive_review + continuous - curriculum_tutor + continuous | retained_usable | 5.8 | 3.745 | 27 | 3 | 30 | 8.43e-06 |
| scheduler | continuous_forget | continuous + continuous_forget - curriculum_tutor + continuous_forget | retained_usable | -1.233 | 2.079 | 8 | 19 | 30 | 0.05224 |
| scheduler | continuous_forget | adaptive_review + continuous_forget - curriculum_tutor + continuous_forget | retained_usable | -2.9 | 1.423 | 0 | 28 | 30 | 7.451e-09 |
| scheduler | oracle | continuous + oracle - curriculum_tutor + oracle | retained_usable | -7.1 | 1.029 | 0 | 30 | 30 | 1.863e-09 |
| scheduler | oracle | adaptive_review + oracle - curriculum_tutor + oracle | retained_usable | -6.867 | 0.9371 | 0 | 30 | 30 | 1.863e-09 |
