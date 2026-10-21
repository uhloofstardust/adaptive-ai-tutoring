# Easy and hard questions (study)

A study of Sir's idea that easy and hard questions should teach differently:
easy questions raise mastery slowly or only up to a limit, hard questions raise it
a lot when the student can solve them. It asks which difficulty to give inside a
concept, and what that does to CurriculumTutor.

**Read first:** `easy_hard_note.pdf` (15 pages, 12 figures). It explains the rule,
every experiment, the literature, the open questions for Sir, and the limits.

**Status.** A standalone study on the `difficulty` branch, made from `main`. It does
not use the repository's `cursim` package and changes nothing outside this folder.
The simulator files it needs are copied unchanged into `simcore/` from the
`forgetting` branch (commit `5ae59c6`, Sanved's reorganised simulator), so the study
does not depend on that branch; `simcore/PROVENANCE.md` lists each file and how to
check the copies. All settings are guesses until Sir decides them (note, Section 9).

## What is here

| File | What it does |
|---|---|
| `simcore/` | Unchanged copy of the simulator files the study needs (see `simcore/PROVENANCE.md`) |
| `data/curricula/layered_40.json`, `data/params.json` | The 40-concept graph and the shared settings, copied with `simcore/` |
| `harness.py` | The easy/hard learning rule on top of the simulator's continuous student; best-case tutors; CurriculumTutor wrappers |
| `harness2.py` | Within-concept policies (random, all easy first, k easy first) and their metrics |
| `models.py`, `hetero.py` | One-concept models and the different-students study |
| `make_single.py`, `make_single2.py` | One-concept results -> `data/single_*.csv` |
| `run_grid.py` | First 40-concept grid (100 students) -> `data/graph_rows.csv.gz` |
| `run_ef.py` | Easy first vs random (200 students) -> `data/ef_rows.csv.gz` |
| `make_extra.py` | Extra graph runs (200 students) -> `data/extra_rows.csv.gz` |
| `make_figs.py`, `make_numbers.py` | Every figure (`figs/`) and every number and table in the note (`gen/`), read only from `data/` |
| `report.tex` | Source of the note; numbers enter only as generated macros |
| `run_all.sh` | Runs everything above and builds the PDF |

## Reproduce

    cd experiments/difficulty
    ./run_all.sh          # about 5 minutes on 12 cores; WORKERS=4 ./run_all.sh to use fewer

Seeds are fixed, so the result files come out byte for byte the same (the
compressed files are written with a fixed timestamp). The figures and the PDF are
written without a creation date, so a rerun leaves them unchanged too. The figures and the note
can be rebuilt from the committed `data/` alone:

    python3 make_figs.py && python3 make_numbers.py && latexmk -pdf report.tex && cp report.pdf easy_hard_note.pdf

Needs Python 3 with numpy and matplotlib, and LaTeX for the PDF.
