/**
 * OSR::Requirements::SF
 * =====================
 * System Function requirements — 34 requirement defs
 * Source: systems_engineering/02_system_analysis/system_functions.md
 *         systems_engineering/requirements_register.md § SF Layer
 *
 * SF requirements express WHAT the system shall do (not how).
 * They are satisfied by logical components in 03_logical_architecture/.
 */
package 'OSR::Requirements::SF' {

    private import ScalarValues::*;
    private import 'OSR::Core::Relations'::*;

    // ════════════════════════════════════════════════════════════════════
    // SF-01 — Receive and Decode Command
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-SF-01-01'> CmdVelInterface :> InterfaceReq {
        doc /* System shall accept motion commands as geometry_msgs/Twist
              on /cmd_vel. */
        :>> layer        = "SF";
        :>> source       = "02_system_analysis/system_functions.md#sf-01";
        :>> rosTopicName = "/cmd_vel";
        :>> rosMsgType   = "geometry_msgs/Twist";
    }
    requirement def <'REQ-SF-01-02'> CommandWatchdog :> SafetyCriticalReq {
        doc /* System shall apply a 1-second command watchdog, outputting
              zero velocity on timeout. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-01";
        :>> hazardRef  = "H-04";
        :>> responseMs = 1000.0;
    }
    requirement def <'REQ-SF-01-03'> NaNDiscard :> SafetyCriticalReq {
        doc /* System shall discard command messages containing NaN or Inf
              values. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-01";
        :>> hazardRef  = "H-05";
        :>> responseMs = 0.0;
    }
    requirement def <'REQ-SF-01-04'> CommandRate :> PerformanceReq {
        doc /* System shall process command messages at a minimum rate of
              10 Hz. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-01";
        :>> measuredBy = "rostopic hz /cmd_vel measurement";
    }

    // ════════════════════════════════════════════════════════════════════
    // SF-02 — Execute Mobility
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-SF-02-01'> KinematicModel :> OSRRequirement {
        doc /* System shall compute per-wheel speed setpoints using the OSR
              rocker-bogie kinematic model. */
        :>> layer  = "SF";
        :>> source = "02_system_analysis/system_functions.md#sf-02";
    }
    requirement def <'REQ-SF-02-02'> DriveUpdateRate :> PerformanceReq {
        doc /* Drive wheel setpoints shall be updated at ≥ 20 Hz. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-02";
        :>> measuredBy = "oscilloscope on RoboClaw serial or rostopic hz";
    }
    requirement def <'REQ-SF-02-03'> DriveSetpointClamp :> OSRRequirement {
        doc /* System shall clamp drive setpoints to motor controller rated
              maximum speed. */
        :>> layer  = "SF";
        :>> source = "02_system_analysis/system_functions.md#sf-02";
    }
    requirement def <'REQ-SF-02-04'> SteeringResponse :> PerformanceReq {
        doc /* System shall position corner steering servos to
              Ackermann-correct angles within 250 ms. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-02";
        :>> measuredBy = "timed angle-change test with angular encoder";
    }
    requirement def <'REQ-SF-02-05'> HaltMotorResponse :> SafetyCriticalReq {
        doc /* Upon halt signal from SF-06, SF-02 shall set all drive motor
              setpoints to zero within ≤ 50 ms. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-02";
        :>> hazardRef  = "H-01";
        :>> responseMs = 50.0;
    }

    // ════════════════════════════════════════════════════════════════════
    // SF-03 — Manage Power
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-SF-03-01'> RegulatedVoltage :> PerformanceReq {
        doc /* System shall provide regulated 5V ±5% to RPi and logic
              peripherals. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-03";
        :>> measuredBy = "multimeter measurement under full load";
        :>> tolerance  = 0.25;   // ±5% of 5V
    }
    requirement def <'REQ-SF-03-02'> BatteryPublishRate :> PerformanceReq {
        doc /* System shall read and publish battery voltage and current at
              ≥ 1 Hz. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-03";
        :>> measuredBy = "rostopic hz /battery_state";
    }
    requirement def <'REQ-SF-03-03'> StateOfCharge :> OSRRequirement {
        doc /* System shall compute and publish state-of-charge as a
              percentage from LiPo discharge curve. */
        :>> layer  = "SF";
        :>> source = "02_system_analysis/system_functions.md#sf-03";
    }
    requirement def <'REQ-SF-03-04'> MotorCurrentSafeStop :> SafetyCriticalReq {
        doc /* System shall trigger safe stop when any motor current exceeds
              10 A. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-03";
        :>> hazardRef  = "H-01";
        :>> responseMs = 100.0;
    }
    requirement def <'REQ-SF-03-05'> LowBatteryWarning :> SafetyCriticalReq {
        doc /* System shall publish low-battery warning when voltage falls
              below 11.0 V. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-03";
        :>> hazardRef  = "H-03";
        :>> responseMs = 1000.0;
    }
    requirement def <'REQ-SF-03-06'> BatteryVoltageSafeStop :> SafetyCriticalReq {
        doc /* System shall trigger safe stop when battery voltage falls
              below 10.5 V. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-03";
        :>> hazardRef  = "H-03";
        :>> responseMs = 1000.0;
    }

    // ════════════════════════════════════════════════════════════════════
    // SF-04 — Process and Publish Telemetry
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-SF-04-01'> EncoderSampleRate :> PerformanceReq {
        doc /* System shall sample wheel encoder counts at ≥ 20 Hz per
              wheel. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-04";
        :>> measuredBy = "rostopic hz /wheel_encoders";
    }
    requirement def <'REQ-SF-04-02'> IMUSampleRate :> PerformanceReq {
        doc /* System shall sample IMU acceleration and gyroscope at
              ≥ 50 Hz. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-04";
        :>> measuredBy = "rostopic hz /imu/raw";
    }
    requirement def <'REQ-SF-04-03'> OdometryPublishRate :> PerformanceReq {
        doc /* System shall publish odometry (/odom) at ≥ 10 Hz. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-04";
        :>> measuredBy = "rostopic hz /odom";
    }
    requirement def <'REQ-SF-04-04'> AttitudePublishRate :> PerformanceReq {
        doc /* System shall publish attitude (/imu) at ≥ 20 Hz. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-04";
        :>> measuredBy = "rostopic hz /imu";
    }
    requirement def <'REQ-SF-04-05'> TelemetryPublishRate :> PerformanceReq {
        doc /* System shall publish telemetry topics to ground station at
              ≥ 5 Hz. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-04";
        :>> measuredBy = "rostopic hz /diagnostics from ground station";
    }
    requirement def <'REQ-SF-04-06'> TelemetryLatency :> PerformanceReq {
        doc /* Telemetry latency from sensor read to Wi-Fi transmission
              shall not exceed 200 ms. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-04";
        :>> measuredBy = "timestamped end-to-end latency measurement";
    }

    // ════════════════════════════════════════════════════════════════════
    // SF-05 — Capture and Stream Video
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-SF-05-01'> VideoFrameRate :> PerformanceReq {
        doc /* System shall capture and publish video at ≥ 15 fps at
              640×480 when camera is installed. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-05";
        :>> measuredBy = "frame count over 10 s at ground station";
    }
    requirement def <'REQ-SF-05-02'> VideoTopic :> InterfaceReq {
        doc /* System shall publish compressed video on
              /camera/image_raw/compressed. */
        :>> layer        = "SF";
        :>> source       = "02_system_analysis/system_functions.md#sf-05";
        :>> rosTopicName = "/camera/image_raw/compressed";
        :>> rosMsgType   = "sensor_msgs/CompressedImage";
    }
    requirement def <'REQ-SF-05-03'> VideoLatency :> PerformanceReq {
        doc /* Video stream latency shall not exceed 500 ms over local
              Wi-Fi. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-05";
        :>> measuredBy = "timestamp comparison: rover clock vs display frame";
    }
    requirement def <'REQ-SF-05-04'> CameraOptional :> OSRRequirement {
        doc /* System shall start without error when camera is absent;
              SF-05 shall be inactive without affecting other functions. */
        :>> layer  = "SF";
        :>> source = "02_system_analysis/system_functions.md#sf-05";
    }

    // ════════════════════════════════════════════════════════════════════
    // SF-06 — Detect and Handle Faults
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-SF-06-01'> MotorCurrentMonitorRate :> SafetyCriticalReq {
        doc /* System shall monitor motor channel current at ≥ 10 Hz. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-06";
        :>> hazardRef  = "H-01";
        :>> responseMs = 100.0;
    }
    requirement def <'REQ-SF-06-02'> MotorCurrentTripResponse :> SafetyCriticalReq {
        doc /* System shall trigger safe stop within 100 ms of any motor
              current exceeding 10 A. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-06";
        :>> hazardRef  = "H-01";
        :>> responseMs = 100.0;
    }
    requirement def <'REQ-SF-06-03'> BatteryFaultThresholds :> SafetyCriticalReq {
        doc /* System shall publish battery warning at < 11.0 V and trigger
              safe stop at < 10.5 V. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-06";
        :>> hazardRef  = "H-03";
        :>> responseMs = 1000.0;
    }
    requirement def <'REQ-SF-06-04'> TiltMonitorRate :> SafetyCriticalReq {
        doc /* System shall monitor rover roll and pitch at ≥ 10 Hz. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-06";
        :>> hazardRef  = "H-02";
        :>> responseMs = 100.0;
    }
    requirement def <'REQ-SF-06-05'> TiltTripResponse :> SafetyCriticalReq {
        doc /* System shall trigger safe stop within 100 ms of roll or
              pitch exceeding 35°. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-06";
        :>> hazardRef  = "H-02";
        :>> responseMs = 100.0;
    }
    requirement def <'REQ-SF-06-06'> SafeStopAction :> SafetyCriticalReq {
        doc /* Upon safe stop, system shall zero all drive motor setpoints
              and publish fault event to /diagnostics. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-06";
        :>> hazardRef  = "H-01";
        :>> responseMs = 50.0;
    }
    requirement def <'REQ-SF-06-07'> SafeStopLatch :> SafetyCriticalReq {
        doc /* Safe stop shall latch; rover shall not resume motion until
              operator clear command is received and fault resolved. */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-06";
        :>> hazardRef  = "H-01";
        :>> responseMs = 0.0;
    }

    // ════════════════════════════════════════════════════════════════════
    // SF-07 — Support Payload Interface
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-SF-07-01'> PayloadPowerRails :> OSRRequirement {
        doc /* System shall provide switchable 5V @ ≥ 2 A and 12V @ ≥ 2 A
              to payload connector. */
        :>> layer  = "SF";
        :>> source = "02_system_analysis/system_functions.md#sf-07";
    }
    requirement def <'REQ-SF-07-02'> PayloadCurrentProtection :> SafetyCriticalReq {
        doc /* System shall monitor payload current and disable rail if
              exceeding configured limit (default 2 A). */
        :>> layer      = "SF";
        :>> source     = "02_system_analysis/system_functions.md#sf-07";
        :>> hazardRef  = "H-07";
        :>> responseMs = 1000.0;
    }
    requirement def <'REQ-SF-07-03'> PayloadConnectivity :> InterfaceReq {
        doc /* System shall provide USB, I²C, and UART connectivity to
              payload from Raspberry Pi. */
        :>> layer  = "SF";
        :>> source = "02_system_analysis/system_functions.md#sf-07";
    }
    requirement def <'REQ-SF-07-04'> PayloadPowerSwitch :> OSRRequirement {
        doc /* Payload power enable/disable shall be controllable via
              software (GPIO). */
        :>> layer  = "SF";
        :>> source = "02_system_analysis/system_functions.md#sf-07";
    }
    requirement def <'REQ-SF-07-05'> PayloadRailIsolation :> OSRRequirement {
        doc /* Payload power rail switching shall not interrupt or reset
              any other system power rail. */
        :>> layer  = "SF";
        :>> source = "02_system_analysis/system_functions.md#sf-07";
    }

}
