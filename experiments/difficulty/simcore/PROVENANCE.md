# Where these files come from

This folder is a copy of the parts of the shared simulator that this study needs,
so the study runs from `main` without depending on the `forgetting` branch.

Copied unchanged (byte for byte) from branch `forgetting`, commit `5ae59c6`
(Sanved's reorganised simulator):

| Here | Original |
|---|---|
| `simcore/__init__.py` | `cursim/__init__.py` |
| `simcore/curriculum.py` | `cursim/curriculum.py` |
| `simcore/params.py` | `cursim/params.py` |
| `simcore/mastery.py` | `cursim/mastery.py` |
| `simcore/students/continuous.py` | `cursim/students/continuous.py` |
| `simcore/schedulers/base.py` | `cursim/schedulers/base.py` |
| `simcore/schedulers/curriculum_tutor_paper.py` | `cursim/schedulers/curriculum_tutor_paper.py` |
| `data/curricula/layered_40.json` | `data/curricula/layered_40.json` |
| `data/params.json` | `data/params.json` |

Written here (not copies): `simcore/students/__init__.py` and
`simcore/schedulers/__init__.py` contain only a one-line docstring (no imports), so
that importing one student or one scheduler does not load the rest of the package.

Check that all nine copies still match the original. Run this from the
repository root, after `git fetch origin forgetting` so that commit `5ae59c6` is
available. It prints nothing when every file matches:

    for f in __init__.py curriculum.py params.py mastery.py students/continuous.py schedulers/base.py schedulers/curriculum_tutor_paper.py; do
      git show 5ae59c6:cursim/$f | cmp - experiments/difficulty/simcore/$f; done
    for f in curricula/layered_40.json params.json; do
      git show 5ae59c6:data/$f | cmp - experiments/difficulty/data/$f; done

If the shared simulator later gets the easy/hard rule properly, this copy should
be removed and the study pointed at the shared code.
