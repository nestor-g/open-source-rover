/**
 * OSR::SA::SystemFunctions
 * ========================
 * SF-01..SF-07 as SysML v2 action definitions.
 * Each action def maps to one Arcadia System Function.
 *
 * Arcadia parallel: systems_engineering/02_system_analysis/system_functions.md
 *
 * Key difference vs Arcadia:
 *   Arcadia SF: prose description in markdown, no formal input/output ports
 *   SysML v2:   action def with typed in/out parameters — simulatable,
 *               allocatable to physical nodes via traceability/satisfy_matrix.sysml
 */
package 'OSR::SA::SystemFunctions' {

    private import ScalarValues::*;
    private import 'OSR::Core::Types'::*;

    // ── Shared message type stubs ─────────────────────────────────────────
    // Lightweight attribute defs representing ROS message shapes.
    attribute def TwistMsg   { attribute linearX : Real;  attribute angularZ : Real; }
    attribute def OdometryMsg{ attribute x : Real; attribute y : Real; attribute theta : Real; }
    attribute def IMUMsg     { attribute roll : Real; attribute pitch : Real; attribute yaw : Real;
                               attribute ax : Real;   attribute ay : Real;   attribute az : Real; }
    attribute def BatteryMsg { attribute voltage : Real; attribute current : Real; attribute soc : Real; }
    attribute def DiagMsg    { attribute level : Integer; attribute name : String; attribute message : String; }

    // ════════════════════════════════════════════════════════════════════
    // SF-01 — Receive and Decode Command
    // ════════════════════════════════════════════════════════════════════
    action def ReceiveAndDecodeCommand {
        doc /* Accept motion commands from ground station, validate, apply
              watchdog, and forward to mobility controller. */

        in  rawCmd     : TwistMsg;          // from /cmd_vel (Wi-Fi)
        out validCmd   : TwistMsg;          // clamped, NaN-filtered command
        out watchdogOut: Boolean;           // true = watchdog expired → zero cmd
    }

    // ════════════════════════════════════════════════════════════════════
    // SF-02 — Execute Mobility
    // ════════════════════════════════════════════════════════════════════
    action def ExecuteMobility {
        doc /* Compute per-wheel speed setpoints via rocker-bogie kinematics
              and Ackermann steering, then command actuators. */

        in  cmd         : TwistMsg;         // from SF-01
        in  haltSignal  : Boolean;          // from SF-06
        out driveSetpoints : Real[6];       // one per wheel, QPPS
        out steeringAngles : Real[4];       // corner wheel angles, degrees
    }

    // ════════════════════════════════════════════════════════════════════
    // SF-03 — Manage Power
    // ════════════════════════════════════════════════════════════════════
    action def ManagePower {
        doc /* Regulate and distribute power; monitor battery state; issue
              threshold alerts to SF-06. */

        out batteryState : BatteryMsg;      // to /battery_state
        out haltRequest  : Boolean;         // voltage < 10.5 V → halt
        out lowBatWarning: Boolean;         // voltage < 11.0 V
        out payloadEnabled: Boolean;        // GPIO payload rail state
    }

    // ════════════════════════════════════════════════════════════════════
    // SF-04 — Process and Publish Telemetry
    // ════════════════════════════════════════════════════════════════════
    action def ProcessAndPublishTelemetry {
        doc /* Sample all sensors; fuse encoder + IMU into odometry; publish
              all telemetry topics at required rates. */

        out odometry     : OdometryMsg;     // to /odom  ≥ 10 Hz
        out attitude     : IMUMsg;          // to /imu   ≥ 20 Hz
        out motorCurrents: Real[6];         // per-wheel, A — to SF-06
        out diagnostics  : DiagMsg;         // to /diagnostics
    }

    // ════════════════════════════════════════════════════════════════════
    // SF-05 — Capture and Stream Video
    // ════════════════════════════════════════════════════════════════════
    action def CaptureAndStreamVideo {
        doc /* Capture frames from Pi Camera; compress as MJPEG; publish on
              /camera/image_raw/compressed.  Optional — shall not block
              startup when camera is absent. */

        in  cameraPresent : Boolean;        // hardware detection result
        out frameStream   : String;         // topic: /camera/image_raw/compressed
        out frameRateFps  : Real;           // actual fps achieved
    }

    // ════════════════════════════════════════════════════════════════════
    // SF-06 — Detect and Handle Faults
    // ════════════════════════════════════════════════════════════════════
    action def DetectAndHandleFaults {
        doc /* Monitor motor currents, battery voltage, and IMU tilt.
              Trigger safe stop (latch) within specified response times. */

        in  motorCurrents : Real[6];        // from SF-04
        in  batteryVoltage: Real;           // from SF-03
        in  imuAttitude   : IMUMsg;         // from SF-04
        in  clearFault    : Boolean;        // operator clear command
        out haltSignal    : Boolean;        // to SF-02 — zero all motors
        out faultEvent    : DiagMsg;        // to /diagnostics
        out faultLatched  : Boolean;        // latch state
    }

    // ════════════════════════════════════════════════════════════════════
    // SF-07 — Support Payload Interface
    // ════════════════════════════════════════════════════════════════════
    action def SupportPayloadInterface {
        doc /* Provide switchable 5V and 12V payload power rails and
              USB/I2C/UART connectivity.  Monitor payload current. */

        in  enablePayload   : Boolean;      // software enable
        out payloadPower5V  : Boolean;      // GPIO rail state
        out payloadPower12V : Boolean;      // GPIO rail state
        out payloadCurrentA : Real;         // monitored current
        out payloadFault    : Boolean;      // overcurrent detected
    }

}
