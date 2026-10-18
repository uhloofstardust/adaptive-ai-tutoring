"""Builds poster/summary_one_page.pdf: a one-page plain-language summary of
the knob_sweep results. Run from the repo root: python poster/build_summary.py"""

import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (Image, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

R = "results/knob_sweep"
grid = list(csv.DictReader(open(f"{R}/grid.csv")))
best = list(csv.DictReader(open(f"{R}/best.csv")))
fixed = list(csv.DictReader(open(f"{R}/fixed_settings.csv")))
PAPER_H = "7.82"

# ---- chart: topics still usable against revision budget, one line per break
fig, ax = plt.subplots(figsize=(4.6, 3.3), dpi=220)
cols = {0: "#14412C", 1: "#2F7A52", 3: "#6FAE82", 5: "#E09A10",
        7: "#B4482B", 10: "#6B4FA0"}
for d, c in cols.items():
    pts = sorted((float(r["revision"]), float(r["eval_mean"])) for r in grid
                 if r["half_life_days"] == "14" and r["depth_h"] == PAPER_H
                 and int(r["break_days"]) == d)
    ax.plot(*zip(*pts), marker="o", ms=3, lw=1.8, color=c, label=f"{d}-day break")
    i = max(range(len(pts)), key=lambda k: pts[k][1])
    ax.plot([pts[i][0]], [pts[i][1]], marker="*", ms=11, color=c, mec="black", mew=.5)
ax.set_xlabel("Revision budget (share of questions spent revising)", fontsize=8)
ax.set_ylabel("Topics still usable (of 40)", fontsize=8)
ax.tick_params(labelsize=8)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(alpha=.25)
ax.legend(fontsize=7, frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.22))
fig.tight_layout()
fig.savefig("/tmp/summary_chart.png")

# ---- table rows
def pick(d, fam):
    return next(r for r in best if r["half_life_days"] == "14"
                and int(r["break_days"]) == d and r["family"] == fam)

trows = [["Break", "Published tutor", "Best revision budget alone",
          "Best revision + depth"]]
for d in (0, 1, 3, 5, 7, 10):
    rv, bo = pick(d, "revision only"), pick(d, "both")
    trows.append([f"{d} d", f"{float(bo['published_ct']):.1f}",
                  f"{float(rv['usable_eval']):.1f}  (budget {rv['best_revision']})",
                  f"{float(bo['usable_eval']):.1f}  (budget {bo['best_revision']}, "
                  f"{bo['best_correct_in_row']} in a row)"])

fx = {r["setting"]: r for r in fixed if r["half_life_days"] == "14"}
ct, one, pair = (fx["published CurriculumTutor"], fx["best single revision budget"],
                 fx["best single pair of both"])

INK = colors.HexColor("#1F2933")
G = colors.HexColor("#14412C")
H1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=15, leading=18, textColor=G)
H2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=10, leading=12,
                    textColor=G, spaceBefore=5, spaceAfter=1)
B = ParagraphStyle("b", fontName="Helvetica", fontSize=9.2, leading=11.8, textColor=INK)
BL = ParagraphStyle("bl", parent=B, leftIndent=9, bulletIndent=0)
SM = ParagraphStyle("sm", parent=B, fontSize=7.2, leading=8.8, textColor=colors.HexColor("#59636E"))
TC = ParagraphStyle("tc", parent=B, fontSize=8, leading=9.6)
TH = ParagraphStyle("th", parent=TC, fontName="Helvetica-Bold", textColor=colors.white)


def P(t, s=B):
    return Paragraph(t, s)


def bl(t):
    return Paragraph(t, BL, bulletText="•")


doc = SimpleDocTemplate("poster/summary_one_page.pdf", pagesize=A4,
                        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                        topMargin=1.2 * cm, bottomMargin=1.0 * cm,
                        title="Teaching a student who forgets: one-page summary",
                        author="sanved")
st = [P("Teaching a student who forgets: one-page summary", H1),
      P("Thesis work on adaptive tutoring (cursim simulator). Results from 2026-10-18.", SM),

      P("What we are studying", H2),
      P("Students forget. A topic learned today is partly gone after a break. A tutor picks which "
        "question to ask next, and we ask: <b>if we know how long the break will be, how should the "
        "tutor change what it does?</b> The break length is not something the tutor controls; it is "
        "the situation. We look at two things the tutor can change."),
      bl("<b>Revision budget:</b> what share of the questions go to topics already learned."),
      bl("<b>Study depth:</b> how many right answers in a row the tutor wants before it moves on "
         "to the next topic."),

      P("How we tested it", H2),
      P("A simulated student (40 made-up topics, with prerequisites) practises for 20 days, "
        "25 questions a day. Then there is a break of 0 to 28 days. We count the topics the student "
        "can still use after the break (right more than half the time; the maximum is 40). We tried "
        "three memory speeds (half-life 7, 14 and 28 days). The best setting for each break was picked "
        "on 50 students and scored on 100 new ones."),

      P("The tutors", H2),
      P("The base is <b>CurriculumTutor</b>, now coded exactly as in the paper (it picks topics with "
        "a bandit rule and decides a topic is learned with a change-detection test, needing 7 right "
        "answers in a row). Every other tutor is that same tutor with <b>one or two settings changed</b>: "
        "revision budget 0 is CurriculumTutor itself, and depth 7 in a row is the paper's depth. "
        "Nothing else differs. We found that our earlier \"CurriculumTutor\" was a stand-in, not the "
        "paper's algorithm, so the old comparisons are retired and adaptive review is dropped."),

      P("What we found (students with a 14-day memory half-life)", H2),
      bl("<b>The published tutor is far from the best.</b> After a 3-day break it keeps 15.4 topics; the "
         "best settings keep 33.6. On average over breaks it is 17 topics short."),
      bl("<b>Revision budget:</b> the longer the break, the more revision is best "
         "(0.1 with no break, 0.3 at 3 days, 0.4 at 7 days, 0.5 at 10 days)."),
      bl("<b>Study depth on its own does nothing.</b> The paper's depth is already about right "
         "when there is no revision."),
      bl("<b>Together they work:</b> with revision, \"learn it quickly (about 3 in a row), then revise\" "
         "beats \"learn it deeply\". Depth only needs to grow when the break is long (8 in a row at 10 days)."),
      bl(f"<b>No single setting is best for every break.</b> The best fixed revision budget still loses "
         f"{float(one['mean_loss']):.1f} topics on average; the best fixed pair loses "
         f"{float(pair['mean_loss']):.1f} on average and {float(pair['worst_loss']):.1f} at worst, against "
         f"{float(ct['mean_loss']):.1f} for the published tutor."),
      bl("Same pattern for 7-day students (revise 0.4 to 0.5 at once) and 28-day students "
         "(no revision until about 7 days)."),
      Spacer(1, 3)]

left = [Image("/tmp/summary_chart.png", width=8.6 * cm, height=6.15 * cm),
        P("Chart: topics still usable after the break, against the share of questions spent revising "
          "(stars = best for that break; depth as published).", SM)]
tbl = Table([[P(c, TH) for c in trows[0]]] +
            [[P(c, TC) for c in r] for r in trows[1:]],
            colWidths=[1.5 * cm, 1.9 * cm, 3.0 * cm, 3.8 * cm])
tbl.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), G),
                         ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F6F3")]),
                         ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                         ("LINEBELOW", (0, 0), (-1, -1), .3, colors.HexColor("#CBD5CF")),
                         ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
right = [P("Topics usable after the break (14-day half-life)", ParagraphStyle("t", parent=B, fontName="Helvetica-Bold")),
         Spacer(1, 2), tbl]
two = Table([[left, right]], colWidths=[8.9 * cm, 10.0 * cm])
two.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                         ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]))
st.append(two)
st += [P("Limits and next steps", H2),
       P("Simulated students only, on a made-up curriculum; no real-student data yet. The best setting for each "
         "break is slightly flattered because it was chosen on a small group (then scored on fresh students). "
         "Which topic to revise (least recently asked) and the tutor's guess and slip values are our choices. "
         "<b>Next:</b> a tutor that sets its revision budget and depth without being told the break length, "
         "then a test on real learner logs. Code and numbers: results/knob_sweep and experiment_logs.md.")]
doc.build(st)
