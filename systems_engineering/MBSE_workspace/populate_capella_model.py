#!/usr/bin/env python3
"""
populate_capella_model.py
=========================
Populates OSR_capella_model.capella with every element defined in the
OSR MBSE markdown documentation:

  OA  — 10 Operational Entities + 17 Operational Activities (OAct-01…04)
  SA  — 7 System Functions (SF-01…07) + 14 sub-functions
  LA  — 27 Logical Functions (LF-01…07) + 8 Logical Components (LC-01…08)
  PA  — 27 Physical Functions (PF-01…07) + 14 Physical Components (PC-*)
  EPBS— 5 Configuration Items (CI-01…05)

Cross-layer realization links are added for:
  SF → OAct  (function realizations)
  LF → SF    (function realizations)
  PF → LF    (function realizations)
  LC → LC    (component realizations, PA→LA)
  CI → PC    (physical artifact realizations, EPBS→PA)

Usage:
    cd systems_engineering/MBSE_workspace
    python3 populate_capella_model.py

Output: rewrites OSR_capella_model/OSR_capella_model.capella in place.
The file can then be imported into Capella 6.1.0 via:
  File > Import > Existing Projects into Workspace > OSR_capella_model/
"""

import uuid
import sys
from pathlib import Path
from textwrap import indent as _indent

# ---------------------------------------------------------------------------
# Deterministic UUID generation — same name always → same ID
# ---------------------------------------------------------------------------
_NS = uuid.UUID("c0ffee00-c0de-4a7a-b00b-0a0b1c2d3e4f")


def mk(name: str) -> str:
    """Return a deterministic UUID string from a stable element name."""
    return str(uuid.uuid5(_NS, name))


# ---------------------------------------------------------------------------
# Existing scaffold IDs — must not change or Capella loses references
# ---------------------------------------------------------------------------
E = {
    "project":           "382879fb-9f9e-49a6-b613-c4090197549c",
    "model_info":        "792bdb0d-429a-4be5-88a2-86493656961d",
    "progress_status":   "fb39e72f-7a82-4d4f-a84c-6608e258cb71",
    # OA
    "oa_arch":           "1ac666ab-1afe-4aaf-879f-7bc4af137a8f",
    "oa_func_pkg":       "4388b005-675c-413e-8764-dbd7f043cb18",
    "oa_root_act":       "b09e9896-7edf-4ac0-aae8-00f368ecef94",
    "oa_cap_pkg":        "2c1cf999-c595-443b-8ea2-f1746440a579",
    "oa_iface_pkg":      "740dbaf6-8f74-413f-b684-fec5df8be975",
    "oa_data_pkg":       "da04821d-20d0-4b2a-bfec-ac95a17c5603",
    "oa_role_pkg":       "05f20436-bc6e-40b8-8165-ce6f2aaeba1e",
    "oa_entity_pkg":     "8922e142-553f-4747-a9ab-268a146f90e7",
    # SA
    "sa_arch":           "6fbd9a52-0478-48cd-9b2b-49bb3af03a94",
    "sa_func_pkg":       "8cb89079-666c-43b2-8d4c-e59f7526818f",
    "sa_root_sf":        "60a5c18f-74f5-4beb-b1ff-9d9bbd472d25",
    "sa_root_sf_real":   "2d333aab-cc98-4c36-bd3c-4101d6444403",
    "sa_cap_pkg":        "4af6fec2-1650-4a18-b7d3-a691c97dfae9",
    "sa_iface_pkg":      "6618bc5f-d07f-4efd-82a8-fa9d5432940e",
    "sa_data_pkg":       "d0371017-7bce-4c99-bf29-75f76865dab4",
    "sa_predefined_pkg": "4905fdd7-2753-41e6-a65f-446d130f3886",
    "sa_comp_pkg":       "a47bd454-ecc8-4d20-991a-b8dfb67e5828",
    "sa_system_part":    "e0dd1fb8-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
    "sa_system":         "3183326b-ff3d-4163-8353-3e5a1df12e89",
    "sa_state_machine":  "a35b7a4b-8b9c-0d1e-2f3a-4b5c6d7e8f9a",
    "sa_state_region":   "3d6d7a4e-9c0d-1e2f-3a4b-5c6d7e8f9a0b",
    "sa_mission_pkg":    "70466143-7f38-43b9-afa4-fc3cb8a55bb7",
    "sa_oa_real":        "702ea61a-0d1e-2f3a-4b5c-6d7e8f9a0b1c",
    # LA
    "la_arch":           "664d9641-58f1-4945-8e03-f7b98644a30d",
    "la_func_pkg":       "3c2f6ac8-837e-4e1e-b057-53c2961d2431",
    "la_root_lf":        "d2533d31-07f2-4e27-b725-522e1d407568",
    "la_root_lf_real":   "e050ea15-1e2f-3a4b-5c6d-7e8f9a0b1c2d",
    "la_cap_pkg":        "db91feb3-2f3a-4b5c-6d7e-8f9a0b1c2d3e",
    "la_iface_pkg":      "e6d31290-3a4b-5c6d-7e8f-9a0b1c2d3e4f",
    "la_data_pkg":       "3531fbe3-4b5c-6d7e-8f9a-0b1c2d3e4f5a",
    "la_comp_pkg":       "78f38782-c323-474c-bdfe-39ab80436e0a",
    "la_system_part":    "6d74d211-5c6d-7e8f-9a0b-1c2d3e4f5a6b",
    "la_system":         "226ae547-1185-4f75-acf3-7402fbeaae11",
    "la_system_real":    "e50cb970-6d7e-8f9a-0b1c-2d3e4f5a6b7c",
    "la_sa_real":        "5460d99d-7e8f-9a0b-1c2d-3e4f5a6b7c8d",
    # PA
    "pa_arch":           "017a1c6e-b28d-4fbb-9ec7-61686d6cd670",
    "pa_func_pkg":       "6293bb3e-969e-4ec3-a7a0-0214d04d0c49",
    "pa_root_pf":        "6e89423f-a6f5-4001-8be9-8e5cf6e27e3c",
    "pa_root_pf_real":   "838383b6-8f9a-0b1c-2d3e-4f5a6b7c8d9e",
    "pa_cap_pkg":        "7baf2cb8-9a0b-1c2d-3e4f-5a6b7c8d9e0f",
    "pa_iface_pkg":      "a7636c7b-0b1c-2d3e-4f5a-6b7c8d9e0f1a",
    "pa_data_pkg":       "f00052c8-1c2d-3e4f-5a6b-7c8d9e0f1a2b",
    "pa_comp_pkg":       "b1f464a8-54c1-4e88-9857-5bf228177cc3",
    "pa_system_part":    "a0012c5d-2d3e-4f5a-6b7c-8d9e0f1a2b3c",
    "pa_system":         "235eb4bd-deef-4e70-8425-293fceb2d019",
    "pa_system_real":    "2f1cb947-3e4f-5a6b-7c8d-9e0f1a2b3c4d",
    "pa_la_real":        "ee486b51-4f5a-6b7c-8d9e-0f1a2b3c4d5e",
    # EPBS
    "epbs_arch":         "32eb162f-ee45-4b21-a91e-0611caff982a",
    "epbs_cap_pkg":      "19ea0d27-5a6b-7c8d-9e0f-1a2b3c4d5e6f",
    "epbs_ci_pkg":       "a8d91cf8-4ab7-406b-a0f8-db828a92fd21",
    "epbs_system_part":  "1cb36d5a-6b7c-8d9e-0f1a-2b3c4d5e6f7a",
    "epbs_system_ci":    "1c90fcc2-b48f-4b07-b710-45f534e6cd34",
    "epbs_system_real":  "8853599f-7c8d-9e0f-1a2b-3c4d5e6f7a8b",
    "epbs_pa_real":      "8c4bf98f-8d9e-0f1a-2b3c-4d5e6f7a8b9c",
}

# ---------------------------------------------------------------------------
# Model data — all new element definitions
# ---------------------------------------------------------------------------

# OA: Operational Entities
# (actor=True for human roles, False for systems/equipment)
OA_ENTITIES = [
    ("OE-01 Ground Operator",    "OperationalActor"),
    ("OE-02 Developer",          "OperationalActor"),
    ("OE-03 Builder",            "OperationalActor"),
    ("OE-04 Safety Observer",    "OperationalActor"),
    ("OE-05 Contributor",        "OperationalActor"),
    ("OE-06 OSR System",         "Entity"),
    ("OE-07 Ground Station",     "Entity"),
    ("OE-08 Battery Charger",    "Entity"),
    ("OE-09 Payload",            "Entity"),
    ("OE-10 External Terrain",   "Entity"),
]

# OA: Operational Activities (parent → children)
# Each tuple: (activity_name, [children])
OA_ACTIVITIES = [
    ("OAct-01 Conduct Rover Mission", [
        "OAct-01.1 Plan Traverse Route",
        "OAct-01.2 Command Rover Motion",
        "OAct-01.3 Monitor Rover State",
        "OAct-01.4 Respond to Hazard",
        "OAct-01.5 Collect Sensor Data",
    ]),
    ("OAct-02 Maintain Rover", [
        "OAct-02.1 Charge Battery",
        "OAct-02.2 Inspect and Repair Hardware",
        "OAct-02.3 Update Software",
    ]),
    ("OAct-03 Build Rover", [
        "OAct-03.1 Source Components",
        "OAct-03.2 Assemble Mechanical Structure",
        "OAct-03.3 Install Electrical System",
        "OAct-03.4 Install and Configure Software",
    ]),
    ("OAct-04 Extend Rover Capability", [
        "OAct-04.1 Design Payload or Modification",
        "OAct-04.2 Integrate Payload",
        "OAct-04.3 Develop Custom Software",
    ]),
]

# SA: System Functions
# (sf_name, [sub_function_names], realized_oact_names)
SA_FUNCTIONS = [
    ("SF-01 Receive and Decode Command",      [],
     ["OAct-01.2 Command Rover Motion"]),
    ("SF-02 Execute Mobility",
     ["SF-02.1 Compute Drive Commands",
      "SF-02.2 Drive Wheels",
      "SF-02.3 Steer Corner Wheels"],
     ["OAct-01.2 Command Rover Motion"]),
    ("SF-03 Manage Power",
     ["SF-03.1 Distribute Electrical Power",
      "SF-03.2 Monitor Battery State",
      "SF-03.3 Protect Against Overcurrent/Short"],
     ["OAct-02.1 Charge Battery",
      "OAct-01.3 Monitor Rover State"]),
    ("SF-04 Process and Publish Telemetry",
     ["SF-04.1 Sample Sensors",
      "SF-04.2 Estimate Rover State",
      "SF-04.3 Transmit Telemetry"],
     ["OAct-01.3 Monitor Rover State"]),
    ("SF-05 Capture and Stream Video",        [],
     ["OAct-01.5 Collect Sensor Data"]),
    ("SF-06 Detect and Handle Faults",
     ["SF-06.1 Monitor Motor Currents",
      "SF-06.2 Monitor Battery Voltage",
      "SF-06.3 Detect Tip Risk (IMU)",
      "SF-06.4 Execute Safe Stop"],
     ["OAct-01.4 Respond to Hazard"]),
    ("SF-07 Support Payload Interface",
     ["SF-07.1 Provide Power to Payload",
      "SF-07.2 Route Payload Data"],
     ["OAct-04.2 Integrate Payload"]),
]

# LA: Logical Functions
# (lf_name, realized_sf_name)
LA_FUNCTIONS = [
    ("LF-01.1 Receive ROS Command Topic",         "SF-01 Receive and Decode Command"),
    ("LF-01.2 Validate Command Packet Integrity",  "SF-01 Receive and Decode Command"),
    ("LF-01.3 Apply Velocity Limits",              "SF-01 Receive and Decode Command"),
    ("LF-01.4 Detect Command Watchdog Timeout",    "SF-01 Receive and Decode Command"),
    ("LF-02.1 Compute Differential Drive Kinematics", "SF-02.1 Compute Drive Commands"),
    ("LF-02.2 Compute Ackermann Corner Angles",    "SF-02.3 Steer Corner Wheels"),
    ("LF-02.3 Output Drive PWM Setpoints",         "SF-02.2 Drive Wheels"),
    ("LF-02.4 Output Steering Angle Setpoints",    "SF-02.3 Steer Corner Wheels"),
    ("LF-03.1 Read Battery Voltage (ADC)",         "SF-03.2 Monitor Battery State"),
    ("LF-03.2 Estimate State-of-Charge",           "SF-03.2 Monitor Battery State"),
    ("LF-03.3 Distribute Regulated Power Rails",   "SF-03.1 Distribute Electrical Power"),
    ("LF-03.4 Engage Overcurrent Protection",      "SF-03.3 Protect Against Overcurrent/Short"),
    ("LF-04.1 Sample Wheel Encoders",              "SF-04.1 Sample Sensors"),
    ("LF-04.2 Sample IMU",                         "SF-04.1 Sample Sensors"),
    ("LF-04.3 Sample Motor Currents",              "SF-04.1 Sample Sensors"),
    ("LF-04.4 Integrate Odometry from Encoders",   "SF-04.2 Estimate Rover State"),
    ("LF-04.5 Estimate Attitude (IMU Filter)",     "SF-04.2 Estimate Rover State"),
    ("LF-04.6 Publish Telemetry Bundle",           "SF-04.3 Transmit Telemetry"),
    ("LF-05.1 Monitor Per-Motor Current",          "SF-06.1 Monitor Motor Currents"),
    ("LF-05.2 Monitor Battery Voltage",            "SF-06.2 Monitor Battery Voltage"),
    ("LF-05.3 Monitor IMU Tilt",                   "SF-06.3 Detect Tip Risk (IMU)"),
    ("LF-05.4 Execute Safe Stop",                  "SF-06.4 Execute Safe Stop"),
    ("LF-05.5 Publish Fault Events",               "SF-06.4 Execute Safe Stop"),
    ("LF-06.1 Stream Video Frames",                "SF-05 Capture and Stream Video"),
    ("LF-07.1 Enable/Disable Payload Power",       "SF-07.1 Provide Power to Payload"),
    ("LF-07.2 Monitor Payload Current",            "SF-07.1 Provide Power to Payload"),
    ("LF-07.3 Route Payload Data Bus",             "SF-07.2 Route Payload Data"),
]

# LA: Logical Components
# (lc_name, [realized_sf_names])
LA_COMPONENTS = [
    ("LC-01 Communication Manager",
     ["SF-01 Receive and Decode Command",
      "SF-04.3 Transmit Telemetry",
      "SF-05 Capture and Stream Video"]),
    ("LC-02 Command Processor",
     ["SF-01 Receive and Decode Command"]),
    ("LC-03 Mobility Controller",
     ["SF-02.1 Compute Drive Commands",
      "SF-02.2 Drive Wheels",
      "SF-02.3 Steer Corner Wheels"]),
    ("LC-04 State Estimator",
     ["SF-04.1 Sample Sensors",
      "SF-04.2 Estimate Rover State"]),
    ("LC-05 Fault Monitor",
     ["SF-06.1 Monitor Motor Currents",
      "SF-06.2 Monitor Battery Voltage",
      "SF-06.3 Detect Tip Risk (IMU)",
      "SF-06.4 Execute Safe Stop"]),
    ("LC-06 Power Manager",
     ["SF-03.1 Distribute Electrical Power",
      "SF-03.2 Monitor Battery State",
      "SF-03.3 Protect Against Overcurrent/Short"]),
    ("LC-07 Telemetry Publisher",
     ["SF-04.3 Transmit Telemetry"]),
    ("LC-08 Payload Manager",
     ["SF-07.1 Provide Power to Payload",
      "SF-07.2 Route Payload Data"]),
]

# PA: Physical Functions
# (pf_name, realized_lf_name)
PA_FUNCTIONS = [
    ("PF-01.1 Subscribe to /cmd_vel ROS Topic",
     "LF-01.1 Receive ROS Command Topic"),
    ("PF-01.2 Validate Twist Message Fields",
     "LF-01.2 Validate Command Packet Integrity"),
    ("PF-01.3 Clamp Velocity to Configured Limits",
     "LF-01.3 Apply Velocity Limits"),
    ("PF-01.4 Watchdog Timer on /cmd_vel",
     "LF-01.4 Detect Command Watchdog Timeout"),
    ("PF-02.1 Rocker-Bogie Differential Drive Kinematics",
     "LF-02.1 Compute Differential Drive Kinematics"),
    ("PF-02.2 Ackermann Corner Angle Computation",
     "LF-02.2 Compute Ackermann Corner Angles"),
    ("PF-02.3 Write Motor Setpoint to RoboClaw via USB Serial",
     "LF-02.3 Output Drive PWM Setpoints"),
    ("PF-02.4 Write Angle Setpoint to PCA9685 via I2C",
     "LF-02.4 Output Steering Angle Setpoints"),
    ("PF-03.1 Read INA219 Battery Voltage over I2C",
     "LF-03.1 Read Battery Voltage (ADC)"),
    ("PF-03.2 Compute LiPo State-of-Charge from Voltage Curve",
     "LF-03.2 Estimate State-of-Charge"),
    ("PF-03.3 PCB DC-DC Converter Regulation",
     "LF-03.3 Distribute Regulated Power Rails"),
    ("PF-03.4 Software Overcurrent Cutoff via Motor Disable",
     "LF-03.4 Engage Overcurrent Protection"),
    ("PF-04.1 Read RoboClaw Encoder Counts via USB Serial",
     "LF-04.1 Sample Wheel Encoders"),
    ("PF-04.2 Read BNO055 IMU via I2C",
     "LF-04.2 Sample IMU"),
    ("PF-04.3 Read Motor Currents from RoboClaw via Serial",
     "LF-04.3 Sample Motor Currents"),
    ("PF-04.4 Integrate Wheel Ticks to Odometry",
     "LF-04.4 Integrate Odometry from Encoders"),
    ("PF-04.5 Complementary Filter for Attitude",
     "LF-04.5 Estimate Attitude (IMU Filter)"),
    ("PF-04.6 Publish ROS Telemetry Topics at 5 Hz",
     "LF-04.6 Publish Telemetry Bundle"),
    ("PF-05.1 Monitor Current Thresholds per Motor Channel",
     "LF-05.1 Monitor Per-Motor Current"),
    ("PF-05.2 Monitor Battery Voltage Threshold",
     "LF-05.2 Monitor Battery Voltage"),
    ("PF-05.3 Monitor IMU Roll/Pitch Threshold",
     "LF-05.3 Monitor IMU Tilt"),
    ("PF-05.4 Set All Motor Setpoints to Zero (Safe Stop)",
     "LF-05.4 Execute Safe Stop"),
    ("PF-05.5 Publish /diagnostics Fault Message",
     "LF-05.5 Publish Fault Events"),
    ("PF-06.1 Capture Frames from Camera Module",
     "LF-06.1 Stream Video Frames"),
    ("PF-06.2 Compress and Publish Video over Wi-Fi",
     "LF-06.1 Stream Video Frames"),
    ("PF-07.1 Toggle PCB Load Switch for Payload Power",
     "LF-07.1 Enable/Disable Payload Power"),
    ("PF-07.2 Read Payload Rail Current via INA219",
     "LF-07.2 Monitor Payload Current"),
    ("PF-07.3 Pass-Through USB/I2C/UART to RPi Bus",
     "LF-07.3 Route Payload Data Bus"),
]

# PA: Physical Components
# (pc_name, nature, kind, [realized_lc_names])
# nature: NODE (hardware) | BEHAVIOR (software) | UNSET
# kind: UNSET for most components
PA_COMPONENTS = [
    ("PC-COMP-01 Raspberry Pi 4B", "NODE", "UNSET",
     ["LC-01 Communication Manager",
      "LC-02 Command Processor",
      "LC-03 Mobility Controller",
      "LC-04 State Estimator",
      "LC-05 Fault Monitor",
      "LC-07 Telemetry Publisher"]),
    ("PC-MCTL-01 RoboClaw 2x15A Motor Controllers", "NODE", "UNSET",
     ["LC-03 Mobility Controller"]),
    ("PC-MCTL-02 PCA9685 Servo Driver", "NODE", "UNSET",
     ["LC-03 Mobility Controller"]),
    ("PC-PCB-01 Custom OSR PCB", "NODE", "UNSET",
     ["LC-06 Power Manager",
      "LC-08 Payload Manager"]),
    ("PC-SENS-01 BNO055 IMU", "NODE", "UNSET",
     ["LC-04 State Estimator"]),
    ("PC-SENS-02 Wheel Encoders (RoboClaw Built-in)", "NODE", "UNSET",
     ["LC-04 State Estimator"]),
    ("PC-SENS-03 INA219 Power Monitor", "NODE", "UNSET",
     ["LC-06 Power Manager"]),
    ("PC-CAM-01 Camera Module (CSI/USB)", "NODE", "UNSET",
     ["LC-07 Telemetry Publisher"]),
    ("PC-PWR-01 3S LiPo Battery Pack", "NODE", "UNSET",
     []),
    ("PC-PWR-02 LiPo Balance Charger", "NODE", "UNSET",
     []),
    ("PC-MECH-01 Drive Motor Assembly (x6)", "NODE", "UNSET",
     []),
    ("PC-MECH-02 Steering Servo Assembly (x4)", "NODE", "UNSET",
     []),
    ("PC-MECH-03 Rocker-Bogie Chassis Frame", "NODE", "UNSET",
     []),
    ("PC-MECH-04 Wheel and Tire Assembly (x6)", "NODE", "UNSET",
     []),
]

# EPBS: Configuration Items
# (ci_name, kind, [realized_pc_names])
# kind: System | CSCI | HWCI | FIRMWARE
EPBS_CIS = [
    ("CI-01 OSR Software Stack (CSCI)", "CSCI",
     ["PC-COMP-01 Raspberry Pi 4B"]),
    ("CI-02 Compute Hardware (HWCI)", "HWCI",
     ["PC-COMP-01 Raspberry Pi 4B"]),
    ("CI-03 Motor Drive System (HWCI)", "HWCI",
     ["PC-MCTL-01 RoboClaw 2x15A Motor Controllers",
      "PC-MCTL-02 PCA9685 Servo Driver",
      "PC-MECH-01 Drive Motor Assembly (x6)",
      "PC-MECH-02 Steering Servo Assembly (x4)"]),
    ("CI-04 Power and Sensing System (HWCI)", "HWCI",
     ["PC-PCB-01 Custom OSR PCB",
      "PC-PWR-01 3S LiPo Battery Pack",
      "PC-SENS-01 BNO055 IMU",
      "PC-SENS-02 Wheel Encoders (RoboClaw Built-in)",
      "PC-SENS-03 INA219 Power Monitor",
      "PC-CAM-01 Camera Module (CSI/USB)"]),
    ("CI-05 Mechanical Structure (HWCI)", "HWCI",
     ["PC-MECH-03 Rocker-Bogie Chassis Frame",
      "PC-MECH-04 Wheel and Tire Assembly (x6)"]),
]

# ---------------------------------------------------------------------------
# XML rendering helpers
# ---------------------------------------------------------------------------

def xml_attrs(**kv) -> str:
    parts = []
    for k, v in kv.items():
        if v is not None:
            tag = k.replace("__", ":").replace("_", "")
            # restore camelCase: split on uppercase boundaries is tricky,
            # so we just use the key as-is but rename the common ones
            parts.append(f'    {k}="{v}"')
    return "\n".join(parts)


def leaf(tag: str, **attrs) -> str:
    a = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    return f"<{tag} {a}/>"


def node(tag: str, children: list[str], **attrs) -> str:
    a = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    inner = "\n".join(children)
    inner_indented = _indent(inner, "  ")
    return f"<{tag} {a}>\n{inner_indented}\n</{tag}>"


def realization(tag: str, rid: str, target: str, source: str) -> str:
    return (f'<{tag} id="{rid}"'
            f' targetElement="#{target}"'
            f' sourceElement="#{source}"/>')


def fn_real(rid: str, target: str, source: str) -> str:
    return realization("ownedFunctionRealizations", rid, target, source)


def comp_real(rid: str, target: str, source: str) -> str:
    return realization("ownedComponentRealizations", rid, target, source)


def phys_art_real(rid: str, target: str, source: str) -> str:
    return realization("ownedPhysicalArtifactRealizations", rid, target, source)


# ---------------------------------------------------------------------------
# Build OA layer
# ---------------------------------------------------------------------------

def build_oa_entities() -> list[str]:
    lines = []
    for name, etype in OA_ENTITIES:
        lines.append(
            f'<ownedEntities xsi:type="org.polarsys.capella.core.data.oa:{etype}"'
            f' id="{mk(name)}" name="{name}"/>'
        )
    return lines


def build_oa_activity(name: str, children: list[str]) -> str:
    child_elems = [build_oa_activity(c, []) for c in children]
    if child_elems:
        return node("ownedOperationalActivities",
                    child_elems,
                    id=mk(name), name=name)
    else:
        return leaf("ownedOperationalActivities", id=mk(name), name=name)


def build_oa_activities() -> list[str]:
    result = []
    for parent, children in OA_ACTIVITIES:
        result.append(build_oa_activity(parent, children))
    return result


# ---------------------------------------------------------------------------
# Build SA layer
# ---------------------------------------------------------------------------

def build_sa_function(sf_name: str, sub_names: list[str],
                       oact_names: list[str]) -> str:
    sf_id = mk(sf_name)
    children = []
    for oact in oact_names:
        children.append(fn_real(mk(f"real:{sf_name}->{oact}"),
                                mk(oact), sf_id))
    for sub in sub_names:
        sub_id = mk(sub)
        children.append(
            node("ownedSystemFunctions",
                 [fn_real(mk(f"real:{sub}->{sf_name}"),
                           mk(sf_name), sub_id)],
                 id=sub_id, name=sub)
        )
    return node("ownedSystemFunctions", children, id=sf_id, name=sf_name)


def build_sa_functions() -> list[str]:
    result = []
    for sf_name, subs, oacts in SA_FUNCTIONS:
        result.append(build_sa_function(sf_name, subs, oacts))
    return result


# ---------------------------------------------------------------------------
# Build LA layer — Logical Functions
# ---------------------------------------------------------------------------

def build_la_functions() -> list[str]:
    result = []
    for lf_name, sf_name in LA_FUNCTIONS:
        lf_id = mk(lf_name)
        sf_id = mk(sf_name)
        result.append(
            node("ownedLogicalFunctions",
                 [fn_real(mk(f"real:{lf_name}->{sf_name}"), sf_id, lf_id)],
                 id=lf_id, name=lf_name)
        )
    return result


# ---------------------------------------------------------------------------
# Build LA layer — Logical Components (nested in Logical System)
# ---------------------------------------------------------------------------

def build_la_components() -> list[str]:
    result = []
    for lc_name, sf_names in LA_COMPONENTS:
        lc_id = mk(lc_name)
        # Component realizations: LC realizes SA System functions
        # (functional allocation is set via GUI; here we omit it to keep XMI valid)
        result.append(leaf("ownedLogicalComponents", id=lc_id, name=lc_name))
    return result


# ---------------------------------------------------------------------------
# Build PA layer — Physical Functions
# ---------------------------------------------------------------------------

def build_pa_functions() -> list[str]:
    result = []
    for pf_name, lf_name in PA_FUNCTIONS:
        pf_id = mk(pf_name)
        lf_id = mk(lf_name)
        result.append(
            node("ownedPhysicalFunctions",
                 [fn_real(mk(f"real:{pf_name}->{lf_name}"), lf_id, pf_id)],
                 id=pf_id, name=pf_name)
        )
    return result


# ---------------------------------------------------------------------------
# Build PA layer — Physical Components (nested in Physical System)
# ---------------------------------------------------------------------------

def build_pa_components() -> list[str]:
    result = []
    for pc_name, nature, kind, lc_names in PA_COMPONENTS:
        pc_id = mk(pc_name)
        children = []
        for lc_name in lc_names:
            lc_id = mk(lc_name)
            children.append(
                comp_real(mk(f"real:{pc_name}->{lc_name}"), lc_id, pc_id)
            )
        if children:
            result.append(
                node("ownedPhysicalComponents", children,
                     id=pc_id, name=pc_name, nature=nature)
            )
        else:
            result.append(
                leaf("ownedPhysicalComponents",
                     id=pc_id, name=pc_name, nature=nature)
            )
    return result


# ---------------------------------------------------------------------------
# Build EPBS layer — Configuration Items (nested in System CI)
# ---------------------------------------------------------------------------

def build_epbs_cis() -> list[str]:
    result = []
    for ci_name, kind, pc_names in EPBS_CIS:
        ci_id = mk(ci_name)
        children = []
        for pc_name in pc_names:
            pc_id = mk(pc_name)
            children.append(
                phys_art_real(mk(f"real:{ci_name}->{pc_name}"), pc_id, ci_id)
            )
        if children:
            result.append(
                node("ownedConfigurationItems", children,
                     id=ci_id, name=ci_name, kind=kind)
            )
        else:
            result.append(
                leaf("ownedConfigurationItems",
                     id=ci_id, name=ci_name, kind=kind)
            )
    return result


# ---------------------------------------------------------------------------
# Assemble the full XML document
# ---------------------------------------------------------------------------

def join(*lines) -> str:
    return "\n".join(lines)


def ind(text: str, levels: int = 1) -> str:
    return _indent(text, "  " * levels)


def build_xml() -> str:
    oa_entities = "\n".join(build_oa_entities())
    oa_acts     = "\n".join(build_oa_activities())
    sa_fns      = "\n".join(build_sa_functions())
    la_fns      = "\n".join(build_la_functions())
    la_comps    = "\n".join(build_la_components())
    pa_fns      = "\n".join(build_pa_functions())
    pa_comps    = "\n".join(build_pa_components())
    epbs_cis    = "\n".join(build_epbs_cis())

    # Pre-defined type IDs preserved from scaffold
    bool_id  = "01df2fd1-e6e3-4236-a27a-b5f5b6c33c4b"
    byte_id  = "a06c4a34-3a65-4e60-bac1-42f41c694133"
    # ... (predefined types are kept verbatim below in the SA data pkg)

    doc = f"""\
<?xml version="1.0" encoding="UTF-8"?>
<!--Capella_Version_6.1.0-->
<!--Generated by populate_capella_model.py — OSR MBSE documentation-->
<org.polarsys.capella.core.data.capellamodeller:Project xmi:version="2.0"
    xmlns:xmi="http://www.omg.org/XMI"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:libraries="http://www.polarsys.org/capella/common/libraries/6.0.0"
    xmlns:org.polarsys.capella.core.data.capellacommon="http://www.polarsys.org/capella/core/common/6.0.0"
    xmlns:org.polarsys.capella.core.data.capellacore="http://www.polarsys.org/capella/core/core/6.0.0"
    xmlns:org.polarsys.capella.core.data.capellamodeller="http://www.polarsys.org/capella/core/modeller/6.0.0"
    xmlns:org.polarsys.capella.core.data.cs="http://www.polarsys.org/capella/core/cs/6.0.0"
    xmlns:org.polarsys.capella.core.data.ctx="http://www.polarsys.org/capella/core/ctx/6.0.0"
    xmlns:org.polarsys.capella.core.data.epbs="http://www.polarsys.org/capella/core/epbs/6.0.0"
    xmlns:org.polarsys.capella.core.data.fa="http://www.polarsys.org/capella/core/fa/6.0.0"
    xmlns:org.polarsys.capella.core.data.information="http://www.polarsys.org/capella/core/information/6.0.0"
    xmlns:org.polarsys.capella.core.data.information.datatype="http://www.polarsys.org/capella/core/information/datatype/6.0.0"
    xmlns:org.polarsys.capella.core.data.information.datavalue="http://www.polarsys.org/capella/core/information/datavalue/6.0.0"
    xmlns:org.polarsys.capella.core.data.la="http://www.polarsys.org/capella/core/la/6.0.0"
    xmlns:org.polarsys.capella.core.data.oa="http://www.polarsys.org/capella/core/oa/6.0.0"
    xmlns:org.polarsys.capella.core.data.pa="http://www.polarsys.org/capella/core/pa/6.0.0"
    id="{E['project']}"
    name="OSR_capella_model">
  <ownedExtensions xsi:type="libraries:ModelInformation"
      id="{E['model_info']}"/>
  <ownedEnumerationPropertyTypes xsi:type="org.polarsys.capella.core.data.capellacore:EnumerationPropertyType"
      id="{E['progress_status']}"
      name="ProgressStatus">
    <ownedLiterals id="f8da2d96-2595-4331-96de-8f0f4c29402a" name="DRAFT"/>
    <ownedLiterals id="aaf352b9-a695-46ec-9a39-8203f8c7bd83" name="TO_BE_REVIEWED"/>
    <ownedLiterals id="81649bd8-51b0-46c4-b83f-cb5a9e0cdf9f" name="TO_BE_DISCUSSED"/>
    <ownedLiterals id="3d7e8fb6-f869-4ae1-a4bf-8334a7d680cc" name="REWORK_NECESSARY"/>
    <ownedLiterals id="7e11085b-c411-40c1-859e-84d602e43cba" name="UNDER_REWORK"/>
    <ownedLiterals id="54215d92-1a55-4d1e-a982-ad65951c72bf" name="REVIEWED_OK"/>
  </ownedEnumerationPropertyTypes>
  <keyValuePairs id="5fc8b8a8-1302-4080-bb25-3304013257e6"
      key="projectApproach"
      value="SingletonComponents"/>
  <ownedModelRoots xsi:type="org.polarsys.capella.core.data.capellamodeller:SystemEngineering"
      id="2c685d20-f62f-4884-b207-056bb5f2467d"
      name="OSR_capella_model">

    <!-- ===================================================================
         LAYER 1: OPERATIONAL ANALYSIS
         10 Operational Entities (OE-01..10)
         17 Operational Activities (OAct-01..04 + sub-activities)
         =================================================================== -->
    <ownedArchitectures xsi:type="org.polarsys.capella.core.data.oa:OperationalAnalysis"
        id="{E['oa_arch']}"
        name="Operational Analysis">

      <!-- Operational Activities -->
      <ownedFunctionPkg xsi:type="org.polarsys.capella.core.data.oa:RootActivityPkg"
          id="{E['oa_func_pkg']}"
          name="Operational Activities">
        <ownedOperationalActivities id="{E['oa_root_act']}"
            name="Root Operational Activity">
{ind(oa_acts, 5)}
        </ownedOperationalActivities>
      </ownedFunctionPkg>

      <!-- Operational Capabilities (empty — populate via Capella GUI) -->
      <ownedAbstractCapabilityPkg
          xsi:type="org.polarsys.capella.core.data.oa:OperationalCapabilityPkg"
          id="{E['oa_cap_pkg']}"
          name="Operational Capabilities"/>

      <ownedInterfacePkg xsi:type="org.polarsys.capella.core.data.cs:InterfacePkg"
          id="{E['oa_iface_pkg']}"
          name="Interfaces"/>
      <ownedDataPkg xsi:type="org.polarsys.capella.core.data.information:DataPkg"
          id="{E['oa_data_pkg']}"
          name="Data"/>
      <ownedRolePkg xsi:type="org.polarsys.capella.core.data.oa:RolePkg"
          id="{E['oa_role_pkg']}"
          name="Roles"/>

      <!-- Operational Entities -->
      <ownedEntityPkg xsi:type="org.polarsys.capella.core.data.oa:EntityPkg"
          id="{E['oa_entity_pkg']}"
          name="Operational Entities">
{ind(oa_entities, 4)}
      </ownedEntityPkg>

    </ownedArchitectures>

    <!-- ===================================================================
         LAYER 2: SYSTEM ANALYSIS
         7 System Functions (SF-01..07) + 14 sub-functions
         =================================================================== -->
    <ownedArchitectures xsi:type="org.polarsys.capella.core.data.ctx:SystemAnalysis"
        id="{E['sa_arch']}"
        name="System Analysis">

      <ownedFunctionPkg xsi:type="org.polarsys.capella.core.data.ctx:SystemFunctionPkg"
          id="{E['sa_func_pkg']}"
          name="System Functions">
        <ownedSystemFunctions id="{E['sa_root_sf']}"
            name="Root System Function">
          <ownedFunctionRealizations id="{E['sa_root_sf_real']}"
              targetElement="#{E['oa_root_act']}"
              sourceElement="#{E['sa_root_sf']}"/>
{ind(sa_fns, 5)}
        </ownedSystemFunctions>
      </ownedFunctionPkg>

      <ownedAbstractCapabilityPkg xsi:type="org.polarsys.capella.core.data.ctx:CapabilityPkg"
          id="{E['sa_cap_pkg']}"
          name="Capabilities"/>
      <ownedInterfacePkg xsi:type="org.polarsys.capella.core.data.cs:InterfacePkg"
          id="{E['sa_iface_pkg']}"
          name="Interfaces"/>

      <!-- SA Data Package (predefined types preserved) -->
      <ownedDataPkg xsi:type="org.polarsys.capella.core.data.information:DataPkg"
          id="{E['sa_data_pkg']}"
          name="Data">
        <ownedDataPkgs xsi:type="org.polarsys.capella.core.data.information:DataPkg"
            id="{E['sa_predefined_pkg']}"
            name="Predefined Types">
          <ownedDataTypes xsi:type="org.polarsys.capella.core.data.information.datatype:BooleanType"
              id="01df2fd1-e6e3-4236-a27a-b5f5b6c33c4b" name="Boolean" visibility="PUBLIC"/>
          <ownedDataTypes xsi:type="org.polarsys.capella.core.data.information.datatype:NumericType"
              id="a06c4a34-3a65-4e60-bac1-42f41c694133" name="Byte" visibility="PUBLIC" kind="INTEGER">
            <ownedMinValue xsi:type="org.polarsys.capella.core.data.information.datavalue:LiteralNumericValue"
                id="ba38e940-4e30-41b3-aabc-5df9d9e5e6af" value="0"/>
            <ownedMaxValue xsi:type="org.polarsys.capella.core.data.information.datavalue:LiteralNumericValue"
                id="c3e04b11-5b2a-4e9c-b1f0-8d6e2c3a1b2c" value="255"/>
          </ownedDataTypes>
          <ownedDataTypes xsi:type="org.polarsys.capella.core.data.information.datatype:NumericType"
              id="e45cd126-1a2b-3c4d-5e6f-7a8b9c0d1e2f" name="Double" visibility="PUBLIC"
              kind="FLOAT" discrete="false"/>
          <ownedDataTypes xsi:type="org.polarsys.capella.core.data.information.datatype:NumericType"
              id="50317265-2b3c-4d5e-6f7a-8b9c0d1e2f3a" name="Float" visibility="PUBLIC"
              kind="FLOAT" discrete="false"/>
          <ownedDataTypes xsi:type="org.polarsys.capella.core.data.information.datatype:NumericType"
              id="64255554-5e6f-7a8b-9c0d-1e2f3a4b5c6d" name="Integer" visibility="PUBLIC"
              kind="INTEGER"/>
          <ownedDataTypes xsi:type="org.polarsys.capella.core.data.information.datatype:StringType"
              id="9e7d189d-9c0d-1e2f-3a4b-5c6d7e8f9a0b" name="String" visibility="PUBLIC"/>
        </ownedDataPkgs>
      </ownedDataPkg>

      <!-- SA System Component -->
      <ownedSystemComponentPkg xsi:type="org.polarsys.capella.core.data.ctx:SystemComponentPkg"
          id="{E['sa_comp_pkg']}"
          name="Structure">
        <ownedParts id="{E['sa_system_part']}"
            name="System"
            abstractType="#{E['sa_system']}"/>
        <ownedSystemComponents id="{E['sa_system']}"
            name="System">
          <ownedStateMachines xsi:type="org.polarsys.capella.core.data.capellacommon:StateMachine"
              id="{E['sa_state_machine']}"
              name="System State Machine">
            <ownedRegions xsi:type="org.polarsys.capella.core.data.capellacommon:Region"
                id="{E['sa_state_region']}"
                name="Default Region"/>
          </ownedStateMachines>
        </ownedSystemComponents>
      </ownedSystemComponentPkg>

      <ownedMissionPkg xsi:type="org.polarsys.capella.core.data.ctx:MissionPkg"
          id="{E['sa_mission_pkg']}"
          name="Missions"/>
      <ownedOperationalAnalysisRealizations id="{E['sa_oa_real']}"
          targetElement="#{E['oa_arch']}"
          sourceElement="#{E['sa_arch']}"/>
    </ownedArchitectures>

    <!-- ===================================================================
         LAYER 3: LOGICAL ARCHITECTURE
         27 Logical Functions (LF-01.1..LF-07.3)
         8 Logical Components (LC-01..08)
         =================================================================== -->
    <ownedArchitectures xsi:type="org.polarsys.capella.core.data.la:LogicalArchitecture"
        id="{E['la_arch']}"
        name="Logical Architecture">

      <ownedFunctionPkg xsi:type="org.polarsys.capella.core.data.la:LogicalFunctionPkg"
          id="{E['la_func_pkg']}"
          name="Logical Functions">
        <ownedLogicalFunctions id="{E['la_root_lf']}"
            name="Root Logical Function">
          <ownedFunctionRealizations id="{E['la_root_lf_real']}"
              targetElement="#{E['sa_root_sf']}"
              sourceElement="#{E['la_root_lf']}"/>
{ind(la_fns, 5)}
        </ownedLogicalFunctions>
      </ownedFunctionPkg>

      <ownedAbstractCapabilityPkg
          xsi:type="org.polarsys.capella.core.data.la:CapabilityRealizationPkg"
          id="{E['la_cap_pkg']}"
          name="Capabilities"/>
      <ownedInterfacePkg xsi:type="org.polarsys.capella.core.data.cs:InterfacePkg"
          id="{E['la_iface_pkg']}"
          name="Interfaces"/>
      <ownedDataPkg xsi:type="org.polarsys.capella.core.data.information:DataPkg"
          id="{E['la_data_pkg']}"
          name="Data"/>

      <!-- Logical Components: LC-01..LC-08 nested under Logical System -->
      <ownedLogicalComponentPkg xsi:type="org.polarsys.capella.core.data.la:LogicalComponentPkg"
          id="{E['la_comp_pkg']}"
          name="Structure">
        <ownedParts id="{E['la_system_part']}"
            name="Logical System"
            abstractType="#{E['la_system']}"/>
        <ownedLogicalComponents id="{E['la_system']}"
            name="Logical System">
          <ownedComponentRealizations id="{E['la_system_real']}"
              targetElement="#{E['sa_system']}"
              sourceElement="#{E['la_system']}"/>
{ind(la_comps, 5)}
        </ownedLogicalComponents>
      </ownedLogicalComponentPkg>

      <ownedSystemAnalysisRealizations id="{E['la_sa_real']}"
          targetElement="#{E['sa_arch']}"
          sourceElement="#{E['la_arch']}"/>
    </ownedArchitectures>

    <!-- ===================================================================
         LAYER 4: PHYSICAL ARCHITECTURE
         28 Physical Functions (PF-01.1..PF-07.3)
         14 Physical Components (PC-COMP-01, PC-MCTL-01..PC-MECH-04)
         =================================================================== -->
    <ownedArchitectures xsi:type="org.polarsys.capella.core.data.pa:PhysicalArchitecture"
        id="{E['pa_arch']}"
        name="Physical Architecture">

      <ownedFunctionPkg xsi:type="org.polarsys.capella.core.data.pa:PhysicalFunctionPkg"
          id="{E['pa_func_pkg']}"
          name="Physical Functions">
        <ownedPhysicalFunctions id="{E['pa_root_pf']}"
            name="Root Physical Function">
          <ownedFunctionRealizations id="{E['pa_root_pf_real']}"
              targetElement="#{E['la_root_lf']}"
              sourceElement="#{E['pa_root_pf']}"/>
{ind(pa_fns, 5)}
        </ownedPhysicalFunctions>
      </ownedFunctionPkg>

      <ownedAbstractCapabilityPkg
          xsi:type="org.polarsys.capella.core.data.la:CapabilityRealizationPkg"
          id="{E['pa_cap_pkg']}"
          name="Capabilities"/>
      <ownedInterfacePkg xsi:type="org.polarsys.capella.core.data.cs:InterfacePkg"
          id="{E['pa_iface_pkg']}"
          name="Interfaces"/>
      <ownedDataPkg xsi:type="org.polarsys.capella.core.data.information:DataPkg"
          id="{E['pa_data_pkg']}"
          name="Data"/>

      <!-- Physical Components: PC-* nested under Physical System -->
      <ownedPhysicalComponentPkg xsi:type="org.polarsys.capella.core.data.pa:PhysicalComponentPkg"
          id="{E['pa_comp_pkg']}"
          name="Structure">
        <ownedParts id="{E['pa_system_part']}"
            name="Physical System"
            abstractType="#{E['pa_system']}"/>
        <ownedPhysicalComponents id="{E['pa_system']}"
            name="Physical System">
          <ownedComponentRealizations id="{E['pa_system_real']}"
              targetElement="#{E['la_system']}"
              sourceElement="#{E['pa_system']}"/>
{ind(pa_comps, 5)}
        </ownedPhysicalComponents>
      </ownedPhysicalComponentPkg>

      <ownedLogicalArchitectureRealizations id="{E['pa_la_real']}"
          targetElement="#{E['la_arch']}"
          sourceElement="#{E['pa_arch']}"/>
    </ownedArchitectures>

    <!-- ===================================================================
         LAYER 5: EPBS ARCHITECTURE
         5 Configuration Items (CI-01..05) with PA component realizations
         =================================================================== -->
    <ownedArchitectures xsi:type="org.polarsys.capella.core.data.epbs:EPBSArchitecture"
        id="{E['epbs_arch']}"
        name="EPBS Architecture">
      <ownedAbstractCapabilityPkg
          xsi:type="org.polarsys.capella.core.data.la:CapabilityRealizationPkg"
          id="{E['epbs_cap_pkg']}"
          name="Capabilities"/>
      <ownedConfigurationItemPkg xsi:type="org.polarsys.capella.core.data.epbs:ConfigurationItemPkg"
          id="{E['epbs_ci_pkg']}"
          name="Structure">
        <ownedParts id="{E['epbs_system_part']}"
            name="System"
            abstractType="#{E['epbs_system_ci']}"/>
        <ownedConfigurationItems id="{E['epbs_system_ci']}"
            name="System"
            kind="System">
          <ownedPhysicalArtifactRealizations id="{E['epbs_system_real']}"
              targetElement="#{E['pa_system']}"
              sourceElement="#{E['epbs_system_ci']}"/>
{ind(epbs_cis, 5)}
        </ownedConfigurationItems>
      </ownedConfigurationItemPkg>
      <ownedPhysicalArchitectureRealizations id="{E['epbs_pa_real']}"
          targetElement="#{E['pa_arch']}"
          sourceElement="#{E['epbs_arch']}"/>
    </ownedArchitectures>

  </ownedModelRoots>
</org.polarsys.capella.core.data.capellamodeller:Project>
"""
    return doc


# ---------------------------------------------------------------------------
# Element count for reporting
# ---------------------------------------------------------------------------

def count_elements(xml: str) -> dict:
    return {
        "OperationalActivities": xml.count("ownedOperationalActivities"),
        "OperationalEntities":   xml.count("ownedEntities"),
        "SystemFunctions":       xml.count("ownedSystemFunctions"),
        "LogicalFunctions":      xml.count("ownedLogicalFunctions"),
        "LogicalComponents":     xml.count("ownedLogicalComponents"),
        "PhysicalFunctions":     xml.count("ownedPhysicalFunctions"),
        "PhysicalComponents":    xml.count("ownedPhysicalComponents"),
        "ConfigurationItems":    xml.count("ownedConfigurationItems"),
        "FunctionRealizations":  xml.count("ownedFunctionRealizations"),
        "ComponentRealizations": xml.count("ownedComponentRealizations"),
        "PhysArtRealizations":   xml.count("ownedPhysicalArtifactRealizations"),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    script_dir = Path(__file__).parent
    out_path = script_dir / "OSR_capella_model" / "OSR_capella_model.capella"

    if not out_path.parent.exists():
        print(f"ERROR: target directory not found: {out_path.parent}", file=sys.stderr)
        sys.exit(1)

    xml = build_xml()
    out_path.write_text(xml, encoding="utf-8")

    counts = count_elements(xml)
    print(f"Written: {out_path}")
    print()
    print("Element counts:")
    for k, v in counts.items():
        print(f"  {k:<30} {v}")
    total_elements = sum(v for k, v in counts.items()
                         if "Realization" not in k)
    print(f"\n  Total model elements (excl. links): {total_elements}")
    total_links = sum(v for k, v in counts.items()
                      if "Realization" in k)
    print(f"  Total cross-layer links:            {total_links}")
    print()
    print("Open in Capella 6.1.0:")
    print("  File > Import > Existing Projects into Workspace")
    print(f"  Browse to: {script_dir}")
    print("  Select: OSR_capella_model")


if __name__ == "__main__":
    main()
