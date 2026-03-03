"""
osr_world.scenic — OSR Base World Model
========================================
Defines the OSR Rover and Terrain object classes for use in all OSR scenarios.
Imported by other scenario files via:  from osr_world import *

Scenic 3.x, abstract mode (no simulator).

Property ranges are derived from OSR hardware specs and hazard log thresholds:
  - Battery: 10.5 V (safe-stop) to 12.6 V (fully charged)
  - Motor current: 0 to 15 A per channel (RoboClaw rated max)
  - Tilt threshold: 35° (SF-06.3)
  - Velocity limits: ±0.4 m/s linear, ±1.0 rad/s angular (SF-01 clamping)
  - Watchdog: 1.0 s (LF-01.4)
"""

# ── Rover object ─────────────────────────────────────────────────────────────

class Rover(Object):
    """
    Abstract representation of the OSR rover for scenario parameter sampling.
    Dimensions match the physical build; electrical/kinematic properties are
    the primary variables of interest for safety testing.
    """

    # Physical dimensions (m)
    width:  0.46
    length: 0.64
    height: 0.30

    # ── Electrical ───────────────────────────────────────────────────────────
    # 3S LiPo: 10.5 V (empty) to 12.6 V (full)
    battery_voltage:    11.1   # V nominal
    battery_soc:        80.0   # % state-of-charge

    # Per-channel motor current (peak across all 6 motors)
    motor_current_peak: 2.0    # A  (nominal ~1–3 A, stall ~10 A)

    # ── Kinematics ───────────────────────────────────────────────────────────
    linear_velocity:    0.0    # m/s   (limit: ±0.4)
    angular_velocity:   0.0    # rad/s (limit: ±1.0)

    # ── Orientation (terrain-induced) ────────────────────────────────────────
    roll_deg:           0.0    # deg  (safe: |roll|  < 35°)
    pitch_deg:          0.0    # deg  (safe: |pitch| < 35°)

    # ── Communication ────────────────────────────────────────────────────────
    wifi_rssi_dbm:    -55.0    # dBm  (usable: > -80 dBm)
    cmd_vel_age_sec:    0.0    # s since last /cmd_vel  (watchdog: 1.0 s)


# ── Terrain patch ─────────────────────────────────────────────────────────────

class TerrainPatch(Object):
    """
    Terrain feature the rover is traversing.
    Slope angle determines induced roll/pitch on the rover.
    """

    # Physical extent
    width:  4.0    # m
    length: 4.0    # m

    # Terrain properties
    slope_angle:    0.0       # deg (0 = flat, 35 = tilt threshold)
    surface:        "flat"    # flat | gravel | rock | sand
    obstacle_count: 0         # number of discrete obstacles on patch
