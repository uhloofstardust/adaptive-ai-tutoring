"""Shared loaders for make_figs.py and make_numbers.py. Reads only data/*.csv."""
import csv, os, statistics
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, 'data')
INF = float('inf')
import gzip, io
def _open(name):
    p = os.path.join(DATA, name)
    if os.path.exists(p): return open(p, newline='')
    return gzip.open(p + '.gz', 'rt', newline='')
def load(name):
    with _open(name) as f: return list(csv.DictReader(f))
def open_out(path):
    """Text handle for writing a CSV; .gz paths get gzip with mtime 0 (same bytes every run)."""
    if path.endswith('.gz'):
        return io.TextIOWrapper(gzip.GzipFile(path, 'wb', mtime=0), newline='')
    return open(path, 'w', newline='')
def num(v): return INF if v in ('', 'None', 'inf') else float(v)
def median(v):
    m = statistics.median(v); return m
def group(rows, *keys):
    G = defaultdict(list)
    for r in rows: G[tuple(r[k] for k in keys)].append(r)
    return G
def med_reach(rs, key):
    v = [num(r[key]) for r in rs]; return statistics.median(v), sum(x < INF for x in v) / len(v)
def paired(a_rows, b_rows, key):
    a = {r['seed']: num(r[key]) for r in a_rows}; b = {r['seed']: num(r[key]) for r in b_rows}
    s = sorted(a); ta = [a[x] for x in s]; tb = [b[x] for x in s]
    wins = sum(x < y for x, y in zip(ta, tb)); losses = sum(x > y for x, y in zip(ta, tb))
    d = [min(x, 2001) - min(y, 2001) for x, y in zip(ta, tb)]
    return wins, losses, statistics.median(d), len(s)
VERS = {  # rule id -> plain name used in the documents
    'current': 'today', 'nocap_bH0': 'no cap', 'nocap_bH02': 'no cap, failed hard teaches 0.02',
    'nocap_bH05': 'no cap, failed hard teaches 0.05', 'c60_bH0': 'cap 0.6', 'c70_bH0': 'cap 0.7',
    'c85_bH0': 'cap 0.85', 'nocap_J60': 'no cap, J = 0.6', 'c60_J60': 'cap 0.6, J = 0.6'}
def quart(v):
    """25th, 50th, 75th percentiles, with infinity for a student who never gets there."""
    v = sorted(v); n = len(v)
    def q(p):
        x = p * (n - 1); i = int(x); f = x - i
        if f == 0: return v[i]
        a, b = v[i], v[min(i + 1, n - 1)]
        return INF if INF in (a, b) else a + f * (b - a)
    return q(.25), q(.5), q(.75)
def wilson(k, n, z=1.959964):
    p = k / n; d = 1 + z * z / n; m = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** .5) / d
    return max(0.0, m - h), min(1.0, m + h)
