"""Builds poster/summary_one_page.pdf: a short one-page summary of the
knob_sweep results with its four figures. Run from the repo root:
python poster/build_summary.py"""

import csv

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (Image, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

R = "results/knob_sweep"
fixed = list(csv.DictReader(open(f"{R}/fixed_settings.csv")))
fx = {r["setting"]: r for r in fixed if r["half_life_days"] == "14"}
ct = fx["published CurriculumTutor"]
pair = fx["best single pair of both"]
one = fx["best single revision budget"]

INK = colors.HexColor("#1F2933")
G = colors.HexColor("#14412C")
H1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=15, leading=18, textColor=G)
H2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=9.8, leading=12,
                    textColor=G, spaceBefore=4, spaceAfter=1)
B = ParagraphStyle("b", fontName="Helvetica", fontSize=8.8, leading=11, textColor=INK)
BL = ParagraphStyle("bl", parent=B, leftIndent=9)
SM = ParagraphStyle("sm", parent=B, fontSize=7.2, leading=8.6,
                    textColor=colors.HexColor("#59636E"))


def P(t, s=B):
    return Paragraph(t, s)


def bl(t):
    return Paragraph(t, BL, bulletText="•")


def img(name, w):
    from PIL import Image as PI
    iw, ih = PI.open(f"{R}/{name}.png").size
    return Image(f"{R}/{name}.png", width=w * cm, height=w * cm * ih / iw)


doc = SimpleDocTemplate("poster/summary_one_page.pdf", pagesize=A4,
                        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                        topMargin=1.1 * cm, bottomMargin=0.9 * cm,
                        title="Teaching a student who forgets: one-page summary",
                        author="sanved")
st = [
    P("Teaching a student who forgets: one-page summary", H1),
    P("Thesis work on adaptive tutoring (cursim). Results of 2026-10-18.", SM),

    P("Question", H2),
    P("Students forget during breaks. <b>If the break length is known, how should a tutor "
      "change what it does?</b> We vary two settings: <b>revision budget</b> (share of questions "
      "spent on topics already learned) and <b>study depth</b> (right answers in a row needed "
      "before moving on)."),

    P("Setup", H2),
    P("A simulated student (40 topics with prerequisites) practises 20 days, 25 questions a day, then "
      "takes a 0 to 28 day break. We count topics still usable afterwards (maximum 40), for memory "
      "half-lives of 7, 14 and 28 days. Best settings are picked on 50 students and scored on 100 new ones."),

    P("Tutors", H2),
    P("CurriculumTutor, coded exactly as in the paper (our earlier version was a stand-in, so old "
      "comparisons are retired), plus one or two settings changed. Revision 0 and depth 7 is the "
      "paper's tutor. Adaptive review is dropped."),

    P("Findings (14-day half-life)", H2),
    bl(f"<b>The published tutor is far from the best:</b> 15.4 topics after a 3-day break against 33.6 "
       f"for the best settings, {float(ct['mean_loss']):.1f} topics short on average."),
    bl("<b>Longer break, more revision:</b> best budget 0.1 (no break), 0.3 (3 days), 0.4 (7), 0.5 (10)."),
    bl("<b>Depth alone does nothing;</b> with revision, shallow depth (about 3 in a row) is best, "
       "and it deepens only for long breaks (8 at 10 days)."),
    bl(f"<b>No single setting wins everywhere:</b> the best fixed pair still loses "
       f"{float(pair['mean_loss']):.1f} topics on average, {float(pair['worst_loss']):.1f} at worst."),
    Spacer(1, 3),
    img("knob_curves", 14.6),
    P("Fig. 1. Each knob alone, one line per break length; stars mark the best setting.", SM),
    img("knob_heat", 14.6),
    P("Fig. 2. Both knobs together (darker = more topics usable); the box marks the best cell.", SM),
]
row = Table([[[img("knob_best", 9.4),
               P("Fig. 3. Best pair against break length for three memory speeds (noisy where few topics remain).", SM)],
              [img("knob_loss", 7.6),
               P("Fig. 4. Topics lost by fixed settings; the published tutor and "
                 "depth-only coincide.", SM)]]],
            colWidths=[10.0 * cm, 8.4 * cm])
row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                         ("LEFTPADDING", (0, 0), (-1, -1), 0),
                         ("RIGHTPADDING", (0, 0), (-1, -1), 4)]))
st += [row,
       P("<b>Limits:</b> simulated students and a made-up curriculum; best settings are slightly "
         "flattered by being chosen on a small group. <b>Next:</b> a tutor that sets both knobs "
         "without being told the break, then real learner logs. Details: experiment_logs.md.", B)]
doc.build(st)
