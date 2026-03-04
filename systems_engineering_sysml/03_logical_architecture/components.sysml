/**
 * OSR::LA::Components
 * ===================
 * LC-01..LC-08 as SysML v2 part definitions.
 * Each part def maps to one Arcadia Logical Component.
 *
 * Arcadia parallel: systems_engineering/03_logical_architecture/logical_components.md
 *
 * Key difference vs Arcadia:
 *   Arcadia LC: described in markdown tables — no formal attribute types or ports
 *   SysML v2:  part def with typed attributes and explicit satisfy statements
 *              creates machine-checkable traceability to requirement defs
 */
package 'OSR::LA::Components' {

    private import ScalarValues::*;
    private import 'OSR::Core::Types'::*;
    private import 'OSR::Requirements::SF'::*;
    private import 'OSR::Requirements::LC'::*;

    // ════════════════════════════════════════════════════════════════════
    // LC-01 — Communication Manager
    // ════════════════════════════════════════════════════════════════════
    part def CommunicationManager {
        doc /* Manages all Wi-Fi communication between rover and ground
              station.  Implements command watchdog. */

        attribute watchdogTimeoutS  : Real    = 1.0;
        attribute maxRangeM         : Real    = 50.0;
        attribute cmdVelTopicName   : String  = "/cmd_vel";

        // Formal requirement satisfaction — these are the ones LC-01
        // is responsible for delivering.
        satisfy LC01CmdVelReceive;
        satisfy LC01WatchdogNotify;
        satisfy LC01TelemetryRelay;
        satisfy LC01VideoRelay;
        satisfy LC01NoPacketLoss;
    }

    // ════════════════════════════════════════════════════════════════════
    // LC-02 — Command Processor
    // ════════════════════════════════════════════════════════════════════
    part def CommandProcessor {
        doc /* Validates, clamps, and routes motion commands.  Outputs zero
              velocity on halt or watchdog expiry. */

        attribute maxLinearSpeedMs  : Real = 0.4;     // m/s clamp
        attribute maxAngularSpeedRs : Real = 1.0;     // rad/s clamp

        satisfy LC02TwistParse;
        satisfy LC02NaNDiscard;
        satisfy LC02VelocityClamp;
        satisfy LC02HaltOutput;
        satisfy LC02WatchdogZero;
    }

    // ════════════════════════════════════════════════════════════════════
    // LC-03 — Mobility Controller
    // ════════════════════════════════════════════════════════════════════
    part def MobilityController {
        doc /* Implements rocker-bogie kinematics and Ackermann steering
              model.  Commands all 6 drive motors and 4 steering servos. */

        attribute wheelCount        : Integer = 6;
        attribute cornerWheelCount  : Integer = 4;
        attribute driveUpdateRateHz : Real    = 20.0;
        attribute steeringRangeDeg  : Real    = 30.0;  // ±30° mechanical limit
        attribute steeringSettleMs  : Real    = 250.0;

        satisfy LC03KinematicModel;
        satisfy LC03AckermannSteering;
        satisfy LC03DriveRate;
        satisfy LC03SteeringSettle;
        satisfy LC03SpeedClamp;
        satisfy LC03SteeringClamp;
        satisfy LC03HaltZero;
    }

    // ════════════════════════════════════════════════════════════════════
    // LC-04 — State Estimator
    // ════════════════════════════════════════════════════════════════════
    part def StateEstimator {
        doc /* Fuses wheel encoders and BNO055 IMU into odometry and
              attitude estimates; publishes all sensor telemetry. */

        attribute encoderRateHz     : Real = 20.0;
        attribute imuRateHz         : Real = 50.0;
        attribute currentRateHz     : Real = 10.0;
        attribute odomPublishRateHz : Real = 10.0;
        attribute imuPublishRateHz  : Real = 20.0;
        attribute odomErrorPct      : Real = 0.10;    // ≤ 10% over 1 m

        satisfy LC04EncoderRate;
        satisfy LC04IMURate;
        satisfy LC04CurrentReadRate;
        satisfy LC04OdomPublish;
        satisfy LC04IMUPublish;
        satisfy LC04CurrentToFaultMon;
        satisfy LC04OdomAccuracy;
    }

    // ════════════════════════════════════════════════════════════════════
    // LC-05 — Fault Monitor
    // ════════════════════════════════════════════════════════════════════
    part def FaultMonitor {
        doc /* Safety-critical node.  Monitors motor current, battery
              voltage, and IMU tilt.  Latches halt on threshold breach. */

        attribute currentThresholdA     : Real = 10.0;   // H-01 trip
        attribute currentMonitorRateHz  : Real = 10.0;
        attribute currentResponseMs     : Real = 100.0;
        attribute voltageWarnV          : Real = 11.0;   // H-03
        attribute voltageStopV          : Real = 10.5;   // H-03
        attribute voltageMonitorRateHz  : Real = 1.0;
        attribute tiltThresholdDeg      : Real = 35.0;   // H-02
        attribute tiltMonitorRateHz     : Real = 10.0;
        attribute tiltResponseMs        : Real = 100.0;

        satisfy LC05CurrentMonitor;
        satisfy LC05VoltageMonitor;
        satisfy LC05TiltMonitor;
        satisfy LC05FaultLatch;
        satisfy LC05ClearFaultVerify;
        satisfy LC05DiagPublish;
    }

    // ════════════════════════════════════════════════════════════════════
    // LC-06 — Power Manager
    // ════════════════════════════════════════════════════════════════════
    part def PowerManager {
        doc /* Reads INA219 power monitor; computes SoC; provides
              software-switchable payload power rail. */

        attribute readRateHz        : Real = 1.0;
        attribute voltageAccuracyV  : Real = 0.1;   // ±0.1 V
        attribute fullChargeV       : Real = 12.6;  // 100% SoC
        attribute emptyV            : Real = 10.5;  // 0% SoC
        attribute payloadDefaultOn  : Boolean = false;

        satisfy LC06INA219Rate;
        satisfy LC06BatteryPublish;
        satisfy LC06SoCCompute;
        satisfy LC06PayloadEnable;
        satisfy LC06VoltageAccuracy;
    }

    // ════════════════════════════════════════════════════════════════════
    // LC-07 — Telemetry Publisher
    // ════════════════════════════════════════════════════════════════════
    part def TelemetryPublisher {
        doc /* Aggregates all telemetry and publishes a unified diagnostic
              summary to the ground station. */

        attribute publishRateHz     : Real = 5.0;
        attribute maxLatencyMs      : Real = 50.0;

        satisfy LC07DiagRate;
        satisfy LC07TelemetryContent;
        satisfy LC07VideoRelay;
        satisfy LC07LatencyBudget;
    }

    // ════════════════════════════════════════════════════════════════════
    // LC-08 — Payload Manager
    // ════════════════════════════════════════════════════════════════════
    part def PayloadManager {
        doc /* Controls payload power rails (5V, 12V) and provides
              USB/I2C/UART bus pass-through. */

        attribute powerRail5V_A     : Real = 2.0;   // ≥ 2 A rated
        attribute powerRail12V_A    : Real = 2.0;   // ≥ 2 A rated
        attribute currentLimitA     : Real = 2.0;   // default cut-off
        attribute monitorRateHz     : Real = 1.0;

        satisfy LC08PowerRails;
        satisfy LC08CurrentProtect;
        satisfy LC08PayloadFaultPublish;
        satisfy LC08BusPassthrough;
        satisfy LC08PayloadIsolation;
    }

    // ════════════════════════════════════════════════════════════════════
    // System-level assembly — OSR logical architecture
    // ════════════════════════════════════════════════════════════════════
    part osr : Object {
        part lc01 : CommunicationManager;
        part lc02 : CommandProcessor;
        part lc03 : MobilityController;
        part lc04 : StateEstimator;
        part lc05 : FaultMonitor;
        part lc06 : PowerManager;
        part lc07 : TelemetryPublisher;
        part lc08 : PayloadManager;
    }

}
