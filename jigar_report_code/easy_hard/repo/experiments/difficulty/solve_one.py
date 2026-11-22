"""One-concept solver: backward induction on a very fine level set. The next state is rounded down and up,
which gives an upper and a lower bound on the value (a bracket). Port of verify_sweep/mysolver.py with the goal,
the start and the speed as arguments. Speed multiplies all four factors and leaves c alone.
"""
import math

import numpy as np
from numba import njit

EE, EH = 1.24, 1.96     # 1 + 1.2 d, d = .2 / .8
SLIP_OK, GUESS = 0.93, 0.25
K_DEFAULT = 2000000


@njit(cache=True)
def _idx(t, K, up):
    x = t * K
    if up:
        return int(math.ceil(x - 1e-7))
    return int(math.floor(x + 1e-7))


@njit(cache=True)
def _q(i, p1, j1, p2, j2, V):
    rest = 1.0
    selfp = 0.0
    if p1 > 0.0:
        if j1 == i:
            selfp += p1
        else:
            rest += p1 * V[j1]
    if p2 > 0.0:
        if j2 == i:
            selfp += p2
        else:
            rest += p2 * V[j2]
    if selfp >= 1.0 - 1e-14:
        return np.inf
    return rest / (1.0 - selfp)


@njit(cache=True)
def backward(g, J, f, bH, c, K, goal, mode, up, thr):
    """mode 0 best, 1 easy only, 2 hard only, 3 easy below thr and hard from thr on."""
    T = int(round(goal * K))
    V = np.zeros(T + 1)
    A = np.zeros(T + 1, dtype=np.int8)
    for i in range(T - 1, -1, -1):
        m = i / K
        sE = m ** EE
        sH = m ** EH
        room = max(0.0, 1.0 - m / c)
        top = max(m, c)
        eok = min(top, m + g * room)
        eno = min(top, m + f * room)
        hok = min(1.0, m + J * (1.0 - m))
        hno = min(1.0, m + bH * (1.0 - m))
        if mode != 2 and not (mode == 3 and m >= thr):
            qE = _q(i, sE, min(_idx(eok, K, up), T), 1.0 - sE, min(_idx(eno, K, up), T), V)
        else:
            qE = np.inf
        if mode != 1 and not (mode == 3 and m < thr):
            qH = _q(i, sH, min(_idx(hok, K, up), T), 1.0 - sH, min(_idx(hno, K, up), T), V)
        else:
            qH = np.inf
        if mode == 0:
            if qH < qE:
                V[i] = qH
                A[i] = 1
            else:
                V[i] = qE
                A[i] = 0
        elif mode == 1:
            V[i] = qE
        elif mode == 2:
            V[i] = qH
            A[i] = 1
        else:
            if m >= thr:
                V[i] = qH
                A[i] = 1
            else:
                V[i] = qE
    return V, A


@njit(cache=True)
def forward(g, J, f, bH, c, K, goal, m0, A, up):
    T = int(round(goal * K))
    i0 = int(round(m0 * K))
    inflow = np.zeros(T + 1)
    pre = np.zeros(T + 1)
    vis = np.zeros(T)
    qE = qH = rE = rH = ever = 0.0
    if i0 >= T:
        return qE, qH, rE, rH, ever, vis
    inflow[i0] = 1.0
    pre[i0] = 1.0
    for i in range(i0, T):
        if inflow[i] <= 0.0:
            continue
        m = i / K
        h = A[i] == 1
        s = m ** (EH if h else EE)
        if h:
            ok = min(1.0, m + J * (1.0 - m))
            no = min(1.0, m + bH * (1.0 - m))
        else:
            room = max(0.0, 1.0 - m / c)
            top = max(m, c)
            ok = min(top, m + g * room)
            no = min(top, m + f * room)
        j1 = min(_idx(ok, K, up), T)
        j2 = min(_idx(no, K, up), T)
        selfp = (s if j1 == i else 0.0) + ((1.0 - s) if j2 == i else 0.0)
        if selfp >= 1.0 - 1e-14:
            vis[i] = np.inf
            continue
        v = inflow[i] / (1.0 - selfp)
        vis[i] = v
        if j1 != i:
            inflow[j1] += v * s
        if j2 != i:
            inflow[j2] += v * (1.0 - s)
        pr = SLIP_OK * s + GUESS * (1.0 - s)
        if h:
            qH += v
            rH += v * pr
            ever += pre[i]
        else:
            qE += v
            rE += v * pr
            vp = pre[i] / (1.0 - selfp)
            if j1 != i:
                pre[j1] += vp * s
            if j2 != i:
                pre[j2] += vp * (1.0 - s)
    return qE, qH, rE, rH, ever, vis


def compress(seq):
    out = ''
    for a in seq:
        if not out or out[-1] != a:
            out += a
    return out


def solve_cell(g, J, f, bH, c, goal, speed, starts, K=K_DEFAULT):
    """One row per start. Bracket on best, easy only and hard only. Pattern and shares use the rounded-down chain."""
    G, JJ, F, B = g * speed, J * speed, f * speed, bH * speed
    T = int(round(goal * K))
    i02 = int(round(.02 * K))
    Vh, Ah = backward(G, JJ, F, B, c, K, goal, 0, False, 0.)
    Vl, Al = backward(G, JJ, F, B, c, K, goal, 0, True, 0.)
    Hh, _ = backward(G, JJ, F, B, c, K, goal, 2, False, 0.)
    Hl, _ = backward(G, JJ, F, B, c, K, goal, 2, True, 0.)
    Eh = El = None
    if c > goal:
        Eh, _ = backward(G, JJ, F, B, c, K, goal, 1, False, 0.)
        El, _ = backward(G, JJ, F, B, c, K, goal, 1, True, 0.)
    idx = np.where(Ah[i02:T] == 1)[0]
    first = (idx[0] + i02) / K if len(idx) else float('nan')
    n_changes = int(np.count_nonzero(np.diff(Ah[i02:T])))
    out = []
    for m0 in starts:
        i0 = int(round(m0 * K))
        qe, qh, re, rh, ever, vis = forward(G, JJ, F, B, c, K, goal, m0, Ah, False)
        v = np.where(vis > 1e-9)[0]
        q = qe + qh
        out.append(dict(g=g, J=J, f=f, bH=bH, c=c, goal=goal, speed=speed, start=m0,
                        best_hi=float(Vh[i0]), best_lo=float(Vl[i0]),
                        best=(float(Vh[i0]) + float(Vl[i0])) / 2,
                        easy=(float(Eh[i0]) + float(El[i0])) / 2 if Eh is not None else float('inf'),
                        hard=(float(Hh[i0]) + float(Hl[i0])) / 2,
                        hard_start=int(Ah[i0]), hard_start_lo=int(Al[i0]), first_hard=first, n_changes=n_changes,
                        pattern=compress(['H' if Ah[i] else 'E' for i in v]),
                        ever_hard=float(ever), q_easy=float(qe), q_hard=float(qh),
                        right=float((re + rh) / q) if q > 0 else float('nan')))
    return out


def best_threshold(g, J, f, bH, c, goal, m0=.05, K=200000):
    """Best single switch on a .01 grid, against the best plan at the same K and the same rounding."""
    i0 = int(round(m0 * K))
    best = float(backward(g, J, f, bH, c, K, goal, 0, False, 0.)[0][i0])
    bv, bt = np.inf, float('nan')
    for thr in np.arange(0.0, goal + 1e-9, .01):
        V, _ = backward(g, J, f, bH, c, K, goal, 3, False, float(thr))
        if V[i0] < bv - 1e-12:
            bv, bt = float(V[i0]), float(round(thr, 2))
    return dict(best_K2e5=best, thr_value=bv, thr_best=bt)
