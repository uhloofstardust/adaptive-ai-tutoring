"""Heterogeneous students: does adaptivity start to matter?"""
import numpy as np
from models import K, SLIP, GUESS, D_E, D_H, solve, p_right

TARGET = 0.9

def step(m, a, st, rng):
    """M3 dynamics with per-student params st = (cE, beta, lr). Returns (new_m, observed_correct)."""
    cE, beta, lr = st
    d = D_E if a == 'E' else D_H
    s = solve(m, d)
    solved = rng.random() < s
    # observed answer: genuine solve answers right unless slip; otherwise lucky guess
    correct = (rng.random() > SLIP) if solved else (rng.random() < GUESS)
    if a == 'E':
        room = max(0.0, cE - m)
        m = m + lr * (0.45 if solved else 0.10) * room
    else:
        m = min(1.0, m + lr * beta * 0.45 * (1 - m)) if solved else m   # bH = 0
    return min(m, 1.0), correct

def oracle_threshold(st, grid=np.linspace(0, 1, 801)):
    """Per-student SSP optimum (vectorised value iteration). Returns switch m*."""
    cE, beta, lr = st
    sE, sH = solve(grid, D_E), solve(grid, D_H)
    room = np.maximum(0.0, cE - grid)
    E_ok, E_no = grid + lr*0.45*room, grid + lr*0.10*room
    H_ok = np.minimum(1.0, grid + lr*beta*0.45*(1-grid))
    done = grid >= TARGET
    V = np.where(done, 0, 60.0)
    for _ in range(4000):
        qE = 1 + sE*np.interp(E_ok, grid, V) + (1-sE)*np.interp(E_no, grid, V)
        # hard failure leaves m unchanged: V = 1 + sH*V(H_ok) + (1-sH)*V  ->  solve for V
        with np.errstate(divide='ignore'):
            qH = np.where(sH > 1e-9, (1 + sH*np.interp(H_ok, grid, V)) / sH, 1e9)
        newV = np.where(done, 0, np.minimum(qE, qH))
        if np.max(np.abs(newV-V)) < 1e-6: V = newV; break
        V = newV
    hard = (qH < qE) & ~done
    idx = np.where(hard)[0]
    return grid[idx[0]] if len(idx) else 1.0

def simulate(policy, students, m0s, seed, cap=200):
    """policy(state) -> 'E'/'H'; state holds history. Returns questions to TARGET (cap if never)."""
    out = []
    for i, (st, m0) in enumerate(zip(students, m0s)):
        rng = np.random.default_rng(seed + i)
        m, hist = m0, []
        t = cap
        for q in range(cap):
            a = policy(dict(m=m, hist=hist, student=i, q=q))
            m, c = step(m, a, st, rng)
            hist.append((a, c))
            if m >= TARGET: t = q + 1; break
        out.append(t)
    return np.array(out)

def population(n, seed):
    r = np.random.default_rng(seed)
    cE   = r.uniform(0.4, 0.8, n)
    beta = r.uniform(1.5, 3.0, n)
    lr   = np.exp(r.normal(0, 0.3, n))
    m0   = r.uniform(0.02, 0.30, n)
    return list(zip(cE, beta, lr)), m0
