# OSR Scenic Scenario Generator

[Scenic](https://scenic-lang.org/) is a probabilistic programming language for scenario
generation developed at UC Berkeley / UC Santa Cruz. We use it to generate concrete test
parameter sets that exercise the safety thresholds identified in the hazard log and FMEA.

## Setup

```bash
pip install scenic          # Scenic 3.x
```

No simulator is required — all scenarios run in **abstract mode** and produce JSON
parameter samples for use in hardware-in-the-loop tests or simulation.

## Scenario Files

| File | Tests | Linked Hazards |
|---|---|---|
| `osr_world.scenic` | Base world model — imported by all scenarios | — |
| `nominal_traverse.scenic` | Normal operation baseline | H-05 (velocity limit) |
| `battery_low.scenic` | Battery near warning/stop thresholds | H-03 (over-discharge) |
| `tilt_risk.scenic` | IMU roll/pitch near tilt threshold | H-02 (tip/rollover) |
| `motor_stall.scenic` | Motor current near overcurrent threshold | H-01 (fire) |
| `comm_loss.scenic` | Command watchdog expiry conditions | H-04 (runaway) |

## Running the Generator

```bash
cd systems_engineering/06_safety/scenarios

# Generate 50 test cases for each scenario (outputs JSON)
python3 generate_scenarios.py --all --n 50

# Single scenario
python3 generate_scenarios.py --scenario tilt_risk --n 100

# Specific scenario with custom output
python3 generate_scenarios.py --scenario motor_stall --n 200 --out motor_stall_cases.json
```

## Output Format

Each generated test case is a JSON object:

```json
{
  "scenario": "tilt_risk",
  "sample_id": 0,
  "battery_voltage_v": 11.8,
  "battery_soc_pct": 62.3,
  "roll_deg": 31.4,
  "pitch_deg": 8.7,
  "motor_current_peak_a": 3.2,
  "linear_velocity_ms": 0.18,
  "angular_velocity_rads": 0.35,
  "wifi_rssi_dbm": -58.0,
  "cmd_vel_age_sec": 0.12,
  "terrain_slope_deg": 31.4,
  "terrain_surface": "rock",
  "expected_fault": "TILT",
  "threshold_margin_deg": 3.6
}
```

## Connecting to Test Execution

The JSON output is designed to be consumed by:

1. **Manual hardware tests** — operator sets rover on a slope of the specified angle,
   charges battery to the specified level, and verifies that the safe stop triggers
   at the correct threshold.

2. **Simulation** — feed parameters into a ROS-based simulator (Gazebo, Webots) as
   initial conditions.

3. **Regression test suite** — unit tests read the JSON and verify software thresholds
   against sampled boundary conditions.

## How Scenic Works Here

Each `.scenic` file defines:
- A `Rover` object with probabilistic properties (distributions over battery level,
  orientation, motor load, etc.)
- Hard constraints (`require`) that enforce valid physical combinations
- Named scenarios (`scenario`) for modular composition

The Python generator calls `scenic.scenarioFromFile()`, samples N concrete scenes,
and serialises them to JSON with derived fields (e.g., `expected_fault`,
`threshold_margin`).

## Traceability to MBSE Model

| Scenic scenario | System Function | Logical Component | Requirement |
|---|---|---|---|
| `battery_low.scenic` | SF-06.2 | LC-05 | REQ-SF-06-02 |
| `tilt_risk.scenic` | SF-06.3 | LC-05 | REQ-SF-06-03 |
| `motor_stall.scenic` | SF-06.1 | LC-05 | REQ-SF-06-01 |
| `comm_loss.scenic` | SF-01 | LC-01, LC-02 | REQ-SF-01-04 |
| `nominal_traverse.scenic` | SF-01, SF-02 | LC-03 | REQ-SF-01-03 |
