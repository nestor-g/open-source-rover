#!/usr/bin/env python3
"""
generate_scenarios.py — OSR Scenic Scenario Generator
=======================================================
Runs Scenic probabilistic scenario files and outputs concrete test parameter
sets as JSON.  No simulator required — runs in abstract mode.

Usage:
    pip install scenic                                   # one-time setup

    python3 generate_scenarios.py --all --n 50           # all scenarios, 50 each
    python3 generate_scenarios.py --scenario tilt_risk   # single scenario
    python3 generate_scenarios.py --list                 # list available scenarios

Output:
    JSON array of test case dicts, written to stdout or --out file.

Each test case contains:
    - scenario / sub_scenario     (which Scenic file / named scenario)
    - sample_id                   (sequential index)
    - All rover properties        (battery, orientation, motor current, etc.)
    - Terrain properties          (if sampled)
    - expected_fault              (derived oracle: NONE | BATTERY_WARN | BATTERY_STOP
                                   | TILT | MOTOR_OVERCURRENT | WATCHDOG)
    - threshold_margins           (dict of distance to each safety threshold)

Scenic docs: https://docs.scenic-lang.org
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

# ── Scenic import with helpful error ─────────────────────────────────────────
try:
    import scenic
    from scenic.core.scenarios import Scenario  # noqa: F401 (import check)
except ImportError:
    print(
        "ERROR: Scenic is not installed.\n"
        "  pip install scenic\n"
        "  https://scenic-lang.org/",
        file=sys.stderr,
    )
    sys.exit(1)

# ── Scenario registry ─────────────────────────────────────────────────────────
SCENARIO_DIR = Path(__file__).parent

#  name → {file, named_scenarios}
#  named_scenarios: list of (scenic_name, short_tag) or None for top-level
REGISTRY: dict[str, dict[str, Any]] = {
    "nominal_traverse": {
        "file": "nominal_traverse.scenic",
        "named": [("NominalTraverse", "nominal")],
    },
    "battery_low": {
        "file": "battery_low.scenic",
        "named": [
            ("BatteryWarning",  "warn"),
            ("BatterySafeStop", "stop"),
            ("BatteryMarginal", "ok"),
        ],
    },
    "tilt_risk": {
        "file": "tilt_risk.scenic",
        "named": [
            ("TiltRollEdge",   "roll"),
            ("TiltPitchEdge",  "pitch"),
            ("TiltCompound",   "compound"),
        ],
    },
    "motor_stall": {
        "file": "motor_stall.scenic",
        "named": [
            ("MotorCurrentHigh",  "high"),
            ("MotorCurrentFault", "fault"),
        ],
    },
    "comm_loss": {
        "file": "comm_loss.scenic",
        "named": [
            ("CommHealthy",    "ok"),
            ("WatchdogExpiry", "expired"),
        ],
    },
}

# ── Safety thresholds (from SF-06 / hazard log) ───────────────────────────────
THRESHOLDS = {
    "motor_current_fault_a":  10.0,   # SF-06.1: safe stop
    "battery_warn_v":         11.0,   # SF-06.2: warning
    "battery_stop_v":         10.5,   # SF-06.2: safe stop
    "tilt_deg":               35.0,   # SF-06.3: both roll and pitch
    "watchdog_sec":            1.0,   # LF-01.4: command watchdog
    "velocity_limit_ms":       0.4,   # LF-01.3: linear velocity clamp
}


# ── Fault oracle ──────────────────────────────────────────────────────────────
def derive_oracle(case: dict) -> dict:
    """
    Given sampled rover properties, compute:
      - expected_fault: which fault (if any) should trigger
      - threshold_margins: signed distance from each threshold (+ = safe)
    """
    v        = case.get("battery_voltage_v",    11.1)
    roll     = case.get("roll_deg",              0.0)
    pitch    = case.get("pitch_deg",             0.0)
    current  = case.get("motor_current_peak_a",  0.0)
    cmd_age  = case.get("cmd_vel_age_sec",        0.0)

    faults = []
    if current >= THRESHOLDS["motor_current_fault_a"]:
        faults.append("MOTOR_OVERCURRENT")
    if v <= THRESHOLDS["battery_stop_v"]:
        faults.append("BATTERY_STOP")
    elif v <= THRESHOLDS["battery_warn_v"]:
        faults.append("BATTERY_WARN")
    if abs(roll) >= THRESHOLDS["tilt_deg"] or abs(pitch) >= THRESHOLDS["tilt_deg"]:
        faults.append("TILT")
    if cmd_age >= THRESHOLDS["watchdog_sec"]:
        faults.append("WATCHDOG")

    # Compound tilt: vector magnitude (informational — not a current threshold)
    tilt_mag = math.sqrt(roll**2 + pitch**2)

    margins = {
        "motor_current_a":  round(THRESHOLDS["motor_current_fault_a"] - current, 3),
        "battery_warn_v":   round(v - THRESHOLDS["battery_warn_v"], 3),
        "battery_stop_v":   round(v - THRESHOLDS["battery_stop_v"],  3),
        "tilt_roll_deg":    round(THRESHOLDS["tilt_deg"] - abs(roll), 3),
        "tilt_pitch_deg":   round(THRESHOLDS["tilt_deg"] - abs(pitch), 3),
        "tilt_vector_deg":  round(THRESHOLDS["tilt_deg"] - tilt_mag,   3),
        "watchdog_sec":     round(THRESHOLDS["watchdog_sec"] - cmd_age, 3),
    }

    return {
        "expected_faults":  faults if faults else ["NONE"],
        "fault_count":      len(faults),
        "tilt_vector_deg":  round(tilt_mag, 2),
        "threshold_margins": margins,
    }


# ── Extract object properties from a Scenic scene ────────────────────────────
def scene_to_dict(
    scene,
    scenario_name: str,
    sub_tag: str,
    sample_id: int,
) -> dict:
    """
    Pull properties from the ego object (Rover) and optional TerrainPatch.
    Scenic stores custom properties as object attributes.
    """
    ego = scene.egoObject

    # Helper: safe attribute read with default
    def attr(obj, name: str, default=None):
        return getattr(obj, name, default)

    case: dict = {
        "scenario":      scenario_name,
        "sub_scenario":  sub_tag,
        "sample_id":     sample_id,

        # Electrical
        "battery_voltage_v":    round(attr(ego, "battery_voltage",    11.1), 3),
        "battery_soc_pct":      round(attr(ego, "battery_soc",        80.0), 1),
        "motor_current_peak_a": round(attr(ego, "motor_current_peak",  2.0), 3),

        # Kinematic
        "linear_velocity_ms":   round(attr(ego, "linear_velocity",    0.0), 3),
        "angular_velocity_rads":round(attr(ego, "angular_velocity",   0.0), 3),

        # Orientation
        "roll_deg":             round(attr(ego, "roll_deg",   0.0), 2),
        "pitch_deg":            round(attr(ego, "pitch_deg",  0.0), 2),

        # Communication
        "wifi_rssi_dbm":        round(attr(ego, "wifi_rssi_dbm",    -55.0), 1),
        "cmd_vel_age_sec":      round(attr(ego, "cmd_vel_age_sec",    0.0), 3),
    }

    # Terrain (if a TerrainPatch exists as second object)
    if len(scene.objects) > 1:
        terrain = scene.objects[0] if scene.objects[0] is not ego else scene.objects[1]
        case["terrain_slope_deg"]  = round(attr(terrain, "slope_angle",     0.0), 1)
        case["terrain_surface"]    = attr(terrain, "surface",  "flat")
        case["terrain_obstacles"]  = attr(terrain, "obstacle_count", 0)

    # Oracle
    case.update(derive_oracle(case))

    return case


# ── Core sampling function ────────────────────────────────────────────────────
def sample_scenario(
    scenario_name: str,
    named_tag: str,
    scenic_name: str | None,
    n: int,
    max_iter: int = 1000,
) -> list[dict]:
    """
    Compile and sample a single (file, named scenario) pair.
    Returns list of n concrete test case dicts.
    """
    file_path = SCENARIO_DIR / REGISTRY[scenario_name]["file"]
    if not file_path.exists():
        print(f"WARN: {file_path} not found — skipping", file=sys.stderr)
        return []

    params = {}
    if scenic_name:
        params["scenario"] = scenic_name

    try:
        compiled = scenic.scenarioFromFile(
            str(file_path),
            params=params,
            mode2D=True,   # 2D abstract mode — no 3D physics simulator
        )
    except Exception as exc:
        print(f"ERROR compiling {file_path} [{scenic_name}]: {exc}", file=sys.stderr)
        return []

    cases = []
    for i in range(n):
        try:
            scene, _ = compiled.generate(maxIterations=max_iter)
            case = scene_to_dict(scene, scenario_name, named_tag, i)
            cases.append(case)
        except Exception as exc:
            print(f"WARN: sample {i} failed ({exc}) — skipping", file=sys.stderr)

    return cases


# ── CLI ───────────────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="OSR Scenic scenario generator — outputs JSON test cases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 generate_scenarios.py --all --n 50
  python3 generate_scenarios.py --scenario tilt_risk --n 100
  python3 generate_scenarios.py --scenario battery_low --n 200 --out cases.json
  python3 generate_scenarios.py --list
        """,
    )
    p.add_argument("--scenario",  "-s",  help="Scenario name (see --list)")
    p.add_argument("--all",       action="store_true", help="Run all scenarios")
    p.add_argument("--n",         type=int, default=50, help="Samples per sub-scenario")
    p.add_argument("--out",       "-o",  help="Output JSON file (default: stdout)")
    p.add_argument("--list",      action="store_true", help="List available scenarios")
    p.add_argument("--max-iter",  type=int, default=1000,
                   help="Max Scenic rejection-sampling iterations per sample")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    if args.list:
        print("Available scenarios:\n")
        for name, info in REGISTRY.items():
            subs = ", ".join(t for _, t in info["named"])
            print(f"  {name:20s}  sub-scenarios: {subs}")
        return

    # Select which scenarios to run
    if args.all:
        targets = list(REGISTRY.keys())
    elif args.scenario:
        if args.scenario not in REGISTRY:
            print(
                f"ERROR: unknown scenario '{args.scenario}'.\n"
                f"Run with --list to see options.",
                file=sys.stderr,
            )
            sys.exit(1)
        targets = [args.scenario]
    else:
        print("Specify --scenario NAME or --all. Use --list to see options.",
              file=sys.stderr)
        sys.exit(1)

    all_cases: list[dict] = []
    for name in targets:
        info = REGISTRY[name]
        for scenic_name, tag in info["named"]:
            print(
                f"Sampling {name}/{tag} ({scenic_name}) × {args.n} ...",
                file=sys.stderr,
            )
            cases = sample_scenario(name, tag, scenic_name, args.n, args.max_iter)
            all_cases.extend(cases)
            print(f"  → {len(cases)} cases generated", file=sys.stderr)

    # Summary statistics
    fault_counts: dict[str, int] = {}
    for case in all_cases:
        for f in case.get("expected_faults", ["NONE"]):
            fault_counts[f] = fault_counts.get(f, 0) + 1

    print(f"\nTotal cases: {len(all_cases)}", file=sys.stderr)
    print("Fault distribution:", file=sys.stderr)
    for fault, count in sorted(fault_counts.items()):
        pct = 100 * count / max(1, len(all_cases))
        print(f"  {fault:25s} {count:5d}  ({pct:.1f}%)", file=sys.stderr)

    # Output
    output = json.dumps(all_cases, indent=2)
    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"\nWritten: {args.out}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
