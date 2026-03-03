"""
nominal_traverse.scenic — Baseline Traverse Scenario
======================================================
Tests: SF-01 (velocity limits), SF-02 (mobility), SF-04 (telemetry)
Hazard: H-05 (collision from excessive speed)
Requirements: REQ-SF-01-03, REQ-SF-02-01

Generates rover states representing normal, safe operation across a range of
terrain conditions. Used to verify that nominal missions stay within safe
operating envelopes and that no spurious faults are triggered.

All sampled parameters should satisfy:
  - No fault conditions triggered (motor current < 8 A, tilt < 25°, battery > 11.0 V)
  - Velocity within software limits (|v| ≤ 0.4 m/s, |ω| ≤ 1.0 rad/s)
"""

from osr_world import *

scenario NominalTraverse():
    """
    Rover traverses varied but safe terrain with a healthy battery and
    normal motor loads. No faults should trigger.
    """
    setup:
        terrain = new TerrainPatch with
            slope_angle: Range(0, 20),              # safe slope range
            surface:     Uniform("flat", "gravel", "rock"),
            obstacle_count: DiscreteRange(0, 3)

        ego = new Rover at (0, 0, 0) with
            # Battery: healthy (>50% SoC, >11.0 V)
            battery_voltage:    Range(11.0, 12.6),
            battery_soc:        Range(40, 100),

            # Motor current: normal traverse loads
            motor_current_peak: Range(0.5, 6.0),

            # Velocity: within commanded limits
            linear_velocity:    Range(-0.4, 0.4),
            angular_velocity:   Range(-1.0, 1.0),

            # Orientation: safe (well below 35° threshold)
            roll_deg:           Normal(0, 8),
            pitch_deg:          Normal(terrain.slope_angle / 2, 5),

            # Communication: healthy link
            wifi_rssi_dbm:      Range(-70, -30),
            cmd_vel_age_sec:    Range(0.0, 0.8)    # < 1 s watchdog

        # Hard constraints: this is the NOMINAL (no-fault) scenario
        require ego.motor_current_peak < 8.0       # below fault threshold
        require abs(ego.roll_deg) < 25.0           # below tilt threshold
        require abs(ego.pitch_deg) < 25.0
        require ego.battery_voltage > 11.0         # above warning threshold
        require ego.cmd_vel_age_sec < 1.0          # watchdog not expired

        # Velocity must respect software limits
        require abs(ego.linear_velocity)  <= 0.4
        require abs(ego.angular_velocity) <= 1.0
