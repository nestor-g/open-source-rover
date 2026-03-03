"""
motor_stall.scenic — Motor Overcurrent / Stall Scenarios
==========================================================
Tests: SF-06.1 (Monitor Motor Currents), LF-05.1, PF-05.1
Hazard: H-01 (motor fire / overcurrent)
Requirements: REQ-SF-06-01, REQ-LC-05-01

Samples motor peak current near the 10 A safe-stop threshold defined in SF-06.1.
The Pololu 37D 12V 19:1 gearmotors have a stall current of ~10 A;
sustained operation above this risks motor damage and potential fire.

Two sub-scenarios: approaching threshold and exceeding threshold.
"""

from osr_world import *

# ─── Approaching threshold ────────────────────────────────────────────────────
scenario MotorCurrentHigh():
    """
    Motor current elevated but below safe-stop threshold.
    SF-06.1 should NOT yet trigger. Tests false-positive rejection.
    Expected: /motor_currents published; no fault.
    """
    setup:
        terrain = new TerrainPatch with
            slope_angle:  Range(10, 25),       # moderate incline causes higher load
            surface:      Uniform("gravel", "rock"),
            obstacle_count: DiscreteRange(0, 2)

        ego = new Rover at (0, 0, 0) with
            battery_voltage:    Range(11.0, 12.6),
            battery_soc:        Range(30, 100),

            # High but sub-threshold motor current (7–9.9 A)
            motor_current_peak: Range(7.0, 9.9),

            linear_velocity:    Range(0.0, 0.3),   # pushing hard on incline
            angular_velocity:   Range(-0.3, 0.3),

            roll_deg:           Normal(0, 5),
            pitch_deg:          Normal(terrain.slope_angle / 2, 4),

            wifi_rssi_dbm:      Range(-75, -30),
            cmd_vel_age_sec:    Range(0.0, 0.7)

        # Current high but below fault threshold
        require ego.motor_current_peak >= 7.0
        require ego.motor_current_peak < 10.0

        # Tilt and battery: non-faulting (isolate motor fault)
        require ego.battery_voltage > 11.0
        require abs(ego.roll_deg) < 30.0
        require abs(ego.pitch_deg) < 30.0


# ─── Exceeding threshold (fault expected) ────────────────────────────────────
scenario MotorCurrentFault():
    """
    Motor current exceeds 10 A safe-stop threshold.
    SF-06.1 MUST trigger SF-06.4 within 100 ms.
    Expected: all motor setpoints zeroed; /diagnostics ERROR MOTOR_OVERCURRENT.

    Physically: wheel jammed against obstacle, or rover commanded into immovable object.
    """
    setup:
        terrain = new TerrainPatch with
            slope_angle:  Range(0, 15),        # stall usually from jam, not slope
            surface:      Uniform("flat", "gravel", "rock"),
            obstacle_count: DiscreteRange(1, 5)

        ego = new Rover at (0, 0, 0) with
            battery_voltage:    Range(11.0, 12.6),
            battery_soc:        Range(30, 100),

            # Stall current range: 10–13 A (above threshold)
            motor_current_peak: Range(10.0, 13.0),

            # Rover trying to push through obstacle at low speed
            linear_velocity:    Range(0.0, 0.15),
            angular_velocity:   Range(-0.2, 0.2),

            roll_deg:           Normal(0, 4),
            pitch_deg:          Normal(0, 4),

            wifi_rssi_dbm:      Range(-75, -30),
            cmd_vel_age_sec:    Range(0.0, 0.5)

        # Must be in fault zone
        require ego.motor_current_peak >= 10.0

        # Isolate motor fault — tilt and battery OK
        require ego.battery_voltage > 11.0
        require abs(ego.roll_deg) < 30.0
        require abs(ego.pitch_deg) < 30.0
