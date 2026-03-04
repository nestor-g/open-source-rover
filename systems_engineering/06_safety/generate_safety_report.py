#!/usr/bin/env python3
"""
generate_safety_report.py — OSR Interactive Safety Dashboard
=============================================================
Generates a self-contained interactive HTML safety dashboard equivalent to
ATICA4Capella (FHA + FMEA) outputs — without needing Capella installed.

Features:
  • Bootstrap 5 tab navigation (7 tabs)
  • Clickable 5×5 risk matrix → cross-filters Hazard Log
  • FMEA table: sortable columns, SF-filter dropdown, min-RPN slider
  • Hazard log: filter by post-mitigation risk level
  • Scenic scenario coverage matrix
  • All data embedded as JSON — fully self-contained, no server required

Usage:
    cd systems_engineering/06_safety
    python3 generate_safety_report.py
    python3 generate_safety_report.py --out /path/to/report.html

Output: safety_report.html  (default, next to this script)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# scenic_module lives alongside this script
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from scenic_module import quick_sweep, SweepReport
    from scenic_module.parameter_space import ALL_PARAMETERS, PARAMETER_GROUPS
    _HAS_SWEEP = True
except ImportError:
    _HAS_SWEEP = False

# ---------------------------------------------------------------------------
# Hazard log data   (source: hazard_log.md)
# Each entry: (id, title, cause, effect, s_pre, l_pre, s_post, l_post,
#              mitigation, reqs, scenario)
# S = Severity 1–5, L = Likelihood 1–5
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
# Scenic scenario → hazard coverage
# ---------------------------------------------------------------------------

SCENARIO_COVERAGE = [
    ("nominal_traverse", "Nominal Traverse",  ["H-05"]),
    ("battery_low",      "Battery Low",        ["H-03", "H-10"]),
    ("tilt_risk",        "Tilt Risk",           ["H-02"]),
    ("motor_stall",      "Motor Stall",         ["H-01"]),
    ("comm_loss",        "Comm Loss",           ["H-04"]),
]

ALL_HAZARD_IDS = [h[0] for h in HAZARDS]

# ---------------------------------------------------------------------------
# Serialise to JSON for embedding
# ---------------------------------------------------------------------------

def _to_json() -> dict:
    hazards = [
        {"id": h[0], "title": h[1], "cause": h[2], "effect": h[3],
         "s_pre": h[4], "l_pre": h[5], "s_post": h[6], "l_post": h[7],
         "risk_pre": h[4] * h[5], "risk_post": h[6] * h[7],
         "mitigation": h[8], "reqs": h[9], "scenario": h[10]}
        for h in HAZARDS
    ]
    fmea = [
        {"id": f[0], "sf": f[1], "mode": f[2], "effect": f[3], "cause": f[4],
         "s": f[5], "o": f[6], "d": f[7], "rpn": f[5] * f[6] * f[7],
         "hazard": f[8], "mitigation": f[9]}
        for f in FMEA
    ]
    fta = [
        {"hazard_id": c[0], "hazard_name": c[1],
         "cut_sets": c[2]}
        for c in FTA_CUTS
    ]
    scenarios = [
        {"id": s[0], "name": s[1], "covers": s[2]}
        for s in SCENARIO_COVERAGE
    ]
    return {
        "hazards":   hazards,
        "fmea":      fmea,
        "fta":       fta,
        "scenarios": scenarios,
        "all_hazard_ids": ALL_HAZARD_IDS,
    }


def _build_scenic_params_js() -> str:
    """Build the SCENIC_PARAMS JS constant from parameter_space.py (or fallback)."""
    if not _HAS_SWEEP:
        # Hardcoded fallback matching the previous version
        return """\
const SCENIC_PARAMS = {
  motor_stall:      [{name:'Motor Current',    unit:'A',   min:10.0, max:13.0, absMin:8,   absMax:15,  thresholds:[{v:10.0, lbl:'Trip ≥10 A'}]}],
  battery_low:      [{name:'Bus Voltage',      unit:'V',   min:9.5,  max:11.5, absMin:9,   absMax:13,  thresholds:[{v:11.0, lbl:'Warn ≤11 V'},{v:10.5, lbl:'Stop ≤10.5 V'}]}],
  tilt_risk:        [{name:'Roll Angle',       unit:'°',  min:20,   max:45,   absMin:0,   absMax:60,  thresholds:[{v:35,   lbl:'Stop ≥35°'}]}],
  comm_loss:        [{name:'Silence Duration', unit:'s',   min:0.5,  max:3.0,  absMin:0,   absMax:4,   thresholds:[{v:1.0,  lbl:'Halt ≥1 s'}]}],
  nominal_traverse: [{name:'Max Speed',        unit:'m/s', min:0.1,  max:0.35, absMin:0,   absMax:0.5, thresholds:[{v:0.4,  lbl:'Limit 0.4 m/s'}]}],
};"""

    # Build from parameter_space.py — one entry per scenario tag
    scenario_params: dict = {}
    for p in ALL_PARAMETERS.values():
        for scenario_tag in p.scenarios:
            if scenario_tag not in scenario_params:
                scenario_params[scenario_tag] = []
            thresh_list = [
                {"v": v, "lbl": f"{k.capitalize()} {v} {p.unit}"}
                for k, v in p.thresholds.items()
            ]
            scenario_params[scenario_tag].append({
                "name":      p.name,
                "unit":      p.unit,
                "min":       p.scenic_min,
                "max":       p.scenic_max,
                "absMin":    p.phys_min,
                "absMax":    p.phys_max,
                "thresholds": thresh_list,
            })

    lines = ["const SCENIC_PARAMS = {"]
    for tag, params in scenario_params.items():
        params_js = json.dumps(params, ensure_ascii=False)
        lines.append(f"  {tag}: {params_js},")
    lines.append("};")
    return "\n".join(lines)


def _run_sweep_json(n: int = 300, method: str = "lhs", seed: int = 42) -> str:
    """Run a quick parametric sweep and return its JSON string."""
    if not _HAS_SWEEP:
        return "null"
    try:
        result = quick_sweep(n=n, method=method, seed=seed)
        return SweepReport(result).to_json()
    except Exception as exc:
        print(f"  [warn] Sweep failed: {exc}")
        return "null"


# ---------------------------------------------------------------------------
# HTML template
# ---------------------------------------------------------------------------

_STYLE = """\
:root { --bs-body-font-size: .9rem; }
body  { background: #f8f9fa; }
.dash-header { background: #0d6efd; color: #fff; padding: 1.25rem 1.5rem; margin-bottom: 1.5rem; border-radius: 0 0 8px 8px; }
.dash-header h1 { font-size: 1.4rem; margin: 0 0 .25rem; }
.dash-header .meta { font-size: .8rem; opacity: .85; }
.badge-stat { font-size: .75rem; padding: .35em .65em; }
.nav-tabs .nav-link { font-size: .85rem; }
/* risk matrix */
.risk-matrix { border-collapse: collapse; }
.risk-matrix td, .risk-matrix th { width: 90px; height: 70px; text-align: center;
  vertical-align: middle; border: 2px solid #fff; cursor: pointer; font-size: .75rem; }
.risk-matrix th { background: #343a40; color: #fff; cursor: default; font-weight: 600; }
.risk-matrix td:hover { filter: brightness(.85); }
.risk-matrix td.selected { outline: 3px solid #0d6efd; outline-offset: -3px; }
.rm-badge { display: inline-block; background: rgba(0,0,0,.18); border-radius: 4px;
  padding: 1px 5px; margin: 1px; font-weight: 700; }
/* tables */
.sortable th { cursor: pointer; user-select: none; white-space: nowrap; }
.sortable th::after { content: " ↕"; opacity: .4; font-size: .7em; }
.sortable th.asc::after  { content: " ↑"; opacity: 1; }
.sortable th.desc::after { content: " ↓"; opacity: 1; }
.rpn-high   { background: #f8d7da !important; font-weight: 700; }
.rpn-med    { background: #fff3cd !important; }
.rpn-low    { background: #d4edda !important; }
.risk-high  { background: #f8d7da !important; }
.risk-med   { background: #fff3cd !important; }
.risk-low   { background: #d4edda !important; }
.cov-yes    { background: #d4edda; text-align: center; }
.cov-no     { background: #f8f9fa; text-align: center; color: #adb5bd; }
.filter-bar { background: #fff; border: 1px solid #dee2e6; border-radius: 6px;
  padding: .75rem 1rem; margin-bottom: 1rem; }
.cut-set { background: #fff3cd; border-radius: 4px; padding: .4rem .75rem;
  margin-bottom: .4rem; font-size: .85rem; }
.cut-event { display: inline-block; background: #ffc107; border-radius: 3px;
  padding: 2px 7px; margin: 2px; font-size: .8rem; font-weight: 600; }
.and-gate { font-weight: 700; color: #495057; margin: 0 4px; }
/* editable FMEA */
.fmea-sod { width:52px !important; padding:.15rem .3rem; font-size:.8rem; text-align:center; }
tr.fmea-edited td { background-color:#e7f1ff !important; }
/* scenic range bars */
.param-bar-wrap { margin-bottom:.75rem; }
.param-label { font-size:.8rem; font-weight:600; margin-bottom:.25rem; }
.param-track { position:relative; height:22px; background:#dee2e6; border-radius:4px; margin-top:20px; }
.param-fill  { position:absolute; height:100%; background:#0d6efd; border-radius:4px; opacity:.7; }
.param-thresh { position:absolute; width:2px; height:100%; background:#dc3545; }
.param-tick  { position:absolute; font-size:.7rem; top:-18px; transform:translateX(-50%); color:#6c757d; }
.param-thresh-lbl { position:absolute; font-size:.7rem; bottom:-16px; transform:translateX(-50%); color:#dc3545; font-weight:600; white-space:nowrap; }
.param-vals  { font-size:.78rem; color:#495057; margin-top:20px; }
/* tool nav strip */
.tool-nav { background:#fff; border-bottom:1px solid #dee2e6; padding:.4rem 1.5rem;
            display:flex; align-items:center; gap:.75rem; font-size:.82rem; }
.tool-nav a { color:#6c757d; text-decoration:none; display:flex; align-items:center; gap:.3rem; }
.tool-nav a:hover { color:#0d6efd; }
.tool-nav .active-tool { color:#212529; font-weight:600; }
.tool-nav .sep { color:#dee2e6; }
.tool-nav .sweep-badge { margin-left:auto; font-size:.75rem; }
/* sweep panel */
.sweep-stat { text-align:center; padding:.5rem .75rem; background:#f8f9fa;
              border-radius:6px; min-width:80px; }
.sweep-stat-val { font-size:1.4rem; font-weight:700; line-height:1.1; }
.sweep-stat-lbl { font-size:.72rem; color:#6c757d; }
/* ── Dev panel ─────────────────────────────────────────────────────────── */
#dev-chip{position:fixed;bottom:1.1rem;right:1.1rem;z-index:9999;width:36px;height:36px;
  border-radius:50%;background:#495057;color:#fff;display:flex;align-items:center;
  justify-content:center;cursor:pointer;font-size:1.05rem;
  box-shadow:0 2px 8px rgba(0,0,0,.3);user-select:none;transition:background .15s}
#dev-chip:hover{background:#343a40}
#dev-panel{display:none;position:fixed;bottom:4.6rem;right:1.1rem;z-index:9999;width:290px;
  background:#fff;border:1px solid #dee2e6;border-radius:8px;
  box-shadow:0 4px 20px rgba(0,0,0,.18);padding:1rem;font-size:.82rem}
#dev-toast{display:none;position:fixed;bottom:1.1rem;left:50%;transform:translateX(-50%);
  z-index:10000;padding:.4rem 1.2rem;border-radius:6px;font-size:.8rem;font-weight:500;
  box-shadow:0 2px 8px rgba(0,0,0,.2);white-space:nowrap;pointer-events:none}
"""

_SCRIPT = """\
const D  = window.__OSR_SAFETY__;
const SW = window.__OSR_SWEEP__;   // parametric sweep results (null if unavailable)
__SCENIC_PARAMS__
// ── Tab helpers (global — available before DOMContentLoaded) ───────────────
function activateScenariosTab() {
  var t = document.querySelector('#mainTabs [href="#tab-scenarios"]');
  if (t) bootstrap.Tab.getOrCreateInstance(t).show();
}

let fState = {}; // editable FMEA overrides: {id: {s, o, d}}
function getSOD(f) { const st = fState[f.id]; return st || {s:f.s, o:f.o, d:f.d}; }

// ── colour helpers ────────────────────────────────────────────────────────
function riskClass(s, l) {
  const r = s * l;
  return r > 9 ? 'risk-high' : r > 4 ? 'risk-med' : 'risk-low';
}
function riskLabel(s, l) {
  const r = s * l;
  return (r > 9 ? 'High' : r > 4 ? 'Medium' : 'Low') + ' (' + r + ')';
}
function rpnClass(rpn) { return rpn > 16 ? 'rpn-high' : rpn > 8 ? 'rpn-med' : 'rpn-low'; }
function riskBg(s, l) {
  const tbl = {
    '1,1':'#d4edda','1,2':'#d4edda','1,3':'#fff3cd','1,4':'#fff3cd','1,5':'#f8d7da',
    '2,1':'#d4edda','2,2':'#d4edda','2,3':'#fff3cd','2,4':'#f8d7da','2,5':'#f8d7da',
    '3,1':'#d4edda','3,2':'#fff3cd','3,3':'#fff3cd','3,4':'#f8d7da','3,5':'#f8d7da',
    '4,1':'#fff3cd','4,2':'#fff3cd','4,3':'#f8d7da','4,4':'#f8d7da','4,5':'#f8d7da',
    '5,1':'#fff3cd','5,2':'#f8d7da','5,3':'#f8d7da','5,4':'#f8d7da','5,5':'#f8d7da',
  };
  return tbl[s+','+l] || '#fff';
}

// ── risk matrix ──────────────────────────────────────────────────────────
let matrixFilter = null;  // {s, l} or null

function renderMatrix() {
  // group hazards by post-mitigation (s_post, l_post)
  const cells = {};
  D.hazards.forEach(h => {
    const key = h.s_post + ',' + h.l_post;
    (cells[key] = cells[key] || []).push(h.id);
  });

  let html = '<table class="risk-matrix"><thead><tr>';
  html += '<th>L \\ S</th>';
  for (let s = 1; s <= 5; s++) html += '<th>S=' + s + '</th>';
  html += '</tr></thead><tbody>';
  for (let l = 5; l >= 1; l--) {
    html += '<tr><th>L=' + l + '</th>';
    for (let s = 1; s <= 5; s++) {
      const key = s + ',' + l;
      const bg  = riskBg(s, l);
      const ids = cells[key] || [];
      const sel = matrixFilter && matrixFilter.s === s && matrixFilter.l === l ? ' selected' : '';
      const badges = ids.map(id => '<span class="rm-badge">' + id + '</span>').join('');
      html += '<td style="background:' + bg + '" class="' + sel + '" data-s="' + s + '" data-l="' + l + '">'
            + badges + '</td>';
    }
    html += '</tr>';
  }
  html += '</tbody></table>';
  html += '<p class="mt-2 text-muted" style="font-size:.8rem">Click a cell to filter the Hazard Log. Click again to clear.</p>';
  document.getElementById('rm-container').innerHTML = html;

  document.querySelectorAll('.risk-matrix td[data-s]').forEach(td => {
    td.addEventListener('click', () => {
      const s = +td.dataset.s, l = +td.dataset.l;
      matrixFilter = (matrixFilter && matrixFilter.s === s && matrixFilter.l === l) ? null : {s, l};
      renderMatrix();
      renderHazards();
    });
  });
}

// ── hazard log ────────────────────────────────────────────────────────────
let hazardRiskFilter = 'all';

function renderHazards() {
  let data = D.hazards;
  if (matrixFilter) {
    data = data.filter(h => h.s_post === matrixFilter.s && h.l_post === matrixFilter.l);
  }
  if (hazardRiskFilter !== 'all') {
    data = data.filter(h => {
      const r = h.risk_post;
      if (hazardRiskFilter === 'high')   return r > 9;
      if (hazardRiskFilter === 'medium') return r > 4 && r <= 9;
      if (hazardRiskFilter === 'low')    return r <= 4;
    });
  }

  const filterNote = matrixFilter
    ? '<div class="alert alert-info py-1 px-2 mb-2" style="font-size:.82rem">⬅ Filtered by Risk Matrix: S=' + matrixFilter.s + ' L=' + matrixFilter.l + ' &nbsp; <a href="#" id="clear-matrix-filter">Clear</a></div>'
    : '';

  let rows = data.map(h => {
    const reqs = h.reqs.map(r => '<code>' + r + '</code>').join(' ');
    const mvLink = '../MBSE_workspace/model_viewer.html#' + h.id.toLowerCase().replace('-','');
    const scenLink = h.scenario
      ? '<a href="#tab-scenarios" class="text-decoration-none" data-scenario="' + h.scenario + '">'
        + '<code style="font-size:.75rem">' + h.scenario + '.scenic</code></a>'
      : '—';
    return '<tr>'
      + '<td><strong><a href="' + mvLink + '" class="text-decoration-none" title="View in MBSE Model Viewer" target="_blank">'
        + h.id + ' <i class="bi bi-box-arrow-up-right" style="font-size:.6rem;opacity:.5"></i></a></strong></td>'
      + '<td>' + h.title + '</td>'
      + '<td>' + h.cause + '</td>'
      + '<td>' + h.effect + '</td>'
      + '<td class="' + riskClass(h.s_pre, h.l_pre) + '">' + riskLabel(h.s_pre, h.l_pre) + '</td>'
      + '<td class="' + riskClass(h.s_post, h.l_post) + '">' + riskLabel(h.s_post, h.l_post) + '</td>'
      + '<td>' + h.mitigation + '</td>'
      + '<td>' + reqs + '</td>'
      + '<td>' + scenLink + '</td>'
      + '</tr>';
  }).join('');

  document.getElementById('hazard-table-wrap').innerHTML = filterNote +
    '<table class="table table-sm table-bordered table-hover"><thead class="table-dark"><tr>'
    + '<th>ID</th><th>Title</th><th>Cause</th><th>Effect</th>'
    + '<th>Pre-Risk</th><th>Post-Risk</th><th>Mitigation</th><th>Requirements</th><th>Scenario</th>'
    + '</tr></thead><tbody>' + rows + '</tbody></table>'
    + '<p class="text-muted" style="font-size:.8rem">Showing ' + data.length + ' of ' + D.hazards.length + ' hazards.</p>';

  const cl = document.getElementById('clear-matrix-filter');
  if (cl) cl.addEventListener('click', e => { e.preventDefault(); matrixFilter = null; renderMatrix(); renderHazards(); });
}

// ── FMEA table ────────────────────────────────────────────────────────────
let fmeaSort  = {col: 'rpn', dir: -1};
let fmeaSF    = 'all';
let fmeaMinRPN = 0;

function renderFMEA() {
  let data = D.fmea
    .filter(f => fmeaSF === 'all' || f.sf === fmeaSF)
    .filter(f => { const {s,o,d} = getSOD(f); return s*o*d >= fmeaMinRPN; });

  data = [...data].sort((a, b) => {
    let va, vb;
    if (fmeaSort.col === 'rpn') {
      const sa = getSOD(a), sb = getSOD(b);
      va = sa.s*sa.o*sa.d; vb = sb.s*sb.o*sb.d;
    } else if (['s','o','d'].includes(fmeaSort.col)) {
      va = getSOD(a)[fmeaSort.col]; vb = getSOD(b)[fmeaSort.col];
    } else {
      va = a[fmeaSort.col]; vb = b[fmeaSort.col];
    }
    if (typeof va === 'string') va = va.toLowerCase(), vb = vb.toLowerCase();
    return fmeaSort.dir * (va < vb ? -1 : va > vb ? 1 : 0);
  });

  const cols = [
    {key:'id', label:'ID'}, {key:'sf', label:'SF'},
    {key:'mode', label:'Failure Mode'}, {key:'effect', label:'Effect'},
    {key:'cause', label:'Cause'},
    {key:'s', label:'S'}, {key:'o', label:'O'}, {key:'d', label:'D'},
    {key:'rpn', label:'RPN'}, {key:'hazard', label:'Hazard'},
    {key:'mitigation', label:'Mitigation'},
  ];

  const thead = cols.map(c => {
    let cls = '';
    if (fmeaSort.col === c.key) cls = fmeaSort.dir === 1 ? 'asc' : 'desc';
    return '<th class="' + cls + '" data-col="' + c.key + '">' + c.label + '</th>';
  }).join('');

  const tbody = data.map(f => {
    const sod = getSOD(f);
    const rpn = sod.s * sod.o * sod.d;
    const edited = !!fState[f.id];
    return '<tr class="' + (edited ? 'fmea-edited' : '') + '">'
      + '<td>' + f.id + '</td>'
      + '<td><span class="badge bg-secondary">' + f.sf + '</span></td>'
      + '<td>' + f.mode + '</td>'
      + '<td>' + f.effect + '</td>'
      + '<td>' + f.cause + '</td>'
      + '<td class="p-1"><input type="number" class="fmea-sod form-control" min="1" max="5" value="' + sod.s + '" data-id="' + f.id + '" data-field="s"></td>'
      + '<td class="p-1"><input type="number" class="fmea-sod form-control" min="1" max="5" value="' + sod.o + '" data-id="' + f.id + '" data-field="o"></td>'
      + '<td class="p-1"><input type="number" class="fmea-sod form-control" min="1" max="5" value="' + sod.d + '" data-id="' + f.id + '" data-field="d"></td>'
      + '<td class="text-center ' + rpnClass(rpn) + '" id="rpn-' + f.id + '">' + rpn + '</td>'
      + '<td>' + f.hazard + '</td>'
      + '<td>' + f.mitigation + '</td>'
      + '</tr>';
  }).join('');

  document.getElementById('fmea-wrap').innerHTML =
    '<table class="table table-sm table-bordered sortable"><thead class="table-dark"><tr>'
    + thead + '</tr></thead><tbody>' + tbody + '</tbody></table>'
    + '<p class="text-muted" style="font-size:.8rem">Showing ' + data.length + ' of ' + D.fmea.length
    + ' failure modes. <span class="text-primary">S/O/D cells are editable — RPN updates live. Blue rows have unsaved edits.</span></p>';

  document.querySelectorAll('#fmea-wrap th[data-col]').forEach(th => {
    th.addEventListener('click', () => {
      const col = th.dataset.col;
      fmeaSort = {col, dir: fmeaSort.col === col ? -fmeaSort.dir : -1};
      renderFMEA();
    });
  });

  document.querySelectorAll('.fmea-sod').forEach(inp => {
    inp.addEventListener('input', () => {
      const id = inp.dataset.id, field = inp.dataset.field;
      const val = Math.max(1, Math.min(5, parseInt(inp.value) || 1));
      inp.value = val;
      const orig = D.fmea.find(f => f.id === id);
      if (!fState[id]) fState[id] = {s: orig.s, o: orig.o, d: orig.d};
      fState[id][field] = val;
      const sod = fState[id];
      const rpn = sod.s * sod.o * sod.d;
      const cell = document.getElementById('rpn-' + id);
      if (cell) { cell.textContent = rpn; cell.className = 'text-center ' + rpnClass(rpn); }
      const row = inp.closest('tr');
      if (sod.s === orig.s && sod.o === orig.o && sod.d === orig.d) {
        delete fState[id]; row.classList.remove('fmea-edited');
      } else {
        row.classList.add('fmea-edited');
      }
    });
  });
}

function exportFMEA() {
  const hdr = ['ID','SF','Failure Mode','Effect','Cause','S','O','D','RPN','Hazard','Mitigation'];
  const rows = D.fmea.map(f => {
    const sod = getSOD(f);
    return [f.id, f.sf, f.mode, f.effect, f.cause, sod.s, sod.o, sod.d, sod.s*sod.o*sod.d, f.hazard, f.mitigation];
  });
  const csv = [hdr, ...rows].map(r =>
    r.map(v => '"' + String(v).replace(/"/g, '""') + '"').join(',')
  ).join('\\n');
  const a = document.createElement('a');
  a.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
  a.download = 'OSR_FMEA.csv';
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
}

function resetFMEA() { fState = {}; renderFMEA(); }

// ── FTA ──────────────────────────────────────────────────────────────────
function renderFTA() {
  const html = D.fta.map(ft => {
    const sets = ft.cut_sets.map((cs, i) => {
      const events = cs.map(e => '<span class="cut-event">' + e + '</span>').join('<span class="and-gate">AND</span>');
      return '<div class="cut-set"><strong>CS-' + (i+1) + ':</strong> ' + events + '</div>';
    }).join('');
    return '<div class="mb-4"><h5>' + ft.hazard_id + ' — ' + ft.hazard_name + '</h5>'
      + '<p class="text-muted mb-2" style="font-size:.83rem">Minimal cut sets — each is sufficient to cause the top event:</p>'
      + sets + '</div>';
  }).join('<hr>');
  document.getElementById('fta-wrap').innerHTML = html;
}

// ── Scenario coverage ─────────────────────────────────────────────────────
function renderRangeBar(p) {
  const span = p.absMax - p.absMin;
  const left  = ((p.min - p.absMin) / span * 100).toFixed(1);
  const width = ((p.max - p.min)    / span * 100).toFixed(1);
  const ticks = [p.absMin, p.absMax].map(t => {
    const pct = ((t - p.absMin) / span * 100).toFixed(1);
    return '<div class="param-tick" style="left:' + pct + '%">' + t + '</div>';
  }).join('');
  const threshs = p.thresholds.map(t => {
    const pct = ((t.v - p.absMin) / span * 100).toFixed(1);
    return '<div class="param-thresh" style="left:' + pct + '%"></div>'
         + '<div class="param-thresh-lbl" style="left:' + pct + '%">' + t.lbl + '</div>';
  }).join('');
  return '<div class="param-bar-wrap">'
       + '<div class="param-label">' + p.name + ' (' + p.unit + ')</div>'
       + '<div class="param-track">' + ticks
       + '<div class="param-fill" style="left:' + left + '%;width:' + width + '%"></div>'
       + threshs + '</div>'
       + '<div class="param-vals">Sampled range: <strong>' + p.min + '&ndash;' + p.max + ' ' + p.unit + '</strong></div>'
       + '</div>';
}

function renderScenarios() {
  const ids = D.all_hazard_ids;
  const head = '<tr><th>Scenario</th>' + ids.map(h => '<th>' + h + '</th>').join('') + '</tr>';
  const rows = D.scenarios.map(sc => {
    const cells = ids.map(h =>
      sc.covers.includes(h)
        ? '<td class="cov-yes">✓</td>'
        : '<td class="cov-no">·</td>'
    ).join('');
    return '<tr><td><strong>' + sc.name + '</strong><br><code style="font-size:.75rem">' + sc.id + '.scenic</code></td>' + cells + '</tr>';
  }).join('');
  document.getElementById('scenarios-wrap').innerHTML =
    '<div style="overflow-x:auto"><table class="table table-sm table-bordered">'
    + '<thead class="table-dark">' + head + '</thead><tbody>' + rows + '</tbody></table></div>'
    + '<p class="text-muted" style="font-size:.8rem">&#10003; = scenario explicitly exercises the boundary conditions of that hazard.</p>';

  // Render parameter range bars (one section per scenario, with scroll anchor)
  let rangeHtml = '';
  D.scenarios.forEach(sc => {
    const params = SCENIC_PARAMS[sc.id];
    if (!params) return;
    rangeHtml += '<div class="mb-5" id="range-' + sc.id + '">'
      + '<h6 class="mb-3"><i class="bi bi-play-circle me-1"></i>'
      + sc.name + ' <code style="font-size:.8rem">' + sc.id + '.scenic</code></h6>'
      + '<div class="row g-4">'
      + params.map(p => '<div class="col-md-4">' + renderRangeBar(p) + '</div>').join('')
      + '</div></div>';
  });
  const el = document.getElementById('scenic-ranges-wrap');
  if (el) el.innerHTML = rangeHtml || '<p class="text-muted">No parameter data available.</p>';
}

// ── Action items ──────────────────────────────────────────────────────────
function renderActions() {
  const high = D.fmea.filter(f => f.rpn > 16).sort((a,b) => b.rpn - a.rpn);
  const rows = high.map(f =>
    '<tr><td>' + f.id + '</td>'
    + '<td><span class="badge bg-secondary">' + f.sf + '</span></td>'
    + '<td>' + f.mode + '</td>'
    + '<td class="text-center ' + rpnClass(f.rpn) + '">' + f.rpn + '</td>'
    + '<td>' + f.mitigation + '</td></tr>'
  ).join('');
  document.getElementById('actions-wrap').innerHTML =
    '<table class="table table-sm table-bordered"><thead class="table-dark"><tr>'
    + '<th>FM ID</th><th>SF</th><th>Failure Mode</th><th>RPN</th><th>Required Action</th>'
    + '</tr></thead><tbody>' + rows + '</tbody></table>'
    + '<p class="text-muted" style="font-size:.8rem">' + high.length + ' failure modes with RPN > 16.</p>';
}

// ── Summary stats ─────────────────────────────────────────────────────────
function renderSummary() {
  const hHigh = D.hazards.filter(h => h.risk_post > 9).length;
  const hMed  = D.hazards.filter(h => h.risk_post > 4 && h.risk_post <= 9).length;
  const hLow  = D.hazards.filter(h => h.risk_post <= 4).length;
  const fHigh = D.fmea.filter(f => f.rpn > 16).length;
  document.getElementById('stat-hazards').textContent  = D.hazards.length;
  document.getElementById('stat-h-high').textContent   = hHigh;
  document.getElementById('stat-h-med').textContent    = hMed;
  document.getElementById('stat-h-low').textContent    = hLow;
  document.getElementById('stat-fm').textContent       = D.fmea.length;
  document.getElementById('stat-fm-high').textContent  = fHigh;
  document.getElementById('stat-fta').textContent      = D.fta.length;
  document.getElementById('stat-scen').textContent     = D.scenarios.length;
}

// ── Filter wiring ─────────────────────────────────────────────────────────
function wireFilters() {
  // hazard risk filter
  document.querySelectorAll('[data-hrisk]').forEach(btn => {
    btn.addEventListener('click', () => {
      hazardRiskFilter = btn.dataset.hrisk;
      document.querySelectorAll('[data-hrisk]').forEach(b =>
        b.classList.toggle('active', b === btn));
      renderHazards();
    });
  });

  // FMEA SF filter
  const sfSel = document.getElementById('sf-select');
  if (sfSel) sfSel.addEventListener('change', () => { fmeaSF = sfSel.value; renderFMEA(); });

  // FMEA min RPN
  const rpnSlider = document.getElementById('rpn-min');
  const rpnVal    = document.getElementById('rpn-val');
  if (rpnSlider) {
    rpnSlider.addEventListener('input', () => {
      fmeaMinRPN = +rpnSlider.value;
      rpnVal.textContent = fmeaMinRPN;
      renderFMEA();
    });
  }

  const expBtn = document.getElementById('fmea-export');
  if (expBtn) expBtn.addEventListener('click', exportFMEA);
  const rstBtn = document.getElementById('fmea-reset');
  if (rstBtn) rstBtn.addEventListener('click', resetFMEA);
}

// ── Parametric sweep panel ────────────────────────────────────────────────
function renderSweep() {
  const wrap = document.getElementById('sweep-wrap');
  if (!wrap) return;
  if (!SW) {
    wrap.innerHTML = '<p class="text-muted" style="font-size:.85rem">Sweep data not embedded — re-run <code>generate_safety_report.py</code> with scenic_module available.</p>';
    return;
  }
  const hPct  = (SW.summary.hazard_rate * 100).toFixed(1);
  const hCls  = SW.summary.hazard_rate > 0.5 ? 'text-danger' : SW.summary.hazard_rate > 0.1 ? 'text-warning' : 'text-success';
  const stats = '<div class="d-flex gap-3 mb-3 flex-wrap">'
    + `<div class="sweep-stat"><div class="sweep-stat-val ${hCls}">${hPct}%</div><div class="sweep-stat-lbl">Hazard Rate</div></div>`
    + `<div class="sweep-stat"><div class="sweep-stat-val text-danger">${SW.summary.n_hazardous}</div><div class="sweep-stat-lbl">Hazardous</div></div>`
    + `<div class="sweep-stat"><div class="sweep-stat-val text-warning">${SW.summary.n_boundary}</div><div class="sweep-stat-lbl">Boundary</div></div>`
    + `<div class="sweep-stat"><div class="sweep-stat-val text-success">${SW.summary.n_safe}</div><div class="sweep-stat-lbl">Safe</div></div>`
    + `<div class="sweep-stat"><div class="sweep-stat-val">${SW.summary.n_total}</div><div class="sweep-stat-lbl">Total Samples</div></div>`
    + '</div>';

  const viols = SW.summary.violation_counts || {};
  const bars  = Object.entries(viols).map(([cid, cnt]) => {
    const frac = cnt / SW.summary.n_total;
    const pct  = (frac * 100).toFixed(1);
    const barCls = frac > 0.5 ? 'bg-danger' : frac > 0.2 ? 'bg-warning' : 'bg-success';
    return `<div class="mb-2">
      <div class="d-flex justify-content-between" style="font-size:.78rem">
        <strong>${cid}</strong><span>${cnt}&thinsp;/&thinsp;${SW.summary.n_total} (${pct}%)</span>
      </div>
      <div class="progress" style="height:12px">
        <div class="progress-bar ${barCls}" style="width:${pct}%"></div>
      </div></div>`;
  }).join('');

  const pKeys = ['motor_current_peak','battery_voltage','roll_deg','cmd_vel_age_sec','linear_velocity'];
  const pHdrs = pKeys.map(k => '<th>' + k.replace(/_/g,' ') + '</th>').join('');
  const topRows = (SW.top_hazardous || []).slice(0, 8).map((pt, i) => {
    const violated = (pt.violated_constraints || []).join(', ') || '—';
    const hPct2 = (pt.hazard_level * 100).toFixed(1);
    const hCls2 = pt.hazard_level > 0.3 ? 'text-danger fw-bold' : 'text-warning';
    const cells = pKeys.map(k => {
      const v = pt.params[k];
      return '<td>' + (v !== undefined ? (+v).toFixed(2) : '—') + '</td>';
    }).join('');
    return `<tr><td>${i+1}</td><td class="${hCls2}">${hPct2}%</td>`
      + `<td><code style="font-size:.72rem">${violated}</code></td>${cells}</tr>`;
  }).join('');

  wrap.innerHTML = stats
    + '<div class="row g-3">'
    + '<div class="col-md-5"><h6 style="font-size:.83rem">Constraint Violation Rate</h6>'
    + (bars || '<p class="text-muted">No violations detected.</p>')
    + '</div>'
    + '<div class="col-md-7"><h6 style="font-size:.83rem">Top Hazardous Scenario Points</h6>'
    + '<div style="overflow-x:auto"><table class="table table-sm table-bordered" style="font-size:.76rem">'
    + '<thead class="table-dark"><tr><th>#</th><th>Hazard%</th><th>Violated</th>' + pHdrs + '</tr></thead>'
    + '<tbody>' + topRows + '</tbody></table></div>'
    + '</div></div>'
    + `<p class="text-muted" style="font-size:.76rem">LHS sweep — ${SW.sweep.n_actual} samples, seed=${SW.sweep.seed}. `
    + 'Sweeps the full physical OA/OE range (not just the Scenic sampled range). '
    + '<a href="scenarios/sweep/" class="text-decoration-none">Generated .scenic files →</a></p>';

  // Update sweep badge in tool nav
  const badge = document.getElementById('sweep-nav-stat');
  if (badge) badge.textContent = `Sweep: ${SW.sweep.n_actual} pts · ${hPct}% hazard rate`;
}

// ── Scenario → Sweep cross-link ───────────────────────────────────────────
function wireScenarioLinks() {
  document.querySelectorAll('[data-scenario]').forEach(el => {
    el.addEventListener('click', e => {
      e.preventDefault();
      const tag = el.dataset.scenario;
      // Switch to scenarios tab, then scroll to the relevant range bar
      activateScenariosTab();
      setTimeout(() => {
        const target = document.getElementById('range-' + tag);
        if (target) target.scrollIntoView({behavior:'smooth', block:'center'});
      }, 120);
    });
  });
}

// ── Hash-based tab routing ────────────────────────────────────────────────
function routeHash() {
  const hash = location.hash.slice(1);
  if (!hash) return;
  // Only look inside #mainTabs so we always get the real tab trigger, not
  // other anchors (e.g. tool-nav links) that share the same href.
  const el = document.querySelector('#mainTabs [href="#' + hash + '"]');
  if (el) bootstrap.Tab.getOrCreateInstance(el).show();
}

// ── Boot ──────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  renderSummary();
  renderMatrix();
  renderHazards();
  renderFMEA();
  renderFTA();
  renderScenarios();
  renderSweep();
  renderActions();
  wireFilters();
  wireScenarioLinks();
  routeHash();

  // Update hash on tab change for deep-linking
  document.querySelectorAll('[data-bs-toggle="tab"]').forEach(el => {
    el.addEventListener('shown.bs.tab', e => {
      const target = e.target.getAttribute('href');
      history.replaceState(null, '', target);
    });
  });
});

// ── Dev Panel ────────────────────────────────────────────────────────────────
var _devOpen = false;
function devToggle() {
  _devOpen = !_devOpen;
  document.getElementById('dev-panel').style.display = _devOpen ? 'block' : 'none';
}
function _devToast(msg, ok) {
  var t = document.getElementById('dev-toast');
  t.textContent = msg;
  t.style.background = ok ? '#198754' : '#dc3545';
  t.style.color = '#fff';
  t.style.display = 'block';
  setTimeout(function() { t.style.display = 'none'; }, ok ? 3000 : 5000);
}
function devRegen() {
  var btn = document.getElementById('dev-regen-btn');
  var n   = document.getElementById('dev-n').value;
  var m   = document.getElementById('dev-method').value;
  var s   = document.getElementById('dev-seed').value;
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Running\u2026';
  var t0   = Date.now();
  var ctrl = new AbortController();
  var tid  = setTimeout(function() { ctrl.abort(); }, 300000);
  fetch('http://localhost:8765/regen/safety?n=' + n + '&method=' + m + '&seed=' + s,
        {method: 'POST', signal: ctrl.signal})
    .then(function(r) { clearTimeout(tid); return r.json(); })
    .then(function(d) {
      if (d.ok) {
        _devToast('Regenerated in ' + d.elapsed_s + ' s', true);
        setTimeout(function() { location.reload(); }, 900);
      } else {
        _devToast('Error: ' + (d.stderr || d.error || '?').slice(0, 140), false);
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-arrow-clockwise me-1"></i>Regenerate';
      }
    })
    .catch(function(e) {
      clearTimeout(tid);
      _devToast('Fetch error: ' + e.message, false);
      btn.disabled = false;
      btn.innerHTML = '<i class="bi bi-arrow-clockwise me-1"></i>Regenerate';
    });
}
function devCopy() {
  var cmd = document.getElementById('dev-cli-cmd').textContent;
  if (navigator.clipboard) {
    navigator.clipboard.writeText(cmd).then(function() { _devToast('Copied!', true); });
  }
}
(function() {
  var ctrl = new AbortController();
  var tid  = setTimeout(function() { ctrl.abort(); }, 700);
  fetch('http://localhost:8765/ping', {signal: ctrl.signal})
    .then(function(r) { clearTimeout(tid); return r.json(); })
    .then(function(d) {
      if (d && d.ok) {
        document.getElementById('dev-server-mode').style.display = 'block';
      } else {
        document.getElementById('dev-cli-mode').style.display = 'block';
      }
    })
    .catch(function() {
      clearTimeout(tid);
      document.getElementById('dev-cli-mode').style.display = 'block';
    });
})();
"""


_DEV_PANEL_SAFETY_HTML = """\
<div id="dev-chip" title="Dev Tools (dev_server.py)" onclick="devToggle()">&#9881;</div>
<div id="dev-panel">
  <div style="font-weight:600;margin-bottom:.65rem;color:#343a40;font-size:.85rem">&#9881; Dev Tools</div>
  <div id="dev-server-mode" style="display:none">
    <div class="row g-2 mb-2">
      <div class="col">
        <label style="font-size:.72rem;color:#6c757d;display:block">Method</label>
        <select id="dev-method" class="form-select form-select-sm">
          <option value="lhs">lhs</option>
          <option value="montecarlo">montecarlo</option>
          <option value="grid">grid</option>
        </select>
      </div>
      <div class="col">
        <label style="font-size:.72rem;color:#6c757d;display:block">n</label>
        <input id="dev-n" type="number" class="form-control form-control-sm"
               value="300" min="50" max="2000" step="50">
      </div>
      <div class="col">
        <label style="font-size:.72rem;color:#6c757d;display:block">seed</label>
        <input id="dev-seed" type="number" class="form-control form-control-sm"
               value="42" min="0">
      </div>
    </div>
    <button id="dev-regen-btn" class="btn btn-sm btn-primary w-100 mb-2"
            onclick="devRegen()">
      <i class="bi bi-arrow-clockwise me-1"></i>Regenerate Safety Report
    </button>
    <a href="http://localhost:8765/model_viewer.html"
       class="btn btn-sm btn-outline-secondary w-100" target="_blank">
      <i class="bi bi-box-arrow-up-right me-1"></i>Open Model Viewer
    </a>
    <div id="dev-status" class="mt-2" style="min-height:1rem;font-size:.72rem;color:#6c757d"></div>
  </div>
  <div id="dev-cli-mode" style="display:none">
    <div style="color:#6c757d;margin-bottom:.5rem;font-size:.78rem">Dev server not running.</div>
    <code id="dev-cli-cmd" style="font-size:.7rem;display:block;background:#f8f9fa;
          padding:.35rem .5rem;border-radius:4px;word-break:break-all"
    >python3 generate_safety_report.py</code>
    <button class="btn btn-sm btn-outline-secondary w-100 mt-2" onclick="devCopy()">
      <i class="bi bi-clipboard me-1"></i>Copy command
    </button>
    <div style="color:#6c757d;margin-top:.6rem;font-size:.75rem">
      Start server: <code style="font-size:.7rem">python3 dev_server.py</code>
    </div>
  </div>
</div>
<div id="dev-toast"></div>
"""


def generate_report(sweep_n: int = 300,
                    sweep_method: str = "lhs",
                    sweep_seed: int = 42) -> str:
    data = _to_json()
    data_json  = json.dumps(data, ensure_ascii=False, indent=2)
    date_str   = datetime.now().strftime("%Y-%m-%d")
    all_sfs    = sorted({f[1] for f in FMEA})
    sf_opts    = "".join(f'<option value="{sf}">{sf}</option>' for sf in all_sfs)

    high_count = sum(1 for h in HAZARDS if h[6] * h[7] > 9)
    fm_high    = sum(1 for f in FMEA if f[5] * f[6] * f[7] > 16)

    # Run parametric sweep and embed result
    print(f"  Running parametric sweep (method={sweep_method}, n={sweep_n}, seed={sweep_seed}) …",
          end=" ", flush=True)
    sweep_json = _run_sweep_json(n=sweep_n, method=sweep_method, seed=sweep_seed)
    print("done" if sweep_json != "null" else "skipped (scenic_module not found)")

    # Resolve dynamic JS constant from parameter_space.py
    scenic_params_js = _build_scenic_params_js()
    script = _SCRIPT.replace("__SCENIC_PARAMS__", scenic_params_js)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OSR Safety Dashboard</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
<style>{_STYLE}</style>
</head>
<body>

<!-- Header -->
<div class="dash-header">
  <div class="container-fluid">
    <div class="d-flex justify-content-between align-items-start">
      <div>
        <h1><i class="bi bi-shield-check me-2"></i>JPL Open Source Rover — Safety Dashboard</h1>
        <div class="meta">OSR-SAF-REPORT-001 &nbsp;|&nbsp; DRAFT &nbsp;|&nbsp; Generated: {date_str}</div>
      </div>
      <div class="d-flex gap-2 mt-1">
        <a class="btn btn-sm btn-light" href="../MBSE_workspace/model_viewer.html"
           title="Open MBSE Model Viewer">
          <i class="bi bi-diagram-2-fill me-1"></i>MBSE Model
        </a>
        <a class="btn btn-sm btn-outline-light" href="javascript:void(0)"
           title="Jump to Scenarios &amp; Sweep" onclick="activateScenariosTab()">
          <i class="bi bi-graph-up me-1"></i>Sweep
        </a>
      </div>
    </div>
    <div class="mt-2">
      <span class="badge bg-light text-dark badge-stat me-1">
        <span id="stat-hazards">—</span> hazards
      </span>
      <span class="badge bg-danger badge-stat me-1">
        <span id="stat-h-high">—</span> high post-risk
      </span>
      <span class="badge bg-warning text-dark badge-stat me-1">
        <span id="stat-h-med">—</span> medium
      </span>
      <span class="badge bg-success badge-stat me-1">
        <span id="stat-h-low">—</span> low
      </span>
      <span class="badge bg-light text-dark badge-stat me-1 ms-2">
        <span id="stat-fm">—</span> failure modes
      </span>
      <span class="badge bg-danger badge-stat me-1">
        <span id="stat-fm-high">—</span> RPN&gt;16
      </span>
      <span class="badge bg-light text-dark badge-stat me-1 ms-2">
        <span id="stat-fta">—</span> fault trees
      </span>
      <span class="badge bg-light text-dark badge-stat">
        <span id="stat-scen">—</span> Scenic scenarios
      </span>
    </div>
  </div>
</div>

<!-- Tool nav strip -->
<div class="tool-nav">
  <a href="../MBSE_workspace/model_viewer.html">
    <i class="bi bi-diagram-2-fill"></i> MBSE Model
  </a>
  <span class="sep">|</span>
  <span class="active-tool">
    <i class="bi bi-shield-fill-check text-danger"></i> Safety Dashboard
  </span>
  <span class="sep">|</span>
  <a href="javascript:void(0)" id="tool-nav-sweep" onclick="activateScenariosTab()">
    <i class="bi bi-graph-up"></i> Parametric Sweep
  </a>
  <span class="sweep-badge text-muted" id="sweep-nav-stat"></span>
</div>

<div class="container-fluid px-4">

  <!-- Tab nav -->
  <ul class="nav nav-tabs mb-3" id="mainTabs">
    <li class="nav-item"><a class="nav-link active" data-bs-toggle="tab" href="#tab-summary">
      <i class="bi bi-bar-chart-fill me-1"></i>Summary</a></li>
    <li class="nav-item"><a class="nav-link" data-bs-toggle="tab" href="#tab-matrix">
      <i class="bi bi-grid-3x3-gap-fill me-1"></i>Risk Matrix</a></li>
    <li class="nav-item"><a class="nav-link" data-bs-toggle="tab" href="#tab-hazards">
      <i class="bi bi-exclamation-triangle-fill me-1"></i>Hazard Log</a></li>
    <li class="nav-item"><a class="nav-link" data-bs-toggle="tab" href="#tab-fmea">
      <i class="bi bi-table me-1"></i>FMEA</a></li>
    <li class="nav-item"><a class="nav-link" data-bs-toggle="tab" href="#tab-fta">
      <i class="bi bi-diagram-3-fill me-1"></i>FTA Cut Sets</a></li>
    <li class="nav-item"><a class="nav-link" data-bs-toggle="tab" href="#tab-scenarios">
      <i class="bi bi-play-circle-fill me-1"></i>Scenarios</a></li>
    <li class="nav-item"><a class="nav-link" data-bs-toggle="tab" href="#tab-actions">
      <i class="bi bi-flag-fill me-1"></i>Action Items
      <span class="badge bg-danger ms-1">{fm_high}</span></a></li>
  </ul>

  <div class="tab-content">

    <!-- Summary -->
    <div class="tab-pane fade show active" id="tab-summary">
      <div class="row g-3 mb-3">
        <div class="col-md-3">
          <div class="card h-100">
            <div class="card-body">
              <h6 class="card-title text-muted">Hazards Identified</h6>
              <p class="display-6 mb-0" id="sum-hz">{len(HAZARDS)}</p>
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card h-100 border-danger">
            <div class="card-body">
              <h6 class="card-title text-muted">High Post-Risk Hazards</h6>
              <p class="display-6 mb-0 text-danger" id="sum-hh">{high_count}</p>
              <small class="text-muted">All residual due to S=5 (severity cannot be reduced)</small>
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card h-100">
            <div class="card-body">
              <h6 class="card-title text-muted">Failure Modes (FMEA)</h6>
              <p class="display-6 mb-0">{len(FMEA)}</p>
            </div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card h-100 border-warning">
            <div class="card-body">
              <h6 class="card-title text-muted">High-RPN Items (RPN&gt;16)</h6>
              <p class="display-6 mb-0 text-warning" id="sum-rpm">{fm_high}</p>
              <small class="text-muted">Require priority action</small>
            </div>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="card-body">
          <h6>Legend</h6>
          <div class="d-flex gap-3 flex-wrap">
            <div><span class="badge risk-high">High risk</span> S×L &gt; 9</div>
            <div><span class="badge risk-med">Medium risk</span> S×L 5–9</div>
            <div><span class="badge risk-low">Low risk</span> S×L ≤ 4</div>
            <div><span class="badge rpn-high">RPN &gt; 16</span> Priority action</div>
            <div><span class="badge rpn-med">RPN 9–16</span> Monitor</div>
            <div><span class="badge rpn-low">RPN ≤ 8</span> Acceptable</div>
          </div>
          <p class="text-muted mt-2 mb-0" style="font-size:.82rem">
            S = Severity, L = Likelihood, O = Occurrence, D = Detectability (1–5 each).<br>
            High-severity hazards (S=5) remain red post-mitigation by definition — mitigation
            reduces Likelihood, not Severity. This is expected and correct.
          </p>
        </div>
      </div>
    </div>

    <!-- Risk Matrix -->
    <div class="tab-pane fade" id="tab-matrix">
      <div class="card">
        <div class="card-body">
          <h5 class="card-title">Post-Mitigation Risk Matrix (Severity × Likelihood)</h5>
          <p class="text-muted" style="font-size:.83rem">
            Hazard IDs shown at their post-mitigation (S, L) position.
            Click any cell to filter the Hazard Log to that risk level.
          </p>
          <div id="rm-container"></div>
        </div>
      </div>
    </div>

    <!-- Hazard Log -->
    <div class="tab-pane fade" id="tab-hazards">
      <div class="filter-bar d-flex gap-2 align-items-center flex-wrap">
        <strong>Filter by post-risk:</strong>
        <button class="btn btn-sm btn-outline-secondary active" data-hrisk="all">All</button>
        <button class="btn btn-sm btn-danger"  data-hrisk="high">High</button>
        <button class="btn btn-sm btn-warning" data-hrisk="medium">Medium</button>
        <button class="btn btn-sm btn-success" data-hrisk="low">Low</button>
        <span class="text-muted ms-2" style="font-size:.8rem">Risk Matrix selection also filters this table.</span>
      </div>
      <div id="hazard-table-wrap"></div>
    </div>

    <!-- FMEA -->
    <div class="tab-pane fade" id="tab-fmea">
      <div class="filter-bar d-flex gap-3 align-items-center flex-wrap">
        <div>
          <label class="form-label mb-0 me-1" style="font-size:.83rem"><strong>System Function:</strong></label>
          <select class="form-select form-select-sm d-inline-block w-auto" id="sf-select">
            <option value="all">All SFs</option>
            {sf_opts}
          </select>
        </div>
        <div class="d-flex align-items-center gap-2">
          <label class="mb-0" style="font-size:.83rem"><strong>Min RPN:</strong></label>
          <input type="range" class="form-range" id="rpn-min" min="0" max="25" step="1" value="0" style="width:140px">
          <span id="rpn-val" class="badge bg-secondary">0</span>
        </div>
        <div class="ms-auto d-flex gap-2">
          <button class="btn btn-sm btn-outline-primary" id="fmea-export">
            <i class="bi bi-download me-1"></i>Export CSV
          </button>
          <button class="btn btn-sm btn-outline-secondary" id="fmea-reset">
            <i class="bi bi-arrow-counterclockwise me-1"></i>Reset
          </button>
        </div>
      </div>
      <div id="fmea-wrap"></div>
    </div>

    <!-- FTA -->
    <div class="tab-pane fade" id="tab-fta">
      <div class="card">
        <div class="card-body">
          <h5 class="card-title">Fault Tree Minimal Cut Sets</h5>
          <p class="text-muted" style="font-size:.83rem">
            Each cut set is a minimal combination of basic events sufficient to cause the top-level hazard.
            Eliminating any single cut set breaks the fault path.
          </p>
          <div id="fta-wrap"></div>
        </div>
      </div>
    </div>

    <!-- Scenarios -->
    <div class="tab-pane fade" id="tab-scenarios">
      <div class="card mb-3">
        <div class="card-body">
          <h5 class="card-title">Scenic Scenario Coverage Matrix</h5>
          <p class="text-muted" style="font-size:.83rem">
            Each row is a Scenic probabilistic scenario file. ✓ indicates the scenario
            explicitly exercises the boundary conditions of that hazard.
          </p>
          <div id="scenarios-wrap"></div>
        </div>
      </div>
      <div class="card mb-3">
        <div class="card-body">
          <h5 class="card-title">Scenic Parameter Ranges vs Safety Thresholds</h5>
          <p class="text-muted" style="font-size:.83rem">
            Sampled parameter range
            <span style="display:inline-block;width:18px;height:10px;background:#0d6efd;opacity:.7;border-radius:2px;vertical-align:middle"></span>
            vs safety threshold
            <span style="display:inline-block;width:2px;height:14px;background:#dc3545;vertical-align:middle"></span>.
            Values from <code>parameter_space.py</code> — no Scenic installation required.
          </p>
          <div id="scenic-ranges-wrap"></div>
        </div>
      </div>

      <!-- Parametric Sweep Panel -->
      <div class="card border-primary">
        <div class="card-header bg-primary text-white d-flex align-items-center justify-content-between">
          <span><i class="bi bi-graph-up me-2"></i>Parametric OA/OE Sweep
            <span class="badge bg-light text-primary ms-2" style="font-size:.72rem">scenic_module</span>
          </span>
          <span style="font-size:.78rem;opacity:.85">LHS · n={sweep_n} · all parameters swept</span>
        </div>
        <div class="card-body">
          <p class="text-muted mb-3" style="font-size:.83rem">
            Latin Hypercube Sampling across the full physical OA/OE parameter space —
            wider than the Scenic sampled ranges above. Each point is evaluated against all
            safety constraints (H-01..H-05). Hazardous = at least one constraint violated.
            <a href="../MBSE_workspace/model_viewer.html" class="ms-1">MBSE constraints ↗</a>
          </p>
          <div id="sweep-wrap"></div>
        </div>
      </div>
    </div>

    <!-- Action Items -->
    <div class="tab-pane fade" id="tab-actions">
      <div class="card">
        <div class="card-body">
          <h5 class="card-title">Open Action Items — RPN &gt; 16</h5>
          <p class="text-muted" style="font-size:.83rem">
            These failure modes have a Risk Priority Number above the acceptable threshold
            and require specific mitigation actions before the rover is considered safe to operate.
          </p>
          <div id="actions-wrap"></div>
        </div>
      </div>
    </div>

  </div><!-- /.tab-content -->

  <footer class="text-muted mt-4 mb-3 pt-3 border-top" style="font-size:.78rem">
    Generated by <code>generate_safety_report.py</code> — OSR MBSE safety analysis pipeline.<br>
    Emulates ATICA4Capella FHA + FMEA outputs without requiring Capella.<br>
    Source data: <code>hazard_log.md</code> · <code>fmea_system.md</code> · <code>fta.md</code> · <code>scenarios/</code>
  </footer>
</div>

<script>window.__OSR_SAFETY__ = {data_json};</script>
<script>window.__OSR_SWEEP__   = {sweep_json};</script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script>{script}</script>
{_DEV_PANEL_SAFETY_HTML}
</body>
</html>
"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(
        description="Generate OSR interactive HTML safety dashboard"
    )
    p.add_argument("--out", "-o", default=None,
                   help="Output path (default: safety_report.html next to this script)")
    p.add_argument("--sweep-n", type=int, default=300, metavar="N",
                   help="Number of sweep samples (default: 300)")
    p.add_argument("--sweep-method", default="lhs",
                   choices=["lhs", "montecarlo", "grid"],
                   help="Sweep sampling method (default: lhs)")
    p.add_argument("--sweep-seed", type=int, default=42, metavar="S",
                   help="Random seed (default: 42)")
    args = p.parse_args()

    out = Path(args.out) if args.out else Path(__file__).parent / "safety_report.html"
    out.write_text(
        generate_report(
            sweep_n=args.sweep_n,
            sweep_method=args.sweep_method,
            sweep_seed=args.sweep_seed,
        ),
        encoding="utf-8",
    )

    print(f"Written: {out}")
    print(f"  {len(HAZARDS)} hazards, {len(FMEA)} failure modes, "
          f"{len(FTA_CUTS)} fault trees, {len(SCENARIO_COVERAGE)} scenarios")
    print(f"  Interactive dashboard — open in any browser")


if __name__ == "__main__":
    main()
