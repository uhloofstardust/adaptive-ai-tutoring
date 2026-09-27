"""Render the playback viewer as one self-contained HTML string.

Chart.js is vendored under viewer/ and inlined here, so the viewer
works with no network.
"""

import json
import os

from .viewer_data import build_payload

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TPL = os.path.join(_HERE, "viewer", "viewer.html")
_CHART = os.path.join(_HERE, "viewer", "vendor", "chart.umd.min.js")


def render(cur, spec, seed, run=None) -> str:
    payload = build_payload(cur, spec, seed, run=run)
    with open(_TPL, encoding="utf-8") as f:
        html = f.read()
    with open(_CHART, encoding="utf-8") as f:
        chartjs = f.read()
    body = html.replace("__PAYLOAD__", json.dumps(payload, separators=(",", ":")))
    return f"<script>{chartjs}</script>\n{body}"


def height_for(n_concepts: int) -> int:
    """Roughly how tall the component needs to be. Two columns side by
    side, so height is set by whichever of the graph or the chart grid
    is taller."""
    chart_rows = (n_concepts + 1) // 2          # ~2 charts per row
    charts = 150 + chart_rows * 98
    graph = 400
    return 195 + max(graph, charts)


def build_payload_for_save(cur, spec, seed, run):
    """The same payload the viewer plays, for saving alongside a run."""
    return build_payload(cur, spec, seed, run=run)
