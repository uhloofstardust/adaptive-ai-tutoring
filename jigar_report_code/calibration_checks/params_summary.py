# Summarise the 94 fitted Basic BKT parameter sets of Part 1.
# Usage: python3 params_summary.py bkt-project/results/params.csv
import csv, sys
rows = list(csv.DictReader(open(sys.argv[1])))
def q(v, p):
    v = sorted(v); k = (len(v) - 1) * p; f = int(k); c = min(f + 1, len(v) - 1)
    return v[f] + (v[c] - v[f]) * (k - f)
for key in ['pL0', 'pT', 'pS', 'pG']:
    v = [float(r[key]) for r in rows]
    print(key, 'n', len(v), 'q25', round(q(v, .25), 3), 'median', round(q(v, .5), 3), 'q75', round(q(v, .75), 3))
pS = [float(r['pS']) for r in rows]; pG = [float(r['pG']) for r in rows]
print('pS > 0.1:', sum(x > 0.1 + 1e-9 for x in pS))
print('outside Baker 2008 bounds (pG > 0.3 or pS > 0.1):', sum((g > 0.3 + 1e-9) or (s > 0.1 + 1e-9) for g, s in zip(pG, pS)))
