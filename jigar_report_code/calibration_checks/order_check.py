import csv, sys, statistics as st
from collections import defaultdict, Counter
path = sys.argv[1]
first = {}          # (user, sequence) -> (order_id, problem_id)
probs_per_seq = defaultdict(set)
n_orig = 0
with open(path, newline='', encoding='latin-1') as f:
    for r in csv.DictReader(f):
        if r['original'] != '1':
            continue
        n_orig += 1
        key = (r['user_id'], r['sequence_id'])
        o = int(r['order_id'])
        probs_per_seq[r['sequence_id']].add(r['problem_id'])
        if key not in first or o < first[key][0]:
            first[key] = (o, r['problem_id'])
by_seq = defaultdict(list)
for (u, s), (o, p) in first.items():
    by_seq[s].append(p)
top_share, n_first, n_probs = [], [], []
for s, ps in by_seq.items():
    if len(ps) < 30:
        continue
    c = Counter(ps)
    top_share.append(c.most_common(1)[0][1] / len(ps))
    n_first.append(len(c))
    n_probs.append(len(probs_per_seq[s]))
print('main-problem rows', n_orig)
print('problem sets with >=30 students', len(top_share))
print('median share of students whose first problem is the most common first problem', round(st.median(top_share), 3))
q = sorted(top_share)
print('quartiles of that share', round(q[len(q)//4], 3), round(q[(3*len(q))//4], 3))
print('sets where >=90% start on the same problem', sum(x >= 0.9 for x in top_share))
print('sets where <=50% start on the same problem', sum(x <= 0.5 for x in top_share))
print('median distinct first problems per set', st.median(n_first), ' median problems per set', st.median(n_probs))
