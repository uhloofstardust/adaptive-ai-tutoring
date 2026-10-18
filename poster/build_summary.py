"""Builds poster/summary_two_pages.pdf: a plain-language report on the
knob_sweep experiment, each figure explained, the conclusion, and which
findings can go on the poster. Run from the repo root:
python poster/build_summary.py"""

import csv

from PIL import Image as PI
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

R = "results/knob_sweep"
fixed = list(csv.DictReader(open(f"{R}/fixed_settings.csv")))
fx = {r["setting"]: r for r in fixed if r["half_life_days"] == "14"}
ct, pair, one = (fx["published CurriculumTutor"], fx["best single pair of both"],
                 fx["best single revision budget"])
f7 = {r["setting"]: r for r in fixed if r["half_life_days"] == "7"}
f28 = {r["setting"]: r for r in fixed if r["half_life_days"] == "28"}

INK = colors.HexColor("#1F2933")
G = colors.HexColor("#14412C")
GREY = colors.HexColor("#59636E")
B = ParagraphStyle("b", fontName="Helvetica", fontSize=8.6, leading=11, textColor=INK)
BL = ParagraphStyle("bl", parent=B, leftIndent=10)
H1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=15, leading=18, textColor=G)
H2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=10.5, leading=13,
                    textColor=G, spaceBefore=5, spaceAfter=2)
FT = ParagraphStyle("ft", parent=B, fontName="Helvetica-Bold", fontSize=8.8, textColor=G,
                    spaceAfter=2)
SM = ParagraphStyle("sm", parent=B, fontSize=7.4, leading=9, textColor=GREY)


def P(t, s=B):
    return Paragraph(t, s)


def bl(t):
    return Paragraph(t, BL, bulletText="•")


def img(name, w):
    iw, ih = PI.open(f"{R}/{name}.png").size
    return Image(f"{R}/{name}.png", width=w * cm, height=w * cm * ih / iw)


def fig(name, w, title, paras):
    left = [img(name, w)]
    right = [P(title, FT)] + [P(t) for t in paras]
    t = Table([[left, right]], colWidths=[(w + 0.2) * cm, (18.0 - w - 0.2) * cm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (0, 0), 6),
                           ("RIGHTPADDING", (1, 0), (1, 0), 0),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return t


doc = SimpleDocTemplate("poster/summary_two_pages.pdf", pagesize=A4,
                        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                        topMargin=1.1 * cm, bottomMargin=0.9 * cm,
                        title="Teaching a student who forgets: summary",
                        author="sanved")
st = [
 P("Teaching a student who forgets: what we did and found", H1),
 P("Thesis work on adaptive tutoring (cursim). Results of 2026-10-18. All numbers are from simulated "
   "students.", SM),

 P("1. The question", H2),
 P("Students forget. After a break, part of what they learned is gone. A tutor chooses which question "
   "to ask next. We ask: <b>if we know how long the break will be, how should the tutor change what it "
   "does?</b> The break length is not in the tutor's control. It is the situation. What the tutor can "
   "change is two things:"),
 bl("<b>Revision budget:</b> what share of all questions go to topics the student has already learned "
    "(0 means none, 0.3 means 3 in every 10 questions)."),
 bl("<b>Study depth:</b> how many right answers in a row the tutor wants before it says "
    "\"learned\" and moves to the next topic. More in a row means a deeper first study."),

 P("2. The experiment, step by step", H2),
 bl("<b>The student</b> is simulated. There are 40 made-up topics, and some topics need others first "
    "(prerequisites). The student learns a topic by being asked about it, learns slower if its "
    "prerequisites are weak, and forgets over time. We use three kinds of student: memory half-life "
    "7, 14 and 28 days (half-life = days until half of what they know is gone)."),
 bl("<b>Practice:</b> 20 days, 25 questions a day (500 questions). The tutor only sees the answers "
    "(right or wrong), never what the student truly knows."),
 bl("<b>Break:</b> 0 to 28 days with no questions."),
 bl("<b>Score:</b> the number of <b>usable topics</b> after the break: topics the student would now "
    "answer right more than half the time. The maximum is 40."),
 bl("<b>The tutors.</b> The base is <b>CurriculumTutor</b>, coded exactly as in its paper: it picks "
    "which topic to ask with a bandit rule, and decides a topic is learned after 7 right answers in a "
    "row (a change-detection test). Every other tutor is this tutor with the revision budget and/or "
    "the study depth changed, and nothing else. Budget 0 with depth 7 is the published tutor itself. "
    "(We found our earlier \"CurriculumTutor\" was a stand-in, not the paper's algorithm. Old "
    "comparisons are retired and adaptive review is dropped.)"),
 bl("<b>Choosing the best setting.</b> For each break length we try 7 revision budgets (0 to 0.6) and "
    "10 depths (1 to 18 in a row), pick the best on 50 students, and score it on 100 different "
    "students. So the numbers are not flattered by the picking."),

 P("3. What each plot shows (14-day memory half-life)", H2),
 fig("knob_curves", 11.0, "Fig. 1: each setting on its own",
     ["<b>Left:</b> how many topics are usable (up) as we spend more of the questions on revision "
      "(right). Each line is one break length (0 to 10 days), and the star is the best point.",
      "<b>Reading it:</b> for a short break the peak is at a small budget (0.1 to 0.2). For a 10-day "
      "break the peak moves to 0.5. Longer break, more revision.",
      "<b>Right:</b> the same but for study depth with no revision. Every line peaks at 7, the paper's "
      "own depth, so changing depth alone does not help. Going too shallow leaves the student with "
      "weak knowledge and nothing more is asked."]),
 fig("knob_heat", 11.0, "Fig. 2: both settings together",
     ["Each small square is one pair (revision budget across, study depth up). Darker green means more "
      "topics usable. The black box is the best pair. Panels are 0, 3 and 7 day breaks.",
      "<b>Reading it:</b> the dark area is near the bottom (shallow study) and towards the right (more revision): a <b>shallow first study (2 to 4 in a "
      "row)</b> with a <b>good amount of revision</b>. As the break grows, the dark area shifts to more "
      "revision and the whole picture gets paler, since less survives.",
      "(The box is the best on the 100 test students, so it can be a little higher than the numbers "
      "in the findings, which pick on other students.)"]),
 PageBreak(),
 fig("knob_best", 11.0, "Fig. 3: the best pair, for each break",
     ["For each break length (across) we show the revision budget (left plot) and study depth (right "
      "plot) of the best pair, for three kinds of student.",
      "<b>Reading it:</b> the best budget goes up with the break. Students who forget fast (7-day "
      "half-life) need lots of revision from the start. Students with good memory (28-day) need "
      "little (0 to 0.1) for the first 5 days. Depth grows only for long breaks. Both plots are jumpy "
      "for long breaks because few topics survive, so differences are small."]),
 fig("knob_loss", 8.9, "Fig. 4: what a fixed choice costs",
     ["For each break (across), how many topics we lose (up) if we use one fixed setting instead of "
      "the best one for that break.",
      "<b>Reading it:</b> the published tutor (brown, hidden under the depth-only line) loses 17 to 19 "
      "topics at almost every break. The best fixed revision budget (blue) still loses 5 to 11. The "
      "best fixed pair (orange) is close at short breaks but loses about 10 at 7 to 10 days. The dip "
      "slightly below 0 at 3 days is just luck in picking."]),

 P("4. Conclusion", H2),
 bl(f"<b>The published tutor is far from the best.</b> After a 3-day break it keeps 15.4 topics "
    f"while the best setting keeps 33.6. Averaged over breaks it is {float(ct['mean_loss']):.1f} "
    f"topics short (worst {float(ct['worst_loss']):.1f})."),
 bl("<b>Revision matters most, and the right amount depends on the break:</b> 0.1 with no break, 0.3 at "
    "3 days, 0.4 at 7 days, 0.5 at 10 days. Revision alone adds 9 to 13 topics."),
 bl("<b>Study depth only helps together with revision.</b> With revision, \"learn quickly (about 3 in a "
    "row), then revise\" beats \"learn deeply\". Depth should grow only when the break is long."),
 bl(f"<b>No single setting is best for every break.</b> The best fixed revision budget loses "
    f"{float(one['mean_loss']):.1f} topics on average; the best fixed pair loses "
    f"{float(pair['mean_loss']):.1f} on average and {float(pair['worst_loss']):.1f} at worst. "
    f"Same story for 7-day students ({float(f7['best single pair of both']['mean_loss']):.1f} / "
    f"{float(f7['best single pair of both']['worst_loss']):.1f}) and 28-day students "
    f"({float(f28['best single pair of both']['mean_loss']):.1f} / "
    f"{float(f28['best single pair of both']['worst_loss']):.1f})."),

 P("5. What we can put on the poster", H2),
 bl("<b>Claim 1 (new wording):</b> the best revision budget and study depth change with the break "
    "length. Back it with Fig. 1 (left) and Fig. 3; numbers 0.1 → 0.5 as the break goes 0 → 10 days."),
 bl("<b>Claim 2:</b> we can measure how far any setting is from the best at each break. Back it with "
    "Fig. 4 and the headline 15.4 vs 33.6 topics at 3 days, 17.4 topics short on average."),
 bl("<b>Extra point:</b> \"learn quickly, then revise\" beats deep first study (Fig. 2)."),
 bl("<b>Best figures:</b> Fig. 1 left, Fig. 4, plus Fig. 2 if there is room. Redraw them in poster "
    "style. The old poster draft uses the old results and must be rebuilt."),
 bl("<b>Do not claim:</b> anything about real students (this is simulation only); that depth alone "
    "helps (it does not); that the settings are the true best (best of a grid, picked on 50 students)."),
 P("<b>Limits.</b> Simulated students on a made-up curriculum. Which topic to revise (the one asked "
   "longest ago) and the tutor's guess and slip values are our choices. <b>Next:</b> a tutor that "
   "sets both settings without being told the break length, then real learner logs. Details: "
   "experiment_logs.md, results/knob_sweep.", B),
]
doc.build(st)
