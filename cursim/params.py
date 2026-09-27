"""The one place BKT parameters live.

Values come from `data/params.json`, so they are editable without
touching code. Both the plain BKT student (learner.py) and the BKT
tutor (mastery.py) read from here, so "tutor and student share the
same parameters" is a fact of the code rather than something to
remember to keep in sync.
"""

import json
import os

_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "params.json")

with open(_PATH) as _f:
    _BLOB = json.load(_f)

BKT_PARAMS = dict(_BLOB["bkt"])
DEFAULTS = dict(_BLOB["defaults"])
