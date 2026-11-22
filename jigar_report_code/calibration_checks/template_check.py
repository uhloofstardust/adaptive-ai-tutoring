"""How many templates the problems of each ASSISTments 2009-10 skill builder come from.

Same sets as order_check.py: main problems only (original == 1), grouped by sequence_id,
sets with at least 30 students.
Run: python3 template_check.py bkt-project/data/skill_builder_data.csv
"""
import csv
import statistics as st
import sys
from collections import defaultdict

probs, temps, studs = defaultdict(set), defaultdict(set), defaultdict(set)
with open(sys.argv[1], encoding="latin-1") as f:
    for r in csv.DictReader(f):
        if r["original"] != "1":
            continue
        s = r["sequence_id"]
        probs[s].add(r["problem_id"])
        temps[s].add(r["template_id"])
        studs[s].add(r["user_id"])

sets = [s for s in probs if len(studs[s]) >= 30]
pp = [len(probs[s]) for s in sets]
tt = [len(temps[s]) for s in sets]
print("problem sets with >=30 students:", len(sets))
print("median problems per set", st.median(pp), "| median templates per set", st.median(tt))
print("median problems per template", round(st.median([p / t for p, t in zip(pp, tt)]), 1))
print("sets made from one template:", sum(1 for x in tt if x == 1), "of", len(sets))
print("sets with 3 or fewer templates:", sum(1 for x in tt if x <= 3), "of", len(sets))
