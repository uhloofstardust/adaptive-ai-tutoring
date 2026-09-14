# Step-by-step trace, one run, 20 questions

Plain BKT student and BKT tutor, shared parameters {'p_L0': 0.15, 'p_T': 0.12, 'p_G': 0.25, 'p_S': 0.1}, scheduler = uniform random over the ZPD, mastery threshold 0.9, seed 4242.

| step | ZPD before the question | asked | answer | true state | belief | declared |
|---:|---|---|:---:|:---:|:---:|:---:|
| 1 | Greetings, Numbers 1-5, Colors, Pronouns, Yes / no answers | **Numbers 1-5** | wrong | not yet → not yet | 0.150 → 0.140 |  |
| 2 | Greetings, Numbers 1-5, Colors, Pronouns, Yes / no answers | **Pronouns** | wrong | not yet → not yet | 0.150 → 0.140 |  |
| 3 | Greetings, Numbers 1-5, Colors, Pronouns, Yes / no answers | **Numbers 1-5** | wrong | not yet → not yet | 0.140 → 0.139 |  |
| 4 | Greetings, Numbers 1-5, Colors, Pronouns, Yes / no answers | **Yes / no answers** | wrong | not yet → not yet | 0.150 → 0.140 |  |
| 5 | Greetings, Numbers 1-5, Colors, Pronouns, Yes / no answers | **Greetings** | right | not yet → not yet | 0.150 → 0.462 |  |
| 6 | Greetings, Numbers 1-5, Colors, Pronouns, Yes / no answers | **Greetings** | wrong | not yet → not yet | 0.462 → 0.210 |  |
| 7 | Greetings, Numbers 1-5, Colors, Pronouns, Yes / no answers | **Colors** | right | known → known | 0.150 → 0.462 |  |
| 8 | Greetings, Numbers 1-5, Colors, Pronouns, Yes / no answers | **Yes / no answers** | right | not yet → not yet | 0.140 → 0.446 |  |
| 9 | Greetings, Numbers 1-5, Colors, Pronouns, Yes / no answers | **Numbers 1-5** | wrong | not yet → known | 0.139 → 0.139 |  |
| 10 | Greetings, Numbers 1-5, Colors, Pronouns, Yes / no answers | **Greetings** | wrong | not yet → not yet | 0.210 → 0.150 |  |
| 11 | Greetings, Numbers 1-5, Colors, Pronouns, Yes / no answers | **Greetings** | wrong | not yet → known | 0.150 → 0.140 |  |
| 12 | Greetings, Numbers 1-5, Colors, Pronouns, Yes / no answers | **Numbers 1-5** | right | known → known | 0.139 → 0.443 |  |
| 13 | Greetings, Numbers 1-5, Colors, Pronouns, Yes / no answers | **Numbers 1-5** | right | known → known | 0.443 → 0.772 |  |
| 14 | Greetings, Numbers 1-5, Colors, Pronouns, Yes / no answers | **Colors** | right | known → known | 0.462 → 0.785 |  |
| 15 | Greetings, Numbers 1-5, Colors, Pronouns, Yes / no answers | **Numbers 1-5** | right | known → known | 0.772 → 0.933 | yes |
| 16 | Greetings, Colors, Pronouns, Yes / no answers, Numbers 6-10, Time words | **Numbers 6-10** | wrong | not yet → not yet | 0.150 → 0.140 |  |
| 17 | Greetings, Colors, Pronouns, Yes / no answers, Numbers 6-10, Time words | **Numbers 6-10** | wrong | not yet → not yet | 0.140 → 0.139 |  |
| 18 | Greetings, Colors, Pronouns, Yes / no answers, Numbers 6-10, Time words | **Greetings** | right | known → known | 0.140 → 0.446 |  |
| 19 | Greetings, Colors, Pronouns, Yes / no answers, Numbers 6-10, Time words | **Greetings** | right | known → known | 0.446 → 0.774 |  |
| 20 | Greetings, Colors, Pronouns, Yes / no answers, Numbers 6-10, Time words | **Time words** | right | known → known | 0.150 → 0.462 |  |

20 questions, seed 4242, threshold 0.9. The student learned 2 concept(s) during these steps.
