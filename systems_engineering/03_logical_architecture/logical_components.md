# Logical Components

**LA Layer — Logical Component Register**

Logical Components (LCs) are the **functional subsystems** of the OSR. They are defined by what they do, not by what physical hardware or software implements them. Each LC has a defined set of responsibilities, inputs, outputs, interfaces, requirements, and acceptance criteria.

---

## LC-01 — Communication Manager

**Responsibility:** All wireless data exchange between the rover and the ground station. Acts as the system's network gateway for both inbound commands and outbound telemetry and video.

| Attribute | Detail |
|---|---|
| **Inputs** | Network packets from ground station (motion commands, developer SSH) |
| **Outputs** | Decoded command data to LC-02; outbound telemetry from LC-07; video from LC-08 |
| **Realizes** | SF-01 (reception), SF-04.3 (transmission), SF-05 (video stream) |
| **Watchdog role** | Times out command stream; notifies LC-02 if no packet in > 1 s |

**Sub-functions:**

- `receive_command_packet()` — listens on `/cmd_vel` ROS topic (Wi-Fi bridged)
- `transmit_telemetry_packet()` — forwards serialized telemetry topics to ground station ROS subscriber
- `relay_video_stream()` — proxies compressed camera frames over network via `rosbridge` or direct ROS

**Description:**

LC-01 is the sole point of ingress and egress for all external data. On the inbound side, it receives `geometry_msgs/Twist` messages published to the `/cmd_vel` topic by the operator's ground station and forwards them to LC-02 for validation. On the outbound side, it relays telemetry topics (odometry, IMU, battery, diagnostics) and optionally the camera video stream to the ground station.

The component manages the watchdog boundary: if the inbound command stream is silent for more than 1 second (as detected by a ROS timer), LC-01 signals LC-02 to issue a zero-motion command, preventing the rover from continuing motion after loss of communication.

### Requirements

| ID | Requirement |
|---|---|
| REQ-LC-01-01 | LC-01 shall receive motion commands from the ground station on the `/cmd_vel` ROS topic. |
| REQ-LC-01-02 | LC-01 shall detect command stream timeout (no message within 1 s) and notify LC-02 to command zero velocity. |
| REQ-LC-01-03 | LC-01 shall relay all outbound telemetry topics to the ground station subscriber at their respective publish rates. |
| REQ-LC-01-04 | LC-01 shall relay the video stream from LC-08 to the ground station when SF-05 is active. |
| REQ-LC-01-05 | LC-01 shall not drop or reorder command packets during normal Wi-Fi operation at distances ≤ 50 m. |

### Acceptance Criteria

- [ ] Publishing a `Twist` message from the ground station ROS node results in receipt by LC-02 within 100 ms over local Wi-Fi.
- [ ] Stopping all ground station publications for 1.1 s causes LC-01 to signal watchdog timeout; rover halts.
- [ ] `rostopic echo /odom` on the ground station displays data at ≥ 10 Hz when rover is operating.
- [ ] At 30 m range on local Wi-Fi, no command packet loss observed during a 60-second test (verified via sequence number comparison).

---

## LC-02 — Command Processor

**Responsibility:** Validates incoming commands, enforces safety limits, and dispatches motion intents to the Mobility Controller.

| Attribute | Detail |
|---|---|
| **Inputs** | Raw command packets from LC-01 |
| **Outputs** | Validated motion intent (linear velocity, angular velocity) to LC-03; halt signal to LC-03 on timeout or fault |
| **Realizes** | SF-01 |

**Sub-functions:**

- `decode_command()` — parses `geometry_msgs/Twist` into `(v_linear, v_angular)`
- `apply_velocity_limits()` — clamps to configured maximum speed and turn rate
- `handle_watchdog_timeout()` — outputs zero-motion intent if no command received within 1 s
- `relay_acknowledgment()` — confirms command receipt to LC-01

**Description:**

LC-02 acts as the command validation gate between the raw network input and the motion execution chain. It parses each incoming Twist message, verifies that linear and angular velocities are within the system's configured safe operating envelope (no NaN, no Inf, within max speed limits), and clamps any out-of-range values before forwarding to LC-03.

In the event of a watchdog timeout (signaled by LC-01) or a halt command from LC-05 (fault monitor), LC-02 immediately forwards a zero-velocity motion intent to LC-03, overriding any previously queued motion command.

### Requirements

| ID | Requirement |
|---|---|
| REQ-LC-02-01 | LC-02 shall parse `geometry_msgs/Twist` messages and extract `linear.x` and `angular.z` components. |
| REQ-LC-02-02 | LC-02 shall discard any message containing NaN or Inf values and not forward it to LC-03. |
| REQ-LC-02-03 | LC-02 shall clamp `linear.x` to the configured maximum speed (default ±0.4 m/s) and `angular.z` to the configured maximum turn rate (default ±1.0 rad/s). |
| REQ-LC-02-04 | LC-02 shall output a zero-velocity intent to LC-03 immediately upon receiving a halt command from LC-05. |
| REQ-LC-02-05 | LC-02 shall output a zero-velocity intent to LC-03 when LC-01 signals a watchdog timeout. |

### Acceptance Criteria

- [ ] A `Twist` message with `linear.x = 0.3 m/s` results in LC-03 receiving `0.3 m/s` (within rounding).
- [ ] A `Twist` message with `linear.x = 2.0 m/s` (above limit) results in LC-03 receiving `0.4 m/s` (clamped).
- [ ] A `Twist` message with `linear.x = NaN` is discarded; LC-03 receives no new command (previous intent preserved or zero if watchdog active).
- [ ] LC-05 issuing a halt command causes LC-03 to receive zero velocity within one control cycle (≤ 50 ms).
- [ ] Watchdog timeout from LC-01 causes LC-03 to receive zero velocity within 1.1 seconds of last command.

---

## LC-03 — Mobility Controller

**Responsibility:** Converts commanded robot velocities into per-wheel drive and steering commands. Implements the kinematic model of the rocker-bogie platform.

| Attribute | Detail |
|---|---|
| **Inputs** | Motion intent (v_linear, v_angular) from LC-02 |
| **Outputs** | Six drive wheel speed setpoints; four steering angle setpoints |
| **Realizes** | SF-02.1, SF-02.2, SF-02.3 |

**Sub-functions:**

- `compute_wheel_speeds(v, ω)` — applies differential drive / Ackermann kinematics for the OSR 6-wheel geometry
- `compute_steering_angles(ω)` — derives per-corner servo positions from commanded angular velocity
- `output_drive_commands()` — writes speed setpoints to motor control interface (RoboClaw)
- `output_steering_commands()` — writes angle setpoints to servo driver interface (PCA9685)

**Description:**

LC-03 is the kinematic heart of the rover. The OSR's rocker-bogie suspension means that during a turn, each wheel pair follows a different radius arc and must travel at a different speed to avoid slipping. LC-03 applies the complete differential drive model for six wheels grouped as three pairs (front, middle, rear), with the additional complication that the four corner wheels also steer (Ackermann geometry).

The component outputs setpoints via two different hardware interfaces: USB serial to the three RoboClaw 2×15A motor controllers (two wheels each), and I²C to the PCA9685 16-channel PWM servo driver (four corner servos).

**Kinematics notes:**

- The rocker-bogie geometry requires each wheel pair (front, middle, rear) to be driven at different speeds during a turn
- Corner wheels (front and rear) steer; middle wheels are fixed-heading
- Kinematic model accounts for rover wheelbase (L) and track width (W)
- Ackermann steering: `θ_inner = atan(L / (R - W/2))`, `θ_outer = atan(L / (R + W/2))`

### Requirements

| ID | Requirement |
|---|---|
| REQ-LC-03-01 | LC-03 shall compute individual speed setpoints for all six drive wheels using the OSR rocker-bogie kinematic model. |
| REQ-LC-03-02 | LC-03 shall compute Ackermann steering angles for all four corner wheels. |
| REQ-LC-03-03 | LC-03 shall update drive wheel setpoints at a minimum rate of 20 Hz. |
| REQ-LC-03-04 | LC-03 shall update steering servo angles within 250 ms of a change in commanded angular velocity. |
| REQ-LC-03-05 | LC-03 shall clamp wheel speed setpoints to the motor controller's rated maximum and shall not command a speed exceeding the motor's rated RPM. |
| REQ-LC-03-06 | LC-03 shall clamp steering angles to each servo's mechanical range of motion (default ±30°). |
| REQ-LC-03-07 | LC-03 shall output zero speed to all wheels immediately upon receiving a halt command, regardless of current motion state. |

### Acceptance Criteria

- [ ] Straight-ahead command (`v = 0.3 m/s, ω = 0`) produces equal setpoints on all six wheels within ±5%.
- [ ] Left-turn command (`ω > 0`) produces higher speed on right wheels than left wheels; corner servos position to Ackermann angles.
- [ ] Drive setpoint update rate ≥ 20 Hz confirmed via RoboClaw serial traffic analysis.
- [ ] Corner servos reach target angle within 250 ms of command change (verified by encoder feedback or manual inspection).
- [ ] Command of `v = 5 m/s` (above limit) results in setpoints clamped to rated maximum.
- [ ] Halt command causes all wheel setpoints to reach zero within one control cycle (50 ms).

---

## LC-04 — State Estimator

**Responsibility:** Collects raw sensor data and produces a fused estimate of rover state (position, orientation, velocity). Feeds both telemetry and fault monitoring.

| Attribute | Detail |
|---|---|
| **Inputs** | Wheel encoder ticks (×6), IMU acceleration and gyroscope, motor current readings |
| **Outputs** | Odometry estimate (pose, velocity), attitude estimate (roll, pitch, yaw), per-wheel current readings |
| **Realizes** | SF-04.1, SF-04.2 |

**Sub-functions:**

- `sample_encoders()` — reads encoder counters at ≥ 20 Hz from all three RoboClaw units
- `sample_imu()` — reads BNO055 linear acceleration and angular velocity at ≥ 50 Hz over I²C
- `sample_currents()` — reads per-channel motor current from each RoboClaw at ≥ 10 Hz
- `integrate_odometry()` — dead-reckoning from wheel encoder tick deltas to pose estimate
- `estimate_attitude()` — complementary filter fusing accelerometer and gyroscope for orientation
- `publish_state()` — packages and sends state to LC-07 (telemetry) and LC-05 (fault monitor)

**Description:**

LC-04 is responsible for knowing where the rover is and how it is oriented at all times. It reads wheel encoder ticks at 20 Hz, integrating them into an odometry pose (x, y, heading) using dead-reckoning. It simultaneously reads the BNO055 IMU at 50 Hz, applying a complementary filter to produce a low-drift attitude estimate (roll, pitch, yaw).

Motor current readings are sampled from the RoboClaw units alongside encoder data. These are forwarded directly to LC-05 for fault monitoring without any fusion, preserving the raw values for accurate threshold comparison.

### Requirements

| ID | Requirement |
|---|---|
| REQ-LC-04-01 | LC-04 shall read wheel encoder counts from all six wheels at a minimum rate of 20 Hz. |
| REQ-LC-04-02 | LC-04 shall read IMU acceleration and angular velocity at a minimum rate of 50 Hz. |
| REQ-LC-04-03 | LC-04 shall read per-channel motor currents at a minimum rate of 10 Hz. |
| REQ-LC-04-04 | LC-04 shall publish odometry (`nav_msgs/Odometry`) at a minimum rate of 10 Hz. |
| REQ-LC-04-05 | LC-04 shall publish attitude (`sensor_msgs/Imu`) at a minimum rate of 20 Hz. |
| REQ-LC-04-06 | LC-04 shall publish per-motor current readings to LC-05 at a minimum rate of 10 Hz. |
| REQ-LC-04-07 | Odometry position error shall not exceed 10% of distance travelled in a straight-line test on flat terrain. |

### Acceptance Criteria

- [ ] `rostopic hz /odom` shows ≥ 10 Hz during rover motion.
- [ ] `rostopic hz /imu` shows ≥ 20 Hz during rover motion.
- [ ] Motor current readings are published at ≥ 10 Hz (verify with `rostopic hz /motor_currents`).
- [ ] Rover driven 1 m in a straight line; `/odom` final x position is 0.9–1.1 m.
- [ ] Rover stationary on level surface; `/imu` roll and pitch are ±2° of zero.
- [ ] BNO055 calibration status shows System: 3 before monitoring begins (verify via calibration status topic).

---

## LC-05 — Fault Monitor

**Responsibility:** Continuously watches system health indicators and triggers safe stop actions when thresholds are exceeded.

| Attribute | Detail |
|---|---|
| **Inputs** | Motor currents from LC-04, battery voltage from LC-06, attitude estimate from LC-04 |
| **Outputs** | Fault flags (latched); halt command to LC-02; fault events to LC-07 |
| **Realizes** | SF-06 |

**Description:**

LC-05 is the safety watchdog of the OSR. It runs a continuous monitoring loop at 10 Hz, comparing live system measurements against a threshold table. When any measurement crosses a critical threshold, LC-05 immediately issues a halt to LC-02 (stopping all motion), publishes a fault event to LC-07 (for telemetry), and latches the fault flag.

The fault latch is intentional: the rover must stay stopped until a human operator consciously issues a `clear_fault` service call, after which LC-05 verifies the root cause is no longer present before clearing the latch.

**Monitored conditions:**

| Condition | Threshold | Severity | Action |
|---|---|---|---|
| Motor overcurrent | Any motor > 10 A | Critical | Immediate safe stop + fault flag |
| Low battery (warning) | Voltage < 11.0 V | Warning | Warning flag published to telemetry |
| Low battery (critical) | Voltage < 10.5 V | Critical | Safe stop + fault flag |
| Excessive tilt | Roll or pitch > 35° | Critical | Safe stop + fault flag |
| Command watchdog | No command in > 1.0 s | Informational | Safe stop (no fault, standby) |

**Recovery:** Operator sends explicit `clear_fault` ROS service call; LC-05 verifies condition resolved before clearing halt.

### Requirements

| ID | Requirement |
|---|---|
| REQ-LC-05-01 | LC-05 shall monitor motor currents at a minimum rate of 10 Hz and trigger safe stop within 100 ms of any channel exceeding 10 A. |
| REQ-LC-05-02 | LC-05 shall monitor battery voltage at a minimum rate of 1 Hz, publish a warning at < 11.0 V, and trigger safe stop at < 10.5 V. |
| REQ-LC-05-03 | LC-05 shall monitor rover roll and pitch at a minimum rate of 10 Hz and trigger safe stop within 100 ms of either exceeding 35°. |
| REQ-LC-05-04 | All critical faults shall be latching; the halt command shall persist until a `clear_fault` service call is received. |
| REQ-LC-05-05 | LC-05 shall verify the fault condition is no longer present before responding to a `clear_fault` call; if still present, the latch shall not clear. |
| REQ-LC-05-06 | LC-05 shall publish all fault events with a timestamp and fault classification to `/diagnostics`. |

### Acceptance Criteria

- [ ] Injecting a simulated overcurrent message (> 10 A) causes LC-05 to issue halt to LC-02 within 100 ms.
- [ ] Injecting battery voltage < 11.0 V causes warning entry in `/diagnostics` without halting rover.
- [ ] Injecting battery voltage < 10.5 V causes rover safe stop and critical fault entry in `/diagnostics`.
- [ ] Tilting rover to > 35° causes halt within 100 ms (simulated via modified `/imu` message).
- [ ] After safe stop, `clear_fault` call while overcurrent still injected does not clear latch.
- [ ] After safe stop, `clear_fault` call after removing overcurrent condition clears latch and rover resumes normal command processing.

---

## LC-06 — Power Manager

**Responsibility:** Monitors battery and power rails; manages power distribution and protection. Provides battery state information to fault monitoring and telemetry.

| Attribute | Detail |
|---|---|
| **Inputs** | Battery terminal voltage (INA219 I²C ADC), total system current |
| **Outputs** | Battery state (voltage, current, SoC%) to LC-05 and LC-07; switched power enables to motor controllers and payload |
| **Realizes** | SF-03 |

**Sub-functions:**

- `read_battery_voltage()` — reads INA219 shunt and bus voltage registers over I²C at 1 Hz
- `estimate_state_of_charge()` — voltage-curve lookup for 3S LiPo chemistry
- `monitor_rail_current()` — reads INA219 current channel for total system draw
- `control_power_switches()` — enables/disables PCB load switches on fault or operator command

**Description:**

LC-06 provides the software-side power management: reading the INA219 power monitor IC, computing state-of-charge, and publishing the results as `sensor_msgs/BatteryState` on `/battery_state`. The hardware side (DC-DC converters, fuses, load switches) is implemented in the custom OSR PCB and does not require active software control during normal operation.

The LiPo state-of-charge is estimated from a characterised discharge curve (voltage vs. SoC% at a reference discharge rate). Because LiPo voltage varies with temperature and load current, the SoC estimate is approximate (±10%); the primary protection mechanism remains the voltage threshold comparisons in LC-05.

### Requirements

| ID | Requirement |
|---|---|
| REQ-LC-06-01 | LC-06 shall read battery terminal voltage and total current from the INA219 at a minimum rate of 1 Hz. |
| REQ-LC-06-02 | LC-06 shall publish battery voltage, current, and SoC% as `sensor_msgs/BatteryState` on `/battery_state`. |
| REQ-LC-06-03 | LC-06 shall compute SoC% using the 3S LiPo discharge voltage curve; SoC shall read 100% at ≥ 12.6 V and 0% at ≤ 10.5 V. |
| REQ-LC-06-04 | LC-06 shall provide a software-controllable enable/disable for the payload power rail via GPIO. |
| REQ-LC-06-05 | LC-06 voltage measurement accuracy shall be within ±0.1 V of multimeter reference at the battery terminals. |

### Acceptance Criteria

- [ ] `rostopic hz /battery_state` reports ≥ 1 Hz during rover operation.
- [ ] Battery voltage reported on `/battery_state` is within ±0.1 V of multimeter reading at battery terminals.
- [ ] With a fully charged battery (12.6 V), `/battery_state.percentage` reports ≥ 0.95 (95%).
- [ ] With a battery at 11.0 V, `/battery_state.percentage` reports a value consistent with the discharge curve (expected ≈ 20–30%).
- [ ] GPIO payload enable pin can be toggled via `rosservice call` without affecting other power rails.

---

## LC-07 — Telemetry Publisher

**Responsibility:** Aggregates state estimates, fault flags, and sensor data; formats and forwards to LC-01 for transmission to the ground station.

| Attribute | Detail |
|---|---|
| **Inputs** | State from LC-04, power data from LC-06, fault flags from LC-05 |
| **Outputs** | Serialized telemetry packets to LC-01 |
| **Realizes** | SF-04.3 |
| **Rate** | ≥ 5 Hz publish cycle for aggregated telemetry; per-sensor topics at their native rates |

**Published content:**

- `/odom` — Odometry (pose + velocity) from LC-04
- `/imu` — IMU attitude (roll, pitch, yaw) from LC-04
- `/battery_state` — Battery voltage, current, SoC% from LC-06
- `/motor_currents` — Per-wheel current readings from LC-04
- `/diagnostics` — Active fault flags and health summary from LC-05
- `/camera/image_raw/compressed` — Video frames from LC-08 (if SF-05 enabled)

**Description:**

LC-07 acts as the outbound data aggregator. In the ROS architecture, most "publishing" is handled by the individual sensor nodes (LC-04 publishes `/odom` and `/imu`, LC-06 publishes `/battery_state`). LC-07 represents the logical role of collecting all this data into a coherent telemetry stream that LC-01 forwards over Wi-Fi.

In practice, LC-07's role is implemented by `telemetry_node`, which subscribes to all individual topics and republishes a diagnostic summary at 5 Hz, plus the `diagnostic_aggregator` node which collates fault information.

### Requirements

| ID | Requirement |
|---|---|
| REQ-LC-07-01 | LC-07 shall aggregate and publish all rover state topics at their respective rates; aggregated diagnostic summary shall be published at ≥ 5 Hz. |
| REQ-LC-07-02 | LC-07 shall include battery state, fault flags, odometry, attitude, and motor currents in the telemetry output. |
| REQ-LC-07-03 | LC-07 shall relay video frames from LC-08 when SF-05 is active. |
| REQ-LC-07-04 | LC-07 shall not introduce more than 50 ms of additional latency to individual sensor topic data. |

### Acceptance Criteria

- [ ] Ground station `rostopic echo /diagnostics` shows health summary at ≥ 5 Hz.
- [ ] All expected topics (`/odom`, `/imu`, `/battery_state`, `/motor_currents`, `/diagnostics`) are visible on ground station ROS master.
- [ ] End-to-end latency from sensor read to ground station display is ≤ 200 ms (measured via timestamps).
- [ ] `/camera/image_raw/compressed` appears on ground station when camera is installed.

---

## LC-08 — Payload Manager

**Responsibility:** Controls power delivery to optional payload devices and routes payload data to the compute stack.

| Attribute | Detail |
|---|---|
| **Inputs** | Payload power enable request, payload data (USB / I²C / UART) |
| **Outputs** | Switched 5V/12V power to payload connector; routed data (USB/I²C) to Raspberry Pi |
| **Realizes** | SF-07 |

**Sub-functions:**

- `enable_payload_power(rail, enable)` — controls GPIO-driven load switch for payload power rails
- `monitor_payload_current()` — reads INA219 payload current channel; enforces soft current limit
- `route_payload_data()` — logical pass-through of USB/I²C to RPi compute stack

**Description:**

LC-08 allows the OSR to serve as a mobile platform for user-supplied instruments or experiments. It provides two power rails (5V and 12V battery-direct) to the payload connector, both switchable via RPi GPIO. Current on the payload rail is monitored by a dedicated INA219 channel; if the payload draws more than the configured limit, LC-08 cuts power and raises a fault in `/diagnostics`.

Data connectivity is passive hardware routing: USB, I²C, and UART connections from the payload connector route directly to the Raspberry Pi's interfaces. User payloads are responsible for their own ROS driver or data processing node.

### Requirements

| ID | Requirement |
|---|---|
| REQ-LC-08-01 | LC-08 shall provide GPIO-controlled 5V and 12V power rails to the payload connector. |
| REQ-LC-08-02 | LC-08 shall monitor payload power current at a minimum rate of 1 Hz and disable the payload rail if current exceeds the configured limit (default 2 A). |
| REQ-LC-08-03 | LC-08 shall publish a fault event to `/diagnostics` when payload overcurrent is detected. |
| REQ-LC-08-04 | LC-08 shall provide USB, I²C, and UART pass-through from the payload connector to the Raspberry Pi. |
| REQ-LC-08-05 | Payload power switching shall not affect any other power rail or reset the Raspberry Pi. |

### Acceptance Criteria

- [ ] Calling `enable_payload_power(5V, True)` via GPIO causes 5V to appear at payload connector (verified with multimeter).
- [ ] Payload drawing > 2 A causes LC-08 to disable rail within ≤ 1 s and publish overcurrent entry in `/diagnostics`.
- [ ] USB device connected to payload USB-A connector enumerates in `lsusb` within 5 seconds.
- [ ] Payload power toggle does not reset the Raspberry Pi or cause any running ROS node to restart.
- [ ] I²C device at a non-conflicting address on payload I²C header is detectable with `i2cdetect -y 1`.

---

## Component Dependencies

```
LC-01 (Comms)
  └── LC-02 (Command Processor) ── LC-03 (Mobility Controller)
                                         │
                                  Motor/Servo outputs

LC-04 (State Estimator) ──► LC-05 (Fault Monitor)
        │                           │
        └──────► LC-07 (Telemetry) ◄┘
                        │
                   LC-01 (Comms) ──► Ground Station

LC-06 (Power Manager) ──► LC-05 (Fault Monitor)
                     └──► LC-07 (Telemetry)
                     └──► LC-08 (Payload Manager)
```

## Component-to-System-Function Traceability

| Logical Component | Realized System Functions |
|---|---|
| LC-01 Communication Manager | SF-01, SF-04.3, SF-05 |
| LC-02 Command Processor | SF-01 |
| LC-03 Mobility Controller | SF-02.1, SF-02.2, SF-02.3 |
| LC-04 State Estimator | SF-04.1, SF-04.2 |
| LC-05 Fault Monitor | SF-06 |
| LC-06 Power Manager | SF-03 |
| LC-07 Telemetry Publisher | SF-04.3 |
| LC-08 Payload Manager | SF-07 |
