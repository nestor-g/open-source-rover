"""
comm_loss.scenic — Communication Loss / Watchdog Scenarios
===========================================================
Tests: SF-01 (Receive and Decode Command), LF-01.4 (Watchdog Timer)
Hazard: H-04 (runaway after comm loss)
Requirements: REQ-SF-01-04, REQ-LC-01-01

The 1-second command watchdog (LF-01.4) is the primary defence against H-04.
These scenarios test both sides of the watchdog expiry boundary.

Two sub-scenarios:
  1. CommHealthy      — link active, cmd_vel recent, watchdog should NOT fire
  2. WatchdogExpiry   — cmd_vel stale (> 1 s), safe stop must trigger
"""

from osr_world import *

# ─── Healthy link ─────────────────────────────────────────────────────────────
scenario CommHealthy():
    """
    Active Wi-Fi link with recent /cmd_vel messages.
    Watchdog timer should NOT fire. Tests false-positive rejection.
    """
    setup:
        ego = new Rover at (0, 0, 0) with
            battery_voltage:    Range(11.0, 12.6),
            battery_soc:        Range(30, 100),

            motor_current_peak: Range(0.5, 5.0),
            linear_velocity:    Range(-0.4, 0.4),
            angular_velocity:   Range(-1.0, 1.0),

            roll_deg:           Normal(0, 8),
            pitch_deg:          Normal(0, 8),

            # Good Wi-Fi signal
            wifi_rssi_dbm:      Range(-65, -25),
            # cmd_vel received recently — well within 1 s window
            cmd_vel_age_sec:    Range(0.0, 0.7)

        # Must be within watchdog window
        require ego.cmd_vel_age_sec < 1.0

        # Non-faulting on all other axes
        require ego.battery_voltage > 11.0
        require ego.motor_current_peak < 8.0
        require abs(ego.roll_deg) < 28.0
        require abs(ego.pitch_deg) < 28.0


# ─── Watchdog expiry ─────────────────────────────────────────────────────────
scenario WatchdogExpiry():
    """
    /cmd_vel topic has been silent for > 1 second.
    LF-01.4 MUST emit zero-velocity Twist → motors halt.
    The rover may have been moving when the link dropped.

    Expected: all motor setpoints → 0; /diagnostics WARN WATCHDOG_EXPIRED.

    Note: RSSI is sampled broadly to capture scenarios where link is weak
    (high latency causing old cmd_vel) as well as full dropout.
    """
    setup:
        ego = new Rover at (0, 0, 0) with
            battery_voltage:    Range(11.0, 12.6),
            battery_soc:        Range(30, 100),

            # Rover may have non-zero velocity when link dropped
            motor_current_peak: Range(0.5, 5.0),
            linear_velocity:    Range(-0.4, 0.4),    # last commanded velocity
            angular_velocity:   Range(-1.0, 1.0),

            roll_deg:           Normal(0, 8),
            pitch_deg:          Normal(0, 8),

            # Weak or dropped Wi-Fi link
            wifi_rssi_dbm:      Range(-95, -65),
            # cmd_vel is stale — past the 1-second watchdog threshold
            cmd_vel_age_sec:    Range(1.0, 5.0)

        # Must be past watchdog threshold
        require ego.cmd_vel_age_sec >= 1.0

        # Other parameters: non-faulting (isolate watchdog fault)
        require ego.battery_voltage > 11.0
        require ego.motor_current_peak < 8.0
        require abs(ego.roll_deg) < 28.0
        require abs(ego.pitch_deg) < 28.0
