"""
scenic_module.parameter_space
==============================
OSR OA/OE parameter space definitions.

Each OAParameter represents one physically meaningful variable in the
Operational Analysis / Operational Environment space.  Keys match the
property names used in the existing *.scenic files so that sweep-generated
scenarios and hand-written scenarios share the same vocabulary.

Structure
---------
OA_PARAMETERS  — rover state variables (controlled by the system)
OE_PARAMETERS  — environmental variables (not controlled, world state)
PARAMETER_GROUPS — logical groupings for the sweep UI and report

Links to SysML v2
-----------------
Each parameter includes a `constraint_refs` list of SysML v2 short-IDs
from systems_engineering_sysml/06_safety/constraints.sysml.  This lets
the sweep engine know which constraint to evaluate against each parameter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class OAParameter:
    """Single scalar parameter in the OA/OE space."""

    # Identity
    key:          str     # matches *.scenic property name and JSON output key
    name:         str     # human-readable label for reports and UI
    unit:         str     # e.g. "A", "V", "°", "m/s", "s"

    # Physical range — absolute min/max the variable can ever take
    phys_min:     float
    phys_max:     float

    # Nominal operating value (safe centre-point)
    nominal:      float

    # Range found in the hand-written *.scenic files (for reference/overlay)
    scenic_min:   float
    scenic_max:   float

    # Safety threshold(s) — value at which a hazard activates
    # dict: {threshold_label: value}  e.g. {"trip": 10.0} or {"warn": 11.0, "stop": 10.5}
    thresholds:   dict[str, float] = field(default_factory=dict)

    # Scenario tag(s) this parameter appears in (matches REGISTRY keys in generate_scenarios.py)
    scenarios:    tuple[str, ...] = field(default_factory=tuple)

    # SysML v2 constraint short-IDs from constraints.sysml
    constraint_refs: tuple[str, ...] = field(default_factory=tuple)

    # Hazard IDs from hazard_log.md
    hazard_refs:  tuple[str, ...] = field(default_factory=tuple)

    # If True, a value ABOVE the threshold is hazardous (motor current, tilt)
    # If False, a value BELOW the threshold is hazardous (battery voltage)
    threshold_direction: str = "above"   # "above" | "below"


# ─── OA parameters — rover state (from SF requirements) ──────────────────────

OA_PARAMETERS: dict[str, OAParameter] = {

    "motor_current_peak": OAParameter(
        key          = "motor_current_peak",
        name         = "Motor Peak Current",
        unit         = "A",
        phys_min     = 0.0,
        phys_max     = 15.0,
        nominal      = 2.0,
        scenic_min   = 10.0,
        scenic_max   = 13.0,
        thresholds   = {"trip": 10.0},
        scenarios    = ("motor_stall",),
        constraint_refs = ("H-01",),
        hazard_refs  = ("H-01",),
        threshold_direction = "above",
    ),

    "battery_voltage": OAParameter(
        key          = "battery_voltage",
        name         = "Battery Bus Voltage",
        unit         = "V",
        phys_min     = 9.0,
        phys_max     = 13.0,
        nominal      = 12.0,
        scenic_min   = 9.5,
        scenic_max   = 11.5,
        thresholds   = {"warn": 11.0, "stop": 10.5},
        scenarios    = ("battery_low",),
        constraint_refs = ("H-03", "H-03-warn"),
        hazard_refs  = ("H-03",),
        threshold_direction = "below",
    ),

    "roll_deg": OAParameter(
        key          = "roll_deg",
        name         = "Roll Angle",
        unit         = "°",
        phys_min     = -60.0,
        phys_max     = 60.0,
        nominal      = 0.0,
        scenic_min   = 20.0,
        scenic_max   = 45.0,
        thresholds   = {"trip": 35.0},
        scenarios    = ("tilt_risk",),
        constraint_refs = ("H-02",),
        hazard_refs  = ("H-02",),
        threshold_direction = "above",
    ),

    "pitch_deg": OAParameter(
        key          = "pitch_deg",
        name         = "Pitch Angle",
        unit         = "°",
        phys_min     = -60.0,
        phys_max     = 60.0,
        nominal      = 0.0,
        scenic_min   = 20.0,
        scenic_max   = 45.0,
        thresholds   = {"trip": 35.0},
        scenarios    = ("tilt_risk",),
        constraint_refs = ("H-02",),
        hazard_refs  = ("H-02",),
        threshold_direction = "above",
    ),

    "cmd_vel_age_sec": OAParameter(
        key          = "cmd_vel_age_sec",
        name         = "Command Silence Duration",
        unit         = "s",
        phys_min     = 0.0,
        phys_max     = 5.0,
        nominal      = 0.1,
        scenic_min   = 0.5,
        scenic_max   = 3.0,
        thresholds   = {"watchdog": 1.0},
        scenarios    = ("comm_loss",),
        constraint_refs = ("H-04",),
        hazard_refs  = ("H-04",),
        threshold_direction = "above",
    ),

    "linear_velocity": OAParameter(
        key          = "linear_velocity",
        name         = "Rover Linear Speed",
        unit         = "m/s",
        phys_min     = 0.0,
        phys_max     = 0.5,
        nominal      = 0.2,
        scenic_min   = 0.1,
        scenic_max   = 0.35,
        thresholds   = {"limit": 0.4},
        scenarios    = ("nominal_traverse",),
        constraint_refs = ("H-05",),
        hazard_refs  = ("H-05",),
        threshold_direction = "above",
    ),

    "angular_velocity": OAParameter(
        key          = "angular_velocity",
        name         = "Rover Angular Speed",
        unit         = "rad/s",
        phys_min     = -1.5,
        phys_max     = 1.5,
        nominal      = 0.0,
        scenic_min   = -0.8,
        scenic_max   = 0.8,
        thresholds   = {"limit": 1.0},
        scenarios    = ("nominal_traverse",),
        constraint_refs = ("H-05",),
        hazard_refs  = ("H-05",),
        threshold_direction = "above",
    ),

    "battery_soc": OAParameter(
        key          = "battery_soc",
        name         = "Battery State of Charge",
        unit         = "%",
        phys_min     = 0.0,
        phys_max     = 100.0,
        nominal      = 80.0,
        scenic_min   = 10.0,
        scenic_max   = 100.0,
        thresholds   = {"low": 15.0},
        scenarios    = ("battery_low", "nominal_traverse"),
        constraint_refs = ("H-03",),
        hazard_refs  = ("H-03",),
        threshold_direction = "below",
    ),

    "wifi_rssi_dbm": OAParameter(
        key          = "wifi_rssi_dbm",
        name         = "Wi-Fi Signal Strength",
        unit         = "dBm",
        phys_min     = -95.0,
        phys_max     = -20.0,
        nominal      = -55.0,
        scenic_min   = -85.0,
        scenic_max   = -30.0,
        thresholds   = {"dropout": -85.0},
        scenarios    = ("comm_loss",),
        constraint_refs = ("H-04",),
        hazard_refs  = ("H-04",),
        threshold_direction = "below",
    ),
}


# ─── OE parameters — operational environment ─────────────────────────────────

OE_PARAMETERS: dict[str, OAParameter] = {

    "terrain_slope_deg": OAParameter(
        key          = "terrain_slope_deg",
        name         = "Terrain Slope",
        unit         = "°",
        phys_min     = 0.0,
        phys_max     = 45.0,
        nominal      = 5.0,
        scenic_min   = 0.0,
        scenic_max   = 25.0,
        thresholds   = {"max_traversable": 30.0},
        scenarios    = ("tilt_risk", "motor_stall", "nominal_traverse"),
        constraint_refs = ("H-02", "H-01"),
        hazard_refs  = ("H-02", "H-09"),
        threshold_direction = "above",
    ),

    "terrain_obstacles": OAParameter(
        key          = "terrain_obstacles",
        name         = "Obstacle Count",
        unit         = "count",
        phys_min     = 0.0,
        phys_max     = 10.0,
        nominal      = 0.0,
        scenic_min   = 0.0,
        scenic_max   = 5.0,
        thresholds   = {"high_density": 5.0},
        scenarios    = ("nominal_traverse", "motor_stall"),
        constraint_refs = ("H-01", "H-05"),
        hazard_refs  = ("H-01", "H-05"),
        threshold_direction = "above",
    ),

    "ambient_temp_c": OAParameter(
        key          = "ambient_temp_c",
        name         = "Ambient Temperature",
        unit         = "°C",
        phys_min     = -10.0,
        phys_max     = 50.0,
        nominal      = 20.0,
        scenic_min   = 5.0,
        scenic_max   = 40.0,
        thresholds   = {"battery_cold": 5.0, "battery_hot": 40.0},
        scenarios    = ("battery_low",),
        constraint_refs = ("H-03", "H-10"),
        hazard_refs  = ("H-03", "H-10"),
        threshold_direction = "above",
    ),

    "mission_duration_min": OAParameter(
        key          = "mission_duration_min",
        name         = "Mission Duration",
        unit         = "min",
        phys_min     = 0.0,
        phys_max     = 120.0,
        nominal      = 20.0,
        scenic_min   = 5.0,
        scenic_max   = 60.0,
        thresholds   = {"max_rated": 45.0},
        scenarios    = ("battery_low", "nominal_traverse"),
        constraint_refs = ("H-03",),
        hazard_refs  = ("H-03",),
        threshold_direction = "above",
    ),
}

# Combined space — used by sweep engine
ALL_PARAMETERS: dict[str, OAParameter] = {**OA_PARAMETERS, **OE_PARAMETERS}


# ─── Logical parameter groups for UI and report ───────────────────────────────

PARAMETER_GROUPS = {
    "motor_safety": {
        "label":  "Motor Safety",
        "hazard": "H-01",
        "keys":   ["motor_current_peak", "terrain_slope_deg", "terrain_obstacles"],
    },
    "tilt_safety": {
        "label":  "Tilt / Rollover",
        "hazard": "H-02",
        "keys":   ["roll_deg", "pitch_deg", "terrain_slope_deg"],
    },
    "battery_safety": {
        "label":  "Battery Health",
        "hazard": "H-03",
        "keys":   ["battery_voltage", "battery_soc", "mission_duration_min", "ambient_temp_c"],
    },
    "comm_safety": {
        "label":  "Communication Safety",
        "hazard": "H-04",
        "keys":   ["cmd_vel_age_sec", "wifi_rssi_dbm", "linear_velocity"],
    },
    "motion_safety": {
        "label":  "Motion Envelope",
        "hazard": "H-05",
        "keys":   ["linear_velocity", "angular_velocity", "terrain_obstacles"],
    },
}


def get_parameters_for_hazard(hazard_id: str) -> list[OAParameter]:
    """Return all parameters that contribute to a given hazard."""
    return [p for p in ALL_PARAMETERS.values() if hazard_id in p.hazard_refs]


def get_parameters_for_scenario(scenario_tag: str) -> list[OAParameter]:
    """Return all parameters that appear in a given scenario file."""
    return [p for p in ALL_PARAMETERS.values() if scenario_tag in p.scenarios]
