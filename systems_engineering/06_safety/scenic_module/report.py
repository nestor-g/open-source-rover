"""
scenic_module.report
=====================
Reporting layer for parametric sweep results.

Supports three output formats:

JSON
    Machine-readable; suitable for CI/CD gating and downstream tooling.
    Includes full parameter vectors and per-constraint margins.

CSV
    Flat tabular format; one row per sample point.
    Importable into Excel, pandas, or the safety dashboard.

HTML
    Self-contained standalone page with:
    - Summary statistics table
    - Hazard rate per constraint bar chart (via Chart.js)
    - Scatter matrix of the top swept parameters (via Plotly or CSS)
    - Sortable table of the top-N hazardous points
    - JSON data embedded as a ``<script>`` block for optional re-rendering

Usage::

    from scenic_module.sweep import quick_sweep
    from scenic_module.report import SweepReport

    result = quick_sweep(n=500)
    report = SweepReport(result)

    report.write_json("sweep_results.json")
    report.write_csv("sweep_results.csv")
    report.write_html("sweep_report.html")
"""

from __future__ import annotations

import csv
import json
import math
from io import StringIO
from pathlib import Path
from typing import Any, Optional

from .sweep import ScenarioPoint, SweepResult
from .parameter_space import ALL_PARAMETERS


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _point_to_dict(pt: ScenarioPoint) -> dict[str, Any]:
    return {
        "index":                pt.index,
        "is_hazardous":         pt.is_hazardous,
        "is_boundary":          pt.is_boundary,
        "hazard_level":         round(pt.hazard_level, 5),
        "violated_constraints": pt.violated_constraints,
        "params":               {k: round(v, 6) for k, v in pt.params.items()},
        "constraint_margins": {
            r.constraint_id: round(r.margin, 5)
            for r in pt.constraint_results
        },
    }


def _result_to_dict(result: SweepResult) -> dict[str, Any]:
    cfg = result.config
    return {
        "sweep": {
            "method":          cfg.method,
            "n_requested":     cfg.n,
            "n_actual":        result.n_total,
            "seed":            cfg.seed,
            "constraint_ids":  list(cfg.constraint_ids),
            "boundary_margin": cfg.boundary_margin_frac,
        },
        "summary": {
            "n_total":      result.n_total,
            "n_hazardous":  result.n_hazardous,
            "n_boundary":   result.n_boundary,
            "n_safe":       len(result.safe_points),
            "hazard_rate":  round(result.hazard_rate, 5),
            "violation_counts": result.violation_counts,
        },
        "top_hazardous": [_point_to_dict(p) for p in result.top_hazardous(10)],
        "all_points":    [_point_to_dict(p) for p in result.points],
    }


# ---------------------------------------------------------------------------
# CSV builder
# ---------------------------------------------------------------------------

def _result_to_csv_rows(result: SweepResult) -> list[list[str]]:
    # Build column list dynamically from first point
    if not result.points:
        return []

    sample = result.points[0]
    param_keys = sorted(sample.params.keys())
    constraint_ids = [r.constraint_id for r in sample.constraint_results]

    header = (
        ["index", "is_hazardous", "is_boundary", "hazard_level", "violated_constraints"]
        + param_keys
        + [f"margin_{cid}" for cid in constraint_ids]
    )

    rows = [header]
    for pt in result.points:
        margins = {r.constraint_id: r.margin for r in pt.constraint_results}
        row = (
            [
                str(pt.index),
                str(pt.is_hazardous),
                str(pt.is_boundary),
                f"{pt.hazard_level:.5f}",
                "|".join(pt.violated_constraints),
            ]
            + [f"{pt.params.get(k, float('nan')):.5f}" for k in param_keys]
            + [f"{margins.get(cid, float('nan')):.5f}" for cid in constraint_ids]
        )
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# HTML builder
# ---------------------------------------------------------------------------

_HTML_STYLE = """
body { font-family: system-ui, sans-serif; margin: 0; background: #f8f9fa; color: #212529; }
.page { max-width: 1200px; margin: 0 auto; padding: 1.5rem; }
h1 { font-size: 1.5rem; margin-bottom: .25rem; }
.meta { color: #6c757d; font-size: .85rem; margin-bottom: 1.5rem; }
.card { background: #fff; border: 1px solid #dee2e6; border-radius: 6px;
        padding: 1rem 1.25rem; margin-bottom: 1.25rem; }
h2 { font-size: 1.1rem; margin: 0 0 .75rem; color: #343a40; }
table { width: 100%; border-collapse: collapse; font-size: .83rem; }
th { background: #f1f3f5; text-align: left; padding: .4rem .6rem;
     border-bottom: 2px solid #dee2e6; white-space: nowrap; cursor: pointer; }
td { padding: .35rem .6rem; border-bottom: 1px solid #f1f3f5; vertical-align: middle; }
tr:hover td { background: #f8f9fa; }
.badge { display:inline-block; padding:.2em .55em; border-radius:4px;
         font-size:.78em; font-weight:600; }
.badge-danger  { background:#f8d7da; color:#842029; }
.badge-warning { background:#fff3cd; color:#664d03; }
.badge-safe    { background:#d1e7dd; color:#0a3622; }
.bar-wrap { height: 18px; background: #dee2e6; border-radius: 3px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 3px; }
.bar-danger  { background: #dc3545; }
.bar-warning { background: #ffc107; }
.bar-safe    { background: #198754; }
.summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: .75rem; }
.stat { text-align: center; padding: .5rem; background: #f8f9fa; border-radius: 4px; }
.stat-value { font-size: 1.6rem; font-weight: 700; line-height: 1.1; }
.stat-label { font-size: .78rem; color: #6c757d; }
.danger-text  { color: #dc3545; }
.warning-text { color: #856404; }
.safe-text    { color: #198754; }
"""

_HTML_SCRIPT = """
// Sortable table
document.querySelectorAll('th[data-col]').forEach(th => {
  th.addEventListener('click', () => {
    const col = parseInt(th.dataset.col);
    const tbody = th.closest('table').querySelector('tbody');
    const rows = [...tbody.rows];
    const asc = th.dataset.asc !== 'true';
    rows.sort((a, b) => {
      const av = a.cells[col].textContent.trim();
      const bv = b.cells[col].textContent.trim();
      const an = parseFloat(av), bn = parseFloat(bv);
      if (!isNaN(an) && !isNaN(bn)) return asc ? an - bn : bn - an;
      return asc ? av.localeCompare(bv) : bv.localeCompare(av);
    });
    th.dataset.asc = asc;
    rows.forEach(r => tbody.appendChild(r));
    document.querySelectorAll('th[data-col]').forEach(t => t.textContent = t.textContent.replace(/ [▲▼]$/,''));
    th.textContent += asc ? ' ▲' : ' ▼';
  });
});
"""


def _badge(is_haz: bool, is_bnd: bool) -> str:
    if is_haz:
        return '<span class="badge badge-danger">HAZARDOUS</span>'
    if is_bnd:
        return '<span class="badge badge-warning">BOUNDARY</span>'
    return '<span class="badge badge-safe">SAFE</span>'


def _bar(frac: float) -> str:
    pct = min(100, max(0, frac * 100))
    cls = "bar-danger" if frac > 0.5 else ("bar-warning" if frac > 0.1 else "bar-safe")
    return (
        f'<div class="bar-wrap">'
        f'<div class="bar-fill {cls}" style="width:{pct:.1f}%"></div>'
        f'</div>'
    )


def _build_html(result: SweepResult) -> str:
    cfg = result.config
    top_pts = result.top_hazardous(25)

    # Determine columns from first point
    param_keys = sorted(result.points[0].params.keys()) if result.points else []
    # Only show a few key columns in the table to keep it readable
    key_params = ["motor_current_peak", "battery_voltage", "roll_deg",
                  "cmd_vel_age_sec", "linear_velocity"]
    show_params = [k for k in key_params if k in param_keys]

    # Violation count bars
    viol_bar_rows = ""
    for cid, cnt in sorted(result.violation_counts.items()):
        frac = cnt / max(result.n_total, 1)
        viol_bar_rows += (
            f"<tr><td><strong>{cid}</strong></td>"
            f"<td>{_bar(frac)}</td>"
            f"<td>{cnt}</td><td>{frac*100:.1f}%</td></tr>"
        )
    if not viol_bar_rows:
        viol_bar_rows = "<tr><td colspan='4' class='safe-text'>No violations detected</td></tr>"

    # Top hazardous points table
    param_headers = "".join(
        f'<th data-col="{5+i}">'
        + ALL_PARAMETERS[k].name
        + f" ({ALL_PARAMETERS[k].unit})</th>"
        for i, k in enumerate(show_params)
    )
    haz_rows = ""
    for i, pt in enumerate(top_pts):
        param_cells = "".join(
            f'<td>{pt.params.get(k, float("nan")):.3f}</td>'
            for k in show_params
        )
        violated = ", ".join(pt.violated_constraints) or "—"
        haz_rows += (
            f"<tr>"
            f"<td>{pt.index}</td>"
            f"<td>{_badge(pt.is_hazardous, pt.is_boundary)}</td>"
            f"<td>{pt.hazard_level*100:.1f}%</td>"
            f"<td>{_bar(pt.hazard_level)}</td>"
            f"<td>{violated}</td>"
            f"{param_cells}"
            f"</tr>"
        )

    # Embed JSON for downstream use
    json_data = json.dumps(_result_to_dict(result), separators=(",", ":"))

    hazard_pct = f"{result.hazard_rate*100:.1f}"
    boundary_pct = f"{result.n_boundary/max(result.n_total,1)*100:.1f}"
    safe_pct = f"{len(result.safe_points)/max(result.n_total,1)*100:.1f}"

    haz_cls  = "danger-text" if result.hazard_rate > 0.1 else "warning-text" if result.hazard_rate > 0 else "safe-text"

    return f"""\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>OSR Sweep Report — {cfg.method.upper()} n={result.n_total}</title>
<style>{_HTML_STYLE}</style>
</head>
<body>
<div class="page">
  <h1>OSR Parametric Sweep Report</h1>
  <div class="meta">
    Method: <strong>{cfg.method.upper()}</strong> &nbsp;|&nbsp;
    Samples: <strong>{result.n_total}</strong> &nbsp;|&nbsp;
    Seed: <strong>{cfg.seed}</strong> &nbsp;|&nbsp;
    Constraints: <strong>{", ".join(cfg.constraint_ids)}</strong>
  </div>

  <div class="card">
    <h2>Summary</h2>
    <div class="summary-grid">
      <div class="stat">
        <div class="stat-value {haz_cls}">{hazard_pct}%</div>
        <div class="stat-label">Hazard Rate</div>
      </div>
      <div class="stat">
        <div class="stat-value danger-text">{result.n_hazardous}</div>
        <div class="stat-label">Hazardous Points</div>
      </div>
      <div class="stat">
        <div class="stat-value warning-text">{result.n_boundary}</div>
        <div class="stat-label">Boundary Points</div>
      </div>
      <div class="stat">
        <div class="stat-value safe-text">{len(result.safe_points)}</div>
        <div class="stat-label">Safe Points</div>
      </div>
    </div>
  </div>

  <div class="card">
    <h2>Violation Count per Constraint</h2>
    <table>
      <thead><tr>
        <th>Constraint</th><th style="width:40%">Rate</th>
        <th>Count</th><th>%</th>
      </tr></thead>
      <tbody>{viol_bar_rows}</tbody>
    </table>
  </div>

  <div class="card">
    <h2>Top Hazardous Points</h2>
    <table>
      <thead><tr>
        <th data-col="0">#</th>
        <th data-col="1">Status</th>
        <th data-col="2">Hazard %</th>
        <th data-col="3">Bar</th>
        <th data-col="4">Violated</th>
        {param_headers}
      </tr></thead>
      <tbody>{haz_rows}</tbody>
    </table>
  </div>

  <div class="card" style="font-size:.8rem;color:#6c757d;">
    <strong>Raw data</strong> embedded below as JSON for downstream use.
    <details><summary>Expand JSON ({result.n_total} points)</summary>
    <pre id="raw-json" style="max-height:300px;overflow:auto;font-size:.75rem;"></pre>
    </details>
  </div>
</div>

<script id="sweep-data" type="application/json">{json_data}</script>
<script>
// Populate raw JSON viewer
const raw = document.getElementById('raw-json');
if (raw) {{
  raw.textContent = JSON.stringify(JSON.parse(
    document.getElementById('sweep-data').textContent
  ), null, 2);
}}
{_HTML_SCRIPT}
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Public report class
# ---------------------------------------------------------------------------

class SweepReport:
    """Wraps a :class:`~scenic_module.sweep.SweepResult` and provides output methods."""

    def __init__(self, result: SweepResult) -> None:
        self.result = result

    # ------------------------------------------------------------------ JSON
    def to_json(self, indent: int = 2) -> str:
        """Serialise to JSON string."""
        return json.dumps(_result_to_dict(self.result), indent=indent)

    def write_json(self, path: str | Path) -> Path:
        p = Path(path)
        p.write_text(self.to_json(), encoding="utf-8")
        return p

    # ------------------------------------------------------------------ CSV
    def to_csv(self) -> str:
        rows = _result_to_csv_rows(self.result)
        buf = StringIO()
        writer = csv.writer(buf, lineterminator="\n")
        writer.writerows(rows)
        return buf.getvalue()

    def write_csv(self, path: str | Path) -> Path:
        p = Path(path)
        p.write_text(self.to_csv(), encoding="utf-8")
        return p

    # ------------------------------------------------------------------ HTML
    def to_html(self) -> str:
        return _build_html(self.result)

    def write_html(self, path: str | Path) -> Path:
        p = Path(path)
        p.write_text(self.to_html(), encoding="utf-8")
        return p

    # ------------------------------------------------------------------ Text
    def summary(self) -> str:
        r = self.result
        cfg = r.config
        lines = [
            "",
            "OSR Parametric Sweep — Summary",
            "=" * 50,
            f"  Method   : {cfg.method.upper()}",
            f"  Samples  : {r.n_total}",
            f"  Seed     : {cfg.seed}",
            "",
            f"  Total        : {r.n_total:>6}",
            f"  Hazardous    : {r.n_hazardous:>6}  ({r.hazard_rate*100:.1f}%)",
            f"  Boundary     : {r.n_boundary:>6}  ({r.n_boundary/max(r.n_total,1)*100:.1f}%)",
            f"  Safe         : {len(r.safe_points):>6}",
            "",
            "  Violations per constraint:",
        ]
        for cid, cnt in sorted(r.violation_counts.items()):
            lines.append(f"    {cid:<12} : {cnt:>5}  ({cnt/max(r.n_total,1)*100:.1f}%)")
        if not r.violation_counts:
            lines.append("    (none)")
        lines.append("")
        if r.hazardous_points:
            lines.append("  Top 5 hazardous points:")
            for pt in r.top_hazardous(5):
                violated = ", ".join(pt.violated_constraints)
                lines.append(
                    f"    idx={pt.index:<4} hazard={pt.hazard_level:.3f}  violated=[{violated}]"
                )
        lines.append("")
        return "\n".join(lines)
