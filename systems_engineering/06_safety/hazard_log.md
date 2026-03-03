# Hazard Log

**Document:** OSR-SAF-HAZLOG-001
**Status:** DRAFT

Each hazard is scored before and after mitigation using Severity (S) × Likelihood (L).
Scores: 1 = negligible/very unlikely, 5 = catastrophic/very likely.

---

## Hazard Register

### H-01 — Motor Overcurrent / Fire Risk

| Field | Value |
|---|---|
| **Hazard** | One or more drive motors draws sustained current > safe limit |
| **Cause** | Wheel jam, mechanical binding, commanded motion against immovable obstacle |
| **Effect** | Motor winding damage, wire harness fire, RoboClaw controller damage |
| **Severity** | 4 — Critical (property damage; potential burn hazard to operator) |
| **Pre-mitigation likelihood** | 3 — Possible |
| **Pre-mitigation risk** | **High (12)** |
| **Mitigation** | Software: SF-06.1 monitors per-channel current at 10 Hz; threshold 10 A triggers SF-06.4 safe stop. Hardware: blade fuses on PCB protect wiring. |
| **Post-mitigation likelihood** | 2 — Unlikely |
| **Post-mitigation risk** | **Medium (8)** |
| **Linked requirements** | REQ-SF-06-01, REQ-LC-05-01, REQ-PF-05-01 |
| **Scenic scenario** | `scenarios/motor_stall.scenic` |

---

### H-02 — Rover Tip / Rollover

| Field | Value |
|---|---|
| **Hazard** | Rover rolls over on steep terrain |
| **Cause** | Traversal over slope > safe limit; operator misjudgement of terrain |
| **Effect** | Structural damage; potential injury if rover falls on person |
| **Severity** | 4 — Critical |
| **Pre-mitigation likelihood** | 3 — Possible |
| **Pre-mitigation risk** | **High (12)** |
| **Mitigation** | SF-06.3 monitors BNO055 IMU roll/pitch at 10 Hz; threshold 35° triggers immediate safe stop. Rocker-bogie provides ±30° passive suspension. |
| **Post-mitigation likelihood** | 2 — Unlikely |
| **Post-mitigation risk** | **Medium (8)** |
| **Linked requirements** | REQ-SF-06-03, REQ-LC-05-03 |
| **Scenic scenario** | `scenarios/tilt_risk.scenic` |

---

### H-03 — Battery Over-Discharge

| Field | Value |
|---|---|
| **Hazard** | 3S LiPo battery discharged below minimum cell voltage |
| **Cause** | Extended mission without monitoring; INA219 failure masking low SoC |
| **Effect** | Permanent battery capacity loss; potential LiPo cell failure/swelling |
| **Severity** | 3 — Moderate (equipment damage, mission abort) |
| **Pre-mitigation likelihood** | 3 — Possible |
| **Pre-mitigation risk** | **Medium (9)** |
| **Mitigation** | SF-06.2 monitors voltage at 1 Hz; warning at 11.0 V (≈20% SoC); safe stop at 10.5 V (≈5% SoC). /battery_state published for operator display. |
| **Post-mitigation likelihood** | 2 — Unlikely |
| **Post-mitigation risk** | **Medium (6)** |
| **Linked requirements** | REQ-SF-06-02, REQ-LC-05-02, REQ-SF-03-02 |
| **Scenic scenario** | `scenarios/battery_low.scenic` |

---

### H-04 — Runaway Due to Communication Loss

| Field | Value |
|---|---|
| **Hazard** | Rover continues executing last command after Wi-Fi link drops |
| **Cause** | Wi-Fi dropout, operator moves out of range, ground station crash |
| **Effect** | Rover drives uncontrolled into obstacle, person, or off edge |
| **Severity** | 4 — Critical |
| **Pre-mitigation likelihood** | 3 — Possible |
| **Pre-mitigation risk** | **High (12)** |
| **Mitigation** | SF-01 / LF-01.4 implements 1-second command watchdog: if no /cmd_vel received in 1 s, emit zero-velocity Twist and halt. |
| **Post-mitigation likelihood** | 1 — Very unlikely |
| **Post-mitigation risk** | **Low (4)** |
| **Linked requirements** | REQ-SF-01-04, REQ-LC-01-01, REQ-PF-01-04 |
| **Scenic scenario** | `scenarios/comm_loss.scenic` |

---

### H-05 — Collision with Person or Object

| Field | Value |
|---|---|
| **Hazard** | Rover drives into a person or fragile object |
| **Cause** | Operator error, latency in telemetry, limited field of view |
| **Effect** | Injury (bruising, crush injury from 5 kg rover at 0.4 m/s); equipment damage |
| **Severity** | 3 — Moderate |
| **Pre-mitigation likelihood** | 3 — Possible |
| **Pre-mitigation risk** | **Medium (9)** |
| **Mitigation** | Velocity capped at 0.4 m/s (SF-01 / LF-01.3). Optional: camera stream for SA (SF-05). Operational procedure: safety observer (OE-04) maintains exclusion zone. |
| **Post-mitigation likelihood** | 2 — Unlikely |
| **Post-mitigation risk** | **Medium (6)** |
| **Linked requirements** | REQ-SF-01-03, REQ-OAct-01.4-01 |
| **Scenic scenario** | `scenarios/nominal_traverse.scenic` (velocity limit check) |

---

### H-06 — Electrical Short Circuit

| Field | Value |
|---|---|
| **Hazard** | Short circuit on PCB or wiring harness |
| **Cause** | Wiring error during assembly; connector damage; conductive debris |
| **Effect** | Component damage, fire, power loss |
| **Severity** | 4 — Critical |
| **Pre-mitigation likelihood** | 2 — Unlikely |
| **Pre-mitigation risk** | **Medium (8)** |
| **Mitigation** | Blade fuses (hardware) protect each major circuit. Pre-operation continuity check (OAct-03.3). Wiring routed away from moving parts. |
| **Post-mitigation likelihood** | 1 — Very unlikely |
| **Post-mitigation risk** | **Low (4)** |
| **Linked requirements** | REQ-SF-03-03, REQ-CI-04-01 |
| **Scenic scenario** | Hardware test — not Scenic-testable |

---

### H-07 — Payload Damage Due to Overcurrent

| Field | Value |
|---|---|
| **Hazard** | Payload draws excessive current from rover power rail |
| **Cause** | Payload design error; short circuit in payload connector |
| **Effect** | Payload and OSR PCB damage; potential fire |
| **Severity** | 3 — Moderate |
| **Pre-mitigation likelihood** | 2 — Unlikely |
| **Pre-mitigation risk** | **Medium (6)** |
| **Mitigation** | LF-07.2 monitors payload INA219 at 1 Hz; threshold 2 A disables GPIO load switch. |
| **Post-mitigation likelihood** | 1 — Very unlikely |
| **Post-mitigation risk** | **Low (3)** |
| **Linked requirements** | REQ-SF-07-01, REQ-LC-08-02 |
| **Scenic scenario** | Not directly testable in simulation |

---

### H-08 — Software Crash / Watchdog Failure

| Field | Value |
|---|---|
| **Hazard** | ROS node crash leaves rover in unknown state without safe stop |
| **Cause** | Unhandled exception in Python node; memory exhaustion on RPi |
| **Effect** | Motors may freeze at last setpoint; fault monitor offline; loss of telemetry |
| **Severity** | 3 — Moderate |
| **Pre-mitigation likelihood** | 2 — Unlikely |
| **Pre-mitigation risk** | **Medium (6)** |
| **Mitigation** | RoboClaw hardware timeout: if no command received, motors coast to stop. ROS launch supervisor (`respawn=true`) restarts crashed nodes. Watchdog timer in SF-01. |
| **Post-mitigation likelihood** | 2 — Unlikely |
| **Post-mitigation risk** | **Medium (6)** |
| **Linked requirements** | REQ-SF-01-04, REQ-CI-01-01 |
| **Scenic scenario** | `scenarios/comm_loss.scenic` (watchdog expiry) |

---

### H-09 — Structural Failure

| Field | Value |
|---|---|
| **Hazard** | Chassis or rocker-bogie structural failure during operation |
| **Cause** | Assembly error (missing fasteners); material fatigue; impact damage |
| **Effect** | Rover immobilized; potential secondary falling hazard |
| **Severity** | 3 — Moderate |
| **Pre-mitigation likelihood** | 2 — Unlikely |
| **Pre-mitigation risk** | **Medium (6)** |
| **Mitigation** | Post-build inspection checklist (OAct-02.2). Torque spec compliance during assembly (OAct-03.2). Motor current limit prevents excessive force. |
| **Post-mitigation likelihood** | 1 — Very unlikely |
| **Post-mitigation risk** | **Low (3)** |
| **Linked requirements** | REQ-CI-05-01 |
| **Scenic scenario** | Hardware inspection — not Scenic-testable |

---

### H-10 — LiPo Thermal Runaway

| Field | Value |
|---|---|
| **Hazard** | Battery enters thermal runaway, fire/explosion |
| **Cause** | Physical damage to cells; charging at >1C rate; internal short |
| **Effect** | Fire, toxic fume release, severe property damage |
| **Severity** | 5 — Catastrophic |
| **Pre-mitigation likelihood** | 1 — Very unlikely |
| **Pre-mitigation risk** | **Medium (5)** |
| **Mitigation** | Charge at ≤1C using balance charger (OAct-02.1). Inspect cells for swelling before each session. Never charge unattended. Battery stored in LiPo-safe bag. Voltage monitoring (SF-06.2) prevents deep discharge contributing to cell damage. |
| **Post-mitigation likelihood** | 1 — Very unlikely |
| **Post-mitigation risk** | **Low (5)** |
| **Linked requirements** | REQ-SF-06-02, OAct-02.1 |
| **Scenic scenario** | Not simulation-testable |

---

## Risk Summary

| ID | Hazard | Pre-risk | Post-risk | Status |
|---|---|---|---|---|
| H-01 | Motor overcurrent / fire | High (12) | Medium (8) | Mitigated |
| H-02 | Tip / rollover | High (12) | Medium (8) | Mitigated |
| H-03 | Battery over-discharge | Medium (9) | Medium (6) | Mitigated |
| H-04 | Runaway on comm loss | High (12) | Low (4) | Mitigated |
| H-05 | Collision with person | Medium (9) | Medium (6) | Mitigated |
| H-06 | Electrical short | Medium (8) | Low (4) | Mitigated |
| H-07 | Payload overcurrent | Medium (6) | Low (3) | Mitigated |
| H-08 | Software crash | Medium (6) | Medium (6) | Accepted |
| H-09 | Structural failure | Medium (6) | Low (3) | Mitigated |
| H-10 | LiPo thermal runaway | Medium (5) | Low (5) | Mitigated |

All residual risks are Low or Medium. No Extreme or unacceptable risks remain after mitigation.
