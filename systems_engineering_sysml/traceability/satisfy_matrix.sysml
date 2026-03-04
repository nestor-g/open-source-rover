/**
 * OSR::Traceability::SatisfyMatrix
 * =================================
 * Cross-layer requirement satisfaction and verification links.
 * This is the SysML v2 equivalent of systems_engineering/traceability.md
 * and the PropertyValueGroup "reqIDs" entries in the Capella model.
 *
 * Structure:
 *   OA reqs  satisfied by  SF action defs  (OA → SA)
 *   SF reqs  satisfied by  LC part defs    (SA → LA)
 *   LC reqs  satisfied by  PF parts        (LA → PA)  [future]
 *
 * Arcadia parallel: systems_engineering/traceability.md
 *                   OSR_capella_model.capella :: ownedPropertyValueGroups[reqIDs]
 *
 * Key difference vs Arcadia:
 *   Arcadia: reqIDs stored as a space-separated string in an XML attribute —
 *            no enforcement, pure documentation
 *   SysML v2: satisfy/verify are language keywords — tools can flag unsatisfied
 *             requirements automatically and generate satisfaction matrices
 */
package 'OSR::Traceability::SatisfyMatrix' {

    private import 'OSR::Core::Relations'::*;
    private import 'OSR::Requirements::OA'::*;
    private import 'OSR::Requirements::SF'::*;
    private import 'OSR::Requirements::LC'::*;
    private import 'OSR::Requirements::PF'::*;
    private import 'OSR::SA::SystemFunctions'::*;
    private import 'OSR::LA::Components'::*;
    private import 'OSR::Safety::Constraints'::*;

    // ════════════════════════════════════════════════════════════════════
    // OA → SA traceability
    // OA requirements satisfied by System Analysis functions
    // ════════════════════════════════════════════════════════════════════

    // Motion control chain
    satisfy LinkLossStop         by ReceiveAndDecodeCommand; // REQ-OA-012-04 ← SF-01
    satisfy CommandedStop        by ReceiveAndDecodeCommand; // REQ-OA-012-03 ← SF-01
    satisfy MotionLatency        by ReceiveAndDecodeCommand; // REQ-OA-012-02 ← SF-01
    satisfy SingleControllerCommand by ReceiveAndDecodeCommand;

    // Monitoring / telemetry chain
    satisfy TelemetryRate        by ProcessAndPublishTelemetry; // REQ-OA-013-01
    satisfy BatteryVisible       by ProcessAndPublishTelemetry; // REQ-OA-013-02
    satisfy FaultAlert           by DetectAndHandleFaults;      // REQ-OA-013-03
    satisfy StateDistinction     by ProcessAndPublishTelemetry; // REQ-OA-013-04
    satisfy VideoStream          by CaptureAndStreamVideo;      // REQ-OA-015-01

    // Safety / hazard response
    satisfy HazardResponseTime   by DetectAndHandleFaults;      // REQ-OA-014-01
    satisfy FaultAcknowledgement by DetectAndHandleFaults;      // REQ-OA-014-02

    // Power maintenance
    satisfy BalanceCharger       by ManagePower;  // REQ-OA-021-01 — operational constraint
    satisfy ChargeRate           by ManagePower;  // REQ-OA-021-02
    satisfy FullChargeVoltage    by ManagePower;  // REQ-OA-021-04

    // Payload extension
    satisfy PayloadPowerBudget   by SupportPayloadInterface;   // REQ-OA-041-01
    satisfy PayloadROSInterface  by SupportPayloadInterface;   // REQ-OA-041-03

    // ════════════════════════════════════════════════════════════════════
    // SF → LC traceability
    // SF requirements satisfied by Logical Components
    // (Note: most SF satisfactions are declared directly in components.sysml
    //  via 'satisfy' in each part def; this section shows cross-cutting links)
    // ════════════════════════════════════════════════════════════════════

    // SF-01 satisfied by LC-01 (comms) + LC-02 (validation)
    satisfy CmdVelInterface      by 'OSR::LA::Components'::osr::lc01;
    satisfy CommandWatchdog      by 'OSR::LA::Components'::osr::lc01;
    satisfy NaNDiscard           by 'OSR::LA::Components'::osr::lc02;
    satisfy CommandRate          by 'OSR::LA::Components'::osr::lc01;

    // SF-02 satisfied by LC-03
    satisfy KinematicModel       by 'OSR::LA::Components'::osr::lc03;
    satisfy DriveUpdateRate      by 'OSR::LA::Components'::osr::lc03;
    satisfy HaltMotorResponse    by 'OSR::LA::Components'::osr::lc03;

    // SF-03 satisfied by LC-06
    satisfy RegulatedVoltage     by 'OSR::LA::Components'::osr::lc06;
    satisfy BatteryPublishRate   by 'OSR::LA::Components'::osr::lc06;
    satisfy StateOfCharge        by 'OSR::LA::Components'::osr::lc06;
    satisfy MotorCurrentSafeStop by 'OSR::LA::Components'::osr::lc05;  // delegated to fault mon
    satisfy LowBatteryWarning    by 'OSR::LA::Components'::osr::lc05;
    satisfy BatteryVoltageSafeStop by 'OSR::LA::Components'::osr::lc05;

    // SF-04 satisfied by LC-04 + LC-07
    satisfy EncoderSampleRate    by 'OSR::LA::Components'::osr::lc04;
    satisfy IMUSampleRate        by 'OSR::LA::Components'::osr::lc04;
    satisfy OdometryPublishRate  by 'OSR::LA::Components'::osr::lc04;
    satisfy AttitudePublishRate  by 'OSR::LA::Components'::osr::lc04;
    satisfy TelemetryPublishRate by 'OSR::LA::Components'::osr::lc07;

    // SF-06 satisfied by LC-05
    satisfy MotorCurrentMonitorRate by 'OSR::LA::Components'::osr::lc05;
    satisfy MotorCurrentTripResponse by 'OSR::LA::Components'::osr::lc05;
    satisfy TiltMonitorRate      by 'OSR::LA::Components'::osr::lc05;
    satisfy TiltTripResponse     by 'OSR::LA::Components'::osr::lc05;
    satisfy SafeStopAction       by 'OSR::LA::Components'::osr::lc05;
    satisfy SafeStopLatch        by 'OSR::LA::Components'::osr::lc05;

    // SF-07 satisfied by LC-08
    satisfy PayloadPowerRails      by 'OSR::LA::Components'::osr::lc08;
    satisfy PayloadCurrentProtection by 'OSR::LA::Components'::osr::lc08;
    satisfy PayloadConnectivity    by 'OSR::LA::Components'::osr::lc08;
    satisfy PayloadPowerSwitch     by 'OSR::LA::Components'::osr::lc08;
    satisfy PayloadRailIsolation   by 'OSR::LA::Components'::osr::lc08;

    // ════════════════════════════════════════════════════════════════════
    // Safety constraint assertions
    // Declare that the OSR assembly shall satisfy all hazard constraints
    // ════════════════════════════════════════════════════════════════════
    assert constraint { 'OSR::Safety::Constraints'::MotorCurrentSafe }
    assert constraint { 'OSR::Safety::Constraints'::TiltSafe }
    assert constraint { 'OSR::Safety::Constraints'::BatteryVoltageSafe }
    assert constraint { 'OSR::Safety::Constraints'::CommWatchdogSafe }
    assert constraint { 'OSR::Safety::Constraints'::VelocitySafe }
    assert constraint { 'OSR::Safety::Constraints'::FuseSafe }
    assert constraint { 'OSR::Safety::Constraints'::PayloadCurrentSafe }
    assert constraint { 'OSR::Safety::Constraints'::NodeHealthSafe }
    assert constraint { 'OSR::Safety::Constraints'::StructuralSafe }
    assert constraint { 'OSR::Safety::Constraints'::LiPoChargeSafe }

}
