# Requirements Register

**OSR MBSE — Master Requirements Index**

This register aggregates all formal requirements from the OSR systems engineering documentation. Each requirement is listed with its unique identifier, source document, layer, and a short statement. Requirements are traceable upward through the Arcadia layers: OA → SA → LA → PA.

## How to Use This Register

| Column | Meaning |
|---|---|
| **ID** | Unique identifier in `REQ-[LAYER]-[ACTIVITY/COMPONENT]-[NUMBER]` format |
| **Layer** | Arcadia layer: OA, SF (System Analysis), LC (Logical), PF (Physical) |
| **Statement** | The "shall" requirement text (abbreviated here; full text in source doc) |
| **Source** | Link to the document section containing the full requirement and acceptance criteria |
| **Status** | DRAFT → REVIEWED → VERIFIED |

---

## OA Layer — Operational Analysis Requirements

Requirements originate from: [Operational Activities](01_operational_analysis/operational_activities.md)

### OAct-01 — Conduct Rover Mission

| ID | Statement | Source | Status |
|---|---|---|---|
| REQ-OA-011-01 | Operator shall assess visible terrain for obstacles before commanding motion into any new area. | [OAct-01.1](01_operational_analysis/operational_activities.md#oact-011--plan-traverse-route) | DRAFT |
| REQ-OA-011-02 | Operator shall define a traverse path avoiding obstacles exceeding the rover's mobility limits. | [OAct-01.1](01_operational_analysis/operational_activities.md#oact-011--plan-traverse-route) | DRAFT |
| REQ-OA-011-03 | A go/no-go decision shall be made and communicated before each traverse segment. | [OAct-01.1](01_operational_analysis/operational_activities.md#oact-011--plan-traverse-route) | DRAFT |
| REQ-OA-012-01 | Operator shall command rover motion using a single handheld controller. | [OAct-01.2](01_operational_analysis/operational_activities.md#oact-012--command-rover-motion) | DRAFT |
| REQ-OA-012-02 | Motion commands shall be transmitted with round-trip latency ≤ 200 ms under nominal Wi-Fi. | [OAct-01.2](01_operational_analysis/operational_activities.md#oact-012--command-rover-motion) | DRAFT |
| REQ-OA-012-03 | Rover shall come to a complete stop within 1 s of operator releasing the motion command. | [OAct-01.2](01_operational_analysis/operational_activities.md#oact-012--command-rover-motion) | DRAFT |
| REQ-OA-012-04 | Rover shall execute a commanded stop within 1 s if the wireless link is lost. | [OAct-01.2](01_operational_analysis/operational_activities.md#oact-012--command-rover-motion) | DRAFT |
| REQ-OA-013-01 | Operator shall receive rover telemetry updates at ≥ 5 Hz during active operation. | [OAct-01.3](01_operational_analysis/operational_activities.md#oact-013--monitor-rover-state) | DRAFT |
| REQ-OA-013-02 | Battery state-of-charge shall be visible on the ground station display at all times. | [OAct-01.3](01_operational_analysis/operational_activities.md#oact-013--monitor-rover-state) | DRAFT |
| REQ-OA-013-03 | Any fault condition shall produce a visible alert on the ground station within one telemetry cycle. | [OAct-01.3](01_operational_analysis/operational_activities.md#oact-013--monitor-rover-state) | DRAFT |
| REQ-OA-013-04 | Operator shall distinguish normal from fault operating states from ground station display alone. | [OAct-01.3](01_operational_analysis/operational_activities.md#oact-013--monitor-rover-state) | DRAFT |
| REQ-OA-014-01 | Operator shall issue a stop command within 3 s of recognising a hazard condition. | [OAct-01.4](01_operational_analysis/operational_activities.md#oact-014--respond-to-hazard) | DRAFT |
| REQ-OA-014-02 | Operator shall acknowledge all system-generated fault events before resuming rover motion. | [OAct-01.4](01_operational_analysis/operational_activities.md#oact-014--respond-to-hazard) | DRAFT |
| REQ-OA-014-03 | A clear recovery procedure shall exist for each fault type. | [OAct-01.4](01_operational_analysis/operational_activities.md#oact-014--respond-to-hazard) | DRAFT |
| REQ-OA-015-01 | Rover shall stream live camera video to ground station at ≥ 10 fps during operation. | [OAct-01.5](01_operational_analysis/operational_activities.md#oact-015--collect-sensor-data) | DRAFT |
| REQ-OA-015-02 | All sensor data shall be time-stamped with the rover's system clock. | [OAct-01.5](01_operational_analysis/operational_activities.md#oact-015--collect-sensor-data) | DRAFT |
| REQ-OA-015-03 | Collected data shall be accessible for download via SSH after mission completion. | [OAct-01.5](01_operational_analysis/operational_activities.md#oact-015--collect-sensor-data) | DRAFT |

### OAct-02 — Maintain Rover

| ID | Statement | Source | Status |
|---|---|---|---|
| REQ-OA-021-01 | Battery shall be charged using a balance charger with cell-level voltage monitoring. | [OAct-02.1](01_operational_analysis/operational_activities.md#oact-021--charge-battery) | DRAFT |
| REQ-OA-021-02 | Charge rate shall not exceed 1C. | [OAct-02.1](01_operational_analysis/operational_activities.md#oact-021--charge-battery) | DRAFT |
| REQ-OA-021-03 | Battery shall not be charged while installed in rover unless a dedicated charge circuit with thermal monitoring is present. | [OAct-02.1](01_operational_analysis/operational_activities.md#oact-021--charge-battery) | DRAFT |
| REQ-OA-021-04 | A fully charged 3S LiPo shall measure ≥ 12.6 V at pack terminals. | [OAct-02.1](01_operational_analysis/operational_activities.md#oact-021--charge-battery) | DRAFT |
| REQ-OA-022-01 | A hardware inspection shall be performed after every operating session involving terrain traverse. | [OAct-02.2](01_operational_analysis/operational_activities.md#oact-022--inspect-and-repair-hardware) | DRAFT |
| REQ-OA-022-02 | Any loose fastener shall be re-torqued before the next mission. | [OAct-02.2](01_operational_analysis/operational_activities.md#oact-022--inspect-and-repair-hardware) | DRAFT |
| REQ-OA-022-03 | Worn or damaged components shall be replaced before rover is returned to service. | [OAct-02.2](01_operational_analysis/operational_activities.md#oact-022--inspect-and-repair-hardware) | DRAFT |
| REQ-OA-023-01 | Software updates shall be deployed via SSH without requiring physical disassembly. | [OAct-02.3](01_operational_analysis/operational_activities.md#oact-023--update-software) | DRAFT |
| REQ-OA-023-02 | After any update, all ROS nodes shall be verified running before returning rover to service. | [OAct-02.3](01_operational_analysis/operational_activities.md#oact-023--update-software) | DRAFT |
| REQ-OA-023-03 | Post-update functional test shall include ≥ 0.5 m commanded forward motion and full stop. | [OAct-02.3](01_operational_analysis/operational_activities.md#oact-023--update-software) | DRAFT |

### OAct-03 — Build Rover

| ID | Statement | Source | Status |
|---|---|---|---|
| REQ-OA-031-01 | All sourced components shall meet or exceed BOM specifications. | [OAct-03.1](01_operational_analysis/operational_activities.md#oact-031--source-components) | DRAFT |
| REQ-OA-031-02 | Builder shall verify received quantities against BOM before beginning assembly. | [OAct-03.1](01_operational_analysis/operational_activities.md#oact-031--source-components) | DRAFT |
| REQ-OA-031-03 | Substitute components shall be verified compatible before use. | [OAct-03.1](01_operational_analysis/operational_activities.md#oact-031--source-components) | DRAFT |
| REQ-OA-032-01 | Mechanical assembly shall be completable using only standard hand tools. | [OAct-03.2](01_operational_analysis/operational_activities.md#oact-032--assemble-mechanical-structure) | DRAFT |
| REQ-OA-032-02 | All pivot joints shall use flanged bearings. | [OAct-03.2](01_operational_analysis/operational_activities.md#oact-032--assemble-mechanical-structure) | DRAFT |
| REQ-OA-032-03 | All structural fasteners shall be tightened to finger-tight plus 1/4 turn unless otherwise specified. | [OAct-03.2](01_operational_analysis/operational_activities.md#oact-032--assemble-mechanical-structure) | DRAFT |
| REQ-OA-032-04 | Completed chassis shall support rover total mass without visible deflection. | [OAct-03.2](01_operational_analysis/operational_activities.md#oact-032--assemble-mechanical-structure) | DRAFT |
| REQ-OA-033-01 | A continuity check shall be performed on all power rails before applying battery power for the first time. | [OAct-03.3](01_operational_analysis/operational_activities.md#oact-033--install-electrical-system) | DRAFT |
| REQ-OA-033-02 | Wire gauges shall meet or exceed the minimum specified in the harness guide. | [OAct-03.3](01_operational_analysis/operational_activities.md#oact-033--install-electrical-system) | DRAFT |
| REQ-OA-033-03 | An in-line fuse (≤ 30 A) shall be installed between battery and PCB input. | [OAct-03.3](01_operational_analysis/operational_activities.md#oact-033--install-electrical-system) | DRAFT |
| REQ-OA-033-04 | All motor and servo connectors shall be secured with positive-retention connectors. | [OAct-03.3](01_operational_analysis/operational_activities.md#oact-033--install-electrical-system) | DRAFT |
| REQ-OA-034-01 | Software installation shall be completable following the documented guide without prior ROS expertise. | [OAct-03.4](01_operational_analysis/operational_activities.md#oact-034--install-and-configure-software) | DRAFT |
| REQ-OA-034-02 | All ROS nodes shall start without errors on first launch after fresh installation. | [OAct-03.4](01_operational_analysis/operational_activities.md#oact-034--install-and-configure-software) | DRAFT |
| REQ-OA-034-03 | Rover shall respond to `/cmd_vel` within 5 minutes of completing software installation. | [OAct-03.4](01_operational_analysis/operational_activities.md#oact-034--install-and-configure-software) | DRAFT |
| REQ-OA-034-04 | Wi-Fi connectivity and SSH access shall be confirmed before launching ROS. | [OAct-03.4](01_operational_analysis/operational_activities.md#oact-034--install-and-configure-software) | DRAFT |

### OAct-04 — Extend Rover Capability

| ID | Statement | Source | Status |
|---|---|---|---|
| REQ-OA-041-01 | Payload designs shall not exceed power budget allocations. | [OAct-04.1](01_operational_analysis/operational_activities.md#oact-041--design-payload-or-modification) | DRAFT |
| REQ-OA-041-02 | Mechanical payload attachments shall use the standard M3 bolt pattern without permanent chassis modification. | [OAct-04.1](01_operational_analysis/operational_activities.md#oact-041--design-payload-or-modification) | DRAFT |
| REQ-OA-041-03 | Design package shall include a defined ROS data interface (topic name, message type, update rate). | [OAct-04.1](01_operational_analysis/operational_activities.md#oact-041--design-payload-or-modification) | DRAFT |
| REQ-OA-041-04 | Payload mass shall be documented; total rover mass with payload shall not exceed 10 kg. | [OAct-04.1](01_operational_analysis/operational_activities.md#oact-041--design-payload-or-modification) | DRAFT |
| REQ-OA-042-01 | Payload integration shall not require removal or permanent modification of any baseline rover component. | [OAct-04.2](01_operational_analysis/operational_activities.md#oact-042--integrate-payload) | DRAFT |
| REQ-OA-042-02 | All payload wiring shall be routed clear of rotating and articulating components. | [OAct-04.2](01_operational_analysis/operational_activities.md#oact-042--integrate-payload) | DRAFT |
| REQ-OA-042-03 | Payload integration shall be reversible using only a standard Allen key set. | [OAct-04.2](01_operational_analysis/operational_activities.md#oact-042--integrate-payload) | DRAFT |
| REQ-OA-043-01 | Custom ROS nodes shall be added to OSR catkin workspace without modifying existing baseline nodes. | [OAct-04.3](01_operational_analysis/operational_activities.md#oact-043--develop-custom-software) | DRAFT |
| REQ-OA-043-02 | New ROS topics shall follow the OSR naming convention. | [OAct-04.3](01_operational_analysis/operational_activities.md#oact-043--develop-custom-software) | DRAFT |
| REQ-OA-043-03 | All custom nodes shall handle startup and shutdown gracefully. | [OAct-04.3](01_operational_analysis/operational_activities.md#oact-043--develop-custom-software) | DRAFT |
| REQ-OA-043-04 | A README shall document all new topics, configurable parameters, and their data types. | [OAct-04.3](01_operational_analysis/operational_activities.md#oact-043--develop-custom-software) | DRAFT |

---

## SF Layer — System Function Requirements

Requirements originate from: [System Functions](02_system_analysis/system_functions.md)

| ID | Statement | Source | Status |
|---|---|---|---|
| REQ-SF-01-01 | System shall accept motion commands as `geometry_msgs/Twist` on `/cmd_vel`. | [SF-01](02_system_analysis/system_functions.md#sf-01--receive-and-decode-command) | DRAFT |
| REQ-SF-01-02 | System shall apply a 1-second command watchdog, outputting zero velocity on timeout. | [SF-01](02_system_analysis/system_functions.md#sf-01--receive-and-decode-command) | DRAFT |
| REQ-SF-01-03 | System shall discard command messages containing NaN or Inf values. | [SF-01](02_system_analysis/system_functions.md#sf-01--receive-and-decode-command) | DRAFT |
| REQ-SF-01-04 | System shall process command messages at a minimum rate of 10 Hz. | [SF-01](02_system_analysis/system_functions.md#sf-01--receive-and-decode-command) | DRAFT |
| REQ-SF-02-01 | System shall compute per-wheel speed setpoints using the OSR rocker-bogie kinematic model. | [SF-02](02_system_analysis/system_functions.md#sf-02--execute-mobility) | DRAFT |
| REQ-SF-02-02 | Drive wheel setpoints shall be updated at ≥ 20 Hz. | [SF-02](02_system_analysis/system_functions.md#sf-02--execute-mobility) | DRAFT |
| REQ-SF-02-03 | System shall clamp drive setpoints to motor controller rated maximum speed. | [SF-02](02_system_analysis/system_functions.md#sf-02--execute-mobility) | DRAFT |
| REQ-SF-02-04 | System shall position corner steering servos to Ackermann-correct angles within 250 ms. | [SF-02](02_system_analysis/system_functions.md#sf-02--execute-mobility) | DRAFT |
| REQ-SF-02-05 | Upon halt signal from SF-06, SF-02 shall set all drive motor setpoints to zero within ≤ 50 ms. | [SF-02](02_system_analysis/system_functions.md#sf-02--execute-mobility) | DRAFT |
| REQ-SF-03-01 | System shall provide regulated 5V ± 5% to RPi and logic peripherals. | [SF-03](02_system_analysis/system_functions.md#sf-03--manage-power) | DRAFT |
| REQ-SF-03-02 | System shall read and publish battery voltage and current at ≥ 1 Hz. | [SF-03](02_system_analysis/system_functions.md#sf-03--manage-power) | DRAFT |
| REQ-SF-03-03 | System shall compute and publish state-of-charge as a percentage from LiPo discharge curve. | [SF-03](02_system_analysis/system_functions.md#sf-03--manage-power) | DRAFT |
| REQ-SF-03-04 | System shall trigger safe stop when any motor current exceeds 10 A. | [SF-03](02_system_analysis/system_functions.md#sf-03--manage-power) | DRAFT |
| REQ-SF-03-05 | System shall publish low-battery warning when voltage falls below 11.0 V. | [SF-03](02_system_analysis/system_functions.md#sf-03--manage-power) | DRAFT |
| REQ-SF-03-06 | System shall trigger safe stop when battery voltage falls below 10.5 V. | [SF-03](02_system_analysis/system_functions.md#sf-03--manage-power) | DRAFT |
| REQ-SF-04-01 | System shall sample wheel encoder counts at ≥ 20 Hz per wheel. | [SF-04](02_system_analysis/system_functions.md#sf-04--process-and-publish-telemetry) | DRAFT |
| REQ-SF-04-02 | System shall sample IMU acceleration and gyroscope at ≥ 50 Hz. | [SF-04](02_system_analysis/system_functions.md#sf-04--process-and-publish-telemetry) | DRAFT |
| REQ-SF-04-03 | System shall publish odometry (`/odom`) at ≥ 10 Hz. | [SF-04](02_system_analysis/system_functions.md#sf-04--process-and-publish-telemetry) | DRAFT |
| REQ-SF-04-04 | System shall publish attitude (`/imu`) at ≥ 20 Hz. | [SF-04](02_system_analysis/system_functions.md#sf-04--process-and-publish-telemetry) | DRAFT |
| REQ-SF-04-05 | System shall publish telemetry topics to ground station at ≥ 5 Hz. | [SF-04](02_system_analysis/system_functions.md#sf-04--process-and-publish-telemetry) | DRAFT |
| REQ-SF-04-06 | Telemetry latency from sensor read to Wi-Fi transmission shall not exceed 200 ms. | [SF-04](02_system_analysis/system_functions.md#sf-04--process-and-publish-telemetry) | DRAFT |
| REQ-SF-05-01 | System shall capture and publish video at ≥ 15 fps at 640×480 when camera is installed. | [SF-05](02_system_analysis/system_functions.md#sf-05--capture-and-stream-video) | DRAFT |
| REQ-SF-05-02 | System shall publish compressed video on `/camera/image_raw/compressed`. | [SF-05](02_system_analysis/system_functions.md#sf-05--capture-and-stream-video) | DRAFT |
| REQ-SF-05-03 | Video stream latency shall not exceed 500 ms over local Wi-Fi. | [SF-05](02_system_analysis/system_functions.md#sf-05--capture-and-stream-video) | DRAFT |
| REQ-SF-05-04 | System shall start without error when camera is absent; SF-05 shall be inactive without affecting other functions. | [SF-05](02_system_analysis/system_functions.md#sf-05--capture-and-stream-video) | DRAFT |
| REQ-SF-06-01 | System shall monitor motor channel current at ≥ 10 Hz. | [SF-06](02_system_analysis/system_functions.md#sf-06--detect-and-handle-faults) | DRAFT |
| REQ-SF-06-02 | System shall trigger safe stop within 100 ms of any motor current exceeding 10 A. | [SF-06](02_system_analysis/system_functions.md#sf-06--detect-and-handle-faults) | DRAFT |
| REQ-SF-06-03 | System shall publish battery warning at < 11.0 V and trigger safe stop at < 10.5 V. | [SF-06](02_system_analysis/system_functions.md#sf-06--detect-and-handle-faults) | DRAFT |
| REQ-SF-06-04 | System shall monitor rover roll and pitch at ≥ 10 Hz. | [SF-06](02_system_analysis/system_functions.md#sf-06--detect-and-handle-faults) | DRAFT |
| REQ-SF-06-05 | System shall trigger safe stop within 100 ms of roll or pitch exceeding 35°. | [SF-06](02_system_analysis/system_functions.md#sf-06--detect-and-handle-faults) | DRAFT |
| REQ-SF-06-06 | Upon safe stop, system shall zero all drive motor setpoints and publish fault event to `/diagnostics`. | [SF-06](02_system_analysis/system_functions.md#sf-06--detect-and-handle-faults) | DRAFT |
| REQ-SF-06-07 | Safe stop shall latch; rover shall not resume motion until operator clear command is received and fault resolved. | [SF-06](02_system_analysis/system_functions.md#sf-06--detect-and-handle-faults) | DRAFT |
| REQ-SF-07-01 | System shall provide switchable 5V @ ≥ 2 A and 12V @ ≥ 2 A to payload connector. | [SF-07](02_system_analysis/system_functions.md#sf-07--support-payload-interface) | DRAFT |
| REQ-SF-07-02 | System shall monitor payload current and disable rail if exceeding configured limit (default 2 A). | [SF-07](02_system_analysis/system_functions.md#sf-07--support-payload-interface) | DRAFT |
| REQ-SF-07-03 | System shall provide USB, I²C, and UART connectivity to payload from Raspberry Pi. | [SF-07](02_system_analysis/system_functions.md#sf-07--support-payload-interface) | DRAFT |
| REQ-SF-07-04 | Payload power enable/disable shall be controllable via software (GPIO). | [SF-07](02_system_analysis/system_functions.md#sf-07--support-payload-interface) | DRAFT |
| REQ-SF-07-05 | Payload power rail switching shall not interrupt or reset any other system power rail. | [SF-07](02_system_analysis/system_functions.md#sf-07--support-payload-interface) | DRAFT |

---

## LC Layer — Logical Component Requirements

Requirements originate from: [Logical Components](03_logical_architecture/logical_components.md)

| ID | Statement | Source | Status |
|---|---|---|---|
| REQ-LC-01-01 | LC-01 shall receive motion commands from ground station on `/cmd_vel`. | [LC-01](03_logical_architecture/logical_components.md#lc-01--communication-manager) | DRAFT |
| REQ-LC-01-02 | LC-01 shall detect command stream timeout and notify LC-02 to command zero velocity. | [LC-01](03_logical_architecture/logical_components.md#lc-01--communication-manager) | DRAFT |
| REQ-LC-01-03 | LC-01 shall relay all outbound telemetry topics to ground station at their respective publish rates. | [LC-01](03_logical_architecture/logical_components.md#lc-01--communication-manager) | DRAFT |
| REQ-LC-01-04 | LC-01 shall relay video stream from LC-08 when SF-05 is active. | [LC-01](03_logical_architecture/logical_components.md#lc-01--communication-manager) | DRAFT |
| REQ-LC-01-05 | LC-01 shall not drop or reorder command packets at distances ≤ 50 m. | [LC-01](03_logical_architecture/logical_components.md#lc-01--communication-manager) | DRAFT |
| REQ-LC-02-01 | LC-02 shall parse `geometry_msgs/Twist` and extract `linear.x` and `angular.z`. | [LC-02](03_logical_architecture/logical_components.md#lc-02--command-processor) | DRAFT |
| REQ-LC-02-02 | LC-02 shall discard messages containing NaN or Inf values. | [LC-02](03_logical_architecture/logical_components.md#lc-02--command-processor) | DRAFT |
| REQ-LC-02-03 | LC-02 shall clamp `linear.x` to ±0.4 m/s and `angular.z` to ±1.0 rad/s. | [LC-02](03_logical_architecture/logical_components.md#lc-02--command-processor) | DRAFT |
| REQ-LC-02-04 | LC-02 shall output zero velocity to LC-03 immediately upon halt command from LC-05. | [LC-02](03_logical_architecture/logical_components.md#lc-02--command-processor) | DRAFT |
| REQ-LC-02-05 | LC-02 shall output zero velocity to LC-03 when LC-01 signals watchdog timeout. | [LC-02](03_logical_architecture/logical_components.md#lc-02--command-processor) | DRAFT |
| REQ-LC-03-01 | LC-03 shall compute per-wheel speed setpoints using the OSR rocker-bogie kinematic model. | [LC-03](03_logical_architecture/logical_components.md#lc-03--mobility-controller) | DRAFT |
| REQ-LC-03-02 | LC-03 shall compute Ackermann steering angles for all four corner wheels. | [LC-03](03_logical_architecture/logical_components.md#lc-03--mobility-controller) | DRAFT |
| REQ-LC-03-03 | LC-03 shall update drive wheel setpoints at ≥ 20 Hz. | [LC-03](03_logical_architecture/logical_components.md#lc-03--mobility-controller) | DRAFT |
| REQ-LC-03-04 | LC-03 shall update steering servo angles within 250 ms of angular velocity change. | [LC-03](03_logical_architecture/logical_components.md#lc-03--mobility-controller) | DRAFT |
| REQ-LC-03-05 | LC-03 shall clamp wheel speed setpoints to motor controller rated maximum. | [LC-03](03_logical_architecture/logical_components.md#lc-03--mobility-controller) | DRAFT |
| REQ-LC-03-06 | LC-03 shall clamp steering angles to each servo's mechanical range (±30°). | [LC-03](03_logical_architecture/logical_components.md#lc-03--mobility-controller) | DRAFT |
| REQ-LC-03-07 | LC-03 shall output zero speed to all wheels immediately upon halt command. | [LC-03](03_logical_architecture/logical_components.md#lc-03--mobility-controller) | DRAFT |
| REQ-LC-04-01 | LC-04 shall read wheel encoder counts from all six wheels at ≥ 20 Hz. | [LC-04](03_logical_architecture/logical_components.md#lc-04--state-estimator) | DRAFT |
| REQ-LC-04-02 | LC-04 shall read IMU acceleration and angular velocity at ≥ 50 Hz. | [LC-04](03_logical_architecture/logical_components.md#lc-04--state-estimator) | DRAFT |
| REQ-LC-04-03 | LC-04 shall read per-channel motor currents at ≥ 10 Hz. | [LC-04](03_logical_architecture/logical_components.md#lc-04--state-estimator) | DRAFT |
| REQ-LC-04-04 | LC-04 shall publish `nav_msgs/Odometry` at ≥ 10 Hz. | [LC-04](03_logical_architecture/logical_components.md#lc-04--state-estimator) | DRAFT |
| REQ-LC-04-05 | LC-04 shall publish `sensor_msgs/Imu` at ≥ 20 Hz. | [LC-04](03_logical_architecture/logical_components.md#lc-04--state-estimator) | DRAFT |
| REQ-LC-04-06 | LC-04 shall publish per-motor current readings to LC-05 at ≥ 10 Hz. | [LC-04](03_logical_architecture/logical_components.md#lc-04--state-estimator) | DRAFT |
| REQ-LC-04-07 | Odometry position error shall not exceed 10% of distance travelled in straight-line test. | [LC-04](03_logical_architecture/logical_components.md#lc-04--state-estimator) | DRAFT |
| REQ-LC-05-01 | LC-05 shall monitor motor currents at ≥ 10 Hz and trigger safe stop within 100 ms of 10 A threshold. | [LC-05](03_logical_architecture/logical_components.md#lc-05--fault-monitor) | DRAFT |
| REQ-LC-05-02 | LC-05 shall monitor battery voltage at ≥ 1 Hz, warn at < 11.0 V, and stop at < 10.5 V. | [LC-05](03_logical_architecture/logical_components.md#lc-05--fault-monitor) | DRAFT |
| REQ-LC-05-03 | LC-05 shall monitor roll and pitch at ≥ 10 Hz and trigger safe stop within 100 ms of 35° threshold. | [LC-05](03_logical_architecture/logical_components.md#lc-05--fault-monitor) | DRAFT |
| REQ-LC-05-04 | All critical faults shall latch; halt persists until `clear_fault` service call is received. | [LC-05](03_logical_architecture/logical_components.md#lc-05--fault-monitor) | DRAFT |
| REQ-LC-05-05 | LC-05 shall verify fault condition resolved before responding to `clear_fault`. | [LC-05](03_logical_architecture/logical_components.md#lc-05--fault-monitor) | DRAFT |
| REQ-LC-05-06 | LC-05 shall publish all fault events with timestamp and classification to `/diagnostics`. | [LC-05](03_logical_architecture/logical_components.md#lc-05--fault-monitor) | DRAFT |
| REQ-LC-06-01 | LC-06 shall read battery voltage and current from INA219 at ≥ 1 Hz. | [LC-06](03_logical_architecture/logical_components.md#lc-06--power-manager) | DRAFT |
| REQ-LC-06-02 | LC-06 shall publish `sensor_msgs/BatteryState` on `/battery_state`. | [LC-06](03_logical_architecture/logical_components.md#lc-06--power-manager) | DRAFT |
| REQ-LC-06-03 | LC-06 shall compute SoC% using 3S LiPo discharge curve (100% at ≥ 12.6 V, 0% at ≤ 10.5 V). | [LC-06](03_logical_architecture/logical_components.md#lc-06--power-manager) | DRAFT |
| REQ-LC-06-04 | LC-06 shall provide software-controllable enable/disable for payload power rail. | [LC-06](03_logical_architecture/logical_components.md#lc-06--power-manager) | DRAFT |
| REQ-LC-06-05 | LC-06 voltage measurement accuracy shall be within ±0.1 V of multimeter reference. | [LC-06](03_logical_architecture/logical_components.md#lc-06--power-manager) | DRAFT |
| REQ-LC-07-01 | LC-07 shall publish aggregated diagnostic summary at ≥ 5 Hz. | [LC-07](03_logical_architecture/logical_components.md#lc-07--telemetry-publisher) | DRAFT |
| REQ-LC-07-02 | LC-07 shall include battery state, fault flags, odometry, attitude, and motor currents in telemetry. | [LC-07](03_logical_architecture/logical_components.md#lc-07--telemetry-publisher) | DRAFT |
| REQ-LC-07-03 | LC-07 shall relay video frames from LC-08 when SF-05 is active. | [LC-07](03_logical_architecture/logical_components.md#lc-07--telemetry-publisher) | DRAFT |
| REQ-LC-07-04 | LC-07 shall not introduce more than 50 ms of additional latency to sensor topic data. | [LC-07](03_logical_architecture/logical_components.md#lc-07--telemetry-publisher) | DRAFT |
| REQ-LC-08-01 | LC-08 shall provide GPIO-controlled 5V and 12V power rails to payload connector. | [LC-08](03_logical_architecture/logical_components.md#lc-08--payload-manager) | DRAFT |
| REQ-LC-08-02 | LC-08 shall monitor payload current at ≥ 1 Hz and disable rail if exceeding limit (default 2 A). | [LC-08](03_logical_architecture/logical_components.md#lc-08--payload-manager) | DRAFT |
| REQ-LC-08-03 | LC-08 shall publish a fault event to `/diagnostics` on payload overcurrent. | [LC-08](03_logical_architecture/logical_components.md#lc-08--payload-manager) | DRAFT |
| REQ-LC-08-04 | LC-08 shall provide USB, I²C, and UART pass-through from payload connector to RPi. | [LC-08](03_logical_architecture/logical_components.md#lc-08--payload-manager) | DRAFT |
| REQ-LC-08-05 | Payload power switching shall not affect any other power rail or reset the Raspberry Pi. | [LC-08](03_logical_architecture/logical_components.md#lc-08--payload-manager) | DRAFT |

---

## PF Layer — Physical Function Requirements

Requirements originate from: [Physical Functions](04_physical_architecture/physical_functions.md)

| ID | Statement | Source | Status |
|---|---|---|---|
| REQ-PF-01-01 | `command_node` shall subscribe to `/cmd_vel` and process messages at ≥ 10 Hz. | [PF-01](04_physical_architecture/physical_functions.md#pf-01--command-reception-and-validation) | DRAFT |
| REQ-PF-01-02 | Watchdog timer shall trigger within 1.0–1.1 s of last received message. | [PF-01](04_physical_architecture/physical_functions.md#pf-01--command-reception-and-validation) | DRAFT |
| REQ-PF-01-03 | Velocity clamping shall apply `numpy.clip` to both linear and angular components. | [PF-01](04_physical_architecture/physical_functions.md#pf-01--command-reception-and-validation) | DRAFT |
| REQ-PF-02-01 | `drive_node` shall compute and transmit wheel setpoints to all RoboClaw units at ≥ 20 Hz. | [PF-02](04_physical_architecture/physical_functions.md#pf-02--kinematics-and-actuator-drive) | DRAFT |
| REQ-PF-02-02 | `drive_node` shall update PCA9685 servo angles within 250 ms of angular velocity change. | [PF-02](04_physical_architecture/physical_functions.md#pf-02--kinematics-and-actuator-drive) | DRAFT |
| REQ-PF-02-03 | Motor setpoints shall be clamped to rated maximum before transmission to RoboClaw. | [PF-02](04_physical_architecture/physical_functions.md#pf-02--kinematics-and-actuator-drive) | DRAFT |
| REQ-PF-02-04 | Servo angle setpoints shall be clamped to mechanical range of motion (±30°). | [PF-02](04_physical_architecture/physical_functions.md#pf-02--kinematics-and-actuator-drive) | DRAFT |
| REQ-PF-02-05 | RoboClaw communication failure shall be logged to `/diagnostics` within one cycle. | [PF-02](04_physical_architecture/physical_functions.md#pf-02--kinematics-and-actuator-drive) | DRAFT |
| REQ-PF-03-01 | `power_node` shall read INA219 battery voltage and current at ≥ 1 Hz. | [PF-03](04_physical_architecture/physical_functions.md#pf-03--power-monitoring-and-distribution) | DRAFT |
| REQ-PF-03-02 | INA219 voltage measurement shall be accurate to ±0.1 V versus multimeter reference. | [PF-03](04_physical_architecture/physical_functions.md#pf-03--power-monitoring-and-distribution) | DRAFT |
| REQ-PF-03-03 | PCB DC-DC converter shall maintain 5V rail within ±5% under full system load. | [PF-03](04_physical_architecture/physical_functions.md#pf-03--power-monitoring-and-distribution) | DRAFT |
| REQ-PF-03-04 | `power_node` shall publish `sensor_msgs/BatteryState` to `/battery_state` at ≥ 1 Hz. | [PF-03](04_physical_architecture/physical_functions.md#pf-03--power-monitoring-and-distribution) | DRAFT |
| REQ-PF-03-05 | LiPo SoC lookup shall map ≥ 12.6 V → 100% and ≤ 10.5 V → 0% with monotonic interpolation. | [PF-03](04_physical_architecture/physical_functions.md#pf-03--power-monitoring-and-distribution) | DRAFT |
| REQ-PF-04-01 | `encoder_node` shall read encoder counts from all six wheels at ≥ 20 Hz. | [PF-04](04_physical_architecture/physical_functions.md#pf-04--sensor-sampling-and-state-estimation) | DRAFT |
| REQ-PF-04-02 | `imu_node` shall read BNO055 acceleration and angular velocity at ≥ 50 Hz. | [PF-04](04_physical_architecture/physical_functions.md#pf-04--sensor-sampling-and-state-estimation) | DRAFT |
| REQ-PF-04-03 | `encoder_node` shall read per-channel motor currents at ≥ 10 Hz. | [PF-04](04_physical_architecture/physical_functions.md#pf-04--sensor-sampling-and-state-estimation) | DRAFT |
| REQ-PF-04-04 | `/odom` shall be published at ≥ 10 Hz from integrated encoder ticks. | [PF-04](04_physical_architecture/physical_functions.md#pf-04--sensor-sampling-and-state-estimation) | DRAFT |
| REQ-PF-04-05 | `/imu` shall be published at ≥ 20 Hz from complementary filter output. | [PF-04](04_physical_architecture/physical_functions.md#pf-04--sensor-sampling-and-state-estimation) | DRAFT |
| REQ-PF-04-06 | Odometry position error shall not exceed 10% over a 1 m flat-surface test. | [PF-04](04_physical_architecture/physical_functions.md#pf-04--sensor-sampling-and-state-estimation) | DRAFT |
| REQ-PF-04-07 | BNO055 calibration status shall be System ≥ 2 before IMU data is used by fault monitor. | [PF-04](04_physical_architecture/physical_functions.md#pf-04--sensor-sampling-and-state-estimation) | DRAFT |
| REQ-PF-05-01 | `fault_node` shall evaluate motor current thresholds within 100 ms of 10 A exceedance. | [PF-05](04_physical_architecture/physical_functions.md#pf-05--fault-detection-and-safe-stop) | DRAFT |
| REQ-PF-05-02 | `fault_node` shall evaluate battery voltage thresholds within one cycle (≤ 1 s) of 10.5 V crossing. | [PF-05](04_physical_architecture/physical_functions.md#pf-05--fault-detection-and-safe-stop) | DRAFT |
| REQ-PF-05-03 | `fault_node` shall evaluate IMU tilt threshold within 100 ms of 35° exceedance. | [PF-05](04_physical_architecture/physical_functions.md#pf-05--fault-detection-and-safe-stop) | DRAFT |
| REQ-PF-05-04 | On safe stop trigger, `fault_node` shall transmit `SpeedM1M2(0,0)` to all RoboClaws within 50 ms. | [PF-05](04_physical_architecture/physical_functions.md#pf-05--fault-detection-and-safe-stop) | DRAFT |
| REQ-PF-05-05 | `fault_node` shall publish `DiagnosticStatus` ERROR to `/diagnostics` within one cycle of fault detection. | [PF-05](04_physical_architecture/physical_functions.md#pf-05--fault-detection-and-safe-stop) | DRAFT |
| REQ-PF-05-06 | Safe stop shall latch; `fault_node` shall block commands until `clear_fault` and condition resolved. | [PF-05](04_physical_architecture/physical_functions.md#pf-05--fault-detection-and-safe-stop) | DRAFT |
| REQ-PF-06-01 | `camera_node` shall capture frames at ≥ 15 fps at 640×480 when camera is present. | [PF-06](04_physical_architecture/physical_functions.md#pf-06--camera-capture-and-streaming) | DRAFT |
| REQ-PF-06-02 | Compressed frames shall be published on `/camera/image_raw/compressed` as MJPEG. | [PF-06](04_physical_architecture/physical_functions.md#pf-06--camera-capture-and-streaming) | DRAFT |
| REQ-PF-06-03 | End-to-end video latency shall not exceed 500 ms over local Wi-Fi. | [PF-06](04_physical_architecture/physical_functions.md#pf-06--camera-capture-and-streaming) | DRAFT |
| REQ-PF-06-04 | If no camera is present at launch, `camera_node` shall exit gracefully without affecting other nodes. | [PF-06](04_physical_architecture/physical_functions.md#pf-06--camera-capture-and-streaming) | DRAFT |
| REQ-PF-06-05 | CPU usage by `camera_node` shall not exceed 20% of one RPi core during streaming. | [PF-06](04_physical_architecture/physical_functions.md#pf-06--camera-capture-and-streaming) | DRAFT |
| REQ-PF-07-01 | RPi GPIO toggle of payload load switch shall energise/de-energise payload connector within 10 ms. | [PF-07](04_physical_architecture/physical_functions.md#pf-07--payload-interface) | DRAFT |
| REQ-PF-07-02 | `power_node` shall read payload current at ≥ 1 Hz and disable payload power if > 2 A. | [PF-07](04_physical_architecture/physical_functions.md#pf-07--payload-interface) | DRAFT |
| REQ-PF-07-03 | USB device on payload connector shall enumerate on RPi within 5 s of connection. | [PF-07](04_physical_architecture/physical_functions.md#pf-07--payload-interface) | DRAFT |
| REQ-PF-07-04 | Payload I²C device at non-conflicting address shall be detectable by `i2cdetect`. | [PF-07](04_physical_architecture/physical_functions.md#pf-07--payload-interface) | DRAFT |
| REQ-PF-07-05 | Payload power switching shall not cause > 0.2 V glitch on the 5V logic rail. | [PF-07](04_physical_architecture/physical_functions.md#pf-07--payload-interface) | DRAFT |

---

## Summary Statistics

| Layer | Requirement Count |
|---|---|
| OA — Operational Analysis | 38 |
| SF — System Functions | 34 |
| LC — Logical Components | 44 |
| PF — Physical Functions | 35 |
| **Total** | **151** |

---

## Traceability Index

The table below shows how key system-level requirements trace through all four Arcadia layers.

| Theme | OA Req | SF Req | LC Req | PF Req |
|---|---|---|---|---|
| Command reception | REQ-OA-012-01 | REQ-SF-01-01 | REQ-LC-01-01, REQ-LC-02-01 | REQ-PF-01-01 |
| Watchdog / link loss | REQ-OA-012-04 | REQ-SF-01-02 | REQ-LC-01-02, REQ-LC-02-05 | REQ-PF-01-02 |
| Drive kinematics | REQ-OA-012-01 | REQ-SF-02-01 | REQ-LC-03-01, REQ-LC-03-02 | REQ-PF-02-01 |
| Drive update rate | — | REQ-SF-02-02 | REQ-LC-03-03 | REQ-PF-02-01 |
| Steering accuracy | — | REQ-SF-02-04 | REQ-LC-03-04 | REQ-PF-02-02 |
| Battery monitoring | REQ-OA-013-02 | REQ-SF-03-02, REQ-SF-03-03 | REQ-LC-06-01, REQ-LC-06-02 | REQ-PF-03-01, REQ-PF-03-04 |
| Overcurrent protection | — | REQ-SF-03-04 | REQ-LC-05-01 | REQ-PF-05-01 |
| Tilt protection | — | REQ-SF-06-05 | REQ-LC-05-03 | REQ-PF-05-03 |
| Safe stop | REQ-OA-014-01 | REQ-SF-06-06 | REQ-LC-05-04 | REQ-PF-05-04 |
| Telemetry rate | REQ-OA-013-01 | REQ-SF-04-05 | REQ-LC-07-01 | REQ-PF-04-04 |
| Odometry accuracy | — | — | REQ-LC-04-07 | REQ-PF-04-06 |
| Video streaming | REQ-OA-015-01 | REQ-SF-05-01 | REQ-LC-01-04 | REQ-PF-06-01 |
| Payload power | REQ-OA-041-01 | REQ-SF-07-01 | REQ-LC-08-01 | REQ-PF-07-01 |
| Software update | REQ-OA-023-01 | — | — | — |
| Build / assembly | REQ-OA-032-01 | — | — | — |
