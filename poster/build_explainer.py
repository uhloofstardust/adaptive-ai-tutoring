"""Builds poster/poster_explainer.pdf, a plain-language guide to the poster,
from the CSVs in results/. Run from the repo root: python poster/build_explainer.py"""

import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

OUT = "poster"
R = "results"


def rows(name, table):
    return list(csv.DictReader(open(f"{R}/{name}/{table}.csv")))


gap = rows("poster_gap", "curves")
gaps = rows("poster_gap", "gaps")
rules = {r["arm"]: r for r in rows("forgetting_rules", "summary")}

SET = ["CT as published (binary)", "CT + decay belief, mastered at 0.7",
       "CT + decay belief, mastered at 0.8", "CT + decay belief, mastered at 0.9",
       "adaptive review + decay belief"]
SHORT = {SET[0]: "CurriculumTutor as published", SET[1]: "Fading guess, move on at 0.7",
         SET[2]: "Fading guess, move on at 0.8", SET[3]: "Fading guess, move on at 0.9",
         SET[4]: "Adaptive review"}
COL = dict(zip(SET, ["#B4482B", "#9FC5A8", "#3D7A5B", "#1C4A33", "#E8A020"]))
plt.rcParams.update({"font.size": 12, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 200})


def curve(hl, key):
    return [(int(r["break_days"]), float(r[key])) for r in gap
            if int(r["half_life_days"]) == hl]


def live_max(hl):
    return max(d for d, v in curve(hl, "best_possible") if v >= 1.0)


# ---- figure 1: the main graph, average learner
fig, ax = plt.subplots(figsize=(8, 4.1))
m = live_max(14) + 2
for s in SET:
    pts = [p for p in curve(14, s) if p[0] <= m]
    ax.plot(*zip(*pts), marker="o", ms=4, lw=2.2, color=COL[s], label=SHORT[s])
pts = [p for p in curve(14, "best_possible") if p[0] <= m]
ax.plot(*zip(*pts), color="black", ls="--", lw=1.6, label="Best possible at each break")
ax.set_xlabel("Days of break")
ax.set_ylabel("Topics still usable (out of 40)")
ax.set_ylim(0, 42)
ax.legend(fontsize=9.5, frameon=False)
fig.tight_layout()
fig.savefig(f"{OUT}/fig1_curves.png")
plt.close(fig)

# ---- figure 2: who is best when
fig, axes = plt.subplots(3, 1, figsize=(8, 7.6), gridspec_kw={"hspace": 0.75})
for ax, hl in zip(axes, (7, 14, 28)):
    days = [d for d, _ in curve(hl, "best_possible") if d <= live_max(hl)]
    best = dict(curve(hl, "best_possible"))
    for i, s in enumerate(SET):
        v = dict(curve(hl, s))
        for j, d in enumerate(days):
            if v[d] >= best[d] - 0.05:
                ax.barh(len(SET) - 1 - i, 1, left=j, color=COL[s], edgecolor="white", height=0.8)
    ax.set_yticks(range(len(SET)))
    ax.set_yticklabels([SHORT[s] for s in reversed(SET)], fontsize=9)
    ax.set_xticks([j + 0.5 for j in range(len(days))])
    ax.set_xticklabels(days, fontsize=9)
    ax.set_xlim(0, len(days))
    ax.set_title(f"Students whose memory halves every {hl} days", fontsize=11.5, loc="left", pad=10, fontweight="bold")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
axes[-1].set_xlabel("Days of break")
for ax in axes:
    ax.set_xlabel("Days of break")
fig.text(0.5, 0.008, "A coloured block means this setting is the best (or tied for best) at that break length.", ha="center", fontsize=9.5)
fig.subplots_adjust(left=0.3, right=0.98, top=0.95, bottom=0.1)
fig.savefig(f"{OUT}/fig2_who_wins.png")
plt.close(fig)

# ---- figure 3: cost of one fixed choice (average learner)
g = {r["setting"]: r for r in gaps if r["half_life_days"] == "14"}
fig, ax = plt.subplots(figsize=(8, 4.2))
ys = range(len(SET))
ax.barh([y + 0.2 for y in ys], [float(g[s]["worst_gap"]) for s in SET], 0.38,
        color="#B4482B", label="Worst case (at the worst break length)")
ax.barh([y - 0.2 for y in ys], [float(g[s]["mean_gap"]) for s in SET], 0.38,
        color="#8A8F9A", label="Average over break lengths")
for y, s in zip(ys, SET):
    ax.text(float(g[s]["worst_gap"]) + 0.3, y + 0.2, g[s]["worst_gap"], va="center", fontsize=9)
    ax.text(float(g[s]["mean_gap"]) + 0.3, y - 0.2, g[s]["mean_gap"], va="center", fontsize=9)
ax.set_yticks(list(ys))
ax.set_yticklabels([SHORT[s] for s in SET], fontsize=9.5)
ax.invert_yaxis()
ax.set_xlabel("Topics lost compared with the best setting")
ax.legend(fontsize=9.5, frameon=False, loc="lower right")
fig.tight_layout()
fig.savefig(f"{OUT}/fig3_cost.png")
plt.close(fig)

# ---- figure 4: knowing exactly what the student remembers
arms = [("CT + binary", "Guess never fades\n(as published)", "#B4482B"),
        ("CT + decay belief", "Guess fades\nover time", "#3D7A5B"),
        ("CT + oracle belief", "Knows exactly what\nthe student remembers", "#6B4FA0")]
fig, axes = plt.subplots(1, 2, figsize=(8, 4))
for ax, key, title in zip(axes, ("usable_3d", "robust"),
                          ("After a 3-day break", "Average over breaks of 0 to 10 days")):
    vals = [float(rules[a[0]][key]) for a in arms]
    b = ax.bar(range(3), vals, color=[a[2] for a in arms], width=0.65)
    for x, v in enumerate(vals):
        ax.text(x, v + 0.6, f"{v:.1f}", ha="center", fontsize=10, fontweight="bold")
    ax.set_xticks(range(3))
    ax.set_xticklabels([a[1] for a in arms], fontsize=8)
    ax.set_title(title, fontsize=11)
    ax.set_ylim(0, 44)
axes[0].set_ylabel("Topics still usable (out of 40)")
fig.tight_layout()
fig.savefig(f"{OUT}/fig4_perfect.png")
plt.close(fig)

# ---- the document
INK = colors.HexColor("#1F2933")
H1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=INK, spaceBefore=4, spaceAfter=8)
H2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=colors.HexColor("#3D7A5B"), spaceBefore=10, spaceAfter=4)
B = ParagraphStyle("b", fontName="Helvetica", fontSize=11, leading=16, textColor=INK, spaceAfter=6, alignment=TA_LEFT)
BL = ParagraphStyle("bl", parent=B, leftIndent=14, bulletIndent=2, spaceAfter=3)
SM = ParagraphStyle("sm", parent=B, fontSize=9.5, leading=13, textColor=colors.HexColor("#52606D"))
BOX = ParagraphStyle("box", parent=B, fontSize=11.5, leading=17)


def P(t, s=B):
    return Paragraph(t, s)


def bullets(items):
    return [Paragraph(t, BL, bulletText="•") for t in items]


def box(text):
    t = Table([[Paragraph(text, BOX)]], colWidths=[16.4 * cm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF5F0")),
                           ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#3D7A5B")),
                           ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return t


def fig(path, caption, w=15.5):
    from PIL import Image as PI
    iw, ih = PI.open(path).size
    return KeepTogether([Image(path, width=w * cm, height=w * cm * ih / iw), P(caption, SM), Spacer(1, 6)])


def row(hl, d, key):
    return float(next(r[key] for r in gap if int(r["half_life_days"]) == hl and int(r["break_days"]) == d))


S = []
S += [P("Teaching a student who forgets", ParagraphStyle("t", parent=H1, fontSize=24, leading=28)),
      P("A plain-language guide to our poster", ParagraphStyle("st", parent=B, fontSize=13, textColor=colors.HexColor("#52606D"))),
      Spacer(1, 6),
      P("1. The point of the poster", H1),
      P("Students forget. A student who knew a topic on Monday may not remember it after a week off. "
        "But many tutoring programs choose the next question as if the student never forgets: once the student "
        "answers a topic well, the program moves on and never looks back."),
      P("We built a simulated student who forgets, and tested different ways of choosing questions. "
        "We are making two claims:"),
      box("<b>Claim 1.</b> No single way of tutoring is best for every break length. "
          "A setting that works well for a short break works badly for a long one.<br/><br/>"
          "<b>Claim 2.</b> We can measure how far each way of tutoring is from the best possible, at each break length."),
      Spacer(1, 6),
      P("<b>Why this matters.</b> The goal of our thesis is a new way of choosing questions that plans for forgetting. "
        "These two claims show why such a method is needed, and how much there is to gain."),
      P("<b>What “best possible” means here.</b> We tried five tutoring settings. At each break length, the best possible "
        "is the score of whichever setting did best at that length. It is a bar we can really reach, not a perfect score."),
      P("2. How we tested it", H1),
      P("The simulated student", H2),
      P("Real students cannot be tested again and again with the same starting point. A simulated student can. "
        "Every tutor gets exactly the same simulated students, so the comparison is fair."),
      ] + bullets([
          "For each topic, the student has a hidden “how well I know this” number from 0 (not at all) to 1 (perfectly).",
          "A right answer raises it a lot. A wrong answer raises it a little. Harder questions are harder to get right.",
          "A student learns a topic more slowly if the topics it depends on are weak.",
          "The student sometimes guesses right (25% of the time) and sometimes slips on something they know.",
          "<b>Forgetting:</b> with no practice, the number slowly falls. The <i>half-life</i> is how long it takes to lose "
          "half. For our average student it is 14 days. We also tried students with 7 days (forgetful) and 28 days (good memory).",
          "The tutor never sees the hidden number. It only sees answers, and keeps its own guess about what the student knows.",
      ]) + [
      P("The practice material (the “dataset”)", H2),
      P("We did not use real student records. The material is made up: <b>40 topics</b> (named A01, B02 and so on) with "
        "<b>290 questions</b> in <b>7 levels</b>. Some topics must be learned before others. The topic names mean nothing, "
        "so the results do not depend on any school subject."),
      P("One test", H2),
      ] + bullets([
          "The student practises in 20 daily sessions of 25 questions (500 questions in all).",
          "Then comes a <b>break</b> of 0 to 28 days with no practice.",
          "We count the <b>usable topics</b>: topics the student still knows at least 50%. The most possible is 40.",
          "We used 50 simulated students per case, never used while we were designing the tutors. "
          "We trust a difference only if it shows up across most students, not just on average.",
      ]) + [
      P("The tutors we compared", H2),
      ] + bullets([
          "<b>CurriculumTutor as published</b> (the method from the paper we are improving). Its guess about the student never fades. "
          "Once it thinks a topic is learned, it stays learned.",
          "<b>Fading guess.</b> The same tutor, but its guess about each topic slowly falls as time passes, as the student's memory does. "
          "“Move on at 0.7 / 0.8 / 0.9” means how sure the tutor must be before it stops teaching a topic. "
          "A higher number means more practice per topic, and so fewer topics covered, but a safer margin.",
          "<b>Adaptive review.</b> Goes back to topics whose guess has fallen.",
      ]) + [
      P("3. What we found", H1),
      P("Finding 1: a tutor that plans for forgetting does much better", H2),
      P(f"After a 3-day break, the published CurriculumTutor leaves the average student with "
        f"<b>{row(14, 3, SET[0]):.1f}</b> usable topics out of 40. The same tutor with a fading guess leaves "
        f"<b>{row(14, 3, SET[2]):.1f}</b>."),
      fig(f"{OUT}/fig1_curves.png",
          "Figure 1. Average student (memory half-life 14 days). Higher is better. The dashed black line is the best possible at each break length.", 14.5),
      P("Finding 2: the best setting changes with the break length (Claim 1)", H2),
      P("Look at Figure 1. No coloured line stays on the dashed line the whole way. For the average student, "
        "moving on at 0.7 is best with no break, 0.8 is best after 1 to 4 days, adaptive review is best at 5 to 6 days, "
        "and moving on at 0.9 is best at 7 to 10 days. A tutor that is careful about every topic loses on short breaks "
        "because it covers fewer topics. A relaxed tutor loses on long breaks because the topics fade."),
      fig(f"{OUT}/fig2_who_wins.png",
          "Figure 2. Which setting is best at each break length, for three kinds of student. "
          "The best setting moves to longer breaks as memory gets longer, but it keeps changing in all three.", 14),
      P("Finding 3: how much does one fixed choice cost? (Claim 2)", H2),
      P("If a tutor must pick one setting and cannot know the break length, how far is it from the best possible? "
        "For the average student, even the best single choice (adaptive review) loses "
        f"<b>{g[SET[4]]['mean_gap']}</b> topics on average and <b>{g[SET[4]]['worst_gap']}</b> at its worst. "
        f"The published CurriculumTutor loses <b>{g[SET[0]]['mean_gap']}</b> on average and up to <b>{g[SET[0]]['worst_gap']}</b>."),
      fig(f"{OUT}/fig3_cost.png",
          "Figure 3. Topics lost by each setting compared with the best setting, average student. Lower is better.", 14.5),
      P("This gap is the room for improvement. A tutor that adapts to the break length could win back part of it."),
      P("Finding 4: even a tutor that knows what the student remembers is not the best", H2),
      P("We also tried a tutor that is told exactly what the student knows. Across many break lengths it does better "
        "(28.2 against 25.6). But after a short 3-day break it does <i>worse</i> than the fading guess "
        "(35.1 against 37.0). The fading guess is a little cautious, and that caution helps. "
        "So “knowing exactly” is not a ceiling, and that is why we measure against the best setting instead."),
      fig(f"{OUT}/fig4_perfect.png", "Figure 4. A tutor that knows exactly what the student remembers, compared with the other two.", 14),
      P("Finding 5: popular review rules from research did not add anything", H2),
      P("We tried three review rules from published work on spaced repetition (review the topic with the lowest recall, "
        "review the one closest to a threshold, review in proportion to how much is forgotten). On fresh students they scored "
        "within 0.15 topics of the fading-guess tutor, which is no real difference. "
        "So simply adding a review rule is not enough. How much safety margin to keep matters more."),
      P("4. What this means, and what we did not show", H1),
      ] + bullets([
          "Next step of the thesis: a question-picking method that sets its margin and review plan for forgetting, "
          "judged over a range of possible breaks, without being told the break length.",
          "These are <b>simulated</b> students and a <b>made-up</b> curriculum. They show how tutoring methods behave. "
          "They do not prove anything about real students.",
          "“Best possible” is the best of five settings we tried, picked after seeing the results. A better setting might exist.",
          "The review rules are our own versions fitted to a curriculum with prerequisites, not the exact methods of the papers.",
          "The fading guess assumes 5% forgetting per day. For forgetful students (true rate near 9%) more margin helped; "
          "this shows that a wrongly assumed forgetting speed has a cost.",
      ]) + [
      P("Words used", H2),
      P("<b>Break:</b> days with no practice. <b>Usable topic:</b> a topic the student knows at least 50%. "
        "<b>Half-life:</b> days for the student's knowledge of an unpractised topic to halve. "
        "<b>Guess (belief):</b> what the tutor thinks the student knows. <b>Move on at 0.8:</b> the tutor stops teaching a topic "
        "once its guess reaches 0.8 out of 1.", SM),
      P("5. References", H1),
      ] + [P(t, SM) for t in [
          "Shabana, K. M., Lakshminarayanan, C., and Anil, J. K. <i>CurriculumTutor: An Adaptive Algorithm for Mastering a Curriculum.</i> "
          "(The method we are improving; copy in references/CurriculumTutor.pdf.)",
          "Ebbinghaus, H. (1885). <i>Über das Gedächtnis</i> (Memory: A Contribution to Experimental Psychology). The first measurements of forgetting.",
          "Cepeda, N. J., Vul, E., Rohrer, D., Wixted, J. T., and Pashler, H. (2008). Spacing effects in learning: a temporal ridgeline of optimal retention. <i>Psychological Science.</i>",
          "Lindsey, R. V., Shroyer, J. D., Pashler, H., and Mozer, M. C. (2014). Improving students' long-term knowledge retention through personalized review. <i>Psychological Science.</i>",
          "Settles, B., and Meeder, B. (2016). A trainable spaced repetition model for language learning. <i>ACL.</i>",
          "Reddy, S., Labutov, I., Banerjee, S., and Joachims, T. (2016). Unbounded human learning: optimal scheduling for spaced repetition. <i>KDD.</i>",
          "Tabibian, B., Upadhyay, U., De, A., Zarezade, A., Schölkopf, B., and Gomez-Rodriguez, M. (2019). Enhancing human learning via spaced repetition optimization. <i>PNAS.</i>",
          "Hunziker, A., Chen, Y., Mac Aodha, O., Gomez-Rodriguez, M., Krause, A., Perona, P., Yue, Y., and Singla, A. (2019). Teaching multiple concepts to a forgetful learner. <i>NeurIPS.</i>",
          "Nagatani, K., Zhang, Q., Sato, M., Chen, Y.-Y., Chen, F., and Ohkuma, T. (2019). Augmenting knowledge tracing by considering forgetting behavior. <i>The Web Conference (WWW).</i>",
          "Corbett, A. T., and Anderson, J. R. (1994). Knowledge tracing: modeling the acquisition of procedural knowledge. <i>User Modeling and User-Adapted Interaction.</i>",
      ]] + [Spacer(1, 6),
            P("All numbers come from the code and results in this project (results/poster_gap, results/forgetting_rules).", SM)]


def footer(c, d):
    c.saveState()
    c.setFont("Helvetica", 8.5)
    c.setFillColor(colors.HexColor("#52606D"))
    c.drawString(2.3 * cm, 1.2 * cm, "Teaching a student who forgets: plain-language guide")
    c.drawRightString(A4[0] - 2.3 * cm, 1.2 * cm, f"Page {d.page}")
    c.restoreState()


doc = SimpleDocTemplate(f"{OUT}/poster_explainer.pdf", pagesize=A4, leftMargin=2.3 * cm,
                        rightMargin=2.3 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
                        title="Teaching a student who forgets", author="sanved")
doc.build(S, onFirstPage=footer, onLaterPages=footer)
print("ok")
