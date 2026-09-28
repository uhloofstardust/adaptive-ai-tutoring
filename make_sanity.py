"""Produce every sanity-check artifact from the command line.

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
from cursim.sanity import (calibration, detection, mastery_curve, mismatch,
                           param_sweep, restriction_only, seed_blocks,
                           trace_table, tutor_choice, two_by_two)

OUT = "sanity_outputs"
os.makedirs(OUT, exist_ok=True)
cur = build_curriculum()


def dump(name, out):
    tables = out["tables"]
    for tn, rows in tables.items():
        if len(tables) == 1:
            stem = name
        elif tn.startswith(name) or name.startswith(tn):
            stem = name if name.startswith(tn) else tn
        else:
            stem = f"{name}_{tn}"
        pd.DataFrame(rows).to_csv(f"{OUT}/{stem}.csv", index=False)
    for fn, fig in out["figures"].items():
        fig.savefig(f"{OUT}/{name}.png", dpi=170, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        plt.close(fig)


# ---------------------------------------------------------------- checks
c1 = calibration(n_learners=100, n_steps=120, cur=cur)
dump("check1_calibration", c1)
c1_big = calibration(n_learners=400, n_steps=120, cur=cur)   # the noise check
dump("check1_calibration_400learners", c1_big)
c2 = detection(n_learners=30, n_steps=120, cur=cur)
dump("check2_detection", c2)
x22 = two_by_two(cur=cur)
dump("two_by_two", x22)
# a second budget, so the saturation claim has a source
x22b = two_by_two(n_steps=120, cur=cur)
dump("two_by_two_120", x22b)
ro = restriction_only(cur=cur)
dump("restriction_only", ro)
mc = mastery_curve(cur=cur)
dump("mastery_curve", mc)
sb = seed_blocks(cur=cur)
dump("seed_blocks", sb)
psw = param_sweep(cur=cur)
dump("param_sweep", psw)
mm = mismatch(cur=cur, vary=("p_G", "p_S", "p_T"))
dump("mismatch", mm)
tc = tutor_choice(cur=cur, vary=("p_S", "p_G"))
dump("tutor_choice", tc)

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
fig.patch.set_facecolor("#12151d")
ax.axis("off")
cells = [[r["step"], textwrap.fill(pretty_zpd(r["zpd"]), 44), name_of[r["asked"]],
          r["answer"], f"{r['true_before']} -> {r['true_after']}",
          f"{r['belief_before']:.3f} -> {r['belief_after']:.3f}",
          "yes" if r["declared_mastered"] else ""] for r in rows]
tbl = ax.table(cellText=cells,
               colLabels=["step", "ZPD before the question", "asked", "answer",
                          "true state", "tutor's belief", "declared"],
               colWidths=[0.04, 0.36, 0.14, 0.07, 0.14, 0.15, 0.08],
               loc="upper left", cellLoc="left")
tbl.auto_set_font_size(False); tbl.set_fontsize(7.5)
for (i, j), c in tbl.get_celld().items():
    c.set_edgecolor("#2a3140")
    c.set_height(0.062 if i == 0 else 0.055)
    if i == 0:
        c.set_text_props(weight="bold", color="#0d1016"); c.set_facecolor("#6f8ffb")
    else:
        c.set_facecolor("#171c26")
        c.set_text_props(color="#e6e9f0")
        if j == 3:
            c.set_text_props(
                color="#3ecf8e" if rows[i - 1]["answer"] == "right" else "#f07a54",
                weight="bold")
        elif j == 4 and rows[i - 1]["true_before"] != rows[i - 1]["true_after"]:
            c.set_facecolor("#16342a")      # the step the student actually learned
ax.set_title("One run, 20 questions: what was asked, what happened, what the tutor "
             "believed. Green row = the student learned it on that step.",
             fontsize=9, loc="left", pad=8, color="#e6e9f0")
fig.savefig(f"{OUT}/trace_20.png", bbox_inches="tight",
            facecolor=fig.get_facecolor())
plt.close(fig)

# ---------------------------------------------------------------- summary
d = c2["tables"]["detection"]
with open(f"{OUT}/summary.md", "w") as f:
    f.write("# Sanity check summary\n\n")
    f.write(f"Shared BKT parameters: `{BKT_PARAMS}`\n\n")
    f.write(f"**Check 1.** {c1['summary']}\n\n")
    f.write(f"Noise check at 4x the learners: {c1_big['summary']}\n\n")
    f.write("| belief (bin mean) | truly known | gap | n |\n|---:|---:|---:|---:|\n")
    for x in c1["tables"]["calibration"]:
        if x["n"]:
            f.write(f"| {x['mean_belief']:.3f} | {x['frac_truly_known']:.3f} | "
                    f"{x['gap']:+.3f} | {x['n']} |\n")
    f.write(f"\n**Check 2.** {c2['summary']}\n\n")
    f.write("| threshold | questions on that concept until declared | questions overall "
            "(concepts learned during the run) | false alarms, measured | "
            "predicted by calibration | of which never learned | unresolved at end "
            "(late / unreached / other) |\n|---:|---:|---:|---:|---:|---:|---:|\n")
    for x in d:
        f.write(f"| {x['threshold']:.2f} | {x['delay_on_concept_mean']:.1f} | "
                f"{x['delay_mean']:.1f} | {x['false_alarm_rate']:.1%} | "
                f"{x['predicted_false_alarm_rate']:.1%} | "
                f"{x['false_alarms_never_learned']}/{x['false_alarms']} | "
                f"{x['unresolved']} ({x['unresolved_learned_late']} / "
                f"{x['unresolved_never_reached']} / "
                f"{x['unresolved_asked_not_crossed']}) |\n")
    f.write("\n- 'Questions overall' is reported only for concepts learned during the "
            "run. For concepts known before question 1 it would measure how long the "
            "ZPD took to reach them, which is a curriculum property, not detection.\n"
            "- 'Predicted by calibration' is 1 minus the mean belief at the moment of "
            "declaration; if check 1 holds it must match the measured false-alarm rate.\n"
            "- 'Of which never learned': a falsely declared concept leaves the ZPD and is "
            "never asked again, so the student never gets the chance to learn it.\n"
            "- 'Unresolved': learned but not declared when the run ended. Every one is "
            "either learned in the last 50 questions or never reached by the ZPD.\n")
    f.write(f"\n**Trace.** {tr['summary']} See `trace_20.md` and `trace_20.png`.\n")

    f.write("\n## The 2x2: does the question-selection rule matter?\n\n")
    f.write(x22["summary"] + "\n\n")
    f.write("| student | scheduler | concepts truly known | asked outside the ZPD |\n"
            "|---|---|---:|---:|\n")
    for r in x22["tables"]["two_by_two"]:
        f.write(f"| {r['student']} | {r['scheduler']} | "
                f"{r['learned_mean']:.2f} / {r['n_concepts']} | "
                f"{r['asked_outside_zpd']:.1f} |\n")
    f.write("\n| contrast | Q2 minus Q1 | 95% CI | favours |\n|---|---:|---:|---|\n")
    for r in x22["tables"]["paired"]:
        f.write(f"| {r['student']} | {r['diff_Q2_minus_Q1']:+.2f} | "
                f"+/-{r['ci95']:.2f} | {r['favours']} |\n")

    f.write("\n### The restriction alone\n\n" + ro["summary"] + "\n\n")
    f.write("| student | unrestricted | restricted | restriction effect | 95% CI |\n"
            "|---|---:|---:|---:|---:|\n")
    for r in ro["tables"]["restriction_only"]:
        f.write(f"| {r['student']} | {r['unrestricted']:.3f} | "
                f"{r['restricted']:.3f} | {r['restriction_effect']:+.3f} | "
                f"+/-{r['ci95']:.3f} |\n")
    f.write("\n### At a longer budget\n\n" + x22b["summary"] + "\n\n")
    f.write("| student | scheduler | concepts truly known |\n|---|---|---:|\n")
    for r in x22b["tables"]["two_by_two"]:
        f.write(f"| {r['student']} | {r['scheduler']} | "
                f"{r['learned_mean']:.2f} / {r['n_concepts']} |\n")

    f.write("\n## Concepts mastered over time\n\n" + mc["summary"] + "\n\n")
    f.write("| student | scheduler | known after the budget | reached all | "
            "median questions to all | never finished |\n"
            "|---|---|---:|---:|---:|---:|\n")
    for r in mc["tables"]["questions_to_all"]:
        med = ("n/a" if r["median_questions_to_all"] != r["median_questions_to_all"]
               else f"{r['median_questions_to_all']:.0f}")
        f.write(f"| {r['student']} | {r['scheduler']} | "
                f"{r['final_mean_known']:.2f} / {r['n_concepts']} | "
                f"{r['frac_reached_all']:.0%} | {med} | "
                f"{r['n_censored']}/{r['n_learners']} |\n")
    f.write("\n| student | Q2 minus Q1, questions to full mastery | 95% CI | "
            "faster with Q2 | favours |\n|---|---:|---:|---:|---|\n")
    for r in mc["tables"]["paired"]:
        f.write(f"| {r['student']} | {r['diff_Q2_minus_Q1']:+.1f} | "
                f"+/-{r['ci95']:.1f} | {r['faster_with_Q2']}/{r['n_paired']} | "
                f"{r['favours']} |\n")
    f.write("\nSeed i is the same learner in both arms, so these are paired "
            "differences rather than two independent estimates.\n")

    f.write("\n## What should the tutor assume?\n\n" + tc["summary"] + "\n\n")
    f.write("| students vary in | spread | best fixed tutor | its Brier | "
            "oracle Brier | oracle buys | 95% CI | resolved? |\n"
            "|---|---:|---:|---:|---:|---:|---:|---|\n")
    for r in tc["tables"]["verdict"]:
        res = ("yes" if abs(r["oracle_buys_brier"]) > r["brier_ci95"] else "no")
        f.write(f"| {r['parameter']} | +/-{r['spread']:.2f} | "
                f"{r['best_fixed_value']:.2f} | {r['best_fixed_brier']:.4f} | "
                f"{r['oracle_brier']:.4f} | {r['oracle_buys_brier']:+.4f} | "
                f"+/-{r['brier_ci95']:.4f} | {res} |\n")
    f.write("\nBrier is mean (belief - truth)^2 per pair, a proper "
            "scoring rule, so it is minimised by the true probability "
            "and it does recover the true parameter at 40, 120 and 300 "
            "questions alike. Two other scores are in the CSV and are "
            "NOT used: the pooled signed calibration gap cancels "
            "per-student over- and underconfidence, which under a "
            "symmetric spread is exactly the error adapting removes; "
            "and mean |belief - truth| is improper, minimised by the "
            "median, so at 40 questions it prefers a tutor assuming "
            "p_S=0.02 to the true 0.10. The best fixed value is chosen "
            "by minimising Brier on the same run that reports it, so it "
            "is optimistic; the CSV also carries the tutor sitting at "
            "the true centre. The "
            "interval is a paired bootstrap on the DIFFERENCE between "
            "two arms that share their learners; each arm's own "
            "marginal interval (ci95_marginal) is much wider and "
            "answers a different question. 'Resolved' means the "
            "difference is larger than the interval. A difference "
            "inside the interval means this run could not resolve one "
            "of that size, not that there is none: no equivalence "
            "margin was set in advance.\n")

    f.write("\n## Does the contrast hold across independent samples?\n\n"
            + sb["summary"] + "\n")

    f.write("\n## Parameter sweep\n\n" + psw["summary"] + "\n")
    f.write("\n## Tutor / student mismatch\n\n" + mm["summary"] + "\n\n")
    f.write("| parameter | tutor's value | error | calibration gap | "
            "false alarms | delay |\n|---|---:|---:|---:|---:|---:|\n")
    for r in mm["tables"]["mismatch_one"]:
        f.write(f"| {r['parameter']} | {r['tutor_value']:.2f} | "
                f"{r['error']:+.2f} | {r['calib_gap']:+.3f} | "
                f"{r['false_alarm_rate']:.1%} | "
                f"{r['delay_on_concept_mean']:.1f} |\n")
    f.write("\n| population spread | calibration gap | false alarms | delay |\n"
            "|---:|---:|---:|---:|\n")
    for r in mm["tables"]["mismatch_population"]:
        f.write(f"| +/-{r['spread']:.2f} | {r['calib_gap']:+.3f} | "
                f"{r['false_alarm_rate']:.1%} | "
                f"{r['delay_on_concept_mean']:.1f} |\n")

print("wrote", sorted(os.listdir(OUT)))
