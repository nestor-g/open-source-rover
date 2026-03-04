/**
 * OSR::Requirements::LC
 * =====================
 * Logical Component requirements — 44 requirement defs
 * Source: systems_engineering/03_logical_architecture/logical_components.md
 *         systems_engineering/requirements_register.md § LC Layer
 *
 * LC requirements constrain the design of logical components (LC-01..LC-08).
 * They are satisfied by physical architecture elements in 04_physical_architecture/.
 */
package 'OSR::Requirements::LC' {

    private import ScalarValues::*;
    private import 'OSR::Core::Relations'::*;

    // ════════════════════════════════════════════════════════════════════
    // LC-01 — Communication Manager
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-LC-01-01'> LC01CmdVelReceive :> InterfaceReq {
        doc /* LC-01 shall receive motion commands from ground station on
              /cmd_vel. */
        :>> layer        = "LC";
        :>> source       = "03_logical_architecture/logical_components.md#lc-01";
        :>> rosTopicName = "/cmd_vel";
        :>> rosMsgType   = "geometry_msgs/Twist";
    }
    requirement def <'REQ-LC-01-02'> LC01WatchdogNotify :> SafetyCriticalReq {
        doc /* LC-01 shall detect command stream timeout and notify LC-02
              to command zero velocity. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-01";
        :>> hazardRef  = "H-04";
        :>> responseMs = 1000.0;
    }
    requirement def <'REQ-LC-01-03'> LC01TelemetryRelay :> PerformanceReq {
        doc /* LC-01 shall relay all outbound telemetry topics to ground
              station at their respective publish rates. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-01";
        :>> measuredBy = "end-to-end topic rate at ground station";
    }
    requirement def <'REQ-LC-01-04'> LC01VideoRelay :> OSRRequirement {
        doc /* LC-01 shall relay video stream from LC-08 when SF-05 is
              active. */
        :>> layer  = "LC";
        :>> source = "03_logical_architecture/logical_components.md#lc-01";
    }
    requirement def <'REQ-LC-01-05'> LC01NoPacketLoss :> PerformanceReq {
        doc /* LC-01 shall not drop or reorder command packets at distances
              ≤ 50 m. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-01";
        :>> measuredBy = "packet sequence number check at 50 m range";
    }

    // ════════════════════════════════════════════════════════════════════
    // LC-02 — Command Processor
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-LC-02-01'> LC02TwistParse :> InterfaceReq {
        doc /* LC-02 shall parse geometry_msgs/Twist and extract linear.x
              and angular.z. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-02";
        :>> rosMsgType = "geometry_msgs/Twist";
    }
    requirement def <'REQ-LC-02-02'> LC02NaNDiscard :> SafetyCriticalReq {
        doc /* LC-02 shall discard messages containing NaN or Inf
              values. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-02";
        :>> hazardRef  = "H-05";
        :>> responseMs = 0.0;
    }
    requirement def <'REQ-LC-02-03'> LC02VelocityClamp :> SafetyCriticalReq {
        doc /* LC-02 shall clamp linear.x to ±0.4 m/s and angular.z to
              ±1.0 rad/s. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-02";
        :>> hazardRef  = "H-05";
        :>> responseMs = 0.0;
    }
    requirement def <'REQ-LC-02-04'> LC02HaltOutput :> SafetyCriticalReq {
        doc /* LC-02 shall output zero velocity to LC-03 immediately upon
              halt command from LC-05. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-02";
        :>> hazardRef  = "H-04";
        :>> responseMs = 50.0;
    }
    requirement def <'REQ-LC-02-05'> LC02WatchdogZero :> SafetyCriticalReq {
        doc /* LC-02 shall output zero velocity to LC-03 when LC-01
              signals watchdog timeout. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-02";
        :>> hazardRef  = "H-04";
        :>> responseMs = 1000.0;
    }

    // ════════════════════════════════════════════════════════════════════
    // LC-03 — Mobility Controller
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-LC-03-01'> LC03KinematicModel :> OSRRequirement {
        doc /* LC-03 shall compute per-wheel speed setpoints using the OSR
              rocker-bogie kinematic model. */
        :>> layer  = "LC";
        :>> source = "03_logical_architecture/logical_components.md#lc-03";
    }
    requirement def <'REQ-LC-03-02'> LC03AckermannSteering :> OSRRequirement {
        doc /* LC-03 shall compute Ackermann steering angles for all four
              corner wheels. */
        :>> layer  = "LC";
        :>> source = "03_logical_architecture/logical_components.md#lc-03";
    }
    requirement def <'REQ-LC-03-03'> LC03DriveRate :> PerformanceReq {
        doc /* LC-03 shall update drive wheel setpoints at ≥ 20 Hz. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-03";
        :>> measuredBy = "RoboClaw serial packet rate measurement";
    }
    requirement def <'REQ-LC-03-04'> LC03SteeringSettle :> PerformanceReq {
        doc /* LC-03 shall update steering servo angles within 250 ms of
              angular velocity change. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-03";
        :>> measuredBy = "timed angle change with potentiometer feedback";
    }
    requirement def <'REQ-LC-03-05'> LC03SpeedClamp :> OSRRequirement {
        doc /* LC-03 shall clamp wheel speed setpoints to motor controller
              rated maximum. */
        :>> layer  = "LC";
        :>> source = "03_logical_architecture/logical_components.md#lc-03";
    }
    requirement def <'REQ-LC-03-06'> LC03SteeringClamp :> OSRRequirement {
        doc /* LC-03 shall clamp steering angles to each servo's mechanical
              range (±30°). */
        :>> layer  = "LC";
        :>> source = "03_logical_architecture/logical_components.md#lc-03";
    }
    requirement def <'REQ-LC-03-07'> LC03HaltZero :> SafetyCriticalReq {
        doc /* LC-03 shall output zero speed to all wheels immediately upon
              halt command. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-03";
        :>> hazardRef  = "H-01";
        :>> responseMs = 50.0;
    }

    // ════════════════════════════════════════════════════════════════════
    // LC-04 — State Estimator
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-LC-04-01'> LC04EncoderRate :> PerformanceReq {
        doc /* LC-04 shall read wheel encoder counts from all six wheels at
              ≥ 20 Hz. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-04";
        :>> measuredBy = "rostopic hz wheel encoder topic";
    }
    requirement def <'REQ-LC-04-02'> LC04IMURate :> PerformanceReq {
        doc /* LC-04 shall read IMU acceleration and angular velocity at
              ≥ 50 Hz. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-04";
        :>> measuredBy = "rostopic hz /imu/raw";
    }
    requirement def <'REQ-LC-04-03'> LC04CurrentReadRate :> PerformanceReq {
        doc /* LC-04 shall read per-channel motor currents at ≥ 10 Hz. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-04";
        :>> measuredBy = "rostopic hz motor current topic";
    }
    requirement def <'REQ-LC-04-04'> LC04OdomPublish :> PerformanceReq {
        doc /* LC-04 shall publish nav_msgs/Odometry at ≥ 10 Hz. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-04";
        :>> measuredBy = "rostopic hz /odom";
    }
    requirement def <'REQ-LC-04-05'> LC04IMUPublish :> PerformanceReq {
        doc /* LC-04 shall publish sensor_msgs/Imu at ≥ 20 Hz. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-04";
        :>> measuredBy = "rostopic hz /imu";
    }
    requirement def <'REQ-LC-04-06'> LC04CurrentToFaultMon :> PerformanceReq {
        doc /* LC-04 shall publish per-motor current readings to LC-05 at
              ≥ 10 Hz. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-04";
        :>> measuredBy = "rostopic hz motor current topic at LC-05 subscriber";
    }
    requirement def <'REQ-LC-04-07'> LC04OdomAccuracy :> PerformanceReq {
        doc /* Odometry position error shall not exceed 10% of distance
              travelled in straight-line test. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-04";
        :>> measuredBy = "1 m straight drive with tape measure reference";
        :>> tolerance  = 0.1;
    }

    // ════════════════════════════════════════════════════════════════════
    // LC-05 — Fault Monitor
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-LC-05-01'> LC05CurrentMonitor :> SafetyCriticalReq {
        doc /* LC-05 shall monitor motor currents at ≥ 10 Hz and trigger
              safe stop within 100 ms of 10 A threshold. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-05";
        :>> hazardRef  = "H-01";
        :>> responseMs = 100.0;
    }
    requirement def <'REQ-LC-05-02'> LC05VoltageMonitor :> SafetyCriticalReq {
        doc /* LC-05 shall monitor battery voltage at ≥ 1 Hz, warn at
              < 11.0 V, and stop at < 10.5 V. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-05";
        :>> hazardRef  = "H-03";
        :>> responseMs = 1000.0;
    }
    requirement def <'REQ-LC-05-03'> LC05TiltMonitor :> SafetyCriticalReq {
        doc /* LC-05 shall monitor roll and pitch at ≥ 10 Hz and trigger
              safe stop within 100 ms of 35° threshold. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-05";
        :>> hazardRef  = "H-02";
        :>> responseMs = 100.0;
    }
    requirement def <'REQ-LC-05-04'> LC05FaultLatch :> SafetyCriticalReq {
        doc /* All critical faults shall latch; halt persists until
              clear_fault service call is received. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-05";
        :>> hazardRef  = "H-01";
        :>> responseMs = 0.0;
    }
    requirement def <'REQ-LC-05-05'> LC05ClearFaultVerify :> OSRRequirement {
        doc /* LC-05 shall verify fault condition resolved before responding
              to clear_fault. */
        :>> layer  = "LC";
        :>> source = "03_logical_architecture/logical_components.md#lc-05";
    }
    requirement def <'REQ-LC-05-06'> LC05DiagPublish :> InterfaceReq {
        doc /* LC-05 shall publish all fault events with timestamp and
              classification to /diagnostics. */
        :>> layer        = "LC";
        :>> source       = "03_logical_architecture/logical_components.md#lc-05";
        :>> rosTopicName = "/diagnostics";
        :>> rosMsgType   = "diagnostic_msgs/DiagnosticArray";
    }

    // ════════════════════════════════════════════════════════════════════
    // LC-06 — Power Manager
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-LC-06-01'> LC06INA219Rate :> PerformanceReq {
        doc /* LC-06 shall read battery voltage and current from INA219 at
              ≥ 1 Hz. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-06";
        :>> measuredBy = "I2C read rate measurement";
    }
    requirement def <'REQ-LC-06-02'> LC06BatteryPublish :> InterfaceReq {
        doc /* LC-06 shall publish sensor_msgs/BatteryState on
              /battery_state. */
        :>> layer        = "LC";
        :>> source       = "03_logical_architecture/logical_components.md#lc-06";
        :>> rosTopicName = "/battery_state";
        :>> rosMsgType   = "sensor_msgs/BatteryState";
    }
    requirement def <'REQ-LC-06-03'> LC06SoCCompute :> OSRRequirement {
        doc /* LC-06 shall compute SoC% using 3S LiPo discharge curve
              (100% at ≥ 12.6 V, 0% at ≤ 10.5 V). */
        :>> layer  = "LC";
        :>> source = "03_logical_architecture/logical_components.md#lc-06";
    }
    requirement def <'REQ-LC-06-04'> LC06PayloadEnable :> OSRRequirement {
        doc /* LC-06 shall provide software-controllable enable/disable for
              payload power rail. */
        :>> layer  = "LC";
        :>> source = "03_logical_architecture/logical_components.md#lc-06";
    }
    requirement def <'REQ-LC-06-05'> LC06VoltageAccuracy :> PerformanceReq {
        doc /* LC-06 voltage measurement accuracy shall be within ±0.1 V
              of multimeter reference. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-06";
        :>> measuredBy = "INA219 vs calibrated multimeter at 3 voltage points";
        :>> tolerance  = 0.1;
    }

    // ════════════════════════════════════════════════════════════════════
    // LC-07 — Telemetry Publisher
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-LC-07-01'> LC07DiagRate :> PerformanceReq {
        doc /* LC-07 shall publish aggregated diagnostic summary at
              ≥ 5 Hz. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-07";
        :>> measuredBy = "rostopic hz /diagnostics";
    }
    requirement def <'REQ-LC-07-02'> LC07TelemetryContent :> OSRRequirement {
        doc /* LC-07 shall include battery state, fault flags, odometry,
              attitude, and motor currents in telemetry. */
        :>> layer  = "LC";
        :>> source = "03_logical_architecture/logical_components.md#lc-07";
    }
    requirement def <'REQ-LC-07-03'> LC07VideoRelay :> OSRRequirement {
        doc /* LC-07 shall relay video frames from LC-08 when SF-05 is
              active. */
        :>> layer  = "LC";
        :>> source = "03_logical_architecture/logical_components.md#lc-07";
    }
    requirement def <'REQ-LC-07-04'> LC07LatencyBudget :> PerformanceReq {
        doc /* LC-07 shall not introduce more than 50 ms of additional
              latency to sensor topic data. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-07";
        :>> measuredBy = "timestamp comparison sensor read vs published";
        :>> tolerance  = 50.0;
    }

    // ════════════════════════════════════════════════════════════════════
    // LC-08 — Payload Manager
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-LC-08-01'> LC08PowerRails :> OSRRequirement {
        doc /* LC-08 shall provide GPIO-controlled 5V and 12V power rails
              to payload connector. */
        :>> layer  = "LC";
        :>> source = "03_logical_architecture/logical_components.md#lc-08";
    }
    requirement def <'REQ-LC-08-02'> LC08CurrentProtect :> SafetyCriticalReq {
        doc /* LC-08 shall monitor payload current at ≥ 1 Hz and disable
              rail if exceeding limit (default 2 A). */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-08";
        :>> hazardRef  = "H-07";
        :>> responseMs = 1000.0;
    }
    requirement def <'REQ-LC-08-03'> LC08PayloadFaultPublish :> InterfaceReq {
        doc /* LC-08 shall publish a fault event to /diagnostics on payload
              overcurrent. */
        :>> layer        = "LC";
        :>> source       = "03_logical_architecture/logical_components.md#lc-08";
        :>> rosTopicName = "/diagnostics";
        :>> rosMsgType   = "diagnostic_msgs/DiagnosticArray";
    }
    requirement def <'REQ-LC-08-04'> LC08BusPassthrough :> InterfaceReq {
        doc /* LC-08 shall provide USB, I²C, and UART pass-through from
              payload connector to RPi. */
        :>> layer  = "LC";
        :>> source = "03_logical_architecture/logical_components.md#lc-08";
    }
    requirement def <'REQ-LC-08-05'> LC08PayloadIsolation :> SafetyCriticalReq {
        doc /* Payload power switching shall not affect any other power
              rail or reset the Raspberry Pi. */
        :>> layer      = "LC";
        :>> source     = "03_logical_architecture/logical_components.md#lc-08";
        :>> hazardRef  = "H-07";
        :>> responseMs = 0.0;
    }

}
