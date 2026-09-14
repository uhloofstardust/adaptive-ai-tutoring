"""Produce every artifact Surya's mail asks for, from the command line.

    python3 make_sanity.py            -> sanity_outputs/

  check1_calibration.png / .csv
  check2_detection.png   / .csv
  trace_20.md  / trace_20.csv / trace_20.png
  summary.md   (the numbers, in words)
"""
import os
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from cursim.curriculum import build_curriculum
from cursim.params import BKT_PARAMS
from cursim.sanity import calibration, detection, trace_table

OUT = "sanity_outputs"
os.makedirs(OUT, exist_ok=True)
cur = build_curriculum()


def dump(name, out):
    for tn, rows in out["tables"].items():
        pd.DataFrame(rows).to_csv(f"{OUT}/{name}.csv", index=False)
    for fn, fig in out["figures"].items():
        fig.savefig(f"{OUT}/{name}.png", dpi=170, bbox_inches="tight")
        plt.close(fig)


# ---------------------------------------------------------------- checks
c1 = calibration(n_learners=100, n_steps=400, cur=cur)
dump("check1_calibration", c1)
c2 = detection(n_learners=30, n_steps=400, cur=cur)
dump("check2_detection", c2)

# ---------------------------------------------------------------- trace
tr = trace_table(n_steps=20, threshold=0.9, seed=4242, cur=cur)
rows = tr["tables"]["trace"]
pd.DataFrame(rows).to_csv(f"{OUT}/trace_20.csv", index=False)

name_of = {c: cur.concepts[c].name for c in cur.ids()}


def pretty_zpd(z):
    return ", ".join(name_of[c] for c in z.split(", ") if c)


md = ["| step | ZPD before the question | asked | answer | true state | belief | declared |",
      "|---:|---|---|:---:|:---:|:---:|:---:|"]
for r in rows:
    md.append(f"| {r['step']} | {pretty_zpd(r['zpd'])} | **{name_of[r['asked']]}** | "
              f"{r['answer']} | {r['true_before']} → {r['true_after']} | "
              f"{r['belief_before']:.3f} → {r['belief_after']:.3f} | "
              f"{'yes' if r['declared_mastered'] else ''} |")
with open(f"{OUT}/trace_20.md", "w") as f:
    f.write("# Step-by-step trace, one run, 20 questions\n\n")
    f.write(f"Plain BKT student and BKT tutor, shared parameters "
            f"{BKT_PARAMS}, scheduler = uniform random over the ZPD, "
            f"mastery threshold 0.9, seed 4242.\n\n")
    f.write("\n".join(md) + "\n\n" + tr["summary"] + "\n")

# rendered table image, for slides
fig, ax = plt.subplots(figsize=(13, 0.42 * len(rows) + 1.0), dpi=150)
ax.axis("off")
cells = [[r["step"], textwrap.fill(pretty_zpd(r["zpd"]), 44), name_of[r["asked"]],
          r["answer"], f"{r['true_before']} → {r['true_after']}",
          f"{r['belief_before']:.3f} → {r['belief_after']:.3f}",
          "yes" if r["declared_mastered"] else ""] for r in rows]
tbl = ax.table(cellText=cells,
               colLabels=["step", "ZPD before the question", "asked", "answer",
                          "true state", "tutor's belief", "declared"],
               colWidths=[0.04, 0.36, 0.14, 0.07, 0.14, 0.15, 0.08],
               loc="upper left", cellLoc="left")
tbl.auto_set_font_size(False); tbl.set_fontsize(7.5)
for (i, j), c in tbl.get_celld().items():
    c.set_edgecolor("#e5e7eb")
    c.set_height(0.062 if i == 0 else 0.055)
    if i == 0:
        c.set_text_props(weight="bold", color="white"); c.set_facecolor("#1f2937")
    elif j == 3:
        c.set_text_props(color="#2f855a" if rows[i - 1]["answer"] == "right" else "#b5541c",
                         weight="bold")
    elif j == 4 and rows[i - 1]["true_before"] != rows[i - 1]["true_after"]:
        c.set_facecolor("#e6f4ea")          # the step the student actually learned
ax.set_title("One run, 20 questions: what was asked, what happened, what the tutor "
             "believed. Green row = the student learned it on that step.",
             fontsize=9, loc="left", pad=8)
fig.savefig(f"{OUT}/trace_20.png", bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------- summary
d = c2["tables"]["detection"]
with open(f"{OUT}/summary.md", "w") as f:
    f.write("# Sanity check summary\n\n")
    f.write(f"Shared BKT parameters: `{BKT_PARAMS}`\n\n")
    f.write(f"**Check 1.** {c1['summary']}\n\n")
    f.write("| belief (bin mean) | truly known | gap | n |\n|---:|---:|---:|---:|\n")
    for x in c1["tables"]["calibration"]:
        if x["n"]:
            f.write(f"| {x['mean_belief']:.3f} | {x['frac_truly_known']:.3f} | "
                    f"{x['gap']:+.3f} | {x['n']} |\n")
    f.write(f"\n**Check 2.** {c2['summary']}\n\n")
    f.write("| threshold | delay (questions) | delay (on that concept) | "
            "false alarm rate | miss rate | declared |\n|---:|---:|---:|---:|---:|---:|\n")
    for x in d:
        f.write(f"| {x['threshold']:.2f} | {x['delay_mean']:.1f} | "
                f"{x['delay_on_concept_mean']:.1f} | {x['false_alarm_rate']:.1%} | "
                f"{x['miss_rate']:.1%} | {x['n_declared']}/{x['n_concepts']} |\n")
    f.write(f"\n**Trace.** {tr['summary']} See `trace_20.md` and `trace_20.png`.\n")

print("wrote", sorted(os.listdir(OUT)))
