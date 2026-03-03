"""
battery_low.scenic — Battery Depletion Edge Cases
===================================================
Tests: SF-06.2 (Monitor Battery Voltage), LF-05.2, PF-05.2
Hazard: H-03 (battery over-discharge)
Requirements: REQ-SF-06-02, REQ-LC-05-02

Samples battery voltage near the two thresholds defined in SF-06.2:
  - WARNING threshold: 11.0 V  (operator alert)
  - SAFE STOP threshold: 10.5 V (automated halt)

Three sub-scenarios:
  1. BatteryWarning    — voltage in [11.0, 11.5 V]; warning should fire
  2. BatterySafeStop   — voltage in [10.3, 10.9 V]; safe stop must trigger
  3. BatteryMarginal   — voltage just above warning; no fault expected

The generator tags each case with expected_fault to drive test oracle logic.
"""

from osr_world import *

# ─── Warning zone: 11.0–11.5 V ───────────────────────────────────────────────
scenario BatteryWarning():
    """
    Rover is operating with battery in warning zone.
    SF-06.2 should issue a warning but NOT yet trigger safe stop.
    Expected: /diagnostics WARN; mission may continue at operator discretion.
    """
    setup:
        ego = new Rover at (0, 0, 0) with
            battery_voltage:    Range(11.0, 11.4),   # warning zone
            battery_soc:        Range(10, 25),

            motor_current_peak: Range(0.5, 5.0),
            linear_velocity:    Range(0.0, 0.3),     # slower — conserving battery
            angular_velocity:   Range(-0.5, 0.5),

            roll_deg:           Normal(0, 5),
            pitch_deg:          Normal(0, 5),

            wifi_rssi_dbm:      Range(-75, -35),
            cmd_vel_age_sec:    Range(0.0, 0.7)

        # Must be in warning zone, not yet in safe-stop zone
        require ego.battery_voltage >= 11.0
        require ego.battery_voltage < 11.5

        # Other parameters should NOT independently trigger faults
        require ego.motor_current_peak < 9.0
        require abs(ego.roll_deg) < 30.0
        require abs(ego.pitch_deg) < 30.0


# ─── Safe-stop zone: < 10.5 V ────────────────────────────────────────────────
scenario BatterySafeStop():
    """
    Rover voltage is at or below safe-stop threshold.
    SF-06.4 MUST trigger: all motor setpoints zeroed within 100 ms.
    Expected: immediate halt; /diagnostics ERROR BATTERY_LOW.
    """
    setup:
        ego = new Rover at (0, 0, 0) with
            battery_voltage:    Range(10.0, 10.5),   # safe-stop zone
            battery_soc:        Range(0, 8),

            # Rover may still be commanded to move (tests that fault overrides motion)
            motor_current_peak: Range(0.5, 4.0),
            linear_velocity:    Range(-0.2, 0.2),
            angular_velocity:   Range(-0.3, 0.3),

            roll_deg:           Normal(0, 4),
            pitch_deg:          Normal(0, 4),

            wifi_rssi_dbm:      Range(-75, -30),
            cmd_vel_age_sec:    Range(0.0, 0.5)

        # Must be at or below safe-stop threshold
        require ego.battery_voltage <= 10.5

        # Tilt and motor should be non-faulting (isolate battery fault)
        require ego.motor_current_peak < 9.0
        require abs(ego.roll_deg) < 30.0
        require abs(ego.pitch_deg) < 30.0


# ─── Marginal: just above warning ────────────────────────────────────────────
scenario BatteryMarginal():
    """
    Rover is operating just above the warning threshold.
    No fault should trigger. Tests false-positive rejection.
    Expected: /battery_state published; no fault events.
    """
    setup:
        ego = new Rover at (0, 0, 0) with
            battery_voltage:    Range(11.5, 12.6),   # comfortable range
            battery_soc:        Range(25, 100),

            motor_current_peak: Range(0.5, 5.0),
            linear_velocity:    Range(0.0, 0.4),
            angular_velocity:   Range(-1.0, 1.0),

            roll_deg:           Normal(0, 8),
            pitch_deg:          Normal(0, 8),

            wifi_rssi_dbm:      Range(-70, -30),
            cmd_vel_age_sec:    Range(0.0, 0.8)

        # Confirm no-fault zone
        require ego.battery_voltage > 11.5
        require ego.motor_current_peak < 8.0
        require abs(ego.roll_deg) < 25.0
        require abs(ego.pitch_deg) < 25.0
