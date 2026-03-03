# System-Level FMEA

**Document:** OSR-SAF-FMEA-001
**Status:** DRAFT

This FMEA covers failure modes at the System Function (SF) level.
Each entry traces to a hazard (H-xx) and a safety requirement (REQ-SAF-xxx).

Risk Priority Number (RPN) = Severity (S) × Occurrence (O) × Detectability (D)
Scale 1–5 each; lower RPN is better.

---

## SF-01 — Receive and Decode Command

| ID | Failure Mode | Effect | Cause | S | O | D | RPN | Hazard | Mitigation |
|---|---|---|---|---|---|---|---|---|---|
| FM-01-01 | No /cmd_vel received | Rover continues last velocity command | Wi-Fi dropout, ground station crash | 4 | 3 | 2 | 24 | H-04 | 1-second watchdog (LF-01.4) zeroes velocity |
| FM-01-02 | Malformed Twist message | Incorrect motion command executed | Corrupted packet, ROS serialisation bug | 3 | 2 | 2 | 12 | H-05 | NaN/Inf check (LF-01.2) discards bad packets |
| FM-01-03 | Velocity limit bypass | Rover moves faster than safe speed | Software bug in clamping logic | 3 | 1 | 3 | 9 | H-05 | Unit test for LF-01.3 clamp at all boundary values |
| FM-01-04 | Watchdog timer fails to fire | No auto-halt on comm loss | Software bug, rospy.Timer crash | 4 | 2 | 2 | 16 | H-04, H-08 | Node supervisor restarts; hardware RoboClaw timeout |

---

## SF-02 — Execute Mobility

| ID | Failure Mode | Effect | Cause | S | O | D | RPN | Hazard | Mitigation |
|---|---|---|---|---|---|---|---|---|---|
| FM-02-01 | Kinematic model error | Wrong wheel speed ratio — drift or spin | Geometry parameter mismatch | 2 | 2 | 3 | 12 | H-05 | Calibration test during build (OAct-03.4) |
| FM-02-02 | RoboClaw USB serial loss | Motors stop abruptly | Cable fault, USB enumeration failure | 3 | 2 | 1 | 6 | H-09 | RoboClaw has built-in serial timeout; logs error |
| FM-02-03 | PCA9685 I²C lockup | Steering servos freeze at last angle | I²C bus contention, power glitch | 2 | 2 | 2 | 8 | — | I²C bus reset; servo mechanically safe at any fixed angle |
| FM-02-04 | Single wheel encoder failure | Odometry drift | Encoder damaged; cable break | 2 | 2 | 3 | 12 | — | /diagnostics flags abnormal encoder delta; operator notified |

---

## SF-03 — Manage Power

| ID | Failure Mode | Effect | Cause | S | O | D | RPN | Hazard | Mitigation |
|---|---|---|---|---|---|---|---|---|---|
| FM-03-01 | INA219 I²C failure | No battery monitoring | Hardware fault, I²C address conflict | 4 | 2 | 1 | 8 | H-03 | /diagnostics reports sensor loss; operator should halt mission |
| FM-03-02 | Buck converter failure | Loss of 5V logic rail | Component failure, overcurrent | 4 | 1 | 1 | 4 | H-08 | PCB fuse; RPi and RoboClaws lose power simultaneously (safe) |
| FM-03-03 | Fuse blow (expected) | Circuit protected, motor stops | Overcurrent event | 2 | 2 | 1 | 4 | H-01 | Replace fuse; inspect wiring before resuming |
| FM-03-04 | Voltage reading drift | Wrong SoC estimate | INA219 calibration error | 3 | 2 | 3 | 18 | H-03 | Factory calibration; compare against multimeter at setup |

---

## SF-04 — Process and Publish Telemetry

| ID | Failure Mode | Effect | Cause | S | O | D | RPN | Hazard | Mitigation |
|---|---|---|---|---|---|---|---|---|---|
| FM-04-01 | BNO055 IMU data freeze | Stale orientation data; tilt detection fails | I²C lockup, sensor reset | 4 | 2 | 2 | 16 | H-02 | Timestamp staleness check in LC-05; alert on /diagnostics |
| FM-04-02 | Odometry divergence | Position estimate unusable | Wheel slip on loose surface | 2 | 3 | 3 | 18 | — | Expected on loose terrain; operator uses visual navigation |
| FM-04-03 | Telemetry topic drops | Operator loses state visibility | Wi-Fi bandwidth saturation | 3 | 3 | 2 | 18 | H-04 | Reduce camera resolution; prioritise /battery_state and /diagnostics |
| FM-04-04 | IMU attitude filter divergence | Roll/pitch estimate wrong | Gyro bias at startup | 3 | 2 | 3 | 18 | H-02 | Allow 5-second warm-up on level surface before traverse |

---

## SF-05 — Capture and Stream Video

| ID | Failure Mode | Effect | Cause | S | O | D | RPN | Hazard | Mitigation |
|---|---|---|---|---|---|---|---|---|---|
| FM-05-01 | Camera node crash | No video feed | USB disconnect, raspicam error | 2 | 3 | 1 | 6 | H-05 | Optional component; mission continues without video |
| FM-05-02 | Video latency > 1 s | Operator makes control decisions on stale image | Network congestion | 3 | 3 | 3 | 27 | H-05 | Reduce resolution/framerate; operator uses safety observer for proximity |

---

## SF-06 — Detect and Handle Faults

| ID | Failure Mode | Effect | Cause | S | O | D | RPN | Hazard | Mitigation |
|---|---|---|---|---|---|---|---|---|---|
| FM-06-01 | Fault monitor node crash | No automated safe stop | Python exception, OOM | 5 | 2 | 1 | 10 | H-01, H-02, H-04 | respawn=true in ROS launch; hardware RoboClaw timeout as backup |
| FM-06-02 | Current threshold too high | Motor damage before shutdown | Threshold misconfigured | 4 | 1 | 2 | 8 | H-01 | Threshold validated against motor stall current spec (≤10 A) |
| FM-06-03 | Tilt threshold wrong axis | Tip not detected | IMU mounted with wrong orientation | 4 | 2 | 2 | 16 | H-02 | Tilt calibration test during setup; verify correct roll/pitch mapping |
| FM-06-04 | Safe stop doesn't zero all motors | Residual motion after fault | Bug in SF-06.4 implementation | 4 | 1 | 2 | 8 | H-01, H-02 | Integration test: verify all 3 RoboClaws receive 0 setpoint |
| FM-06-05 | Latched halt not clearable | Rover stuck after false positive | Software bug in latch logic | 2 | 2 | 2 | 8 | — | Operator can restart fault_node via SSH |

---

## SF-07 — Support Payload Interface

| ID | Failure Mode | Effect | Cause | S | O | D | RPN | Hazard | Mitigation |
|---|---|---|---|---|---|---|---|---|---|
| FM-07-01 | GPIO load switch failure | Payload always powered / never powered | MOSFET failure | 2 | 1 | 2 | 4 | — | Manual disconnect via battery switch as fallback |
| FM-07-02 | Payload current monitor loss | No overcurrent protection on payload rail | INA219 #2 fault | 3 | 2 | 2 | 12 | H-07 | /diagnostics alerts; operator should disconnect payload manually |

---

## High-RPN Items Requiring Attention

| RPN | ID | Failure Mode | Action |
|---|---|---|---|
| 27 | FM-05-02 | Video latency > 1 s | Operational procedure: reduce resolution; safety observer required near obstacles |
| 24 | FM-01-01 | No /cmd_vel received | Watchdog tested at system integration; verify 1 s timeout in hardware test |
| 18 | FM-03-04 | Voltage reading drift | Calibration procedure added to build docs |
| 18 | FM-04-02 | Odometry divergence | Documented limitation; not a safety issue on its own |
| 18 | FM-04-03 | Telemetry topic drops | QoS tuning for /battery_state and /diagnostics |
| 18 | FM-04-04 | IMU filter divergence | Warm-up procedure added to operating instructions |
| 16 | FM-01-04 | Watchdog timer fails | Node supervisor + RoboClaw hardware timeout as independent layer |
| 16 | FM-04-01 | IMU data freeze | Staleness check in LC-05; alert on /diagnostics |
| 16 | FM-06-03 | Tilt wrong axis | Tilt calibration test step added to CI-04 verification |
