"""Candidate single-concept learning rules for EASY vs HARD questions.
Used by hetero.py.

Answer model is the simulator's current one:
    s_d(m)   = m ** (1 + K*d)            genuine solve probability
    P(right) = s(1-SLIP) + (1-s)*GUESS
"""
import numpy as np
K, SLIP, GUESS = 1.2, 0.07, 0.25
D_E, D_H = 0.2, 0.8

def solve(m, d):    return m ** (1 + K * d)
def p_right(m, d):  s = solve(m, d); return s * (1 - SLIP) + (1 - s) * GUESS

# Each rule: function(m, action) -> list of (prob, new_m)
def M0_current(m, a, lr=1.0):
    """Today's simulator: gain on OBSERVED correctness, toward 1, any question."""
    d = D_E if a == 'E' else D_H
    p = p_right(m, d)
    return [(p, m + lr*0.45*(1-m)), (1-p, m + lr*0.10*(1-m))]

def M1_cap_boost_observed(m, a, cE=0.6, beta=2.0, lr=1.0):
    """Naive version of the idea: easy capped at cE, hard boosted by beta,
    gain still on OBSERVED correctness (lucky guesses on hard still pay)."""
    if a == 'E':
        p = p_right(m, D_E); room = max(0.0, cE - m)
        return [(p, m + lr*0.45*room), (1-p, m + lr*0.10*room)]
    p = p_right(m, D_H)
    return [(p, min(1, m + lr*beta*0.45*(1-m))), (1-p, min(1, m + lr*beta*0.10*(1-m)))]

def M3_cap_boost_genuine(m, a, cE=0.6, beta=2.0, bH=0.0, lr=1.0):
    """The idea with a readiness condition built in: learning comes from
    GENUINELY solving (not a lucky guess). Easy: toward ceiling cE.
    Hard: toward 1, boosted, but a failed hard attempt teaches only bH."""
    if a == 'E':
        s = solve(m, D_E); room = max(0.0, cE - m)
        return [(s, m + lr*0.45*room), (1-s, m + lr*0.10*room)]
    s = solve(m, D_H)
    return [(s, min(1, m + lr*beta*0.45*(1-m))), (1-s, m + lr*bH*(1-m))]

def expected_gain(rule, m, a, **kw):
    return sum(p*(nm - m) for p, nm in rule(m, a, **kw))
