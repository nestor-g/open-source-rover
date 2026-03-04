"""
scenic_module.constraint_oracle
================================
Python-evaluable implementations of each H-xx safety constraint, mirroring
the formal ``constraint def`` blocks in::

    systems_engineering_sysml/06_safety/constraints.sysml

Each constraint function takes only the parameters that appear in the
corresponding SysML v2 ``in`` ports and returns a ``ConstraintResult``
with:

* ``is_safe``  — True if the constraint expression evaluates to True
* ``margin``   — signed distance to the safety boundary (positive = safe,
                 negative = violated); units match the primary input parameter
* ``constraint_id``   — SysML v2 short-ID (e.g. "H-01")
* ``constraint_name`` — human-readable name

Usage::

    from scenic_module.constraint_oracle import evaluate_all, CONSTRAINT_MAP

    params = {
        "motor_current_peak": 11.5,
        "cmd_vel_age_sec": 0.3,
        "roll_deg": 20.0,
        # ... etc.
    }
    results = evaluate_all(params)
    for r in results:
        status = "SAFE" if r.is_safe else "VIOLATED"
        print(f"{r.constraint_id}: {status}  margin={r.margin:+.3f}")
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Optional


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConstraintResult:
    """Outcome of evaluating one safety constraint at a single parameter point."""

    constraint_id:   str    # SysML v2 short-ID, e.g. "H-01"
    constraint_name: str    # human-readable name from constraints.sysml
    is_safe:         bool   # True ↔ constraint expression is satisfied
    margin:          float  # signed distance to safety boundary
    # margin > 0 → safe headroom; margin < 0 → depth of violation
    # units are the same as the primary parameter (A, V, °, s, m/s …)
    primary_value:   float  # value of the key parameter that was evaluated
    threshold:       float  # the limiting threshold value
    note:            str = ""  # optional human-readable annotation


# ---------------------------------------------------------------------------
# Individual constraint evaluators
# Each function follows the signature:
#   def evaluate_H_xx(params: dict[str, float]) -> ConstraintResult
#
# ``params`` is the full scenario parameter dict; functions extract the
# subset they need.  Missing keys are treated as the nominal safe value so
# that partial sweeps still work.
# ---------------------------------------------------------------------------

# H-01 — Motor Overcurrent / Fire
# constraint: (motorCurrentA < 10.0) || (durationMs < 100.0)
# For sweep purposes we treat the peak current as the primary variable and
# assume worst-case continuous duration (≥ 100 ms) unless duration is given.
def _h01(params: dict) -> ConstraintResult:
    current   = float(params.get("motor_current_peak", 0.0))
    duration  = float(params.get("motor_stall_duration_ms", 100.0))  # worst-case default
    threshold = 10.0
    # Safe if current below trip OR duration too short to matter
    is_safe   = (current < threshold) or (duration < 100.0)
    # Margin in amps (positive = headroom below trip)
    margin    = threshold - current
    return ConstraintResult(
        constraint_id   = "H-01",
        constraint_name = "MotorCurrentSafe",
        is_safe         = is_safe,
        margin          = margin,
        primary_value   = current,
        threshold       = threshold,
        note            = f"current={current:.2f} A, duration={duration:.0f} ms",
    )


# H-02 — Tip / Rollover
# constraint: (rollDeg.abs < 35.0) && (pitchDeg.abs < 35.0)
def _h02(params: dict) -> ConstraintResult:
    roll      = float(params.get("roll_deg",  0.0))
    pitch     = float(params.get("pitch_deg", 0.0))
    threshold = 35.0
    roll_safe  = abs(roll)  < threshold
    pitch_safe = abs(pitch) < threshold
    is_safe    = roll_safe and pitch_safe
    # Margin = how far the worst axis is from the threshold
    worst  = max(abs(roll), abs(pitch))
    margin = threshold - worst
    return ConstraintResult(
        constraint_id   = "H-02",
        constraint_name = "TiltSafe",
        is_safe         = is_safe,
        margin          = margin,
        primary_value   = worst,
        threshold       = threshold,
        note            = f"roll={roll:.1f}°, pitch={pitch:.1f}°",
    )


# H-03 — Battery Over-Discharge (stop threshold)
# constraint: busVoltageV >= 10.5
def _h03(params: dict) -> ConstraintResult:
    voltage   = float(params.get("battery_voltage", 12.0))
    threshold = 10.5
    is_safe   = voltage >= threshold
    margin    = voltage - threshold        # positive → safe headroom
    return ConstraintResult(
        constraint_id   = "H-03",
        constraint_name = "BatteryVoltageSafe",
        is_safe         = is_safe,
        margin          = margin,
        primary_value   = voltage,
        threshold       = threshold,
        note            = f"bus voltage={voltage:.2f} V",
    )


# H-03-warn — Battery Low Warning
# constraint: busVoltageV >= 11.0
def _h03_warn(params: dict) -> ConstraintResult:
    voltage   = float(params.get("battery_voltage", 12.0))
    threshold = 11.0
    is_safe   = voltage >= threshold
    margin    = voltage - threshold
    return ConstraintResult(
        constraint_id   = "H-03-warn",
        constraint_name = "BatteryVoltageWarn",
        is_safe         = is_safe,
        margin          = margin,
        primary_value   = voltage,
        threshold       = threshold,
        note            = f"bus voltage={voltage:.2f} V (warn threshold)",
    )


# H-04 — Runaway After Comm Loss
# constraint: (silenceDurationS < 1.0) || (roverSpeedMs == 0.0)
def _h04(params: dict) -> ConstraintResult:
    silence   = float(params.get("cmd_vel_age_sec",  0.0))
    speed     = float(params.get("linear_velocity",  0.0))
    threshold = 1.0   # watchdog timeout in seconds
    is_safe   = (silence < threshold) or (math.isclose(speed, 0.0, abs_tol=0.001))
    margin    = threshold - silence   # positive → still within watchdog window
    return ConstraintResult(
        constraint_id   = "H-04",
        constraint_name = "CommWatchdogSafe",
        is_safe         = is_safe,
        margin          = margin,
        primary_value   = silence,
        threshold       = threshold,
        note            = f"silence={silence:.2f} s, speed={speed:.3f} m/s",
    )


# H-05 — Collision / Unintended Motion
# constraint: linearSpeedMs.abs <= 0.4
def _h05(params: dict) -> ConstraintResult:
    speed     = float(params.get("linear_velocity", 0.0))
    threshold = 0.4   # m/s
    is_safe   = abs(speed) <= threshold
    margin    = threshold - abs(speed)   # positive → headroom below limit
    return ConstraintResult(
        constraint_id   = "H-05",
        constraint_name = "VelocitySafe",
        is_safe         = is_safe,
        margin          = margin,
        primary_value   = abs(speed),
        threshold       = threshold,
        note            = f"|speed|={abs(speed):.3f} m/s",
    )


# H-06 — Electrical Short Circuit
# constraint: fuseRatingA <= 30.0
# (fuse rating is a design-time constant; returns a pass for normal sweeps)
def _h06(params: dict) -> ConstraintResult:
    fuse      = float(params.get("fuse_rating_a", 20.0))   # default OSR fuse = 20 A
    threshold = 30.0
    is_safe   = fuse <= threshold
    margin    = threshold - fuse
    return ConstraintResult(
        constraint_id   = "H-06",
        constraint_name = "FuseSafe",
        is_safe         = is_safe,
        margin          = margin,
        primary_value   = fuse,
        threshold       = threshold,
        note            = f"fuse={fuse:.0f} A",
    )


# H-07 — Payload Overcurrent
# constraint: payloadCurrentA <= limitA
def _h07(params: dict) -> ConstraintResult:
    current   = float(params.get("payload_current_a", 0.0))
    limit     = float(params.get("payload_limit_a",   2.0))   # default 2 A
    is_safe   = current <= limit
    margin    = limit - current
    return ConstraintResult(
        constraint_id   = "H-07",
        constraint_name = "PayloadCurrentSafe",
        is_safe         = is_safe,
        margin          = margin,
        primary_value   = current,
        threshold       = limit,
        note            = f"payload current={current:.2f} A, limit={limit:.1f} A",
    )


# H-08 — Software Crash / Node Failure
# constraint: faultNodeAlive || hardwareTimeoutActive
# (boolean; sweep maps to 0/1 for fault-node-alive probability)
def _h08(params: dict) -> ConstraintResult:
    node_alive  = bool(params.get("fault_node_alive", True))
    hw_timeout  = bool(params.get("hw_timeout_active", True))
    is_safe     = node_alive or hw_timeout
    # Margin: 1 if both alive, 0 if only one alive, -1 if neither
    margin = (1.0 if node_alive else 0.0) + (1.0 if hw_timeout else 0.0) - 1.0
    return ConstraintResult(
        constraint_id   = "H-08",
        constraint_name = "NodeHealthSafe",
        is_safe         = is_safe,
        margin          = margin,
        primary_value   = 1.0 if node_alive else 0.0,
        threshold       = 1.0,
        note            = f"fault_node_alive={node_alive}, hw_timeout={hw_timeout}",
    )


# H-09 — Structural Failure
# constraint: totalMassKg <= 10.0
def _h09(params: dict) -> ConstraintResult:
    mass      = float(params.get("total_mass_kg", 7.5))   # nominal OSR mass
    threshold = 10.0
    is_safe   = mass <= threshold
    margin    = threshold - mass
    return ConstraintResult(
        constraint_id   = "H-09",
        constraint_name = "StructuralSafe",
        is_safe         = is_safe,
        margin          = margin,
        primary_value   = mass,
        threshold       = threshold,
        note            = f"mass={mass:.1f} kg",
    )


# H-10 — LiPo Thermal Runaway
# constraint: (chargeCurrentA <= chargeCapacityAh) && (!chargedInRover || thermalMonPresent)
def _h10(params: dict) -> ConstraintResult:
    charge_a       = float(params.get("charge_current_a",    0.0))
    capacity_ah    = float(params.get("charge_capacity_ah",  3.0))   # 3 Ah pack
    in_rover       = bool(params.get("charged_in_rover",     False))
    thermal_mon    = bool(params.get("thermal_mon_present",  False))
    current_ok     = charge_a <= capacity_ah                    # ≤ 1C
    location_ok    = (not in_rover) or thermal_mon
    is_safe        = current_ok and location_ok
    margin         = capacity_ah - charge_a   # positive = below 1C
    return ConstraintResult(
        constraint_id   = "H-10",
        constraint_name = "LiPoChargeSafe",
        is_safe         = is_safe,
        margin          = margin,
        primary_value   = charge_a,
        threshold       = capacity_ah,
        note            = f"charge={charge_a:.1f} A, 1C={capacity_ah:.1f} A, in_rover={in_rover}",
    )


# ---------------------------------------------------------------------------
# Public constraint map — H-xx short-ID → evaluator function
# ---------------------------------------------------------------------------

CONSTRAINT_MAP: dict[str, Callable[[dict], ConstraintResult]] = {
    "H-01":      _h01,
    "H-02":      _h02,
    "H-03":      _h03,
    "H-03-warn": _h03_warn,
    "H-04":      _h04,
    "H-05":      _h05,
    "H-06":      _h06,
    "H-07":      _h07,
    "H-08":      _h08,
    "H-09":      _h09,
    "H-10":      _h10,
}

# Subset used by the parametric sweep (OA/OE parameters drive these)
SWEEP_CONSTRAINTS: tuple[str, ...] = (
    "H-01", "H-02", "H-03", "H-03-warn", "H-04", "H-05",
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def evaluate_constraint(
    constraint_id: str,
    params: dict,
) -> ConstraintResult:
    """Evaluate one constraint by its SysML v2 short-ID.

    Parameters
    ----------
    constraint_id:
        One of the keys in :data:`CONSTRAINT_MAP` (e.g. ``"H-01"``).
    params:
        Dict mapping OA/OE parameter keys to float values.
        Only the keys needed by the constraint are read; extras are ignored.

    Raises
    ------
    KeyError
        If *constraint_id* is not in :data:`CONSTRAINT_MAP`.
    """
    fn = CONSTRAINT_MAP[constraint_id]
    return fn(params)


def evaluate_all(
    params: dict,
    constraint_ids: Optional[tuple[str, ...]] = None,
) -> list[ConstraintResult]:
    """Evaluate a set of constraints against one parameter point.

    Parameters
    ----------
    params:
        Dict of OA/OE parameter values.
    constraint_ids:
        IDs to evaluate; defaults to :data:`SWEEP_CONSTRAINTS`.

    Returns
    -------
    list of :class:`ConstraintResult`, one per constraint evaluated.
    """
    ids = constraint_ids if constraint_ids is not None else SWEEP_CONSTRAINTS
    return [CONSTRAINT_MAP[cid](params) for cid in ids]


def any_violated(results: list[ConstraintResult]) -> bool:
    """Return True if any constraint in *results* is violated."""
    return any(not r.is_safe for r in results)


def hazard_level(results: list[ConstraintResult]) -> float:
    """Normalised hazard score in [0, 1].

    0.0 = all constraints comfortably safe
    1.0 = multiple constraints severely violated

    Computed as the fraction of :data:`SWEEP_CONSTRAINTS` that are
    violated, weighted by violation depth normalised to the threshold.
    """
    if not results:
        return 0.0
    total = 0.0
    for r in results:
        if not r.is_safe and r.threshold != 0.0:
            depth = abs(r.margin) / abs(r.threshold)
            total += min(depth, 1.0)   # cap each contribution at 1
    return min(total / len(results), 1.0)
