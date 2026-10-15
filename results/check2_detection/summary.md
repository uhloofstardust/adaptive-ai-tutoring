# check2_detection

Threshold 0.5: 0.9 questions on the concept until declared, false alarms 42.9%. Threshold 0.99: 4.5 questions, false alarms 0.8%. 'Unresolved' counts concepts learned but not declared by the end of the 120-question run; every one is either learned in the last 50 questions or never reached by the ZPD, i.e. a horizon effect, not a detector failure.

## detection

| threshold | belief_at_declaration | predicted_false_alarm_rate | n_concepts | n_learned | n_declared | false_alarms | false_alarm_rate | false_alarms_never_learned | delay_mean | delay_median | n_delay | delay_on_concept_mean | n_delay_on_concept | unresolved | unresolved_rate | unresolved_learned_late | unresolved_never_reached | unresolved_asked_not_crossed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.5 | 0.5725 | 0.4275 | 240 | 239 | 240 | 103 | 0.4292 | 1 | 1.465 | 1 | 101 | 0.927 | 137 | 0 | 0 | 0 | 0 | 0 |
| 0.6 | 0.6575 | 0.3425 | 240 | 239 | 240 | 76 | 0.3167 | 1 | 1.539 | 1 | 128 | 1.183 | 164 | 0 | 0 | 0 | 0 | 0 |
| 0.7 | 0.8453 | 0.1547 | 240 | 240 | 240 | 41 | 0.1708 | 0 | 3.067 | 2 | 163 | 1.874 | 199 | 0 | 0 | 0 | 0 | 0 |
| 0.8 | 0.8792 | 0.1208 | 240 | 240 | 240 | 35 | 0.1458 | 0 | 3.556 | 3 | 169 | 2.141 | 205 | 0 | 0 | 0 | 0 | 0 |
| 0.9 | 0.9573 | 0.04269 | 240 | 240 | 240 | 16 | 0.06667 | 0 | 5.069 | 4 | 188 | 3.129 | 224 | 0 | 0 | 0 | 0 | 0 |
| 0.95 | 0.9712 | 0.02879 | 240 | 240 | 240 | 7 | 0.02917 | 0 | 5.36 | 5 | 197 | 3.348 | 233 | 0 | 0 | 0 | 0 | 0 |
| 0.99 | 0.9933 | 0.006656 | 240 | 240 | 240 | 2 | 0.008333 | 0 | 7.911 | 7 | 202 | 4.479 | 238 | 0 | 0 | 0 | 0 | 0 |
