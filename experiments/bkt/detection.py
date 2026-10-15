"""Check 2. Detection delay and false-alarm rate as a function of the mastery threshold.
"""

import statistics as st

import matplotlib.pyplot as plt

from cursim.curriculum import build_curriculum

from ..registry import experiment
from ..style import ACCENT
from ..style import GREY
from ..style import INK

from .common import per_concept, population, spec_from


@experiment('check2_detection',
            'Check 2. Detection delay and false-alarm rate as a function of the mastery threshold.',
            defaults=dict(n_learners=30, n_steps=120),
            curriculum='abstract', theme='dark')
def detection(n_learners=30, n_steps=120,
              thresholds=(0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99),
              seed0=4242, cur=None, **run_kw):
    """One population per threshold, because the threshold also decides
    what the tutor asks (it defines the ZPD). Reports, per threshold:
    detection delay after the true learning step, false-alarm rate
    (share of declarations made before the concept was learned), and
    what was still unresolved when the run ended, decomposed by cause."""
    cur = cur or build_curriculum()
    rows = []
    for th in thresholds:
        spec = spec_from(th, n_steps, run_kw)
        recs = [x for r in population(cur, spec, n_learners, seed0)
                for x in per_concept(r, th)]
        declared = [x for x in recs if x["declared_step"] is not None]
        learned = [x for x in recs if x["learned_step"] is not None]
        delays = [x["delay_questions"] for x in recs
                  if x["delay_questions"] is not None]
        on_c = [x["delay_on_concept"] for x in recs
                if x["delay_on_concept"] is not None]
        unres = [x for x in recs if x["unresolved"]]
        why = {k: sum(1 for x in unres if x["unresolved_why"] == k)
               for k in ("learned in the last 50 questions",
                         "never reached by the ZPD",
                         "asked, not yet over threshold")}
        fa = sum(x["premature"] for x in declared)
        fa_stuck = sum(1 for x in declared if x["premature"]
                       and x["learned_step"] is None)
        b_cross = (st.mean(x["belief_at_declaration"] for x in declared)
                   if declared else float("nan"))
        rows.append(dict(
            threshold=th,
            belief_at_declaration=b_cross,
            # if check 1 holds, this must match false_alarm_rate
            predicted_false_alarm_rate=1.0 - b_cross,
            n_concepts=len(recs), n_learned=len(learned), n_declared=len(declared),
            false_alarms=fa,
            # share of declarations that came before the concept was learned
            false_alarm_rate=fa / len(declared) if declared else float("nan"),
            # of those, how many concepts were then never learned at all:
            # once declared it leaves the ZPD and is never asked again
            false_alarms_never_learned=fa_stuck,
            delay_mean=st.mean(delays) if delays else float("nan"),
            delay_median=st.median(delays) if delays else float("nan"),
            n_delay=len(delays),
            delay_on_concept_mean=st.mean(on_c) if on_c else float("nan"),
            n_delay_on_concept=len(on_c),
            unresolved=len(unres),
            unresolved_rate=len(unres) / len(learned) if learned else float("nan"),
            unresolved_learned_late=why["learned in the last 50 questions"],
            unresolved_never_reached=why["never reached by the ZPD"],
            unresolved_asked_not_crossed=why["asked, not yet over threshold"],
        ))

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 3.8))
    th = [r["threshold"] for r in rows]
    a1.plot(th, [r["delay_on_concept_mean"] for r in rows], "o-", color=ACCENT,
            lw=1.6, label="questions on that concept (all detections)")
    a1.plot(th, [r["delay_mean"] for r in rows], "s--", color=INK, lw=1.4,
            label="questions overall (concepts learned during the run)")
    a1.set_xlabel("mastery threshold"); a1.set_ylabel("mean delay after true learning")
    a1.set_title("How long until the tutor notices")
    a1.legend(frameon=False, fontsize=8.5)
    a2.plot(th, [r["false_alarm_rate"] for r in rows], "o-", color=ACCENT, lw=1.6,
            label="false alarm rate, measured")
    a2.plot(th, [r["predicted_false_alarm_rate"] for r in rows], "x:", color=INK,
            lw=1.2, ms=7, label="1 - belief at declaration (what calibration predicts)")
    a2.plot(th, [r["unresolved_rate"] for r in rows], "s--", color=GREY, lw=1.4,
            label="unresolved when the run ended (horizon effect)")
    a2.set_xlabel("mastery threshold"); a2.set_ylabel("rate")
    top = max(max(r["false_alarm_rate"] for r in rows),
              max(r["unresolved_rate"] for r in rows))
    a2.set_ylim(-0.02, max(0.42, 1.15 * top))
    a2.set_title("Share of declarations that were too early")
    a2.legend(frameon=False, fontsize=8.5)
    fig.tight_layout()

    lo, hi = rows[0], rows[-1]
    summary = (f"Threshold {lo['threshold']}: {lo['delay_on_concept_mean']:.1f} "
               f"questions on the concept until declared, false alarms "
               f"{lo['false_alarm_rate']:.1%}. Threshold {hi['threshold']}: "
               f"{hi['delay_on_concept_mean']:.1f} questions, false alarms "
               f"{hi['false_alarm_rate']:.1%}. 'Unresolved' counts concepts learned "
               f"but not declared by the end of the {n_steps}-question run; every "
               f"one is either learned in the last 50 questions or never reached "
               f"by the ZPD, i.e. a horizon effect, not a detector failure.")
    return {"tables": {"detection": rows}, "figures": {"detection": fig},
            "summary": summary}
