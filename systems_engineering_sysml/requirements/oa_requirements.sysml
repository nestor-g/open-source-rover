/**
 * OSR::Requirements::OA
 * =====================
 * Operational Analysis requirements — 53 requirement defs
 * Source: systems_engineering/01_operational_analysis/operational_activities.md
 *         systems_engineering/requirements_register.md § OA Layer
 *
 * Each requirement def maps 1:1 to a REQ-OA-xxx-xx entry in the Arcadia
 * requirements register.  The <'short-id'> is the canonical ID for cross-
 * referencing in traceability/satisfy_matrix.sysml.
 */
package 'OSR::Requirements::OA' {

    private import ScalarValues::*;
    private import 'OSR::Core::Relations'::*;

    // ════════════════════════════════════════════════════════════════════
    // OAct-01 — Conduct Rover Mission
    // ════════════════════════════════════════════════════════════════════

    // OAct-01.1 — Plan Traverse Route
    requirement def <'REQ-OA-011-01'> TerrainAssessment :> OSRRequirement {
        doc /* Operator shall assess visible terrain for obstacles before
              commanding motion into any new area. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-011";
    }
    requirement def <'REQ-OA-011-02'> TraversePathPlanning :> OSRRequirement {
        doc /* Operator shall define a traverse path avoiding obstacles
              exceeding the rover's mobility limits. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-011";
    }
    requirement def <'REQ-OA-011-03'> GoNoGoDecision :> OSRRequirement {
        doc /* A go/no-go decision shall be made and communicated before
              each traverse segment. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-011";
    }

    // OAct-01.2 — Command Rover Motion
    requirement def <'REQ-OA-012-01'> SingleControllerCommand :> OSRRequirement {
        doc /* Operator shall command rover motion using a single handheld
              controller. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-012";
    }
    requirement def <'REQ-OA-012-02'> MotionLatency :> PerformanceReq {
        doc /* Motion commands shall be transmitted with round-trip latency
              ≤ 200 ms under nominal Wi-Fi. */
        :>> layer      = "OA";
        :>> source     = "01_operational_analysis/operational_activities.md#oact-012";
        :>> measuredBy = "network round-trip time measurement";
        :>> tolerance  = 0.0;
    }
    requirement def <'REQ-OA-012-03'> CommandedStop :> PerformanceReq {
        doc /* Rover shall come to a complete stop within 1 s of operator
              releasing the motion command. */
        :>> layer      = "OA";
        :>> source     = "01_operational_analysis/operational_activities.md#oact-012";
        :>> measuredBy = "timed stop test from 0.4 m/s";
    }
    requirement def <'REQ-OA-012-04'> LinkLossStop :> SafetyCriticalReq {
        doc /* Rover shall execute a commanded stop within 1 s if the
              wireless link is lost. */
        :>> layer      = "OA";
        :>> source     = "01_operational_analysis/operational_activities.md#oact-012";
        :>> hazardRef  = "H-04";
        :>> responseMs = 1000.0;
    }

    // OAct-01.3 — Monitor Rover State
    requirement def <'REQ-OA-013-01'> TelemetryRate :> PerformanceReq {
        doc /* Operator shall receive rover telemetry updates at ≥ 5 Hz
              during active operation. */
        :>> layer      = "OA";
        :>> source     = "01_operational_analysis/operational_activities.md#oact-013";
        :>> measuredBy = "telemetry topic rate measurement";
    }
    requirement def <'REQ-OA-013-02'> BatteryVisible :> OSRRequirement {
        doc /* Battery state-of-charge shall be visible on the ground station
              display at all times. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-013";
    }
    requirement def <'REQ-OA-013-03'> FaultAlert :> OSRRequirement {
        doc /* Any fault condition shall produce a visible alert on the
              ground station within one telemetry cycle. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-013";
    }
    requirement def <'REQ-OA-013-04'> StateDistinction :> OSRRequirement {
        doc /* Operator shall distinguish normal from fault operating states
              from ground station display alone. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-013";
    }

    // OAct-01.4 — Respond to Hazard
    requirement def <'REQ-OA-014-01'> HazardResponseTime :> SafetyCriticalReq {
        doc /* Operator shall issue a stop command within 3 s of recognising
              a hazard condition. */
        :>> layer      = "OA";
        :>> source     = "01_operational_analysis/operational_activities.md#oact-014";
        :>> hazardRef  = "H-05";
        :>> responseMs = 3000.0;
    }
    requirement def <'REQ-OA-014-02'> FaultAcknowledgement :> OSRRequirement {
        doc /* Operator shall acknowledge all system-generated fault events
              before resuming rover motion. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-014";
    }
    requirement def <'REQ-OA-014-03'> RecoveryProcedure :> OSRRequirement {
        doc /* A clear recovery procedure shall exist for each fault type. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-014";
    }

    // OAct-01.5 — Collect Sensor Data
    requirement def <'REQ-OA-015-01'> VideoStream :> PerformanceReq {
        doc /* Rover shall stream live camera video to ground station at
              ≥ 10 fps during operation. */
        :>> layer      = "OA";
        :>> source     = "01_operational_analysis/operational_activities.md#oact-015";
        :>> measuredBy = "frame rate measurement at ground station";
    }
    requirement def <'REQ-OA-015-02'> DataTimestamp :> OSRRequirement {
        doc /* All sensor data shall be time-stamped with the rover's
              system clock. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-015";
    }
    requirement def <'REQ-OA-015-03'> DataDownload :> OSRRequirement {
        doc /* Collected data shall be accessible for download via SSH after
              mission completion. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-015";
    }

    // ════════════════════════════════════════════════════════════════════
    // OAct-02 — Maintain Rover
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-OA-021-01'> BalanceCharger :> SafetyCriticalReq {
        doc /* Battery shall be charged using a balance charger with
              cell-level voltage monitoring. */
        :>> layer      = "OA";
        :>> source     = "01_operational_analysis/operational_activities.md#oact-021";
        :>> hazardRef  = "H-10";
        :>> responseMs = 0.0;
    }
    requirement def <'REQ-OA-021-02'> ChargeRate :> SafetyCriticalReq {
        doc /* Charge rate shall not exceed 1C. */
        :>> layer      = "OA";
        :>> source     = "01_operational_analysis/operational_activities.md#oact-021";
        :>> hazardRef  = "H-10";
        :>> responseMs = 0.0;
    }
    requirement def <'REQ-OA-021-03'> NoInRoverCharging :> SafetyCriticalReq {
        doc /* Battery shall not be charged while installed in rover unless
              a dedicated charge circuit with thermal monitoring is present. */
        :>> layer      = "OA";
        :>> source     = "01_operational_analysis/operational_activities.md#oact-021";
        :>> hazardRef  = "H-10";
        :>> responseMs = 0.0;
    }
    requirement def <'REQ-OA-021-04'> FullChargeVoltage :> PerformanceReq {
        doc /* A fully charged 3S LiPo shall measure ≥ 12.6 V at pack
              terminals. */
        :>> layer      = "OA";
        :>> source     = "01_operational_analysis/operational_activities.md#oact-021";
        :>> measuredBy = "multimeter measurement at battery terminals";
    }

    requirement def <'REQ-OA-022-01'> PostSessionInspection :> OSRRequirement {
        doc /* A hardware inspection shall be performed after every operating
              session involving terrain traverse. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-022";
    }
    requirement def <'REQ-OA-022-02'> FastenerRetorque :> OSRRequirement {
        doc /* Any loose fastener shall be re-torqued before the next
              mission. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-022";
    }
    requirement def <'REQ-OA-022-03'> ComponentReplacement :> OSRRequirement {
        doc /* Worn or damaged components shall be replaced before rover is
              returned to service. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-022";
    }

    requirement def <'REQ-OA-023-01'> SSHUpdate :> OSRRequirement {
        doc /* Software updates shall be deployed via SSH without requiring
              physical disassembly. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-023";
    }
    requirement def <'REQ-OA-023-02'> PostUpdateVerify :> OSRRequirement {
        doc /* After any update, all ROS nodes shall be verified running
              before returning rover to service. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-023";
    }
    requirement def <'REQ-OA-023-03'> PostUpdateFunctionTest :> PerformanceReq {
        doc /* Post-update functional test shall include ≥ 0.5 m commanded
              forward motion and full stop. */
        :>> layer      = "OA";
        :>> source     = "01_operational_analysis/operational_activities.md#oact-023";
        :>> measuredBy = "functional test post-update";
    }

    // ════════════════════════════════════════════════════════════════════
    // OAct-03 — Build Rover
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-OA-031-01'> BOMCompliance :> OSRRequirement {
        doc /* All sourced components shall meet or exceed BOM
              specifications. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-031";
    }
    requirement def <'REQ-OA-031-02'> QuantityVerification :> OSRRequirement {
        doc /* Builder shall verify received quantities against BOM before
              beginning assembly. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-031";
    }
    requirement def <'REQ-OA-031-03'> SubstituteCompatibility :> OSRRequirement {
        doc /* Substitute components shall be verified compatible before
              use. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-031";
    }

    requirement def <'REQ-OA-032-01'> HandToolAssembly :> OSRRequirement {
        doc /* Mechanical assembly shall be completable using only standard
              hand tools. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-032";
    }
    requirement def <'REQ-OA-032-02'> FlangeBearings :> OSRRequirement {
        doc /* All pivot joints shall use flanged bearings. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-032";
    }
    requirement def <'REQ-OA-032-03'> FastenerTorque :> OSRRequirement {
        doc /* All structural fasteners shall be tightened to finger-tight
              plus 1/4 turn unless otherwise specified. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-032";
    }
    requirement def <'REQ-OA-032-04'> ChassisStructural :> OSRRequirement {
        doc /* Completed chassis shall support rover total mass without
              visible deflection. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-032";
    }

    requirement def <'REQ-OA-033-01'> ContinuityCheck :> SafetyCriticalReq {
        doc /* A continuity check shall be performed on all power rails
              before applying battery power for the first time. */
        :>> layer      = "OA";
        :>> source     = "01_operational_analysis/operational_activities.md#oact-033";
        :>> hazardRef  = "H-06";
        :>> responseMs = 0.0;
    }
    requirement def <'REQ-OA-033-02'> WireGauge :> SafetyCriticalReq {
        doc /* Wire gauges shall meet or exceed the minimum specified in
              the harness guide. */
        :>> layer      = "OA";
        :>> source     = "01_operational_analysis/operational_activities.md#oact-033";
        :>> hazardRef  = "H-06";
        :>> responseMs = 0.0;
    }
    requirement def <'REQ-OA-033-03'> InLineFuse :> SafetyCriticalReq {
        doc /* An in-line fuse (≤ 30 A) shall be installed between battery
              and PCB input. */
        :>> layer      = "OA";
        :>> source     = "01_operational_analysis/operational_activities.md#oact-033";
        :>> hazardRef  = "H-06";
        :>> responseMs = 0.0;
    }
    requirement def <'REQ-OA-033-04'> PositiveRetentionConnectors :> OSRRequirement {
        doc /* All motor and servo connectors shall be secured with
              positive-retention connectors. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-033";
    }

    requirement def <'REQ-OA-034-01'> NoROSExpertise :> OSRRequirement {
        doc /* Software installation shall be completable following the
              documented guide without prior ROS expertise. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-034";
    }
    requirement def <'REQ-OA-034-02'> CleanLaunch :> OSRRequirement {
        doc /* All ROS nodes shall start without errors on first launch
              after fresh installation. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-034";
    }
    requirement def <'REQ-OA-034-03'> CmdVelResponse :> PerformanceReq {
        doc /* Rover shall respond to /cmd_vel within 5 minutes of
              completing software installation. */
        :>> layer      = "OA";
        :>> source     = "01_operational_analysis/operational_activities.md#oact-034";
        :>> measuredBy = "timed first-run test";
    }
    requirement def <'REQ-OA-034-04'> WiFiSSHFirst :> OSRRequirement {
        doc /* Wi-Fi connectivity and SSH access shall be confirmed before
              launching ROS. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-034";
    }

    // ════════════════════════════════════════════════════════════════════
    // OAct-04 — Extend Rover Capability
    // ════════════════════════════════════════════════════════════════════

    requirement def <'REQ-OA-041-01'> PayloadPowerBudget :> OSRRequirement {
        doc /* Payload designs shall not exceed power budget allocations. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-041";
    }
    requirement def <'REQ-OA-041-02'> PayloadBoltPattern :> OSRRequirement {
        doc /* Mechanical payload attachments shall use the standard M3 bolt
              pattern without permanent chassis modification. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-041";
    }
    requirement def <'REQ-OA-041-03'> PayloadROSInterface :> InterfaceReq {
        doc /* Design package shall include a defined ROS data interface
              (topic name, message type, update rate). */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-041";
    }
    requirement def <'REQ-OA-041-04'> PayloadMassLimit :> PerformanceReq {
        doc /* Payload mass shall be documented; total rover mass with
              payload shall not exceed 10 kg. */
        :>> layer      = "OA";
        :>> source     = "01_operational_analysis/operational_activities.md#oact-041";
        :>> measuredBy = "weigh rover + payload on calibrated scale";
    }

    requirement def <'REQ-OA-042-01'> NonDestructiveIntegration :> OSRRequirement {
        doc /* Payload integration shall not require removal or permanent
              modification of any baseline rover component. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-042";
    }
    requirement def <'REQ-OA-042-02'> PayloadWireRouting :> OSRRequirement {
        doc /* All payload wiring shall be routed clear of rotating and
              articulating components. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-042";
    }
    requirement def <'REQ-OA-042-03'> ReversibleIntegration :> OSRRequirement {
        doc /* Payload integration shall be reversible using only a standard
              Allen key set. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-042";
    }

    requirement def <'REQ-OA-043-01'> CatkinWorkspace :> OSRRequirement {
        doc /* Custom ROS nodes shall be added to OSR catkin workspace
              without modifying existing baseline nodes. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-043";
    }
    requirement def <'REQ-OA-043-02'> NamingConvention :> OSRRequirement {
        doc /* New ROS topics shall follow the OSR naming convention. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-043";
    }
    requirement def <'REQ-OA-043-03'> GracefulNodeLifecycle :> OSRRequirement {
        doc /* All custom nodes shall handle startup and shutdown
              gracefully. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-043";
    }
    requirement def <'REQ-OA-043-04'> NodeDocumentation :> OSRRequirement {
        doc /* A README shall document all new topics, configurable
              parameters, and their data types. */
        :>> layer  = "OA";
        :>> source = "01_operational_analysis/operational_activities.md#oact-043";
    }

}
