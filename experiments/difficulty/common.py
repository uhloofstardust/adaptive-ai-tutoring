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
VERS = {  # rule id -> plain name used in the report
    'current': 'today', 'slow_bH0': 'slow easy', 'slow_bH02': 'slow easy, failed hard teaches 0.02',
    'slow_bH05': 'slow easy, failed hard teaches 0.05', 'cap60_bH0': 'easy capped at 0.6',
    'cap85_bH0': 'easy capped at 0.85', 'slow_b1': 'slow easy, smaller hard jump', 'cap60_b1': 'cap 0.6, smaller hard jump'}
