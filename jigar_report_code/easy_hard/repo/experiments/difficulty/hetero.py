"""Different students: does adaptivity start to matter? Version with the proposed rule.
Each student has a cap c, a solved-hard gain J and a learning speed l. bH = 0, g = 0.45, f = 0.10."""
import numpy as np
from models import SLIP, GUESS, D_E, D_H, solve
import solve_one as SO

GOAL = 0.9
G, F = 0.45, 0.10


def step(m, a, st, rng):
    """Proposed rule with per-student params st = (c, J, l). Returns (new_m, marked_right)."""
    c, J, l = st
    d = D_E if a == 'E' else D_H
    s = solve(m, d)
    solved = rng.random() < s
    # marked answer: a real solve is marked right unless slip; otherwise a lucky guess
    correct = (rng.random() > SLIP) if solved else (rng.random() < GUESS)
    if a == 'E':
        m = min(max(m, c), m + l * (G if solved else F) * max(0.0, 1.0 - m / c))
    else:
        m = min(1.0, m + l * J * (1 - m)) if solved else m   # bH = 0
    return m, correct


def oracle_threshold(st):
    """Best single switch for this student, on a 0.01 grid, from the start 0.05 (backward induction, 20,001 levels)."""
    c, J, l = st
    return SO.best_threshold(G * l, J * l, F * l, 0.0, float(c), GOAL, m0=0.05, K=20000)['thr_best']


def simulate(policy, students, m0s, seed, cap=200):
    """policy(state) -> 'E'/'H'; state holds history. Returns questions to the goal (cap if never)."""
    out = []
    for i, (st, m0) in enumerate(zip(students, m0s)):
        rng = np.random.default_rng(seed + i)
        m, hist = m0, []
        t = cap
        for q in range(cap):
            a = policy(dict(m=m, hist=hist, student=i, q=q))
            m, c = step(m, a, st, rng)
            hist.append((a, c))
            if m >= GOAL:
                t = q + 1
                break
        out.append(t)
    return np.array(out)
