/**
 * OSR::Safety::Constraints
 * ========================
 * Formal safety constraint definitions for all 10 OSR hazards (H-01..H-10).
 * Each constraint def expresses the safety boundary condition as a
 * computable predicate — directly evaluable by parametric analysis tools.
 *
 * Arcadia parallel: systems_engineering/06_safety/hazard_log.md
 *                   systems_engineering/06_safety/fmea_system.md
 *
 * Key difference vs Arcadia:
 *   Arcadia: hazards as prose rows in a markdown table
 *   SysML v2: constraint def with typed parameters that tools can evaluate,
 *             plus formal 'require constraint' links in part defs
 *
 * Scenic parallel: systems_engineering/06_safety/scenarios/*.scenic
 *   Each constraint maps to one Scenic scenario — the constraint boundary
 *   IS the condition the Scenic scenario is designed to approach and cross.
 */
package 'OSR::Safety::Constraints' {

    private import ScalarValues::*;
    private import 'OSR::Core::Types'::*;
    private import 'OSR::Core::Relations'::*;

    // ────────────────────────────────────────────────────────────────────
    // H-01 — Motor Overcurrent / Fire
    // Scenic: scenarios/motor_stall.scenic
    // ────────────────────────────────────────────────────────────────────
    constraint def <'H-01'> MotorCurrentSafe {
        doc /* No motor channel current shall exceed 10 A continuously for
              more than 100 ms.  Violation → fire risk. */
        in motorCurrentA : Real;
        in durationMs    : Real;
        /* safe iff: not (current ≥ 10 A AND duration ≥ 100 ms) */
        (motorCurrentA < 10.0) || (durationMs < 100.0)
    }

    // ────────────────────────────────────────────────────────────────────
    // H-02 — Tip / Rollover
    // Scenic: scenarios/tilt_risk.scenic
    // ────────────────────────────────────────────────────────────────────
    constraint def <'H-02'> TiltSafe {
        doc /* Rover roll or pitch shall not exceed 35° at any point during
              traverse.  Violation → tip risk. */
        in rollDeg  : Real;
        in pitchDeg : Real;
        (rollDeg.abs  < 35.0) && (pitchDeg.abs < 35.0)
    }

    // ────────────────────────────────────────────────────────────────────
    // H-03 — Battery Over-Discharge
    // Scenic: scenarios/battery_low.scenic
    // ────────────────────────────────────────────────────────────────────
    constraint def <'H-03'> BatteryVoltageSafe {
        doc /* Battery bus voltage shall remain above 10.5 V during
              operation.  Warning at 11.0 V. */
        in busVoltageV   : Real;
        busVoltageV >= 10.5
    }
    constraint def <'H-03-warn'> BatteryVoltageWarn {
        doc /* Low-battery warning threshold — voltage < 11.0 V. */
        in busVoltageV : Real;
        busVoltageV >= 11.0
    }

    // ────────────────────────────────────────────────────────────────────
    // H-04 — Runaway After Comm Loss
    // Scenic: scenarios/comm_loss.scenic
    // ────────────────────────────────────────────────────────────────────
    constraint def <'H-04'> CommWatchdogSafe {
        doc /* Rover shall reach zero velocity within 1 s of last /cmd_vel
              message.  Violation → runaway. */
        in silenceDurationS  : Real;
        in roverSpeedMs      : Real;
        /* if silence ≥ 1 s, speed must be 0 */
        (silenceDurationS < 1.0) || (roverSpeedMs == 0.0)
    }

    // ────────────────────────────────────────────────────────────────────
    // H-05 — Collision / Unintended Motion
    // Scenic: scenarios/nominal_traverse.scenic (speed boundary)
    // ────────────────────────────────────────────────────────────────────
    constraint def <'H-05'> VelocitySafe {
        doc /* Rover linear speed shall not exceed 0.4 m/s under any
              commanded or fault state. */
        in linearSpeedMs : Real;
        linearSpeedMs.abs <= 0.4
    }

    // ────────────────────────────────────────────────────────────────────
    // H-06 — Electrical Short Circuit
    // ────────────────────────────────────────────────────────────────────
    constraint def <'H-06'> FuseSafe {
        doc /* In-line fuse rating shall not exceed 30 A between battery
              and PCB input. */
        in fuseRatingA : Real;
        fuseRatingA <= 30.0
    }

    // ────────────────────────────────────────────────────────────────────
    // H-07 — Payload Overcurrent
    // ────────────────────────────────────────────────────────────────────
    constraint def <'H-07'> PayloadCurrentSafe {
        doc /* Payload rail current shall not exceed 2 A (configurable
              limit). */
        in payloadCurrentA : Real;
        in limitA          : Real;
        payloadCurrentA <= limitA
    }

    // ────────────────────────────────────────────────────────────────────
    // H-08 — Software Crash / Node Failure
    // ────────────────────────────────────────────────────────────────────
    constraint def <'H-08'> NodeHealthSafe {
        doc /* Fault monitor node shall remain alive; any node crash shall
              not propagate to uncontrolled motion. */
        in faultNodeAlive : Boolean;
        in hardwareTimeoutActive : Boolean;
        /* either fault node running OR hardware RoboClaw timeout is armed */
        faultNodeAlive || hardwareTimeoutActive
    }

    // ────────────────────────────────────────────────────────────────────
    // H-09 — Structural Failure
    // ────────────────────────────────────────────────────────────────────
    constraint def <'H-09'> StructuralSafe {
        doc /* Total rover + payload mass shall not exceed 10 kg. */
        in totalMassKg : Real;
        totalMassKg <= 10.0
    }

    // ────────────────────────────────────────────────────────────────────
    // H-10 — LiPo Thermal Runaway
    // Scenic: scenarios/battery_low.scenic (edge — charge abuse scenario)
    // ────────────────────────────────────────────────────────────────────
    constraint def <'H-10'> LiPoChargeSafe {
        doc /* Charge current shall not exceed 1C (3 A for 3 Ah pack);
              battery shall not be charged while installed in rover
              (unless dedicated charge circuit with thermal monitoring). */
        in chargeCurrentA    : Real;
        in chargeCapacityAh  : Real;
        in chargedInRover    : Boolean;
        in thermalMonPresent : Boolean;
        (chargeCurrentA <= chargeCapacityAh) &&          // ≤ 1C
        (!chargedInRover || thermalMonPresent)            // safe charge location
    }

    // ════════════════════════════════════════════════════════════════════
    // FMEA — Risk Priority Number constraint
    // ════════════════════════════════════════════════════════════════════
    // Formalises the RPN threshold used in safety_report.html.
    // Any failure mode part with an riskPriorityNumber > 16 violates this.
    constraint def RPNAcceptable {
        doc /* Risk Priority Number (S × O × D) shall not exceed 16 for
              any failure mode without a documented mitigation plan. */
        in severity      : Integer;
        in occurrence    : Integer;
        in detectability : Integer;
        (severity * occurrence * detectability) <= 16
    }

}
