/**
 * OSR::Requirements::PF
 * =====================
 * Physical Function requirements — 35 requirement defs
 * Source: systems_engineering/04_physical_architecture/physical_functions.md
 *         systems_engineering/requirements_register.md § PF Layer
 *
 * PF requirements constrain specific ROS nodes and hardware implementations.
 * They are the most concrete layer — directly testable on the physical rover.
 */
package 'OSR::Requirements::PF' {

    private import ScalarValues::*;
    private import 'OSR::Core::Relations'::*;

    // ════════════════════════════════════════════════════════════════════
    // PF-01 — Command Reception and Validation (command_node.py)
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-PF-01-01'> CommandNodeSubscribe :> InterfaceReq {
        doc /* command_node shall subscribe to /cmd_vel and process messages
              at ≥ 10 Hz. */
        :>> layer        = "PF";
        :>> source       = "04_physical_architecture/physical_functions.md#pf-01";
        :>> rosTopicName = "/cmd_vel";
        :>> rosMsgType   = "geometry_msgs/Twist";
    }
    requirement def <'REQ-PF-01-02'> WatchdogTiming :> SafetyCriticalReq {
        doc /* Watchdog timer shall trigger within 1.0–1.1 s of last
              received message. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-01";
        :>> hazardRef  = "H-04";
        :>> responseMs = 1100.0;
    }
    requirement def <'REQ-PF-01-03'> VelocityClampImpl :> OSRRequirement {
        doc /* Velocity clamping shall apply numpy.clip to both linear and
              angular components. */
        :>> layer  = "PF";
        :>> source = "04_physical_architecture/physical_functions.md#pf-01";
    }

    // ════════════════════════════════════════════════════════════════════
    // PF-02 — Kinematics and Actuator Drive (drive_node.py)
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-PF-02-01'> DriveNodeRate :> PerformanceReq {
        doc /* drive_node shall compute and transmit wheel setpoints to all
              RoboClaw units at ≥ 20 Hz. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-02";
        :>> measuredBy = "serial packet rate on RoboClaw USB port";
    }
    requirement def <'REQ-PF-02-02'> ServoUpdateTime :> PerformanceReq {
        doc /* drive_node shall update PCA9685 servo angles within 250 ms
              of angular velocity change. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-02";
        :>> measuredBy = "I2C oscilloscope trace from cmd to PCA9685 write";
    }
    requirement def <'REQ-PF-02-03'> MotorSetpointClamp :> OSRRequirement {
        doc /* Motor setpoints shall be clamped to rated maximum before
              transmission to RoboClaw. */
        :>> layer  = "PF";
        :>> source = "04_physical_architecture/physical_functions.md#pf-02";
    }
    requirement def <'REQ-PF-02-04'> ServoAngleClamp :> OSRRequirement {
        doc /* Servo angle setpoints shall be clamped to mechanical range
              of motion (±30°). */
        :>> layer  = "PF";
        :>> source = "04_physical_architecture/physical_functions.md#pf-02";
    }
    requirement def <'REQ-PF-02-05'> RoboClawFaultLog :> InterfaceReq {
        doc /* RoboClaw communication failure shall be logged to /diagnostics
              within one cycle. */
        :>> layer        = "PF";
        :>> source       = "04_physical_architecture/physical_functions.md#pf-02";
        :>> rosTopicName = "/diagnostics";
        :>> rosMsgType   = "diagnostic_msgs/DiagnosticArray";
    }

    // ════════════════════════════════════════════════════════════════════
    // PF-03 — Power Monitoring and Distribution (power_node.py)
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-PF-03-01'> PowerNodeReadRate :> PerformanceReq {
        doc /* power_node shall read INA219 battery voltage and current at
              ≥ 1 Hz. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-03";
        :>> measuredBy = "I2C read cycle rate on BNO055/INA219 bus";
    }
    requirement def <'REQ-PF-03-02'> INA219Accuracy :> PerformanceReq {
        doc /* INA219 voltage measurement shall be accurate to ±0.1 V
              versus multimeter reference. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-03";
        :>> measuredBy = "INA219 reading vs Fluke 87V at 10.5, 11.0, 12.6 V";
        :>> tolerance  = 0.1;
    }
    requirement def <'REQ-PF-03-03'> DCDCRegulation :> PerformanceReq {
        doc /* PCB DC-DC converter shall maintain 5V rail within ±5% under
              full system load. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-03";
        :>> measuredBy = "multimeter on 5V rail with all motors running";
        :>> tolerance  = 0.25;
    }
    requirement def <'REQ-PF-03-04'> BatteryStatePublish :> InterfaceReq {
        doc /* power_node shall publish sensor_msgs/BatteryState to
              /battery_state at ≥ 1 Hz. */
        :>> layer        = "PF";
        :>> source       = "04_physical_architecture/physical_functions.md#pf-03";
        :>> rosTopicName = "/battery_state";
        :>> rosMsgType   = "sensor_msgs/BatteryState";
    }
    requirement def <'REQ-PF-03-05'> SoCLookup :> OSRRequirement {
        doc /* LiPo SoC lookup shall map ≥ 12.6 V → 100% and ≤ 10.5 V →
              0% with monotonic interpolation. */
        :>> layer  = "PF";
        :>> source = "04_physical_architecture/physical_functions.md#pf-03";
    }

    // ════════════════════════════════════════════════════════════════════
    // PF-04 — Sensor Sampling and State Estimation
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-PF-04-01'> EncoderNodeRate :> PerformanceReq {
        doc /* encoder_node shall read encoder counts from all six wheels
              at ≥ 20 Hz. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-04";
        :>> measuredBy = "RoboClaw GetEncoders call rate";
    }
    requirement def <'REQ-PF-04-02'> IMUNodeRate :> PerformanceReq {
        doc /* imu_node shall read BNO055 acceleration and angular velocity
              at ≥ 50 Hz. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-04";
        :>> measuredBy = "I2C BNO055 read cycle measurement";
    }
    requirement def <'REQ-PF-04-03'> CurrentReadRate :> PerformanceReq {
        doc /* encoder_node shall read per-channel motor currents at
              ≥ 10 Hz. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-04";
        :>> measuredBy = "RoboClaw GetCurrents call rate";
    }
    requirement def <'REQ-PF-04-04'> OdomPublishRate :> PerformanceReq {
        doc /* /odom shall be published at ≥ 10 Hz from integrated encoder
              ticks. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-04";
        :>> measuredBy = "rostopic hz /odom";
    }
    requirement def <'REQ-PF-04-05'> IMUPublishRate :> PerformanceReq {
        doc /* /imu shall be published at ≥ 20 Hz from complementary
              filter output. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-04";
        :>> measuredBy = "rostopic hz /imu";
    }
    requirement def <'REQ-PF-04-06'> OdomPositionAccuracy :> PerformanceReq {
        doc /* Odometry position error shall not exceed 10% over a 1 m
              flat-surface test. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-04";
        :>> measuredBy = "1 m drive on flat floor, measure /odom vs tape";
        :>> tolerance  = 0.1;
    }
    requirement def <'REQ-PF-04-07'> IMUCalibration :> SafetyCriticalReq {
        doc /* BNO055 calibration status shall be System ≥ 2 before IMU
              data is used by fault monitor. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-04";
        :>> hazardRef  = "H-02";
        :>> responseMs = 0.0;
    }

    // ════════════════════════════════════════════════════════════════════
    // PF-05 — Fault Detection and Safe Stop (fault_node.py)
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-PF-05-01'> FaultNodeCurrentTrip :> SafetyCriticalReq {
        doc /* fault_node shall evaluate motor current thresholds within
              100 ms of 10 A exceedance. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-05";
        :>> hazardRef  = "H-01";
        :>> responseMs = 100.0;
    }
    requirement def <'REQ-PF-05-02'> FaultNodeVoltageTrip :> SafetyCriticalReq {
        doc /* fault_node shall evaluate battery voltage thresholds within
              one cycle (≤ 1 s) of 10.5 V crossing. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-05";
        :>> hazardRef  = "H-03";
        :>> responseMs = 1000.0;
    }
    requirement def <'REQ-PF-05-03'> FaultNodeTiltTrip :> SafetyCriticalReq {
        doc /* fault_node shall evaluate IMU tilt threshold within 100 ms
              of 35° exceedance. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-05";
        :>> hazardRef  = "H-02";
        :>> responseMs = 100.0;
    }
    requirement def <'REQ-PF-05-04'> SafeStopTransmit :> SafetyCriticalReq {
        doc /* On safe stop trigger, fault_node shall transmit SpeedM1M2(0,0)
              to all RoboClaws within 50 ms. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-05";
        :>> hazardRef  = "H-01";
        :>> responseMs = 50.0;
    }
    requirement def <'REQ-PF-05-05'> FaultNodeDiagPublish :> InterfaceReq {
        doc /* fault_node shall publish DiagnosticStatus ERROR to /diagnostics
              within one cycle of fault detection. */
        :>> layer        = "PF";
        :>> source       = "04_physical_architecture/physical_functions.md#pf-05";
        :>> rosTopicName = "/diagnostics";
        :>> rosMsgType   = "diagnostic_msgs/DiagnosticArray";
    }
    requirement def <'REQ-PF-05-06'> FaultNodeLatch :> SafetyCriticalReq {
        doc /* Safe stop shall latch; fault_node shall block commands until
              clear_fault and condition resolved. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-05";
        :>> hazardRef  = "H-01";
        :>> responseMs = 0.0;
    }

    // ════════════════════════════════════════════════════════════════════
    // PF-06 — Camera Capture and Streaming (camera_node.py)
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-PF-06-01'> CameraFrameRate :> PerformanceReq {
        doc /* camera_node shall capture frames at ≥ 15 fps at 640×480
              when camera is present. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-06";
        :>> measuredBy = "frame count over 10 s from ground station";
    }
    requirement def <'REQ-PF-06-02'> CameraTopic :> InterfaceReq {
        doc /* Compressed frames shall be published on
              /camera/image_raw/compressed as MJPEG. */
        :>> layer        = "PF";
        :>> source       = "04_physical_architecture/physical_functions.md#pf-06";
        :>> rosTopicName = "/camera/image_raw/compressed";
        :>> rosMsgType   = "sensor_msgs/CompressedImage";
    }
    requirement def <'REQ-PF-06-03'> CameraLatency :> PerformanceReq {
        doc /* End-to-end video latency shall not exceed 500 ms over local
              Wi-Fi. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-06";
        :>> measuredBy = "clock comparison rover frame timestamp vs display";
    }
    requirement def <'REQ-PF-06-04'> CameraOptionalShutdown :> OSRRequirement {
        doc /* If no camera is present at launch, camera_node shall exit
              gracefully without affecting other nodes. */
        :>> layer  = "PF";
        :>> source = "04_physical_architecture/physical_functions.md#pf-06";
    }
    requirement def <'REQ-PF-06-05'> CameraCPU :> PerformanceReq {
        doc /* CPU usage by camera_node shall not exceed 20% of one RPi
              core during streaming. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-06";
        :>> measuredBy = "top/htop measurement during 60 s stream";
        :>> tolerance  = 5.0;
    }

    // ════════════════════════════════════════════════════════════════════
    // PF-07 — Payload Interface
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-PF-07-01'> PayloadSwitchTiming :> PerformanceReq {
        doc /* RPi GPIO toggle of payload load switch shall energise/
              de-energise payload connector within 10 ms. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-07";
        :>> measuredBy = "oscilloscope on payload connector vs GPIO signal";
    }
    requirement def <'REQ-PF-07-02'> PayloadCurrentCutoff :> SafetyCriticalReq {
        doc /* power_node shall read payload current at ≥ 1 Hz and disable
              payload power if > 2 A. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-07";
        :>> hazardRef  = "H-07";
        :>> responseMs = 1000.0;
    }
    requirement def <'REQ-PF-07-03'> USBEnumeration :> PerformanceReq {
        doc /* USB device on payload connector shall enumerate on RPi
              within 5 s of connection. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-07";
        :>> measuredBy = "lsusb check after device connect";
    }
    requirement def <'REQ-PF-07-04'> I2CDetect :> OSRRequirement {
        doc /* Payload I²C device at non-conflicting address shall be
              detectable by i2cdetect. */
        :>> layer  = "PF";
        :>> source = "04_physical_architecture/physical_functions.md#pf-07";
    }
    requirement def <'REQ-PF-07-05'> PayloadVoltageGlitch :> SafetyCriticalReq {
        doc /* Payload power switching shall not cause > 0.2 V glitch on
              the 5V logic rail. */
        :>> layer      = "PF";
        :>> source     = "04_physical_architecture/physical_functions.md#pf-07";
        :>> hazardRef  = "H-08";
        :>> responseMs = 0.0;
    }

}
