r"""Write every data table in docs/simulator.tex from the committed CSVs.

    python3 make_tables.py        -> docs/tables/*.tex

The document \input{}s these, so a number can only reach the PDF by
coming out of sanity_outputs/ (or data/params.json). Typing one in by
hand is no longer possible, which is the point: run make_sanity.py, then
this, and the document cannot disagree with the data.

Run it after make_sanity.py. `python3 make_tables.py --check` re-emits
into a temp dir and fails if anything differs from what is committed,
which is what CI or a pre-submission check should call.
"""
import csv
import difflib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "docs", "tables")
CSV = os.path.join(HERE, "sanity_outputs")


def rows(name):
    with open(os.path.join(CSV, f"{name}.csv")) as f:
        return list(csv.DictReader(f))


def by(rs, **kw):
    for r in rs:
        if all(r[k] == v for k, v in kw.items()):
            return r
    raise KeyError(f"no row matching {kw}")


def wrap(body, spec, header):
    return ("\\begin{center}\n\\small\n"
            f"\\begin{{tabular}}{{{spec}}}\n\\toprule\n"
            f"{header}\\\\\n\\midrule\n"
            + body +
            "\\bottomrule\n\\end{tabular}\n\\end{center}\n")


# ------------------------------------------------------------- parameters
def t_params():
    with open(os.path.join(HERE, "data", "params.json")) as f:
        p = json.load(f)["bkt"]
    meaning = [
        ("p_L0", "p(L_0)", "probability the concept is known before any question"),
        ("p_T",  "p(T)",   "probability an unknown concept becomes known at an attempt"),
        ("p_G",  "p(G)",   "probability of a correct answer while it is unknown"),
        ("p_S",  "p(S)",   "probability of a wrong answer while it is known"),
    ]
    body = "".join(f"${sym}$ & {text} & {p[key]:.2f}\\\\\n"
                   for key, sym, text in meaning)
    return wrap(body, "@{}cll@{}", " & \\textbf{Meaning} & \\textbf{Default}")


# ------------------------------------------------------------------- 2x2
def t_two_by_two():
    cells = rows("two_by_two")
    pair = rows("two_by_two_paired")
    body = ""
    for s in ("S1", "S2"):
        q1 = float(by(cells, student=s, scheduler="Q1")["learned_mean"])
        q2 = float(by(cells, student=s, scheduler="Q2")["learned_mean"])
        d = by(pair, student=s)
        body += (f"{s} & {q1:.2f} & {q2:.2f} & "
                 f"${float(d['diff_Q2_minus_Q1']):+.2f}$ & "
                 f"$\\pm {float(d['ci95']):.2f}$\\\\\n")
    ix = by(pair, student="interaction (S2 minus S1)")
    body += ("\\midrule\n\\multicolumn{3}{@{}l}{interaction (S2 $-$ S1)} & "
             f"${float(ix['diff_Q2_minus_Q1']):+.2f}$ & "
             f"$\\pm {float(ix['ci95']):.2f}$\\\\\n")
    return wrap(body, "@{}lcccc@{}",
                " & \\textbf{Q1} & \\textbf{Q2} & \\textbf{Q2 $-$ Q1} "
                "& \\textbf{95\\% CI}")


def t_pairing():
    """The sentence that justifies pairing, with its own numbers in it."""
    ix = by(rows("two_by_two_paired"), student="interaction (S2 minus S1)")
    return (f"$r={float(ix['corr_S1_S2']):+.2f}$, and the interval would be "
            f"$\\pm {float(ix['ci95_if_unpaired']):.2f}$ rather than "
            f"$\\pm {float(ix['ci95']):.2f}$ if the two were treated as "
            f"independent.\n")


# ------------------------------------------------------ restriction alone
def t_restriction():
    rs = rows("restriction_only")
    body = ""
    for s in ("S1", "S2"):
        r = by(rs, student=s)
        body += (f"{s} & {float(r['unrestricted']):.3f} & "
                 f"{float(r['restricted']):.3f} & "
                 f"${float(r['restriction_effect']):+.3f} \\pm "
                 f"{float(r['ci95']):.3f}$\\\\\n")
    return wrap(body, "@{}lccc@{}",
                " & \\textbf{unrestricted} & \\textbf{restricted} "
                "& \\textbf{effect}")


# ------------------------------------------------- what should the tutor be
def t_tutor_choice():
    body = ""
    for r in rows("tutor_choice_verdict"):
        buys, ci = float(r["oracle_buys_brier"]), float(r["brier_ci95"])
        body += (f"{r['parameter'].replace('_', '$\\_$')} & "
                 f"$\\pm {float(r['spread']):.2f}$ & "
                 f"{float(r['best_fixed_value']):.2f} & "
                 f"{float(r['best_fixed_brier']):.4f} & "
                 f"{float(r['oracle_brier']):.4f} & "
                 f"${buys:+.4f}$ & $\\pm {ci:.4f}$ & "
                 f"{'yes' if abs(buys) > ci else 'no'}\\\\\n")
    return wrap(body, "@{}llcccccc@{}",
                "\\textbf{vary} & \\textbf{spread} & \\textbf{best fixed} "
                "& \\textbf{its Brier} & \\textbf{oracle} "
                "& \\textbf{buys} & \\textbf{95\\% CI} "
                "& \\textbf{resolved}")


# ---------------------------------------------------- mastery over time
def t_mastery():
    qa = rows("mastery_curve_questions_to_all")
    pr = rows("mastery_curve_paired")
    body = ""
    for s in ("S1", "S2"):
        q1 = by(qa, student=s, scheduler="Q1")
        q2 = by(qa, student=s, scheduler="Q2")
        d = by(pr, student=s)
        body += (f"{s} & {float(q1['median_questions_to_all']):.0f} & "
                 f"{float(q2['median_questions_to_all']):.0f} & "
                 f"${float(d['diff_Q2_minus_Q1']):+.1f} \\pm "
                 f"{float(d['ci95']):.1f}$ & "
                 f"${float(d['median_diff_Q2_minus_Q1']):+.1f}$ & "
                 f"{d['favours']}\\\\\n")
    return wrap(body, "@{}lccccl@{}",
                " & \\textbf{Q1} & \\textbf{Q2} & \\textbf{mean diff} "
                "& \\textbf{median diff} & \\textbf{favours}")


TABLES = {
    "params": t_params,
    "two_by_two": t_two_by_two,
    "pairing_sentence": t_pairing,
    "restriction_only": t_restriction,
    "tutor_choice": t_tutor_choice,
    "mastery_curve": t_mastery,
}

BANNER = ("% GENERATED by make_tables.py from sanity_outputs/. Do not edit:\n"
          "% edit the experiment, rerun make_sanity.py, then make_tables.py.\n")


def build():
    return {name: BANNER + fn() for name, fn in TABLES.items()}


def main():
    built = build()
    if "--check" in sys.argv:
        bad = []
        for name, text in built.items():
            path = os.path.join(OUT, f"{name}.tex")
            have = open(path).read() if os.path.exists(path) else ""
            if have != text:
                bad.append(name)
                print(f"--- {name}.tex differs ---")
                sys.stdout.writelines(difflib.unified_diff(
                    have.splitlines(True), text.splitlines(True),
                    "committed", "regenerated"))
        if bad:
            print(f"\nFAIL: {len(bad)} table(s) out of date: {', '.join(bad)}")
            return 1
        print(f"OK: all {len(built)} tables match the CSVs")
        return 0
    os.makedirs(OUT, exist_ok=True)
    for name, text in built.items():
        with open(os.path.join(OUT, f"{name}.tex"), "w") as f:
            f.write(text)
    print("wrote", sorted(os.listdir(OUT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
