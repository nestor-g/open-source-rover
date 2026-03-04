/**
 * OSR::Core::Types
 * ================
 * Common scalar values, units, and OSR-specific attribute definitions
 * shared across all SysML v2 packages in this model.
 *
 * Arcadia parallel: systems_engineering/04_physical_architecture/physical_components.md
 *                   (hardware specs section)
 */
package 'OSR::Core::Types' {

    private import ScalarValues::*;

    // ── OSR safety thresholds — single source of truth ───────────────────
    // These values are referenced by constraint defs in 06_safety/ and by
    // requirement defs in requirements/. Changing them here propagates everywhere.
    attribute def SafetyThresholds {
        attribute motorCurrentTrip    : Real = 10.0;   // A   — H-01 motor overcurrent
        attribute batteryWarnVoltage  : Real = 11.0;   // V   — H-03 low-battery warning
        attribute batteryStopVoltage  : Real = 10.5;   // V   — H-03 safe stop
        attribute batteryFullVoltage  : Real = 12.6;   // V   — fully charged 3S LiPo
        attribute batteryMinVoltage   : Real =  9.0;   // V   — absolute minimum (damaged cell)
        attribute tiltStopAngleDeg    : Real = 35.0;   // °   — H-02 tip/rollover
        attribute commWatchdogSec     : Real =  1.0;   // s   — H-04 runaway on comm loss
        attribute maxLinearSpeed      : Real =  0.4;   // m/s — velocity clamp
        attribute maxAngularSpeed     : Real =  1.0;   // rad/s
        attribute payloadCurrentLimit : Real =  2.0;   // A   — H-07 payload overcurrent
        attribute fuseRating          : Real = 30.0;   // A   — H-06 electrical short
        attribute motorResponseMs     : Real = 100.0;  // ms  — fault → stop latency
        attribute servoResponseMs     : Real = 250.0;  // ms  — steering settle time
    }

    // ── Hardware physical parameters ─────────────────────────────────────
    attribute def RoverPhysical {
        attribute wheelCount      : Integer = 6;
        attribute cornerWheels    : Integer = 4;
        attribute driveWheels     : Integer = 6;
        attribute wheelDiameterM  : Real    = 0.13;    // m
        attribute wheelbaseM      : Real    = 0.37;    // m
        attribute trackWidthM     : Real    = 0.49;    // m
        attribute massKg          : Real    = 5.4;     // kg (without payload)
        attribute massMaxKg       : Real    = 10.0;    // kg (with payload, REQ-OA-041-04)
    }

    // ── ROS interface descriptors ─────────────────────────────────────────
    // Not executable — used as documentation attributes on ports/actions.
    attribute def ROSTopic {
        attribute topicName : String;
        attribute msgType   : String;
        attribute minRateHz : Real;
    }

    // ── Predefined ROS topics used across the model ───────────────────────
    attribute cmdVelTopic    : ROSTopic { :>> topicName = "/cmd_vel";
                                          :>> msgType   = "geometry_msgs/Twist";
                                          :>> minRateHz = 10.0; }
    attribute odomTopic      : ROSTopic { :>> topicName = "/odom";
                                          :>> msgType   = "nav_msgs/Odometry";
                                          :>> minRateHz = 10.0; }
    attribute imuTopic       : ROSTopic { :>> topicName = "/imu";
                                          :>> msgType   = "sensor_msgs/Imu";
                                          :>> minRateHz = 20.0; }
    attribute batteryTopic   : ROSTopic { :>> topicName = "/battery_state";
                                          :>> msgType   = "sensor_msgs/BatteryState";
                                          :>> minRateHz = 1.0; }
    attribute diagnosticsTopic: ROSTopic { :>> topicName = "/diagnostics";
                                           :>> msgType   = "diagnostic_msgs/DiagnosticArray";
                                           :>> minRateHz = 5.0; }
    attribute cameraTopic    : ROSTopic { :>> topicName = "/camera/image_raw/compressed";
                                          :>> msgType   = "sensor_msgs/CompressedImage";
                                          :>> minRateHz = 15.0; }

}
