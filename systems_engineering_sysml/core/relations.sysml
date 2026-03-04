/**
 * OSR::Core::Relations
 * ====================
 * Base requirement stereotypes and traceability metadata used across all
 * OSR requirement packages. Import this wherever you declare requirements.
 *
 * Key formalism vs Arcadia:
 *   Arcadia: requirements stored as prose in markdown + PropertyValueGroups
 *            on model elements (no formal satisfy/verify verbs)
 *   SysML v2: requirement def + satisfy/verify are first-class language
 *             constructs with formal semantics — tool-enforced traceability
 *
 * Arcadia parallel: systems_engineering/requirements_register.md (register)
 *                   systems_engineering/traceability.md (links)
 */
package 'OSR::Core::Relations' {

    private import ScalarValues::*;

    // ── Base OSR requirement ──────────────────────────────────────────────
    // All OSR requirement defs specialise this.  The attributes here mirror
    // the columns in requirements_register.md so the two can be diffed
    // directly (benchmark/compare.py uses these field names).
    abstract requirement def OSRRequirement {
        attribute layer    : String;           // OA | SF | LC | PF
        attribute priority : String = "nominal"; // nominal | safety-critical | info
        attribute status   : String = "DRAFT";   // DRAFT | REVIEWED | VERIFIED
        attribute source   : String;           // relative path to Arcadia source doc
    }

    // ── Safety-critical specialisation ───────────────────────────────────
    // Used for any requirement that maps to a hazard in hazard_log.md.
    // The hazardRef must match an H-xx ID in 06_safety/constraints.sysml.
    abstract requirement def SafetyCriticalReq :> OSRRequirement {
        :>> priority = "safety-critical";
        attribute hazardRef   : String;        // "H-01" | "H-02" | ...
        attribute responseMs  : Real;          // maximum allowed fault response latency
    }

    // ── Performance requirement specialisation ────────────────────────────
    abstract requirement def PerformanceReq :> OSRRequirement {
        attribute measuredBy  : String;        // test ID or measurement method
        attribute tolerance   : Real = 0.0;    // allowed deviation
    }

    // ── Interface / protocol requirement ─────────────────────────────────
    abstract requirement def InterfaceReq :> OSRRequirement {
        attribute rosTopicName : String = "";
        attribute rosMsgType   : String = "";
    }

    // ── Traceability metadata ─────────────────────────────────────────────
    // Attach to satisfy/verify usages to record how the link was established.
    // Usage:  @SatisfyLink { allocatedTo = "fault_node.py"; testMethod = "test"; }
    //          satisfy MotorCurrentMonitoring;
    metadata def SatisfyLink {
        attribute allocatedTo : String;        // ROS node or physical component
        attribute testMethod  : String;        // analysis | inspection | demonstration | test
        attribute testId      : String = "";   // test case reference
        attribute verified    : Boolean = false;
    }

    // ── Verification cross-reference ──────────────────────────────────────
    // Used in traceability/satisfy_matrix.sysml to annotate verify usages.
    metadata def VerifyLink {
        attribute testProcedure : String;
        attribute testResult    : String = "NOT_RUN"; // NOT_RUN | PASS | FAIL
        attribute dateRun       : String = "";
    }

}
