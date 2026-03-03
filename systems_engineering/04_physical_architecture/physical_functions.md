# Physical Functions

**PA Layer — Physical Function Deployment**

Physical Functions (PFs) refine Logical Functions and deploy them onto specific Physical Components. This layer specifies which processor, microcontroller, or hardware circuit executes each function, along with timing constraints, implementation technology, and verification criteria.

---

## PF-01 — Command Reception and Validation

**Description:** All software associated with receiving motion commands from the operator and validating them before forwarding to the drive chain. These functions execute on the Raspberry Pi 4B (`PC-COMP-01`) as part of `command_node`, which subscribes to the `/cmd_vel` ROS topic and enforces the command watchdog and velocity limits.

PF-01 is the first stage of the control chain and sets the cadence for all downstream motion updates. The node runs at 10 Hz, which is sufficient for human-operated teleoperation; higher update rates provide diminishing returns given wireless latency.

| PF ID | Physical Function | Parent LF | Deployed on PC | Technology |
|---|---|---|---|---|
| PF-01.1 | Subscribe to `/cmd_vel` ROS topic | LF-01.1 | PC-COMP-01 RPi | ROS Noetic subscriber node |
| PF-01.2 | Validate twist message fields (NaN/Inf check) | LF-01.2 | PC-COMP-01 RPi | Python `math.isfinite()` |
| PF-01.3 | Clamp velocity to configured limits | LF-01.3 | PC-COMP-01 RPi | Python `numpy.clip` |
| PF-01.4 | Watchdog timer on `/cmd_vel` (1 s timeout) | LF-01.4 | PC-COMP-01 RPi | ROS `rospy.Timer` callback |

### Requirements

| ID | Requirement |
|---|---|
| REQ-PF-01-01 | `command_node` shall subscribe to `/cmd_vel` and process incoming messages at a minimum rate of 10 Hz. |
| REQ-PF-01-02 | The watchdog timer shall trigger within 1.0–1.1 s of the last received message. |
| REQ-PF-01-03 | Velocity clamping shall apply `numpy.clip(v, -v_max, v_max)` to both linear and angular components before forwarding. |

### Acceptance Criteria

- [ ] `rostopic hz /cmd_vel` on the rover shows ≥ 10 Hz when ground station publishes at 10 Hz.
- [ ] Stopping ground station publications for 1.1 s triggers watchdog; `/diagnostics` shows watchdog event.
- [ ] Publishing `linear.x = 2.0 m/s` results in `command_node` forwarding ≤ `v_max` (default 0.4 m/s) to drive chain.

---

## PF-02 — Kinematics and Actuator Drive

**Description:** All software and hardware involved in translating velocity commands into physical motion: kinematic computations on the Raspberry Pi and actuator commands transmitted to motor controllers and servo drivers.

`drive_node` runs at 20 Hz on the RPi. It reads the most recent validated velocity command from `command_node`, applies the rocker-bogie kinematic model, and issues speed setpoints to the three RoboClaw 2×15A motor controllers over USB serial. Simultaneously, it computes Ackermann steering angles and writes them to the PCA9685 PWM servo driver via I²C.

The three RoboClaw units are addressed as separate USB serial devices (typically `/dev/ttyACM0`, `/dev/ttyACM1`, `/dev/ttyACM2`). Each controls one left-right wheel pair.

| PF ID | Physical Function | Parent LF | Deployed on PC | Technology |
|---|---|---|---|---|
| PF-02.1 | Rocker-bogie differential drive kinematics | LF-02.1 | PC-COMP-01 RPi | Python matrix solve |
| PF-02.2 | Ackermann corner angle computation | LF-02.2 | PC-COMP-01 RPi | Python trigonometry |
| PF-02.3 | Write motor setpoint to RoboClaw via USB serial | LF-02.3 | PC-COMP-01 RPi → PC-MCTL-01 | `roboclaw` Python library |
| PF-02.4 | Write angle setpoint to PCA9685 via I²C | LF-02.4 | PC-COMP-01 RPi → PC-MCTL-02 | `adafruit_servokit` library |

### Requirements

| ID | Requirement |
|---|---|
| REQ-PF-02-01 | `drive_node` shall compute and transmit wheel speed setpoints to all three RoboClaw units at a minimum rate of 20 Hz. |
| REQ-PF-02-02 | `drive_node` shall update PCA9685 servo angle setpoints within 250 ms of any change in commanded angular velocity. |
| REQ-PF-02-03 | Motor setpoints shall be clamped to the maximum rated speed of the drive motors; the `roboclaw` library call shall never receive an out-of-range value. |
| REQ-PF-02-04 | Servo angle setpoints shall be clamped to the mechanical range of motion (±30° from centre). |
| REQ-PF-02-05 | Communication failure to any RoboClaw unit (NACK or serial timeout) shall be logged to `/diagnostics` within one cycle. |

### Acceptance Criteria

- [ ] `drive_node` ROS loop confirmed at ≥ 20 Hz via `rostopic hz /commanded_vel`.
- [ ] Straight-line command produces equal setpoints on all RoboClaw units (verified via serial traffic dump).
- [ ] Turn command produces differential setpoints matching kinematic model (inner < outer wheel speed).
- [ ] Servo positions measured with protractor during turn match Ackermann angle within ±3°.
- [ ] Disconnecting one RoboClaw USB cable causes NACK log entry in `/diagnostics` without crashing `drive_node`.

---

## PF-03 — Power Monitoring and Distribution

**Description:** Power management combines passive hardware functions (DC-DC conversion, fuse protection) on the custom OSR PCB (`PC-PCB-01`) with active software monitoring on the Raspberry Pi via the INA219 I²C power monitor IC.

The PCB buck converters operate continuously without RPi intervention. The RPi `power_node` reads INA219 telemetry at 1 Hz and publishes to `/battery_state`. Software overcurrent cutoff is implemented in `fault_node` (see PF-05), which subscribes to motor current readings.

| PF ID | Physical Function | Parent LF | Deployed on PC | Technology |
|---|---|---|---|---|
| PF-03.1 | Read INA219 battery voltage over I²C | LF-03.1 | PC-PCB-01 + PC-COMP-01 | INA219 Python driver |
| PF-03.2 | Compute LiPo state-of-charge from voltage curve | LF-03.2 | PC-COMP-01 RPi | Python lookup table |
| PF-03.3 | PCB DC-DC converter regulation (5V, motor rail) | LF-03.3 | PC-PCB-01 | Hardware buck converter |
| PF-03.4 | Software overcurrent cutoff via motor disable | LF-03.4 | PC-COMP-01 RPi | ROS `fault_node` |

### Requirements

| ID | Requirement |
|---|---|
| REQ-PF-03-01 | `power_node` shall read INA219 battery voltage and current over I²C at a minimum rate of 1 Hz. |
| REQ-PF-03-02 | INA219 voltage measurement shall be accurate to ±0.1 V versus a calibrated multimeter reference. |
| REQ-PF-03-03 | PCB DC-DC converter shall maintain 5V rail within ±5% (4.75–5.25 V) under full system load. |
| REQ-PF-03-04 | `power_node` shall publish `sensor_msgs/BatteryState` to `/battery_state` at ≥ 1 Hz. |
| REQ-PF-03-05 | LiPo SoC lookup shall map ≥ 12.6 V → 100% and ≤ 10.5 V → 0%, with monotonic interpolation between. |

### Acceptance Criteria

- [ ] `rostopic hz /battery_state` reports ≥ 1 Hz during operation.
- [ ] Multimeter reading at battery terminals matches `/battery_state.voltage` within ±0.1 V.
- [ ] 5V rail measured under full motor load remains 4.75–5.25 V.
- [ ] Fully charged battery (12.6 V) causes `/battery_state.percentage` ≥ 0.95.
- [ ] I²C bus scan (`i2cdetect -y 1`) shows INA219 at expected address (0x40 or 0x41).

---

## PF-04 — Sensor Sampling and State Estimation

**Description:** Sensor reading and state estimation are distributed across two dedicated ROS nodes running on the Raspberry Pi: `encoder_node` (reads RoboClaw encoders and motor currents at 20 Hz over USB serial) and `imu_node` (reads BNO055 IMU at 50 Hz over I²C).

Dead-reckoning odometry is integrated inside `encoder_node` at each encoder read cycle. The complementary attitude filter runs inside `imu_node` at the IMU sample rate. Both nodes publish their results immediately upon computation, so downstream consumers (telemetry, fault monitor) see the freshest available data.

| PF ID | Physical Function | Parent LF | Deployed on PC | Technology |
|---|---|---|---|---|
| PF-04.1 | Read RoboClaw encoder counts via USB serial | LF-04.1 | PC-COMP-01 RPi ← PC-MCTL-01 | `roboclaw` Python library |
| PF-04.2 | Read BNO055 / MPU-6050 IMU via I²C | LF-04.2 | PC-COMP-01 RPi ← PC-SENS-01 | IMU Python driver |
| PF-04.3 | Read motor currents from RoboClaw via serial | LF-04.3 | PC-COMP-01 RPi ← PC-MCTL-01 | `roboclaw` library |
| PF-04.4 | Integrate wheel ticks to odometry (dead-reckoning) | LF-04.4 | PC-COMP-01 RPi | Python dead-reckoning |
| PF-04.5 | Complementary filter for attitude (roll, pitch, yaw) | LF-04.5 | PC-COMP-01 RPi | Python filter (α = 0.98) |
| PF-04.6 | Publish ROS telemetry topics (`/odom`, `/imu`) | LF-04.6 | PC-COMP-01 RPi | ROS publishers |

### Requirements

| ID | Requirement |
|---|---|
| REQ-PF-04-01 | `encoder_node` shall read encoder counts from all six wheels via RoboClaw USB serial at ≥ 20 Hz. |
| REQ-PF-04-02 | `imu_node` shall read BNO055 linear acceleration and angular velocity via I²C at ≥ 50 Hz. |
| REQ-PF-04-03 | `encoder_node` shall read per-channel motor currents at ≥ 10 Hz from each RoboClaw unit. |
| REQ-PF-04-04 | `/odom` shall be published at ≥ 10 Hz with position derived from integrated encoder ticks. |
| REQ-PF-04-05 | `/imu` shall be published at ≥ 20 Hz with orientation derived from complementary filter output. |
| REQ-PF-04-06 | Odometry shall report forward displacement within ±10% of true distance over a 1 m flat-surface test. |
| REQ-PF-04-07 | BNO055 shall report calibration status System ≥ 2 before IMU data is used by the fault monitor. |

### Acceptance Criteria

- [ ] `rostopic hz /odom` reports ≥ 10 Hz during rover motion.
- [ ] `rostopic hz /imu` reports ≥ 20 Hz during rover motion.
- [ ] Motor current topic (`/motor_currents`) publishes at ≥ 10 Hz.
- [ ] 1 m straight-line test: `/odom` final x position is 0.90–1.10 m.
- [ ] Rover on level surface: `/imu` roll and pitch within ±2° of zero.
- [ ] BNO055 calibration status confirmed System: 3 via calibration topic before operation (or after < 30 s of figure-eight motion for calibration).

---

## PF-05 — Fault Detection and Safe Stop

**Description:** `fault_node` is the dedicated ROS node for real-time safety monitoring. It subscribes to motor current, battery voltage, and IMU topics and evaluates them against the fault threshold table at 10 Hz. Upon detecting any critical fault, it publishes a direct stop command to all RoboClaw units via USB serial and publishes a `diagnostic_msgs/DiagnosticArray` fault event.

The safe stop command bypasses the normal command chain: `fault_node` writes directly to the RoboClaw serial interface, ensuring zero motor speed is achieved even if `drive_node` or `command_node` is in a bad state.

| PF ID | Physical Function | Parent LF | Deployed on PC | Technology |
|---|---|---|---|---|
| PF-05.1 | Monitor current thresholds per motor channel | LF-05.1 | PC-COMP-01 RPi | ROS subscriber (`/motor_currents`) |
| PF-05.2 | Monitor battery voltage threshold | LF-05.2 | PC-COMP-01 RPi | ROS subscriber (`/battery_state`) |
| PF-05.3 | Monitor IMU roll/pitch threshold | LF-05.3 | PC-COMP-01 RPi | ROS subscriber (`/imu`) |
| PF-05.4 | Set all motor setpoints to zero (safe stop) | LF-05.4 | PC-COMP-01 RPi → PC-MCTL-01 | Direct RoboClaw `SpeedM1M2(0,0)` |
| PF-05.5 | Publish `/diagnostics` fault message | LF-05.5 | PC-COMP-01 RPi | `diagnostic_msgs/DiagnosticArray` |

### Requirements

| ID | Requirement |
|---|---|
| REQ-PF-05-01 | `fault_node` shall evaluate motor current thresholds within 100 ms of any channel exceeding 10 A. |
| REQ-PF-05-02 | `fault_node` shall evaluate battery voltage thresholds within one monitoring cycle (≤ 1 s) of voltage crossing 10.5 V. |
| REQ-PF-05-03 | `fault_node` shall evaluate IMU tilt threshold within 100 ms of roll or pitch exceeding 35°. |
| REQ-PF-05-04 | On safe stop trigger, `fault_node` shall transmit `SpeedM1M2(0, 0)` to all three RoboClaw units via USB serial within 50 ms. |
| REQ-PF-05-05 | `fault_node` shall publish a `DiagnosticStatus` message with severity ERROR and a description to `/diagnostics` within one monitoring cycle of fault detection. |
| REQ-PF-05-06 | Safe stop shall latch; `fault_node` shall block command forwarding until `clear_fault` service is called and condition resolved. |

### Acceptance Criteria

- [ ] Simulating overcurrent (> 10 A on any channel via test message) causes `fault_node` to transmit stop to RoboClaw within 100 ms.
- [ ] `/diagnostics` shows `ERROR` level entry within one cycle of fault trigger.
- [ ] Rover physically stops within 50 ms of `fault_node` transmitting safe stop command (observed by wheel motion cessation).
- [ ] Publishing valid `/cmd_vel` after fault does not restart motion; command is blocked until `clear_fault` service is called.
- [ ] `clear_fault` while fault condition still active returns error and does not clear latch.

---

## PF-06 — Camera Capture and Streaming

**Description:** `camera_node` uses `cv2` or `raspicam_node` to interface with the Raspberry Pi Camera Module (CSI) or a USB webcam. It captures frames, optionally compresses them (MJPEG at ≈ 70% quality for bandwidth efficiency), and publishes to the ROS image transport layer. This function is optional and will not execute if no camera device is detected.

Streaming video over Wi-Fi consumes significant bandwidth. At 640×480 MJPEG 30 fps, approximate bandwidth is 2–5 Mbps, which is well within 802.11n Wi-Fi capacity at short range but may cause issues at longer distances. Frame rate can be reduced to 15 fps or resolution lowered to 320×240 if bandwidth is constrained.

| PF ID | Physical Function | Parent LF | Deployed on PC | Technology |
|---|---|---|---|---|
| PF-06.1 | Capture frames from camera module | LF-06.1 | PC-COMP-01 RPi ← PC-CAM-01 | `cv2.VideoCapture` / `raspicam_node` |
| PF-06.2 | Compress and publish video over Wi-Fi | LF-06.2 | PC-COMP-01 RPi | MJPEG via `image_transport` |

### Requirements

| ID | Requirement |
|---|---|
| REQ-PF-06-01 | `camera_node` shall capture frames at ≥ 15 fps at 640×480 resolution when camera hardware is present. |
| REQ-PF-06-02 | Compressed frames shall be published on `/camera/image_raw/compressed` using MJPEG encoding. |
| REQ-PF-06-03 | End-to-end video latency (capture to display on ground station) shall not exceed 500 ms over local Wi-Fi. |
| REQ-PF-06-04 | If no camera device is present at launch, `camera_node` shall exit gracefully without causing other nodes to fail. |
| REQ-PF-06-05 | CPU usage by `camera_node` shall not exceed 20% of one RPi core during 640×480 @ 30 fps streaming. |

### Acceptance Criteria

- [ ] `rostopic hz /camera/image_raw/compressed` reports ≥ 15 Hz when camera is connected.
- [ ] Ground station displays live video with latency ≤ 500 ms (assessed by clapping hands in front of camera and comparing audio/video timing).
- [ ] System launches without camera present; all other ROS nodes start and operate normally.
- [ ] `htop` shows `camera_node` consuming ≤ 20% CPU on one core during active streaming.

---

## PF-07 — Payload Interface

**Description:** Payload power is controlled by a GPIO pin on the Raspberry Pi that drives a load switch transistor on the custom OSR PCB. The RPi GPIO is toggled by `power_node` or by direct operator command. Payload current is measured by a dedicated INA219 channel on the PCB and read by `power_node` at 1 Hz.

Physical data connectivity to the payload is passive hardware routing on the PCB: traces connect the payload connector USB pins to the RPi USB hub, I²C header to the main I²C bus, and UART header to the RPi UART pins. No software mediation is needed for data routing beyond any user-supplied ROS driver for the specific payload.

| PF ID | Physical Function | Parent LF | Deployed on PC | Technology |
|---|---|---|---|---|
| PF-07.1 | Toggle PCB load switch for payload power | LF-07.1 | PC-PCB-01 + RPi GPIO | GPIO `RPi.GPIO` output |
| PF-07.2 | Read payload rail current via INA219 | LF-07.2 | PC-PCB-01 + PC-COMP-01 | INA219 driver |
| PF-07.3 | Pass-through USB/I²C/UART to RPi bus | LF-07.3 | PC-PCB-01 | Hardware PCB traces |

### Requirements

| ID | Requirement |
|---|---|
| REQ-PF-07-01 | RPi GPIO toggle of payload load switch shall energise/de-energise the payload connector within 10 ms. |
| REQ-PF-07-02 | `power_node` shall read payload current via INA219 at ≥ 1 Hz and disable payload power if current exceeds 2 A. |
| REQ-PF-07-03 | USB device connected to payload USB-A connector shall enumerate on RPi within 5 s of connection. |
| REQ-PF-07-04 | Payload I²C device at a non-conflicting address shall be detectable by `i2cdetect` on the RPi main I²C bus. |
| REQ-PF-07-05 | Payload power switching shall not cause voltage glitches > 0.2 V on the 5V logic rail. |

### Acceptance Criteria

- [ ] GPIO toggle causes payload connector voltage to change within 10 ms (measured with oscilloscope or multimeter).
- [ ] Payload drawing > 2 A causes `power_node` to disable payload rail within 1 s and publish fault to `/diagnostics`.
- [ ] USB device connected to payload port appears in `lsusb` within 5 s.
- [ ] I²C device at address not used by onboard sensors (e.g., 0x48) appears in `i2cdetect -y 1` output.
- [ ] Multimeter on 5V rail during payload power toggle shows < 0.2 V transient (< 5 ms).

---

## Software Execution Environment

All software PFs run on the Raspberry Pi 4B under:

```
OS:       Raspberry Pi OS (Debian Bullseye)
Kernel:   Linux 5.15 (ARM64)
Runtime:  Python 3.9 + ROS Noetic
ROS WS:   ~/osr_ws/
Launch:   roslaunch osr_bringup osr.launch
```

**Process architecture:**

```
rosmaster (ROS core)
  ├── command_node     (10 Hz)   ← /cmd_vel
  ├── drive_node       (20 Hz)   ← /commanded_vel → RoboClaw serial
  ├── encoder_node     (20 Hz)   ← RoboClaw serial → /odom
  ├── imu_node         (50 Hz)   ← I²C BNO055 → /imu
  ├── fault_node       (10 Hz)   ← /motor_currents, /battery_state, /imu
  ├── telemetry_node   (5 Hz)    → /diagnostics, /battery_state
  ├── camera_node      (30 Hz)   ← CSI/USB → /camera/image_raw  [optional]
  └── power_node       (1 Hz)    ← I²C INA219 → /battery_state
```

---

## Hardware Timing Constraints

| Function | Required Rate | Available Margin | Notes |
|---|---|---|---|
| Command reception | ≥ 10 Hz | ~40 Hz possible | Bounded by Wi-Fi latency |
| Drive PWM update | ≥ 20 Hz | RoboClaw supports 64 Hz | USB serial is bottleneck |
| IMU sampling | ≥ 50 Hz | BNO055 supports 100 Hz | I²C clock rate dependent |
| Encoder read | ≥ 20 Hz | RoboClaw encoder rate unlimited | Shared serial bus with drive |
| Fault check | ≥ 10 Hz | Limited by current sensor read rate | Safety-critical timing |
| Telemetry publish | ≥ 5 Hz | Wi-Fi bandwidth >> required | Aggregate diagnostic summary |
| Battery monitor | ≥ 1 Hz | Adequate for slow SoC changes | INA219 ADC conversion time |

---

## Physical Function to Logical Component Traceability

| PF Group | Physical Functions | Logical Component |
|---|---|---|
| PF-01 | PF-01.1 – PF-01.4 | LC-01, LC-02 |
| PF-02 | PF-02.1 – PF-02.4 | LC-03 |
| PF-03 | PF-03.1 – PF-03.4 | LC-06 |
| PF-04 | PF-04.1 – PF-04.6 | LC-04, LC-07 |
| PF-05 | PF-05.1 – PF-05.5 | LC-05 |
| PF-06 | PF-06.1 – PF-06.2 | LC-01, LC-07 |
| PF-07 | PF-07.1 – PF-07.3 | LC-08 |
