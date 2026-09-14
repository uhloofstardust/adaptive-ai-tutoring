"""The one place BKT parameters live.

Both the plain BKT student (learner.py) and the BKT tutor (mastery.py)
read from here, so "tutor and student share the same parameters" is a
fact of the code rather than something to remember to keep in sync.
"""

BKT_PARAMS = dict(
    p_L0=0.15,   # chance a concept is known before any practice
    p_T=0.12,    # chance an unknown concept becomes known after one question
    p_G=0.25,    # chance of a correct answer while unknown (4-option MCQ)
    p_S=0.10,    # chance of a wrong answer while known
)
