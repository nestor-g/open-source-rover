# Operational Activities

**OA Layer — Operational Activity Register**

Operational Activities (OActs) describe **what must be done** in the operational world — independent of how the system does it. Each activity is owned by an Operational Entity and may exchange data or artifacts with other activities.

## Activity Hierarchy

```
Root Operational Activity (OAct-00)
├── OAct-01  Conduct Rover Mission
│   ├── OAct-01.1  Plan Traverse Route
│   ├── OAct-01.2  Command Rover Motion
│   ├── OAct-01.3  Monitor Rover State
│   ├── OAct-01.4  Respond to Hazard
│   └── OAct-01.5  Collect Sensor Data
├── OAct-02  Maintain Rover
│   ├── OAct-02.1  Charge Battery
│   ├── OAct-02.2  Inspect and Repair Hardware
│   └── OAct-02.3  Update Software
├── OAct-03  Build Rover
│   ├── OAct-03.1  Source Components
│   ├── OAct-03.2  Assemble Mechanical Structure
│   ├── OAct-03.3  Install Electrical System
│   └── OAct-03.4  Install and Configure Software
└── OAct-04  Extend Rover Capability
    ├── OAct-04.1  Design Payload or Modification
    ├── OAct-04.2  Integrate Payload
    └── OAct-04.3  Develop Custom Software
```

---

## OAct-01 — Conduct Rover Mission

The core operational scenario: a human operator directs the rover through a terrain environment to accomplish a task (traverse, exploration, demonstration, data collection).

### OAct-01.1 — Plan Traverse Route

| Attribute | Detail |
|---|---|
| **Owner** | Ground Operator |
| **Inputs** | Terrain knowledge, mission objectives, rover capability limits |
| **Outputs** | Planned waypoints, go/no-go decision, hazard list |

**Description:** The operator assesses the terrain ahead of the rover and determines a safe path to traverse. This includes identifying obstacles that exceed the rover's mobility limits (height > ~75 mm, slope > 20°, loose substrate), selecting waypoints, and making a go/no-go decision before commanding motion.

**Requirements:**

| ID | Requirement |
|---|---|
| REQ-OA-011-01 | The operator shall assess visible terrain for obstacles before commanding motion into any new area. |
| REQ-OA-011-02 | The operator shall define a traverse path that avoids obstacles exceeding the rover's stated mobility limits. |
| REQ-OA-011-03 | A go/no-go decision shall be made and communicated before beginning each traverse segment. |

**Acceptance Criteria:**
- [ ] Operator can identify and verbally describe hazards from visual inspection of terrain
- [ ] Planned path avoids all obstacles taller than one wheel radius (~75 mm)
- [ ] Go/no-go decision is documented or verbally confirmed before traverse

---

### OAct-01.2 — Command Rover Motion

| Attribute | Detail |
|---|---|
| **Owner** | Ground Operator → Ground Station → OSR System |
| **Inputs** | Operator intent (gamepad axes/buttons) |
| **Outputs** | Motion commands (linear velocity, angular velocity) transmitted to rover |

**Description:** The operator translates intended rover motion into gamepad inputs. The ground station software encodes these into ROS `Twist` messages and transmits them over Wi-Fi. The rover decodes and executes the commanded velocity. The operator must account for the latency between input and rover response (≤ 200 ms nominal).

**Requirements:**

| ID | Requirement |
|---|---|
| REQ-OA-012-01 | The operator shall be able to command rover motion (forward, reverse, left turn, right turn, stop) using a single handheld controller. |
| REQ-OA-012-02 | Motion commands shall be transmitted wirelessly with a round-trip latency not exceeding 200 ms under nominal Wi-Fi conditions. |
| REQ-OA-012-03 | The rover shall come to a complete stop within 1 second of the operator releasing the motion command. |
| REQ-OA-012-04 | The rover shall execute a commanded stop within 1 second if the wireless link is lost. |

**Acceptance Criteria:**
- [ ] Operator issues forward command → rover moves forward within 200 ms
- [ ] Operator releases joystick → rover stops within 1 s
- [ ] Wi-Fi link interrupted → rover stops within 1 s (watchdog)
- [ ] Full range of motion (forward, reverse, left, right, spin) achievable from operator station

---

### OAct-01.3 — Monitor Rover State

| Attribute | Detail |
|---|---|
| **Owner** | Ground Operator |
| **Inputs** | Telemetry stream from rover (battery voltage, motor currents, wheel speeds, IMU orientation, fault flags) |
| **Outputs** | Situational awareness, anomaly detection, operator decisions |

**Description:** The operator continuously monitors the rover's health and position during the mission using the ground station display. Key indicators are battery state-of-charge, motor currents (identifying stall or slip), wheel odometry, IMU attitude, and any active fault flags. The operator uses this information to make real-time decisions about mission continuation.

**Requirements:**

| ID | Requirement |
|---|---|
| REQ-OA-013-01 | The operator shall receive rover telemetry updates at a rate of ≥ 5 Hz during active operation. |
| REQ-OA-013-02 | Battery state-of-charge shall be visible on the ground station display at all times during operation. |
| REQ-OA-013-03 | Any fault condition shall produce a visible alert on the ground station display within one telemetry cycle. |
| REQ-OA-013-04 | The operator shall be able to distinguish between normal and fault operating states from the ground station display alone. |

**Acceptance Criteria:**
- [ ] Ground station displays battery %, motor currents, wheel speeds, and orientation in real time
- [ ] Telemetry updates visible at ≥ 5 Hz (no more than 200 ms between refreshes)
- [ ] Simulated fault (e.g., overcurrent) produces visible alert within 200 ms
- [ ] Operator with no prior training can identify a fault state within 10 seconds of it occurring

---

### OAct-01.4 — Respond to Hazard

| Attribute | Detail |
|---|---|
| **Owner** | Ground Operator |
| **Inputs** | Hazard detection (visual observation or telemetry anomaly) |
| **Outputs** | Corrective commands (stop, reverse, re-route), fault acknowledgment |

**Description:** When the operator detects a hazard — a wheel stall, tip risk indicated by IMU attitude, approaching obstacle, or low battery critical threshold — they take corrective action. This includes issuing an immediate stop, reversing to free a stuck wheel, rerouting to avoid terrain, or returning the rover to base for battery swap. If the system has triggered an autonomous safe stop, the operator must acknowledge the fault before resuming operation.

**Requirements:**

| ID | Requirement |
|---|---|
| REQ-OA-014-01 | The operator shall issue a stop command within 3 seconds of recognising a hazard condition. |
| REQ-OA-014-02 | The operator shall acknowledge all system-generated fault events before resuming rover motion. |
| REQ-OA-014-03 | A clear recovery procedure shall exist for each fault type (overcurrent, tilt, low battery, link loss). |

**Acceptance Criteria:**
- [ ] Operator stops rover within 3 s of stall event being visible on display
- [ ] Rover cannot resume motion after autonomous safe stop until operator sends explicit clear command
- [ ] Recovery procedures documented and verified for each fault type listed in [SF-06](../02_system_analysis/system_functions.md#sf-06--detect-and-handle-faults)

---

### OAct-01.5 — Collect Sensor Data

| Attribute | Detail |
|---|---|
| **Owner** | Ground Operator / Developer |
| **Inputs** | Camera stream, optional payload sensor outputs |
| **Outputs** | Recorded images, logged telemetry, payload data files |

**Description:** During traverse, the operator or a co-located developer captures data from onboard sensors. At minimum this includes the camera video stream. With optional payloads installed, additional data (LIDAR scans, moisture readings, spectral data, etc.) may be logged to disk on the Raspberry Pi or streamed to the ground station. Logging is typically initiated at mission start and terminated at mission end.

**Requirements:**

| ID | Requirement |
|---|---|
| REQ-OA-015-01 | The rover shall stream live camera video to the ground station at ≥ 10 fps during operation. |
| REQ-OA-015-02 | All sensor data shall be time-stamped with the rover's system clock. |
| REQ-OA-015-03 | Collected data shall be accessible for download via SSH after mission completion. |

**Acceptance Criteria:**
- [ ] Camera stream visible on ground station at ≥ 10 fps
- [ ] ROS bag file recorded during mission contains all published topics with timestamps
- [ ] Data retrievable via `scp` over Wi-Fi after mission

---

## OAct-02 — Maintain Rover

### OAct-02.1 — Charge Battery

| Attribute | Detail |
|---|---|
| **Owner** | Builder / Operator |
| **Inputs** | Depleted 3S LiPo battery pack |
| **Outputs** | Fully charged battery (≥ 12.6 V), restored operational capacity |

**Description:** After operation, the battery pack must be charged using a LiPo balance charger before the next mission. The battery is removed from the rover (or charged in-situ if a charge port is installed), connected to the balance charger, and charged at ≤ 1C rate with balance leads connected. Charging must not be left unattended. A full charge cycle takes approximately 1–2 hours depending on depth of discharge.

**Requirements:**

| ID | Requirement |
|---|---|
| REQ-OA-021-01 | The battery shall be charged using a balance charger with cell-level voltage monitoring. |
| REQ-OA-021-02 | Charge rate shall not exceed 1C (≤ 5.2 A for a 5200 mAh pack). |
| REQ-OA-021-03 | Battery shall not be charged while installed in the rover unless a dedicated charge circuit with thermal monitoring is present. |
| REQ-OA-021-04 | A fully charged 3S LiPo shall measure ≥ 12.6 V (4.20 V per cell) at the pack terminals. |

**Acceptance Criteria:**
- [ ] Charger reports "full" or terminates current before reaching 12.6 V per-pack voltage
- [ ] All 3 cells balanced to within 0.05 V of each other at end of charge
- [ ] No swelling or heat above ambient + 20°C during charge
- [ ] Pack voltage remains ≥ 12.4 V 30 minutes after charge completion (no excessive self-discharge)

---

### OAct-02.2 — Inspect and Repair Hardware

| Attribute | Detail |
|---|---|
| **Owner** | Builder |
| **Inputs** | Post-mission rover, fault log, visual inspection |
| **Outputs** | Inspection report, repaired or replaced components, mission-ready rover |

**Description:** After each operating session, the builder performs a structured inspection of the rover's mechanical and electrical systems. This includes checking fastener tightness, joint articulation, wheel and tire condition, wiring integrity, and connector security. Any worn or damaged components are replaced before the next mission. Inspection should follow the checklist below.

**Inspection Checklist:**

| Item | Check | Pass Criterion |
|---|---|---|
| Wheel fasteners | Tighten and inspect | No loose fasteners; hub spins true |
| Rocker-bogie joints | Articulate through full range | No binding; smooth pivot |
| Wiring harness | Visual inspection | No chafed insulation; all connectors seated |
| Motor shafts | Check for axial play | < 1 mm axial play per wheel |
| Corner steering servos | Command full range | Reaches ±30° without binding |
| PCB and connectors | Visual and touch check | No burn marks; all terminals secure |
| Battery connector | Inspect XT60 contacts | No arcing marks; positive retention |

**Requirements:**

| ID | Requirement |
|---|---|
| REQ-OA-022-01 | A hardware inspection shall be performed after every operating session involving terrain traverse. |
| REQ-OA-022-02 | Any fastener found loose during inspection shall be re-torqued before the next mission. |
| REQ-OA-022-03 | Worn or damaged components shall be replaced before the rover is returned to service. |

**Acceptance Criteria:**
- [ ] All checklist items pass after inspection
- [ ] No loose fasteners found after applying specified torque
- [ ] Rocker-bogie articulates full range with < 2 N·m manual effort

---

### OAct-02.3 — Update Software

| Attribute | Detail |
|---|---|
| **Owner** | Developer |
| **Inputs** | Updated software version, SSH access to rover |
| **Outputs** | Deployed and verified updated software; updated rover |

**Description:** The developer connects to the Raspberry Pi via SSH over Wi-Fi and pulls the latest software from the git repository. After building the updated ROS workspace, the developer restarts the ROS launch file and verifies that all nodes are running and publishing expected topics. A smoke-test traverse is performed to confirm functionality has not regressed.

**Requirements:**

| ID | Requirement |
|---|---|
| REQ-OA-023-01 | Software updates shall be deployed via SSH over the rover's Wi-Fi interface without requiring physical disassembly. |
| REQ-OA-023-02 | After any software update, all ROS nodes shall be verified as running before returning the rover to operational service. |
| REQ-OA-023-03 | A post-update functional test shall include at minimum a commanded forward motion of ≥ 0.5 m and a full stop. |

**Acceptance Criteria:**
- [ ] `git pull` + `catkin_make` completes without errors
- [ ] `roslaunch osr_bringup osr.launch` starts all expected nodes
- [ ] `rostopic list` shows all required topics
- [ ] Rover responds to `/cmd_vel` command with visible wheel motion

---

## OAct-03 — Build Rover

### OAct-03.1 — Source Components

| Attribute | Detail |
|---|---|
| **Owner** | Builder |
| **Inputs** | Bill of Materials (BOM) from [configuration_items.md](../05_epbs/configuration_items.md), budget |
| **Outputs** | Complete procured parts kit, ready for assembly |

**Description:** The builder reviews the complete BOM and sources all components from the listed suppliers. Components include mechanical hardware (aluminum extrusion, plate, fasteners, bearings), electronics (Raspberry Pi, RoboClaw controllers, PCB, IMU, camera, servos), power (LiPo battery, charger), and consumables (wire, connectors, heat shrink). The builder verifies received items against the BOM before beginning assembly.

**Requirements:**

| ID | Requirement |
|---|---|
| REQ-OA-031-01 | All sourced components shall meet or exceed the specifications listed in the BOM. |
| REQ-OA-031-02 | The builder shall verify received quantities against the BOM before beginning assembly. |
| REQ-OA-031-03 | Substituted components not listed in the BOM shall be verified compatible with adjacent interfaces before use. |

**Acceptance Criteria:**
- [ ] All BOM line items received and checked off
- [ ] No items with visible damage accepted into kit
- [ ] Substitute parts (if any) documented with justification

---

### OAct-03.2 — Assemble Mechanical Structure

| Attribute | Detail |
|---|---|
| **Owner** | Builder |
| **Inputs** | Procured mechanical parts, assembly instructions, standard hand tools |
| **Outputs** | Assembled chassis with rocker-bogie suspension and six wheel modules |

**Description:** The builder follows the step-by-step assembly guide to construct the rover body frame from aluminum extrusion and plate, attach the rocker-bogie suspension linkage with flanged bearings and shoulder screw pivots, mount the corner steering assemblies, and attach all six wheel modules. No welding or CNC machining is required. Assembly is performed with standard hand tools (Allen keys, open-end wrenches, screwdrivers). Each sub-assembly is verified before proceeding to the next.

**Step Sequence:**
1. Assemble body frame (top/bottom plates, side extrusion)
2. Assemble rocker arms (×2) with pivot bearings
3. Assemble bogie arms (×2) with pivot bearings
4. Mount rocker-bogie to body frame with differential bar
5. Assemble six wheel modules (motor + hub + tire)
6. Attach wheels to bogie/rocker arms
7. Install corner steering assemblies (×4)

**Requirements:**

| ID | Requirement |
|---|---|
| REQ-OA-032-01 | The mechanical assembly shall be completable using only standard hand tools (no welding, CNC, or press tools required). |
| REQ-OA-032-02 | All pivot joints shall use flanged bearings; no metal-on-metal pivoting joints are permitted. |
| REQ-OA-032-03 | All structural fasteners shall be tightened to finger-tight plus 1/4 turn unless a specific torque is specified. |
| REQ-OA-032-04 | The completed chassis shall support the rover's total mass without visible deflection. |

**Acceptance Criteria:**
- [ ] All six wheel modules installed and rotate freely
- [ ] Rocker-bogie articulates ±30° on each side with no binding
- [ ] Differential bar equalises rocker motion symmetrically
- [ ] No loose fasteners detectable by hand
- [ ] Rover stands unsupported on all six wheels on flat surface

---

### OAct-03.3 — Install Electrical System

| Attribute | Detail |
|---|---|
| **Owner** | Builder |
| **Inputs** | Electronics kit, wiring harness, wiring diagrams |
| **Outputs** | Fully wired and powered electrical system, verified by continuity and power-on test |

**Description:** The builder mounts the custom OSR PCB inside the body enclosure, installs the three RoboClaw motor controllers, connects the six drive motors and four steering servos per the wiring diagram, installs the IMU, camera, and battery monitor, and performs the initial power-on test. Wiring follows the documented harness guide with correct gauge wire for each circuit. All connections are verified before applying battery power.

**Step Sequence:**
1. Mount PCB and standoffs in body enclosure
2. Connect drive motors to RoboClaw terminals (×6)
3. Connect RoboClaw units to PCB power outputs
4. Connect RoboClaw USB cables to Raspberry Pi
5. Wire IMU (I²C) to Raspberry Pi GPIO
6. Wire PCA9685 servo driver (I²C) to Raspberry Pi GPIO
7. Connect servo PWM cables to PCA9685 outputs
8. Connect battery monitor (INA219) to PCB I²C bus
9. Install battery connector (XT60) and in-line fuse
10. Perform continuity check before first power-on
11. Apply battery power and verify all rails (5V, 12V)

**Requirements:**

| ID | Requirement |
|---|---|
| REQ-OA-033-01 | A continuity check shall be performed on all power rails before applying battery power for the first time. |
| REQ-OA-033-02 | Wire gauges shall meet or exceed the minimum specified in the harness guide for each circuit. |
| REQ-OA-033-03 | An in-line fuse (≤ 30 A) shall be installed between the battery and the PCB input. |
| REQ-OA-033-04 | All motor and servo connectors shall be secured with positive-retention connectors (no bare screw terminals for high-current paths). |

**Acceptance Criteria:**
- [ ] Continuity check passes (no shorts between positive and negative rails)
- [ ] 5V rail within 4.75–5.25 V under load
- [ ] 12V (battery voltage) present at all RoboClaw power inputs
- [ ] Each RoboClaw powers on (LED indicator active) after first power-on
- [ ] No smoke, burning smell, or components above ambient + 30°C after 60 s of idle power-on

---

### OAct-03.4 — Install and Configure Software

| Attribute | Detail |
|---|---|
| **Owner** | Developer / Builder |
| **Inputs** | Raspberry Pi + microSD, software repository, Wi-Fi network |
| **Outputs** | Operational rover with ROS running, wireless link established, first motion test passed |

**Description:** The developer flashes Raspberry Pi OS to the microSD card, configures Wi-Fi credentials, enables SSH, and boots the Raspberry Pi. After confirming SSH access, they clone the OSR software repository, install ROS dependencies, build the ROS workspace, and configure the launch parameters (RoboClaw serial addresses, IMU I²C address, servo channel mapping). A first-motion test verifies end-to-end operation.

**Step Sequence:**
1. Flash Raspberry Pi OS (Bullseye 64-bit) to ≥ 32 GB microSD
2. Enable SSH and configure Wi-Fi SSID/password via `raspi-config` or `wpa_supplicant.conf`
3. Boot RPi; confirm SSH login (`ssh pi@rover.local`)
4. Install ROS Noetic (`ros-noetic-desktop`)
5. Clone OSR repo: `git clone https://github.com/nasa-jpl/osr-rover-code`
6. Run `pip install -r requirements.txt` and `catkin_make`
7. Configure RoboClaw addresses in `osr_params.yaml`
8. Launch: `roslaunch osr_bringup osr.launch`
9. Verify all ROS nodes running: `rosnode list`
10. Perform first motion test: send `/cmd_vel` via gamepad

**Requirements:**

| ID | Requirement |
|---|---|
| REQ-OA-034-01 | The software installation shall be completable by following the documented guide without prior ROS expertise. |
| REQ-OA-034-02 | All ROS nodes shall start without errors on first launch after fresh installation. |
| REQ-OA-034-03 | The rover shall respond to a `/cmd_vel` command within 5 minutes of completing software installation. |
| REQ-OA-034-04 | Wi-Fi connectivity shall be established and SSH access confirmed before launching ROS. |

**Acceptance Criteria:**
- [ ] `roslaunch osr_bringup osr.launch` starts without error output
- [ ] `rosnode list` shows all 7+ expected nodes
- [ ] `rostopic echo /battery_state` returns valid voltage reading
- [ ] Gamepad command produces visible wheel motion in all six wheels
- [ ] Corner servos move to commanded steering angle

---

## OAct-04 — Extend Rover Capability

### OAct-04.1 — Design Payload or Modification

| Attribute | Detail |
|---|---|
| **Owner** | Developer / Engineer Contributor |
| **Inputs** | Extension requirements, rover interface specifications ([physical interfaces](../04_physical_architecture/interfaces.md)), CAD files |
| **Outputs** | Payload design package (mechanical drawings, electrical schematic, software interface spec) |

**Description:** The contributor designs a new payload or rover modification to extend capability beyond the baseline (e.g., robotic arm, LIDAR, moisture sensor, solar panel). The design must respect the rover's published interface constraints: mechanical mounting (M3 bolt pattern on body top plate), electrical power limits (5V @ 2A, 12V @ 3A), and data interfaces (USB 2.0, I²C, UART). The design package must include sufficient detail for a builder to integrate the payload without modifying the rover's core systems.

**Requirements:**

| ID | Requirement |
|---|---|
| REQ-OA-041-01 | Payload designs shall not exceed the power budget allocations defined in [IF-05](../02_system_analysis/interfaces.md#if-05--payload-power-output). |
| REQ-OA-041-02 | Mechanical payload attachments shall use the standard M3 bolt pattern on the rover body plate without permanent modification to the chassis. |
| REQ-OA-041-03 | The design package shall include a defined data interface specifying the ROS topic name, message type, and update rate for any payload data stream. |
| REQ-OA-041-04 | Payload mass shall be documented; total rover mass with payload shall not exceed 10 kg. |

**Acceptance Criteria:**
- [ ] Design reviewed against all interface constraints before fabrication
- [ ] Power draw calculated and shown to be within budget
- [ ] Mechanical fit verified in CAD or by physical mockup before final build

---

### OAct-04.2 — Integrate Payload

| Attribute | Detail |
|---|---|
| **Owner** | Builder |
| **Inputs** | Payload hardware, rover with payload interface connectors, integration guide |
| **Outputs** | Rover with integrated and functional payload |

**Description:** The builder physically mounts the payload onto the rover body using the M3 bolt pattern, connects power from the switched payload rail on the PCB, connects the data interface (USB, I²C, or UART), and performs a power-on verification. The integration must not require permanent modification to the rover's structural frame, wiring harness, or PCB. Cable management must ensure no wires can contact rotating or articulating components.

**Requirements:**

| ID | Requirement |
|---|---|
| REQ-OA-042-01 | Payload integration shall not require removal or permanent modification of any baseline rover component. |
| REQ-OA-042-02 | All payload wiring shall be routed clear of rotating wheels, articulating suspension joints, and hot components. |
| REQ-OA-042-03 | Payload integration shall be reversible — the rover shall return to baseline configuration by removing the payload without tools beyond a standard Allen key set. |

**Acceptance Criteria:**
- [ ] Payload physically secured with ≥ 3 M3 fasteners; no movement under hand-shake test
- [ ] Payload power verified with multimeter at payload connector
- [ ] No payload wiring within 20 mm of any moving part
- [ ] Rover drives nominal M-01 traverse with payload installed without performance degradation

---

### OAct-04.3 — Develop Custom Software

| Attribute | Detail |
|---|---|
| **Owner** | Developer |
| **Inputs** | Payload data interface spec, ROS APIs, osr-rover-code repository |
| **Outputs** | Custom ROS node(s) packaged in the OSR ROS workspace; updated launch file |

**Description:** The developer writes one or more ROS nodes to interface with the payload hardware, process payload data, and publish results as ROS topics. Nodes should follow the existing OSR code patterns (Python, `rospy`, parameter server for configuration). The developer adds the new nodes to the `osr_bringup` launch file so they start automatically, and writes a README documenting the new topics, parameters, and any hardware dependencies.

**Requirements:**

| ID | Requirement |
|---|---|
| REQ-OA-043-01 | Custom ROS nodes shall be added to the OSR catkin workspace without modifying existing baseline nodes. |
| REQ-OA-043-02 | New ROS topics shall follow the OSR naming convention (`/osr/<subsystem>/<signal>`). |
| REQ-OA-043-03 | All custom nodes shall handle startup and shutdown gracefully (no blocking waits, clean `rospy.on_shutdown` hooks). |
| REQ-OA-043-04 | A README shall document all new topics, configurable parameters, and their data types. |

**Acceptance Criteria:**
- [ ] `catkin_make` succeeds with new nodes included
- [ ] New nodes appear in `rosnode list` after launch
- [ ] `rostopic echo /<new_topic>` returns valid data while payload is active
- [ ] Rover returns to baseline operation when new nodes are not launched

---

## Operational Scenario: Nominal Mission

```
Operator powers on rover
    └──► Rover boots (~30 s), establishes wireless link
Operator verifies link via Ground Station
    └──► Telemetry stream confirmed (battery, orientation displayed)
Operator performs pre-mission check
    └──► Battery ≥ 50%, no fault flags, all wheels visible in camera
Operator commands forward motion (v = 0.2 m/s)
    └──► Rover accelerates, traverses flat surface
Operator steers left to avoid obstacle
    └──► Corner servos adjust, rover arcs around obstacle
Operator detects low battery warning (< 11.0 V)
    └──► Operator commands return to start position
Operator commands stop
    └──► Rover decelerates to rest
Operator powers off rover, connects battery to charger
```
