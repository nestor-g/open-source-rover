# System Functions

**SA Layer — System Function Register**

System Functions (SFs) define **what the OSR system does** at its boundary. Each SF receives inputs from outside and produces outputs that go outside the system, or internally transforms state to enable other functions. Functions are decomposed hierarchically from a root.

## Function Hierarchy

```
Root System Function (SF-00)
├── SF-01  Receive and Decode Command
├── SF-02  Execute Mobility
│   ├── SF-02.1  Compute Drive Commands
│   ├── SF-02.2  Drive Wheels
│   └── SF-02.3  Steer Corner Wheels
├── SF-03  Manage Power
│   ├── SF-03.1  Distribute Electrical Power
│   ├── SF-03.2  Monitor Battery State
│   └── SF-03.3  Protect Against Overcurrent/Short
├── SF-04  Process and Publish Telemetry
│   ├── SF-04.1  Sample Sensors
│   ├── SF-04.2  Estimate Rover State
│   └── SF-04.3  Transmit Telemetry
├── SF-05  Capture and Stream Video
├── SF-06  Detect and Handle Faults
│   ├── SF-06.1  Monitor Motor Currents
│   ├── SF-06.2  Monitor Battery Voltage
│   ├── SF-06.3  Detect Tip Risk (IMU)
│   └── SF-06.4  Execute Safe Stop
└── SF-07  Support Payload Interface
    ├── SF-07.1  Provide Power to Payload
    └── SF-07.2  Route Payload Data
```

---

## SF-01 — Receive and Decode Command

### Description

SF-01 is the entry point for all operator-issued motion commands. The system subscribes to the `/cmd_vel` ROS topic over the Wi-Fi network and accepts `geometry_msgs/Twist` messages that encode the desired linear and angular velocity of the rover. Upon receipt, the function validates message integrity (field types, timestamp), checks that velocity magnitudes fall within the system's configured envelope, and delivers a verified motion intent to SF-02.

A watchdog timer is armed on receipt of every command packet. If no new packet arrives within 1 second, SF-01 outputs a zero-velocity intent and signals the watchdog timeout to SF-06 for fault logging.

**Execution steps:**

1. Subscribe to `/cmd_vel` (ROS Noetic, `geometry_msgs/Twist`).
2. On message receipt, extract `linear.x` (m/s) and `angular.z` (rad/s).
3. Validate that neither field is NaN or Inf; discard malformed packets.
4. Reset the 1-second watchdog timer.
5. Forward the verified (v_linear, v_angular) pair to SF-02.

| Attribute | Value |
|---|---|
| **Inputs** | `geometry_msgs/Twist` packet via Wi-Fi / ROS |
| **Outputs** | Decoded motion intent (linear velocity m/s, angular velocity rad/s) |
| **Realizes** | OAct-01.2 Command Rover Motion |
| **Watchdog** | Zero-motion output + timeout flag if no packet within 1 s |

### Requirements

| ID | Requirement |
|---|---|
| REQ-SF-01-01 | The system shall accept motion commands encoded as `geometry_msgs/Twist` messages on the `/cmd_vel` ROS topic. |
| REQ-SF-01-02 | The system shall apply a 1-second command watchdog; upon timeout the system shall output zero linear and angular velocity. |
| REQ-SF-01-03 | The system shall discard any command message containing NaN or Inf values without forwarding it to the mobility subsystem. |
| REQ-SF-01-04 | The system shall process command messages at a minimum rate of 10 Hz. |

### Acceptance Criteria

- [ ] A `geometry_msgs/Twist` message published to `/cmd_vel` results in rover motion matching the commanded direction within one control cycle.
- [ ] Withholding all `/cmd_vel` messages for 1.1 seconds causes the rover to stop and a watchdog flag to appear in `/diagnostics`.
- [ ] A message with `linear.x = NaN` is discarded; rover maintains previous motion intent (or standby if none).
- [ ] Command reception latency from Wi-Fi receipt to motor setpoint update is ≤ 100 ms at 10 Hz publish rate.

---

## SF-02 — Execute Mobility

### Description

SF-02 translates the verified motion intent from SF-01 into concrete actuator commands for all six drive motors and four corner steering servos. This function implements the kinematic model of the OSR's rocker-bogie suspension, which requires unequal wheel speeds during turns to prevent slip and ensure smooth traversal of uneven terrain.

The function has three sub-functions: computing per-wheel speed setpoints, commanding the drive motors, and positioning the steering servos.

**Execution steps:**

1. Receive (v_linear, v_angular) from SF-01.
2. SF-02.1: Apply rocker-bogie kinematics to derive six individual wheel speed setpoints.
3. SF-02.1: Apply Ackermann geometry to derive four corner servo angle setpoints.
4. SF-02.2: Transmit drive speed setpoints to motor controllers.
5. SF-02.3: Transmit steering angle setpoints to servo driver.
6. Enforce hardware limits (max RPM per wheel, max servo angle).

| Attribute | Value |
|---|---|
| **Inputs** | Motion intent (v_linear m/s, v_angular rad/s) from SF-01 |
| **Outputs** | Six drive wheel PWM speed setpoints; four servo angle setpoints |
| **Realizes** | OAct-01.2 Command Rover Motion |

### SF-02.1 — Compute Drive Commands

Converts linear and angular velocity into per-wheel speed setpoints using the rover's kinematic model. The rocker-bogie geometry requires that the outer wheels travel farther than the inner wheels during a turn, so each wheel receives an individual speed scaled to its turning radius.

- Applies differential drive model: `v_left = v - ω·W/2`, `v_right = v + ω·W/2` per side pair
- Applies Ackermann steering angles: `θ_front = atan(L / R_turn)` per corner
- Clamps final setpoints to configured maximum wheel RPM

### SF-02.2 — Drive Wheels

Sends computed speed setpoints to the three RoboClaw 2×15A motor controllers (one per wheel pair: front, middle, rear) via USB serial.

- Issues `SpeedM1M2` commands to each RoboClaw unit
- Confirms command acknowledgment; logs NACK events to fault monitor
- Applies an emergency zero-setpoint on receiving halt from SF-06

### SF-02.3 — Steer Corner Wheels

Positions the four corner wheel servo motors (via PCA9685 I²C servo driver) to achieve the commanded heading.

- Converts angular velocity to Ackermann front/rear steering angles
- Converts angles to servo PWM pulse widths (500–2500 µs range)
- Respects per-servo mechanical limits (±30° from centre)

### Requirements

| ID | Requirement |
|---|---|
| REQ-SF-02-01 | The system shall compute individual wheel speed setpoints using the OSR rocker-bogie kinematic model for all commanded (v, ω) pairs. |
| REQ-SF-02-02 | Drive wheel setpoints shall be updated at a minimum rate of 20 Hz. |
| REQ-SF-02-03 | The system shall clamp drive setpoints to the motor controller's rated maximum speed and shall not command speeds that exceed the physical limit. |
| REQ-SF-02-04 | The system shall position corner steering servos to Ackermann-correct angles within 250 ms of receiving a new angular velocity command. |
| REQ-SF-02-05 | Upon receiving a halt signal from SF-06, SF-02 shall set all drive motor setpoints to zero within one control cycle (≤ 50 ms). |

### Acceptance Criteria

- [ ] Commanding `v = 0.3 m/s, ω = 0` results in all six drive wheels spinning at equal speed within ±5%.
- [ ] Commanding `v = 0, ω = 0.5 rad/s` results in correct differential speed ratios between inner and outer wheel pairs, and steering servos positioned to Ackermann angles.
- [ ] Drive setpoints are updated at ≥ 20 Hz under normal operating conditions (verified via `/odom` publish rate).
- [ ] Corner servo positions are updated within 250 ms of a new angular velocity command.
- [ ] A halt signal from SF-06 causes all drive speeds to reach zero within 50 ms.

---

## SF-03 — Manage Power

### Description

SF-03 encompasses all power-related functions: distributing raw battery voltage to system consumers via regulated rails, continuously monitoring the battery state-of-charge, and protecting the system against electrical faults. The OSR uses a 3S LiPo battery (nominally 11.1 V, peak 12.6 V) as its sole power source, with DC-DC buck converters on the custom PCB generating regulated 5V (compute) and motor supply rails.

Power management is primarily implemented in hardware (buck converters, fuses), with software monitoring and cutoff logic running on the Raspberry Pi via the INA219 I²C power monitor.

**Execution steps:**

1. SF-03.1: PCB DC-DC converters provide regulated power on startup (passive/hardware).
2. SF-03.2: At 1 Hz, read battery terminal voltage and total current from INA219.
3. SF-03.2: Compute state-of-charge from LiPo voltage curve; publish to `/battery_state`.
4. SF-03.3: On each reading, compare current against overcurrent threshold; if exceeded, trigger SF-06.4.

| Attribute | Value |
|---|---|
| **Inputs** | Raw DC from 3S LiPo battery; load current demands from all subsystems |
| **Outputs** | Regulated 5V/12V to compute and motors; battery SoC% to telemetry |
| **Realizes** | OAct-02.1 Charge Battery (monitoring); OAct-01.3 Monitor Rover State |

### SF-03.1 — Distribute Electrical Power

The custom OSR PCB provides the power distribution function in hardware:

- Main power switch connects LiPo positive terminal to distribution bus
- Buck converters step down battery voltage to regulated rails:
  - **5V rail:** Raspberry Pi, PCA9685, sensors
  - **Motor supply rail (unregulated ~11.1V):** Three RoboClaw controllers
- Blade fuses on each major branch prevent wiring damage on short circuit
- Reverse-polarity protection diode on input

### SF-03.2 — Monitor Battery State

Software monitoring executed by the `power_node` process on the Raspberry Pi:

- Reads INA219 registers over I²C at 1 Hz
- Converts raw ADC counts to voltage (mV) and current (mA)
- Looks up SoC% on a pre-characterised LiPo discharge curve
- Publishes `sensor_msgs/BatteryState` to `/battery_state`

### SF-03.3 — Protect Against Overcurrent/Short

Hardware fuses provide first-line protection. Software provides secondary:

- `fault_node` subscribes to motor current readings published by `encoder_node`
- If any motor channel exceeds 10 A, the fault node triggers SF-06.4 (Safe Stop)
- PCB fuses rated for maximum combined load; blow before wiring reaches thermal limit

### Requirements

| ID | Requirement |
|---|---|
| REQ-SF-03-01 | The system shall provide regulated 5V ± 5% to the Raspberry Pi and logic-level peripherals at all times when the main power switch is on. |
| REQ-SF-03-02 | The system shall read and publish battery voltage and current at a minimum rate of 1 Hz. |
| REQ-SF-03-03 | The system shall compute and publish state-of-charge as a percentage derived from the LiPo discharge voltage curve. |
| REQ-SF-03-04 | The system shall trigger a safe stop (SF-06.4) when any monitored motor current exceeds 10 A. |
| REQ-SF-03-05 | The system shall publish a low-battery warning flag when battery voltage falls below 11.0 V. |
| REQ-SF-03-06 | The system shall trigger a safe stop when battery voltage falls below 10.5 V. |

### Acceptance Criteria

- [ ] Measure 5V rail with multimeter while rover is operating; reading is 4.75–5.25 V.
- [ ] `/battery_state` topic publishes at ≥ 1 Hz during normal operation (verify with `rostopic hz`).
- [ ] Forcing a motor stall condition causes fault node to publish a fault flag within one fault-check cycle (≤ 100 ms).
- [ ] Battery voltage below 11.0 V causes a warning entry in `/diagnostics` without stopping the rover.
- [ ] Battery voltage below 10.5 V causes rover to stop and fault flag to be set in `/diagnostics`.

---

## SF-04 — Process and Publish Telemetry

### Description

SF-04 collects raw sensor data from all onboard sensors, fuses the data to produce an estimated rover state, and publishes the result to the ground station via Wi-Fi. This function provides the operator with situational awareness of the rover's position, orientation, motion, power, and health in near-real-time.

Telemetry is the primary feedback loop for a human operator controlling the rover manually. Low-latency, high-fidelity state estimation enables safe operation in challenging terrain where the operator cannot directly observe the rover.

**Execution steps:**

1. SF-04.1: `encoder_node` reads RoboClaw encoder counts at 20 Hz.
2. SF-04.1: `imu_node` reads BNO055 IMU over I²C at 50 Hz.
3. SF-04.1: `encoder_node` reads motor current from RoboClaw at 20 Hz.
4. SF-04.2: Dead-reckoning integration of encoder ticks produces odometry pose.
5. SF-04.2: Complementary filter fuses accelerometer and gyroscope for attitude estimate.
6. SF-04.3: At 5 Hz, serialize all state data and publish ROS topics to Wi-Fi.

| Attribute | Value |
|---|---|
| **Inputs** | Encoder ticks (×6), IMU acceleration + gyroscope, motor currents |
| **Outputs** | `/odom`, `/imu`, `/battery_state`, `/motor_currents`, `/diagnostics` ROS topics |
| **Realizes** | OAct-01.3 Monitor Rover State |

### SF-04.1 — Sample Sensors

Periodic hardware reads executed by dedicated ROS nodes:

- **Encoders:** `encoder_node` issues `ReadEncM1M2` via USB serial to each RoboClaw at 20 Hz; returns tick count since last read
- **IMU:** `imu_node` reads BNO055 linear acceleration (m/s²) and angular velocity (rad/s) registers over I²C at 50 Hz; reads calibration status
- **Motor currents:** `encoder_node` reads `ReadCurrents` from RoboClaw simultaneously with encoder reads at 20 Hz

### SF-04.2 — Estimate Rover State

State estimation runs as part of `encoder_node` and `imu_node`:

- **Odometry:** `Δticks × (2π·r / ticks_per_rev)` → linear displacement per wheel; six-wheel average used for forward displacement; angular displacement from differential
- **Dead-reckoning pose:** Integrate odometry to maintain x, y, θ estimate; published as `nav_msgs/Odometry` on `/odom`
- **Attitude:** Complementary filter: `θ = α·(θ + gyro·dt) + (1-α)·accel_angle` with α = 0.98; provides roll, pitch, yaw at 50 Hz on `/imu` as `sensor_msgs/Imu`

### SF-04.3 — Transmit Telemetry

`telemetry_node` and individual sensor nodes publish at their configured rates:

- All ROS topics are bridged to the ground station via `rosbridge_server` (WebSocket) or direct ROS network (same ROS_MASTER_URI)
- Compressed image stream on `/camera/image_raw/compressed` if camera present
- `diagnostic_aggregator` collects individual diagnostics into `/diagnostics`

### Requirements

| ID | Requirement |
|---|---|
| REQ-SF-04-01 | The system shall sample wheel encoder counts at a minimum rate of 20 Hz per wheel. |
| REQ-SF-04-02 | The system shall sample IMU acceleration and gyroscope at a minimum rate of 50 Hz. |
| REQ-SF-04-03 | The system shall publish odometry (`/odom`) at a minimum rate of 10 Hz. |
| REQ-SF-04-04 | The system shall publish attitude (`/imu`) at a minimum rate of 20 Hz. |
| REQ-SF-04-05 | The system shall publish telemetry topics to the ground station at a minimum rate of 5 Hz. |
| REQ-SF-04-06 | Telemetry latency from sensor read to Wi-Fi transmission shall not exceed 200 ms. |

### Acceptance Criteria

- [ ] `rostopic hz /odom` reports ≥ 10 Hz during rover operation.
- [ ] `rostopic hz /imu` reports ≥ 20 Hz during rover operation.
- [ ] With rover stationary on a flat surface, `/imu` roll and pitch are within ±2° of zero.
- [ ] Driving the rover in a 1 m straight line and stopping; `/odom` reports forward displacement within ±10% of 1 m.
- [ ] Telemetry topics appear on ground station ROS subscriber within 200 ms of sensor read (measured end-to-end with `rosbag`).

---

## SF-05 — Capture and Stream Video

### Description

SF-05 provides real-time visual situational awareness to the operator by capturing video from an onboard camera and streaming it to the ground station. This is an optional function — it is active only when a camera is physically installed and the camera ROS node is launched.

The camera is mounted on the rover mast or body, providing a forward-facing view. The video stream allows the operator to detect obstacles, assess terrain, and confirm that the rover is behaving as commanded in environments where direct line-of-sight is not possible.

**Execution steps:**

1. `camera_node` opens camera device (`/dev/videoX` or CSI interface).
2. Captures frames at configured resolution and frame rate (typically 640×480 @ 30 fps).
3. Encodes frames to MJPEG (low-latency) or H.264 (higher compression) format.
4. Publishes encoded frames on `/camera/image_raw` (raw) and `/camera/image_raw/compressed` (compressed).
5. Ground station subscriber receives and decodes frames for display.

| Attribute | Value |
|---|---|
| **Inputs** | Camera sensor data (CSI or USB camera) |
| **Outputs** | Compressed video stream (MJPEG or H.264) on ROS topic |
| **Realizes** | OAct-01.5 Collect Sensor Data |
| **Availability** | Optional; enabled when camera hardware is present |

### Requirements

| ID | Requirement |
|---|---|
| REQ-SF-05-01 | When a camera is installed, the system shall capture and publish video at a minimum of 15 fps at 640×480 resolution. |
| REQ-SF-05-02 | The system shall publish compressed video on `/camera/image_raw/compressed` to reduce Wi-Fi bandwidth. |
| REQ-SF-05-03 | Video stream latency from frame capture to ground station display shall not exceed 500 ms over local Wi-Fi. |
| REQ-SF-05-04 | If the camera device is not present, the system shall start without error and SF-05 shall remain inactive without affecting other system functions. |

### Acceptance Criteria

- [ ] With camera installed, `rostopic hz /camera/image_raw/compressed` reports ≥ 15 Hz.
- [ ] Ground station video display shows live feed with visible latency ≤ 500 ms (assessed by waving hand in front of camera).
- [ ] System boot completes normally with camera hardware absent; no error messages related to SF-05.
- [ ] CPU load on RPi from camera node alone does not exceed 20% (verified via `htop`).

---

## SF-06 — Detect and Handle Faults

### Description

SF-06 provides the safety monitoring layer for the OSR. It continuously evaluates system health indicators against predefined thresholds and, when a fault condition is detected, executes a safe stop to halt all motion and alert the operator. Faults are latching — the rover remains stopped until the operator explicitly acknowledges and clears the fault.

This function is critical for preventing hardware damage (motor burnout, battery deep-discharge) and physical hazards (rover tipping, collision). It is the primary means by which the system responds autonomously to unsafe conditions without operator intervention.

**Execution steps:**

1. SF-06.1: At 10 Hz, read per-channel motor currents from RoboClaw.
2. SF-06.2: At 1 Hz, read battery terminal voltage from INA219.
3. SF-06.3: At 10 Hz, read roll and pitch from IMU attitude estimate.
4. Compare each measurement against its threshold table.
5. On any threshold breach, classify fault severity (warning vs. critical).
6. On critical fault, invoke SF-06.4 (Execute Safe Stop).
7. Publish fault details to `/diagnostics` and latch fault flag.
8. Wait for operator clear command; verify condition resolved before resuming.

| Attribute | Value |
|---|---|
| **Inputs** | Motor current readings (per channel), battery voltage, IMU roll/pitch |
| **Outputs** | Fault flags (latched), safe-stop command to SF-02, fault event to `/diagnostics` |
| **Realizes** | OAct-01.4 Respond to Hazard |

### SF-06.1 — Monitor Motor Currents

The `fault_node` subscribes to motor current data published by `encoder_node`. Each RoboClaw reports per-channel current in milliamps.

**Threshold:** Any motor channel exceeding **10 A** triggers an immediate critical fault.

- High continuous current indicates mechanical obstruction, stall condition, or motor failure
- Current spike above 10 A sustained for > 100 ms is treated as a critical fault
- Per-channel monitoring catches single-motor faults that a total-current sensor would miss

### SF-06.2 — Monitor Battery Voltage

The `fault_node` subscribes to `/battery_state` published by `power_node`.

| Level | Voltage Threshold | Action |
|---|---|---|
| Warning | < 11.0 V | Publish warning flag; continue operation |
| Critical | < 10.5 V | Execute safe stop; publish critical fault |

- A 3S LiPo should not be discharged below 3.0 V/cell (9.0 V) to avoid permanent damage; 10.5 V provides safety margin
- Voltage sag under high current draw can cause false warnings; hysteresis of 0.2 V applied before clearing a warning

### SF-06.3 — Detect Tip Risk (IMU)

The `fault_node` subscribes to `/imu` and monitors BNO055-reported roll and pitch angles.

**Threshold:** Roll or pitch exceeding **±35°** triggers an immediate critical fault.

- The OSR rocker-bogie can traverse ≈ 45° slopes; 35° threshold provides margin for dynamic effects
- If the rover is about to tip, halting motors prevents the tip-over from being driven into
- IMU must be calibrated before threshold monitoring is reliable; calibration status checked at startup

### SF-06.4 — Execute Safe Stop

Invoked by any critical fault condition (SF-06.1, SF-06.2, SF-06.3, or watchdog timeout from SF-01):

1. Immediately publish `Twist(0, 0)` to `/cmd_vel_safe` (overrides normal command path).
2. Send zero-speed `SpeedM1M2(0, 0)` directly to all three RoboClaw units via serial.
3. Publish fault classification and timestamp to `/diagnostics`.
4. Set latched fault flag; block SF-01 from forwarding new motion commands.
5. Await operator `clear_fault` service call; verify fault condition no longer present.
6. Clear latch and resume normal command forwarding.

### Requirements

| ID | Requirement |
|---|---|
| REQ-SF-06-01 | The system shall monitor each motor channel current at a minimum rate of 10 Hz. |
| REQ-SF-06-02 | The system shall trigger a safe stop within 100 ms of any motor channel current exceeding 10 A. |
| REQ-SF-06-03 | The system shall publish a battery warning when voltage falls below 11.0 V and trigger a safe stop when voltage falls below 10.5 V. |
| REQ-SF-06-04 | The system shall monitor rover roll and pitch at a minimum rate of 10 Hz. |
| REQ-SF-06-05 | The system shall trigger a safe stop within 100 ms of roll or pitch exceeding 35°. |
| REQ-SF-06-06 | Upon safe stop, the system shall set all drive motor setpoints to zero and publish the fault event to `/diagnostics`. |
| REQ-SF-06-07 | The safe stop condition shall latch; the rover shall not resume motion until an operator-issued clear command is received and the fault condition is verified to have cleared. |

### Acceptance Criteria

- [ ] Manually commanding a motor to stall (block wheel by hand) causes `fault_node` to publish an overcurrent fault within 100 ms and halt all motors.
- [ ] Battery voltage injected below 11.0 V (simulated via modified `battery_state` message) causes a warning entry in `/diagnostics` without halting motors.
- [ ] Battery voltage injected below 10.5 V causes rover safe stop and fault flag in `/diagnostics`.
- [ ] Tilting the rover to > 35° causes safe stop within 100 ms.
- [ ] After safe stop, publishing a valid `/cmd_vel` does not cause rover to move until `clear_fault` service is called.
- [ ] `clear_fault` service call while fault condition still active does not clear the latch; latch clears only after condition is resolved.

---

## SF-07 — Support Payload Interface

### Description

SF-07 allows the OSR to carry and power optional scientific or custom payload devices. The system provides both electrical power (switched 5V and 12V rails from the PCB) and data connectivity (USB, I²C, UART) to payload devices, enabling the rover to act as a mobile platform for user-defined experiments or instruments.

The payload interface is intentionally generic: the OSR hardware and software provide the connection points, but the payload itself defines what data it produces and what power it needs.

**Execution steps:**

1. SF-07.1: Operator or autonomous command enables the payload power load switch via GPIO.
2. SF-07.1: `power_node` monitors payload rail current via INA219 channel; disables power if current exceeds allocation.
3. SF-07.2: Payload device connects to RPi USB port, I²C bus, or UART header.
4. SF-07.2: Payload data arrives on RPi as a device file or ROS topic (user-configured).
5. SF-07.2: Data is passed through to ground station via the normal telemetry path (LC-01/SF-04.3).

| Attribute | Value |
|---|---|
| **Inputs** | Payload power enable request; payload data output (USB/I²C/UART) |
| **Outputs** | Switched 5V/12V power; routed data bus to Raspberry Pi |
| **Realizes** | OAct-04.2 Integrate Payload |

### SF-07.1 — Provide Power to Payload

- Custom PCB includes a GPIO-controlled load switch for the payload power rail
- RPi GPIO pin toggles the switch on/off; default state is off (unpowered at boot)
- INA219 monitors payload current at 1 Hz; software cutoff at configurable limit (default 2 A)
- Supported rails: 5V @ 2 A, 12V (battery-direct) @ 2 A

### SF-07.2 — Route Payload Data

- Physical connectors on the PCB/body expose USB-A, I²C header (3.3V), and UART header
- RPi acts as USB host; payload USB devices enumerate as standard Linux devices
- Payload I²C devices join the main I²C bus (ensure no address conflict with onboard sensors)
- User-provided ROS node or script reads payload data and publishes to a ROS topic for telemetry forwarding

### Requirements

| ID | Requirement |
|---|---|
| REQ-SF-07-01 | The system shall provide switchable 5V @ ≥ 2 A and 12V @ ≥ 2 A power rails to the payload connector. |
| REQ-SF-07-02 | The system shall monitor payload power rail current and disable the rail if current exceeds the configured limit (default 2 A). |
| REQ-SF-07-03 | The system shall provide USB, I²C, and UART connectivity to payload devices from the Raspberry Pi. |
| REQ-SF-07-04 | Payload power enable and disable shall be controllable via software (GPIO) without requiring hardware intervention. |
| REQ-SF-07-05 | Payload power rail switching shall not interrupt or reset any other system power rail. |

### Acceptance Criteria

- [ ] GPIO-toggling the payload enable pin causes the payload connector to energize/de-energize (verified with multimeter).
- [ ] Connecting a 2 A resistive load to payload rail causes no voltage sag on 5V logic rail (< 0.1 V droop).
- [ ] Connecting a load drawing > 2 A causes `power_node` to disable the payload rail within one monitoring cycle (≤ 1 s) and publish an entry in `/diagnostics`.
- [ ] USB device connected to payload USB-A port enumerates in `lsusb` within 5 seconds.
- [ ] Payload power toggle does not reset the Raspberry Pi or any other running ROS node.

---

## Function-to-Operational-Activity Traceability

| System Function | Realized Operational Activity | OA Stakeholder |
|---|---|---|
| SF-01 | OAct-01.2 Command Rover Motion | Operator (SH-01) |
| SF-02 | OAct-01.2 Command Rover Motion | Operator (SH-01) |
| SF-03 | OAct-02.1 Charge Battery, OAct-01.3 Monitor Rover State | Operator (SH-01), Safety Officer (SH-03) |
| SF-04 | OAct-01.3 Monitor Rover State | Operator (SH-01), Scientist (SH-02) |
| SF-05 | OAct-01.5 Collect Sensor Data | Scientist (SH-02), Operator (SH-01) |
| SF-06 | OAct-01.4 Respond to Hazard | Safety Officer (SH-03), Operator (SH-01) |
| SF-07 | OAct-04.2 Integrate Payload | Scientist (SH-02), Engineer (SH-04) |
