"""
tilt_risk.scenic — IMU Tilt Near-Threshold Scenarios
=====================================================
Tests: SF-06.3 (Detect Tip Risk), LF-05.3, PF-05.3
Hazard: H-02 (tip / rollover)
Requirements: REQ-SF-06-03, REQ-LC-05-03

Samples roll and pitch angles near the 35° safe-stop threshold defined in SF-06.3.
Three sub-scenarios cover roll-dominant, pitch-dominant, and compound tilt cases.

Threshold: |roll| > 35° OR |pitch| > 35° → immediate safe stop (SF-06.4).
"""

from osr_world import *

# ─── Roll-dominant tilt ───────────────────────────────────────────────────────
scenario TiltRollEdge():
    """
    Rover on a side slope. Roll angle is the primary risk axis.
    Tests that SF-06.3 triggers on roll > 35° independent of pitch.
    """
    setup:
        terrain = new TerrainPatch with
            slope_angle:  Range(28, 42),          # straddles the 35° threshold
            surface:      Uniform("gravel", "rock"),
            obstacle_count: DiscreteRange(0, 2)

        ego = new Rover at (0, 0, 0) with
            battery_voltage:    Range(11.0, 12.6),
            battery_soc:        Range(30, 100),

            motor_current_peak: Range(0.5, 5.0),
            linear_velocity:    Range(-0.1, 0.3),  # slow on steep terrain
            angular_velocity:   Range(-0.3, 0.3),

            # Roll is induced by side slope; pitch is near-zero (traversing contour)
            roll_deg:           Normal(terrain.slope_angle, 3),
            pitch_deg:          Normal(0, 4),

            wifi_rssi_dbm:      Range(-75, -30),
            cmd_vel_age_sec:    Range(0.0, 0.6)

        # Sample terrain slopes near the 35° boundary (20° margin either side)
        require terrain.slope_angle > 25.0

        # Other faults isolated (battery and motor are healthy)
        require ego.battery_voltage > 11.0
        require ego.motor_current_peak < 8.0


# ─── Pitch-dominant tilt ─────────────────────────────────────────────────────
scenario TiltPitchEdge():
    """
    Rover climbing or descending a steep slope. Pitch is the primary risk axis.
    Tests that SF-06.3 triggers on pitch > 35° independent of roll.
    """
    setup:
        terrain = new TerrainPatch with
            slope_angle:  Range(25, 45),
            surface:      Uniform("flat", "gravel", "rock"),
            obstacle_count: 0

        ego = new Rover at (0, 0, 0) with
            battery_voltage:    Range(11.0, 12.6),
            battery_soc:        Range(30, 100),

            motor_current_peak: Range(1.0, 7.0),   # higher on incline
            linear_velocity:    Range(0.0, 0.25),   # climbing

            # Pitch induced by slope; roll near-zero (going straight up/down)
            roll_deg:           Normal(0, 3),
            pitch_deg:          Normal(terrain.slope_angle, 3),

            angular_velocity:   Range(-0.2, 0.2),

            wifi_rssi_dbm:      Range(-75, -30),
            cmd_vel_age_sec:    Range(0.0, 0.6)

        require terrain.slope_angle > 22.0
        require ego.battery_voltage > 11.0
        require ego.motor_current_peak < 9.5


# ─── Compound tilt ───────────────────────────────────────────────────────────
scenario TiltCompound():
    """
    Rover on a combined slope (both roll and pitch non-zero).
    The combined tilt vector may exceed 35° even when neither axis alone does.
    Tests the most dangerous terrain geometry.

    Note: SF-06.3 as currently specified checks each axis independently.
    This scenario reveals a gap: combined tilt of (25°, 25°) has vector
    magnitude ~35° but neither axis triggers the threshold alone.
    """
    setup:
        ego = new Rover at (0, 0, 0) with
            battery_voltage:    Range(11.0, 12.6),
            battery_soc:        Range(30, 100),

            motor_current_peak: Range(1.0, 6.0),
            linear_velocity:    Range(-0.2, 0.2),
            angular_velocity:   Range(-0.3, 0.3),

            # Both axes tilted simultaneously
            roll_deg:           Range(15, 35),
            pitch_deg:          Range(15, 35),

            wifi_rssi_dbm:      Range(-75, -30),
            cmd_vel_age_sec:    Range(0.0, 0.7)

        # Compound tilt: vector magnitude = sqrt(roll² + pitch²)
        # Require at least one axis > 20° to be interesting
        require abs(ego.roll_deg) > 18.0
        require abs(ego.pitch_deg) > 18.0

        require ego.battery_voltage > 11.0
        require ego.motor_current_peak < 8.0
