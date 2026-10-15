"""Named groups of runs: the exact settings whose outputs are committed.

An entry is (output_name, experiment, parameters). Registry defaults are
tuned for quick interactive use; a suite pins the full settings, so
`python -m experiments suite <name>` regenerates `results/` exactly.
"""

SUITES = {
    "bkt_validation": [
        ("check1_calibration", "check1_calibration",
         dict(n_learners=100, n_steps=120)),
        ("check1_calibration_400learners", "check1_calibration",
         dict(n_learners=400, n_steps=120)),
        ("check2_detection", "check2_detection",
         dict(n_learners=30, n_steps=120)),
        ("two_by_two", "s1s2_x_q1q2", dict(n_learners=400, n_steps=40)),
        ("two_by_two_120", "s1s2_x_q1q2", dict(n_learners=400, n_steps=120)),
        ("restriction_only", "restriction_only",
         dict(n_learners=400, n_steps=40)),
        ("mastery_curve", "mastery_curve",
         dict(n_learners=400, n_steps=300)),
        ("seed_blocks", "seed_blocks",
         dict(n_blocks=6, n_learners=400, n_steps=300)),
        ("param_sweep", "param_sweep", dict(n_learners=30, n_steps=120)),
        ("mismatch", "mismatch",
         dict(n_learners=200, n_steps=120, vary=("p_G", "p_S", "p_T"))),
        ("tutor_choice", "tutor_choice",
         dict(n_learners=600, n_steps=120, vary=("p_S", "p_G"))),
        ("trace_20_steps", "trace_20_steps",
         dict(n_steps=20, threshold=0.9, seed=4242)),
    ],
    "forgetting": [
        ("curriculum_graph", "curriculum_graph", {}),
        ("representation", "representation", dict(n_learners=30)),
        ("forgetting_worlds", "forgetting_worlds", dict(n_learners=30)),
        ("learner_types", "learner_types", dict(n_learners=30)),
        ("halflife_sweep", "halflife_sweep", dict(n_learners=30)),
        ("belief_schedulers", "belief_schedulers", dict(n_learners=30)),
    ],
}
