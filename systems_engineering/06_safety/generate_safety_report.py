#!/usr/bin/env python3
"""
generate_safety_report.py — OSR Safety Analysis Report
=======================================================
Generates a self-contained HTML safety report equivalent to the outputs of
ATICA4Capella (FHA + FMEA worksheets) — without needing Capella installed.

Sections produced:
  1. Executive Summary — aggregate risk statistics
  2. Risk Matrix — 5×5 Severity × Likelihood heatmap of all hazards
  3. Hazard Log (FHA) — H-01…H-10 with pre/post risk scores and mitigations
  4. System-Level FMEA — all 28 failure modes with S/O/D/RPN, colour-coded
  5. Fault Tree Cut Sets — minimal cut sets for H-01/H-02/H-04
  6. Scenic Scenario Coverage — which scenarios exercise which hazards
  7. Open Action Items — high-RPN items still requiring mitigation work

Usage:
    cd systems_engineering/06_safety
    python3 generate_safety_report.py
    python3 generate_safety_report.py --out /path/to/report.html

Output: safety_report.html  (default, next to this script)
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

# ---------------------------------------------------------------------------
# Hazard log data   (source: hazard_log.md)
# Each entry: (id, title, cause, effect, s_pre, l_pre, s_post, l_post, mitigation, reqs, scenario)
# S = Severity 1–5, L = Likelihood 1–5, Risk = S × L
# ---------------------------------------------------------------------------

HAZARDS = [
    ("H-01", "Motor Overcurrent / Fire",
     "Wheel stall, obstacle jam, short circuit",
     "Motor winding damage, PCB damage, potential fire",
     5, 3, 5, 1,
     "SF-06.1 monitors per-motor current; safe stop at ≥ 10 A (100 ms response); in-line fuse",
     ["REQ-SF-06-01", "REQ-SF-06-02"], "motor_stall"),

    ("H-02", "Tip / Rollover",
     "Excessive slope, dynamic cornering at speed",
     "Rover inversion, hardware damage, injury risk",
     5, 2, 5, 1,
     "SF-06.3 monitors BNO055 IMU roll/pitch; safe stop at ≥ 35° within 100 ms",
     ["REQ-SF-06-04", "REQ-SF-06-05"], "tilt_risk"),

    ("H-03", "Battery Over-Discharge",
     "Extended mission without monitoring, sensor failure",
     "LiPo cell damage, reduced lifespan, potential venting",
     4, 3, 4, 1,
     "SF-06.2 warns at < 11.0 V and stops at < 10.5 V; INA219 voltage monitoring at ≥ 1 Hz",
     ["REQ-SF-06-03"], "battery_low"),

    ("H-04", "Runaway After Comm Loss",
     "Wi-Fi dropout while rover is moving",
     "Uncontrolled motion, collision with persons or objects",
     5, 3, 5, 1,
     "SF-01 1-second watchdog (LF-01.4) zeros velocity on /cmd_vel timeout",
     ["REQ-SF-01-02"], "comm_loss"),

    ("H-05", "Collision / Unintended Motion",
     "Operator error, malformed command, velocity bypass",
     "Impact with obstacles, persons, or terrain",
     4, 3, 4, 2,
     "Velocity clamped to ±0.4 m/s; NaN/Inf discard; safety observer protocol",
     ["REQ-SF-01-03", "REQ-LC-02-03"], None),

    ("H-06", "Electrical Short Circuit",
     "Wiring fault, connector failure, PCB fault",
     "PCB damage, fire, loss of rover",
     5, 2, 5, 1,
     "In-line fuse ≤ 30 A between battery and PCB; positive-retention connectors",
     ["REQ-OA-033-03"], None),

    ("H-07", "Payload Overcurrent",
     "Payload draws more than rated power (> 2 A)",
     "PCB rail damage, system reset, payload damage",
     3, 3, 3, 1,
     "SF-07.2 monitors payload current via INA219; software cutoff at configurable limit",
     ["REQ-SF-07-02"], None),

    ("H-08", "Software Crash / Node Failure",
     "Python exception, OOM, kernel panic",
     "Loss of control, no safe stop if fault monitor crashes",
     4, 3, 4, 2,
     "ROS node respawn; hardware RoboClaw serial timeout as independent backup",
     ["REQ-OA-023-02"], None),

    ("H-09", "Structural Failure",
     "Excessive load, manufacturing defect, fatigue",
     "Collapse during traverse, hardware damage",
     4, 1, 4, 1,
     "Mechanical design with safety factor; post-session hardware inspection",
     ["REQ-OA-022-01"], None),

    ("H-10", "LiPo Thermal Runaway",
     "Overcharge, cell damage, puncture during transport",
     "Fire, toxic gas release",
     5, 1, 5, 1,
     "Charge at ≤ 1C; never charge unattended; store in LiPo-safe bag; no in-rover charging",
     ["REQ-OA-021-01", "REQ-OA-021-02", "REQ-OA-021-03"], None),
]

# ---------------------------------------------------------------------------
# FMEA data   (source: fmea_system.md)
# Each entry: (fm_id, sf, failure_mode, effect, cause, s, o, d, hazard, mitigation)
# ---------------------------------------------------------------------------

FMEA = [
    # SF-01
    ("FM-01-01", "SF-01", "No /cmd_vel received",
     "Rover continues last velocity command",
     "Wi-Fi dropout, ground station crash", 4, 3, 2, "H-04",
     "1-second watchdog (LF-01.4) zeroes velocity"),
    ("FM-01-02", "SF-01", "Malformed Twist message",
     "Incorrect motion command executed",
     "Corrupted packet, ROS serialisation bug", 3, 2, 2, "H-05",
     "NaN/Inf check (LF-01.2) discards bad packets"),
    ("FM-01-03", "SF-01", "Velocity limit bypass",
     "Rover moves faster than safe speed",
     "Software bug in clamping logic", 3, 1, 3, "H-05",
     "Unit test for LF-01.3 clamp at all boundary values"),
    ("FM-01-04", "SF-01", "Watchdog timer fails to fire",
     "No auto-halt on comm loss",
     "Software bug, rospy.Timer crash", 4, 2, 2, "H-04 H-08",
     "Node supervisor restarts; hardware RoboClaw timeout"),
    # SF-02
    ("FM-02-01", "SF-02", "Kinematic model error",
     "Wrong wheel speed ratio — drift or spin",
     "Geometry parameter mismatch", 2, 2, 3, "H-05",
     "Calibration test during build"),
    ("FM-02-02", "SF-02", "RoboClaw USB serial loss",
     "Motors stop abruptly",
     "Cable fault, USB enumeration failure", 3, 2, 1, "H-09",
     "RoboClaw has built-in serial timeout; logs error"),
    ("FM-02-03", "SF-02", "PCA9685 I2C lockup",
     "Steering servos freeze at last angle",
     "I2C bus contention, power glitch", 2, 2, 2, "—",
     "I2C bus reset; servo mechanically safe at any fixed angle"),
    ("FM-02-04", "SF-02", "Single wheel encoder failure",
     "Odometry drift",
     "Encoder damaged; cable break", 2, 2, 3, "—",
     "/diagnostics flags abnormal encoder delta"),
    # SF-03
    ("FM-03-01", "SF-03", "INA219 I2C failure",
     "No battery monitoring",
     "Hardware fault, I2C address conflict", 4, 2, 1, "H-03",
     "/diagnostics reports sensor loss; operator should halt"),
    ("FM-03-02", "SF-03", "Buck converter failure",
     "Loss of 5V logic rail",
     "Component failure, overcurrent", 4, 1, 1, "H-08",
     "PCB fuse; RPi and RoboClaws lose power simultaneously (safe)"),
    ("FM-03-03", "SF-03", "Fuse blow (expected)",
     "Circuit protected, motor stops",
     "Overcurrent event", 2, 2, 1, "H-01",
     "Replace fuse; inspect wiring before resuming"),
    ("FM-03-04", "SF-03", "Voltage reading drift",
     "Wrong SoC estimate",
     "INA219 calibration error", 3, 2, 3, "H-03",
     "Factory calibration; compare against multimeter at setup"),
    # SF-04
    ("FM-04-01", "SF-04", "BNO055 IMU data freeze",
     "Stale orientation; tilt detection fails",
     "I2C lockup, sensor reset", 4, 2, 2, "H-02",
     "Timestamp staleness check in LC-05; alert on /diagnostics"),
    ("FM-04-02", "SF-04", "Odometry divergence",
     "Position estimate unusable",
     "Wheel slip on loose surface", 2, 3, 3, "—",
     "Expected on loose terrain; operator uses visual navigation"),
    ("FM-04-03", "SF-04", "Telemetry topic drops",
     "Operator loses state visibility",
     "Wi-Fi bandwidth saturation", 3, 3, 2, "H-04",
     "Reduce camera resolution; prioritise /battery_state and /diagnostics"),
    ("FM-04-04", "SF-04", "IMU attitude filter divergence",
     "Roll/pitch estimate wrong",
     "Gyro bias at startup", 3, 2, 3, "H-02",
     "Allow 5-second warm-up on level surface before traverse"),
    # SF-05
    ("FM-05-01", "SF-05", "Camera node crash",
     "No video feed",
     "USB disconnect, raspicam error", 2, 3, 1, "H-05",
     "Optional component; mission continues without video"),
    ("FM-05-02", "SF-05", "Video latency > 1 s",
     "Operator makes control decisions on stale image",
     "Network congestion", 3, 3, 3, "H-05",
     "Reduce resolution/framerate; operator uses safety observer for proximity"),
    # SF-06
    ("FM-06-01", "SF-06", "Fault monitor node crash",
     "No automated safe stop",
     "Python exception, OOM", 5, 2, 1, "H-01 H-02 H-04",
     "respawn=true in ROS launch; hardware RoboClaw timeout as backup"),
    ("FM-06-02", "SF-06", "Current threshold too high",
     "Motor damage before shutdown",
     "Threshold misconfigured", 4, 1, 2, "H-01",
     "Threshold validated against motor stall current spec (≤ 10 A)"),
    ("FM-06-03", "SF-06", "Tilt threshold wrong axis",
     "Tip not detected",
     "IMU mounted with wrong orientation", 4, 2, 2, "H-02",
     "Tilt calibration test during setup; verify correct roll/pitch mapping"),
    ("FM-06-04", "SF-06", "Safe stop doesn't zero all motors",
     "Residual motion after fault",
     "Bug in SF-06.4 implementation", 4, 1, 2, "H-01 H-02",
     "Integration test: verify all 3 RoboClaws receive 0 setpoint"),
    ("FM-06-05", "SF-06", "Latched halt not clearable",
     "Rover stuck after false positive",
     "Software bug in latch logic", 2, 2, 2, "—",
     "Operator can restart fault_node via SSH"),
    # SF-07
    ("FM-07-01", "SF-07", "Payload power switch failure",
     "Payload always on or always off",
     "GPIO driver bug, transistor failure", 2, 1, 2, "H-07",
     "Manual power disconnect available; software toggle verified in test"),
    ("FM-07-02", "SF-07", "Payload overcurrent",
     "PCB rail damage, system reset",
     "Payload hardware fault", 3, 2, 2, "H-07",
     "SF-07.2 cuts rail at configurable limit (default 2 A)"),
    ("FM-07-03", "SF-07", "I2C bus contention from payload",
     "LC-04 sensor reads corrupted",
     "Payload device using same I2C address", 3, 2, 2, "H-08",
     "Reserve I2C addresses in payload interface spec"),
    ("FM-07-04", "SF-07", "Payload pulls voltage rail low",
     "RPi undervoltage, system reset",
     "Payload draws excessive current on 5V rail", 4, 2, 1, "H-08",
     "Separate payload 5V rail from RPi 5V rail on PCB"),
]

# ---------------------------------------------------------------------------
# Fault tree cut sets   (source: fta.md)
# ---------------------------------------------------------------------------

FTA_CUTS = [
    ("H-01", "Motor Overcurrent", [
        ["Current sensor fails", "Software threshold not reached"],
        ["RoboClaw ignores setpoint = 0", "SF-06.4 bug"],
        ["In-line fuse rated too high"],
    ]),
    ("H-02", "Tip / Rollover", [
        ["IMU data frozen", "Staleness check bypassed"],
        ["IMU orientation wrong", "Tilt threshold on wrong axis"],
        ["Rover speed > 0.4 m/s", "Velocity clamp bypassed"],
    ]),
    ("H-04", "Runaway After Comm Loss", [
        ["Wi-Fi drops", "Watchdog timer fails"],
        ["Wi-Fi drops", "RoboClaw serial timeout not configured"],
    ]),
]

# ---------------------------------------------------------------------------
# Scenic scenario → hazard coverage matrix
# ---------------------------------------------------------------------------

SCENARIO_COVERAGE = [
    ("nominal_traverse", "Nominal Traverse",   ["H-05"]),
    ("battery_low",      "Battery Low",         ["H-03", "H-10"]),
    ("tilt_risk",        "Tilt Risk",            ["H-02"]),
    ("motor_stall",      "Motor Stall",          ["H-01"]),
    ("comm_loss",        "Comm Loss",            ["H-04"]),
]

ALL_HAZARDS = [h[0] for h in HAZARDS]

# ---------------------------------------------------------------------------
# HTML rendering helpers
# ---------------------------------------------------------------------------

_RISK_COLOR = {
    (1, 1): "#d4edda", (1, 2): "#d4edda", (1, 3): "#fff3cd",
    (1, 4): "#fff3cd", (1, 5): "#f8d7da",
    (2, 1): "#d4edda", (2, 2): "#d4edda", (2, 3): "#fff3cd",
    (2, 4): "#f8d7da", (2, 5): "#f8d7da",
    (3, 1): "#d4edda", (3, 2): "#fff3cd", (3, 3): "#fff3cd",
    (3, 4): "#f8d7da", (3, 5): "#f8d7da",
    (4, 1): "#fff3cd", (4, 2): "#fff3cd", (4, 3): "#f8d7da",
    (4, 4): "#f8d7da", (4, 5): "#f8d7da",
    (5, 1): "#fff3cd", (5, 2): "#f8d7da", (5, 3): "#f8d7da",
    (5, 4): "#f8d7da", (5, 5): "#f8d7da",
}


def _risk_label(s: int, l: int) -> str:
    risk = s * l
    if risk <= 4:
        return f"Low ({risk})"
    if risk <= 9:
        return f"Medium ({risk})"
    return f"High ({risk})"


def _rpn_color(rpn: int) -> str:
    if rpn <= 8:
        return "#d4edda"
    if rpn <= 16:
        return "#fff3cd"
    return "#f8d7da"


def _risk_cell(s: int, l: int) -> str:
    color = _RISK_COLOR.get((s, l), "#ffffff")
    label = _risk_label(s, l)
    return f'<td style="background:{color};text-align:center">{label}</td>'


def _rpn_cell(rpn: int) -> str:
    color = _rpn_color(rpn)
    return f'<td style="background:{color};text-align:center;font-weight:bold">{rpn}</td>'


def section(title: str, content: str, anchor: str = "") -> str:
    aid = anchor or title.lower().replace(" ", "-")
    return (
        f'<section id="{aid}">\n'
        f'<h2>{title}</h2>\n'
        f'{content}\n'
        f'</section>\n'
    )


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def build_summary() -> str:
    high   = sum(1 for h in HAZARDS if h[6] * h[7] > 9)
    med    = sum(1 for h in HAZARDS if 4 < h[6] * h[7] <= 9)
    low    = sum(1 for h in HAZARDS if h[6] * h[7] <= 4)
    hi_rpn = sum(1 for f in FMEA if f[5] * f[6] * f[7] > 16)
    total  = len(FMEA)
    return f"""
<table class="summary">
  <tr><th>Metric</th><th>Value</th></tr>
  <tr><td>Total hazards identified</td><td>{len(HAZARDS)}</td></tr>
  <tr><td>Post-mitigation: High risk</td><td style="background:#f8d7da">{high}</td></tr>
  <tr><td>Post-mitigation: Medium risk</td><td style="background:#fff3cd">{med}</td></tr>
  <tr><td>Post-mitigation: Low risk</td><td style="background:#d4edda">{low}</td></tr>
  <tr><td>Total FMEA failure modes</td><td>{total}</td></tr>
  <tr><td>High-RPN failure modes (RPN &gt; 16)</td><td style="background:#f8d7da">{hi_rpn}</td></tr>
  <tr><td>Fault trees analysed</td><td>{len(FTA_CUTS)}</td></tr>
  <tr><td>Scenic test scenarios</td><td>{len(SCENARIO_COVERAGE)}</td></tr>
</table>
<p><strong>Legend:</strong>
<span class="legend-green">Low</span>
<span class="legend-yellow">Medium</span>
<span class="legend-red">High</span>
</p>
"""


def build_risk_matrix() -> str:
    # 5×5 matrix: rows = Likelihood, cols = Severity
    rows = []
    rows.append("<table class='matrix'><thead><tr><th>L \\ S</th>"
                + "".join(f"<th>S={s}</th>" for s in range(1, 6))
                + "</tr></thead><tbody>")
    for l in range(5, 0, -1):
        row = f"<tr><th>L={l}</th>"
        for s in range(1, 6):
            color = _RISK_COLOR.get((s, l), "#ffffff")
            hazard_ids = [h[0] for h in HAZARDS if h[6] == s and h[7] == l]
            label = "<br>".join(hazard_ids) if hazard_ids else ""
            row += f'<td style="background:{color};text-align:center;min-width:60px">{label}</td>'
        row += "</tr>"
        rows.append(row)
    rows.append("</tbody></table>")
    return "\n".join(rows)


def build_hazard_log() -> str:
    rows = ["""<table><thead><tr>
      <th>ID</th><th>Title</th><th>Cause</th><th>Effect</th>
      <th>Pre-Risk (S×L)</th><th>Post-Risk (S×L)</th>
      <th>Mitigation</th><th>Key Requirements</th><th>Scenario</th>
    </tr></thead><tbody>"""]
    for h in HAZARDS:
        hid, title, cause, effect, s_pre, l_pre, s_post, l_post, mitigation, reqs, scenario = h
        reqs_str = " ".join(reqs) if reqs else "—"
        scen_str = scenario if scenario else "—"
        rows.append(
            f"<tr><td>{hid}</td><td>{title}</td><td>{cause}</td><td>{effect}</td>"
            + _risk_cell(s_pre, l_pre)
            + _risk_cell(s_post, l_post)
            + f"<td>{mitigation}</td><td><code>{reqs_str}</code></td><td>{scen_str}</td></tr>"
        )
    rows.append("</tbody></table>")
    return "\n".join(rows)


def build_fmea() -> str:
    rows = ["""<table><thead><tr>
      <th>ID</th><th>SF</th><th>Failure Mode</th><th>Effect</th>
      <th>Cause</th><th>S</th><th>O</th><th>D</th><th>RPN</th>
      <th>Hazard</th><th>Mitigation</th>
    </tr></thead><tbody>"""]
    for f in sorted(FMEA, key=lambda x: -(x[5] * x[6] * x[7])):
        fm_id, sf, mode, effect, cause, s, o, d, hazard, mitigation = f
        rpn = s * o * d
        rows.append(
            f"<tr><td>{fm_id}</td><td>{sf}</td><td>{mode}</td><td>{effect}</td>"
            f"<td>{cause}</td>"
            f'<td style="text-align:center">{s}</td>'
            f'<td style="text-align:center">{o}</td>'
            f'<td style="text-align:center">{d}</td>'
            + _rpn_cell(rpn)
            + f"<td>{hazard}</td><td>{mitigation}</td></tr>"
        )
    rows.append("</tbody></table>")
    rows.append('<p><em>Table sorted by descending RPN. S = Severity, O = Occurrence, D = Detectability (1–5 each).</em></p>')
    return "\n".join(rows)


def build_fta() -> str:
    parts = []
    for hazard_id, hazard_name, cut_sets in FTA_CUTS:
        parts.append(f"<h3>{hazard_id} — {hazard_name}</h3>")
        parts.append("<p><strong>Minimal cut sets (each is sufficient to cause the top event):</strong></p>")
        parts.append("<ol>")
        for cs in cut_sets:
            events = " AND ".join(f"<em>{e}</em>" for e in cs)
            parts.append(f"  <li>{events}</li>")
        parts.append("</ol>")
    return "\n".join(parts)


def build_scenario_coverage() -> str:
    cols = ALL_HAZARDS
    rows = [
        "<table><thead><tr><th>Scenario</th>"
        + "".join(f"<th>{h}</th>" for h in cols)
        + "</tr></thead><tbody>"
    ]
    for scen_id, scen_name, covered in SCENARIO_COVERAGE:
        cells = "".join(
            f'<td style="text-align:center;background:{"#d4edda" if h in covered else "#f8f9fa"}">'
            + ("✓" if h in covered else "")
            + "</td>"
            for h in cols
        )
        rows.append(f"<tr><td><strong>{scen_name}</strong><br><code>{scen_id}.scenic</code></td>{cells}</tr>")
    rows.append("</tbody></table>")
    rows.append('<p><em>✓ = scenario explicitly exercises this hazard\'s boundary conditions.</em></p>')
    return "\n".join(rows)


def build_action_items() -> str:
    high = [(f[0], f[1], f[2], f[5] * f[6] * f[7], f[-1]) for f in FMEA if f[5] * f[6] * f[7] > 16]
    high.sort(key=lambda x: -x[3])
    rows = ["""<table><thead><tr>
      <th>FM ID</th><th>SF</th><th>Failure Mode</th><th>RPN</th><th>Required Action</th>
    </tr></thead><tbody>"""]
    for fm_id, sf, mode, rpn, mitigation in high:
        rows.append(
            f"<tr><td>{fm_id}</td><td>{sf}</td><td>{mode}</td>"
            + _rpn_cell(rpn)
            + f"<td>{mitigation}</td></tr>"
        )
    rows.append("</tbody></table>")
    return "\n".join(rows)


# ---------------------------------------------------------------------------
# Full HTML document
# ---------------------------------------------------------------------------

CSS = """
* { box-sizing: border-box; }
body { font-family: system-ui, sans-serif; margin: 2rem; color: #212529; max-width: 1400px; }
h1 { border-bottom: 3px solid #0d6efd; padding-bottom: .5rem; }
h2 { margin-top: 2.5rem; border-bottom: 1px solid #dee2e6; padding-bottom: .25rem; color: #0d6efd; }
h3 { margin-top: 1.5rem; color: #495057; }
nav { background: #f8f9fa; border: 1px solid #dee2e6; padding: 1rem 1.5rem;
      border-radius: 4px; margin-bottom: 2rem; }
nav a { display: inline-block; margin-right: 1.5rem; color: #0d6efd; text-decoration: none; }
table { width: 100%; border-collapse: collapse; font-size: .88rem; margin: 1rem 0; }
th, td { border: 1px solid #dee2e6; padding: .4rem .6rem; vertical-align: top; }
thead th { background: #343a40; color: #fff; }
tr:nth-child(even) { background: #f8f9fa; }
.summary td:last-child, .summary th:last-child { font-weight: bold; }
.matrix td, .matrix th { min-width: 70px; }
.legend-green  { background: #d4edda; padding: 2px 8px; border-radius: 3px; margin-right: .5rem; }
.legend-yellow { background: #fff3cd; padding: 2px 8px; border-radius: 3px; margin-right: .5rem; }
.legend-red    { background: #f8d7da; padding: 2px 8px; border-radius: 3px; margin-right: .5rem; }
code { background: #f8f9fa; padding: 1px 4px; border-radius: 3px; font-size: .85em; }
footer { margin-top: 3rem; color: #6c757d; font-size: .85rem; border-top: 1px solid #dee2e6; padding-top: 1rem; }
"""


def generate_report() -> str:
    from datetime import datetime
    date_str = datetime.now().strftime("%Y-%m-%d")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OSR Safety Analysis Report</title>
<style>{CSS}</style>
</head>
<body>

<h1>JPL Open Source Rover — Safety Analysis Report</h1>
<p><strong>Document:</strong> OSR-SAF-REPORT-001 &nbsp;|&nbsp;
   <strong>Status:</strong> DRAFT &nbsp;|&nbsp;
   <strong>Generated:</strong> {date_str}</p>

<nav>
  <strong>Contents:</strong>
  <a href="#executive-summary">1. Executive Summary</a>
  <a href="#risk-matrix">2. Risk Matrix</a>
  <a href="#hazard-log">3. Hazard Log (FHA)</a>
  <a href="#fmea">4. System FMEA</a>
  <a href="#fault-tree-cut-sets">5. FTA Cut Sets</a>
  <a href="#scenic-scenario-coverage">6. Scenario Coverage</a>
  <a href="#open-action-items">7. Open Action Items</a>
</nav>

{section("Executive Summary", build_summary(), "executive-summary")}
{section("Risk Matrix", build_risk_matrix(), "risk-matrix")}
{section("Hazard Log (FHA)", build_hazard_log(), "hazard-log")}
{section("System-Level FMEA", build_fmea(), "fmea")}
{section("Fault Tree Cut Sets", build_fta(), "fault-tree-cut-sets")}
{section("Scenic Scenario Coverage", build_scenario_coverage(), "scenic-scenario-coverage")}
{section("Open Action Items (RPN > 16)", build_action_items(), "open-action-items")}

<footer>
  Generated by <code>generate_safety_report.py</code> — OSR MBSE safety analysis pipeline.<br>
  Emulates ATICA4Capella FHA + FMEA outputs (ANZEN Engineering) without requiring Capella.<br>
  Source data: <code>hazard_log.md</code>, <code>fmea_system.md</code>, <code>fta.md</code>,
  <code>scenarios/</code>
</footer>

</body>
</html>
"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(
        description="Generate OSR standalone HTML safety report"
    )
    p.add_argument("--out", "-o", default=None,
                   help="Output path (default: safety_report.html next to this script)")
    args = p.parse_args()

    out = Path(args.out) if args.out else Path(__file__).parent / "safety_report.html"
    out.write_text(generate_report(), encoding="utf-8")

    print(f"Written: {out}")
    print(f"  {len(HAZARDS)} hazards, {len(FMEA)} failure modes, "
          f"{len(FTA_CUTS)} fault trees, {len(SCENARIO_COVERAGE)} scenarios")


if __name__ == "__main__":
    main()
