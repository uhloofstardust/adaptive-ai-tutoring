"""Control for the ported solver, against three saved grids.
my_bracket_2e6: goal .9, start .05, K = 2e6, independent recheck solver.
goal_grid: goals .9 and .8, K = 2e5, a second independent solver. lam_grid: speed and start, K = 2e5, the same solver."""
import csv
import math
import os
import random
import sys

import solve_one as SO

SW, RF = os.environ['SW'], os.environ['RF']
rd = random.Random(20261106)
bad = 0


def close(a, b, tol):
    if math.isinf(a) or math.isinf(b):
        return math.isinf(a) and math.isinf(b)
    return abs(a - b) <= tol


def fl(x):
    return float('inf') if x in ('inf', '') else float(x)


B = list(csv.DictReader(open(f'{SW}/verify_sweep/my_bracket_2e6.csv')))
n = 0
for x in rd.sample(B, 40):
    a = [float(x[k]) for k in 'g J f bH c'.split()]
    o = SO.solve_cell(*a, .9, 1., (.05,))[0]
    n += 1
    checks = [close(o['best_hi'], fl(x['best_hi']), 1e-9), close(o['best_lo'], fl(x['best_lo']), 1e-9),
              o['hard_start'] == int(x['hard_start_hi']), o['pattern'] == x['visited_hi'],
              close(o['ever_hard'], fl(x['ever_hard_hi']), 1e-9), close(o['right'], fl(x['right_hi']), 1e-9),
              close(o['hard'], (fl(x['hard_hi']) + fl(x['hard_lo'])) / 2, 1e-9),
              close(o['easy'], (fl(x['easy_hi']) + fl(x['easy_lo'])) / 2, 1e-9)]
    if not all(checks):
        bad += 1
        print('bracket differs', a, checks, o, flush=True)
print('bracket cells', n, 'bad so far', bad, flush=True)

G = list(csv.DictReader(open(f'{RF}/goal_grid.csv')))
K = 200000
n = 0
for x in rd.sample(G, 120):
    a = [float(x[k]) for k in 'g J f bH c'.split()]
    goal = float(x['goal'])
    i0 = int(round(.05 * K))
    V, A = SO.backward(*a, K, goal, 0, False, 0.)
    E, _ = SO.backward(*a, K, goal, 1, False, 0.)
    n += 1
    if not (close(float(V[i0]), fl(x['best']), 1e-9) and int(A[i0]) == int(x['hs']) and close(float(E[i0]), fl(x['easy']), 1e-9)):
        bad += 1
        print('goal grid differs', goal, a, V[i0], x['best'], A[i0], x['hs'], E[i0], x['easy'], flush=True)
print('goal grid cells', n, 'bad so far', bad, flush=True)

L = list(csv.DictReader(open(f'{RF}/lam_grid.csv')))
n = 0
for x in rd.sample(L, 60):
    g, J, f, b, c = [float(x[k]) for k in 'g J f bH c'.split()]
    i0 = int(round(.05 * K))
    for lam in (1., .5, .25):
        V, A = SO.backward(g * lam, J * lam, f * lam, b * lam, c, K, .9, 0, False, 0.)
        n += 1
        if not (close(float(V[i0]), fl(x[f'best{lam}']), 1e-9) and int(A[i0]) == int(x[f'hs{lam}'])):
            bad += 1
            print('speed grid differs', lam, g, J, f, b, c, V[i0], x[f'best{lam}'], flush=True)
    V, A = SO.backward(g, J, f, b, c, K, .9, 0, False, 0.)
    for m0 in (.3, .65):
        n += 1
        if int(A[int(round(m0 * K))]) != int(x[f'hs_m{m0}']):
            bad += 1
            print('start differs', m0, g, J, f, b, c, flush=True)
print('speed and start checks', n, 'total bad', bad, flush=True)

# one threshold sanity: at a setting where the best plan has one switch, the threshold plan must equal it closely
t = SO.best_threshold(.45, .9, .10, 0., .6, .9)
print('threshold check at baseline c=.6', t, flush=True)
if t['thr_value'] < t['best_K2e5'] - 1e-9:
    bad += 1
    print('threshold plan beat the best plan', flush=True)
sys.exit(1 if bad else 0)
