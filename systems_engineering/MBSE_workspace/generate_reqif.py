#!/usr/bin/env python3
"""
generate_reqif.py — OSR Requirements → ReqIF 1.0
=================================================
Generates a valid ReqIF 1.0 XML file from the OSR requirements register.

ReqIF (Requirements Interchange Format, OMG standard) is the native import
format for Capella's Requirements Viewpoint.  It is also supported by IBM
DOORS, Polarion, Jama Connect, and most other requirements tools.

This script emulates what the Requirements Viewpoint plugin would produce
inside Capella, without needing the GUI installed:

  1. Run this script → OSR_requirements.reqif
  2. Open Capella with Requirements Viewpoint installed
  3. File > Import > ReqIF > select OSR_requirements.reqif
     → Requirements appear in the Requirements browser, already structured
        by layer, ready to link to model elements

Alternatively the .reqif is a complete deliverable on its own.

Usage:
    cd systems_engineering/MBSE_workspace
    python3 generate_reqif.py
    python3 generate_reqif.py --out /path/to/custom.reqif

Output: OSR_requirements.reqif  (default, next to this script)
"""

from __future__ import annotations

import argparse
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

# ---------------------------------------------------------------------------
# Deterministic UUIDs (same ID every run → stable cross-references)
# ---------------------------------------------------------------------------
_NS = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


def _id(name: str) -> str:
    return "_" + str(uuid.uuid5(_NS, name)).replace("-", "")


TIMESTAMP = "2024-01-01T00:00:00Z"

# ---------------------------------------------------------------------------
# Requirements data
# Each tuple: (req_id, layer, statement, status)
# Source: systems_engineering/requirements_register.md
# ---------------------------------------------------------------------------

OA_REQUIREMENTS: list[tuple[str, str, str]] = [
    # OAct-01
    ("REQ-OA-011-01", "OA", "Operator shall assess visible terrain for obstacles before commanding motion into any new area."),
    ("REQ-OA-011-02", "OA", "Operator shall define a traverse path avoiding obstacles exceeding the rover's mobility limits."),
    ("REQ-OA-011-03", "OA", "A go/no-go decision shall be made and communicated before each traverse segment."),
    ("REQ-OA-012-01", "OA", "Operator shall command rover motion using a single handheld controller."),
    ("REQ-OA-012-02", "OA", "Motion commands shall be transmitted with round-trip latency ≤ 200 ms under nominal Wi-Fi."),
    ("REQ-OA-012-03", "OA", "Rover shall come to a complete stop within 1 s of operator releasing the motion command."),
    ("REQ-OA-012-04", "OA", "Rover shall execute a commanded stop within 1 s if the wireless link is lost."),
    ("REQ-OA-013-01", "OA", "Operator shall receive rover telemetry updates at ≥ 5 Hz during active operation."),
    ("REQ-OA-013-02", "OA", "Battery state-of-charge shall be visible on the ground station display at all times."),
    ("REQ-OA-013-03", "OA", "Any fault condition shall produce a visible alert on the ground station within one telemetry cycle."),
    ("REQ-OA-013-04", "OA", "Operator shall distinguish normal from fault operating states from ground station display alone."),
    ("REQ-OA-014-01", "OA", "Operator shall issue a stop command within 3 s of recognising a hazard condition."),
    ("REQ-OA-014-02", "OA", "Operator shall acknowledge all system-generated fault events before resuming rover motion."),
    ("REQ-OA-014-03", "OA", "A clear recovery procedure shall exist for each fault type."),
    ("REQ-OA-015-01", "OA", "Rover shall stream live camera video to ground station at ≥ 10 fps during operation."),
    ("REQ-OA-015-02", "OA", "All sensor data shall be time-stamped with the rover's system clock."),
    ("REQ-OA-015-03", "OA", "Collected data shall be accessible for download via SSH after mission completion."),
    # OAct-02
    ("REQ-OA-021-01", "OA", "Battery shall be charged using a balance charger with cell-level voltage monitoring."),
    ("REQ-OA-021-02", "OA", "Charge rate shall not exceed 1C."),
    ("REQ-OA-021-03", "OA", "Battery shall not be charged while installed in rover unless a dedicated charge circuit with thermal monitoring is present."),
    ("REQ-OA-021-04", "OA", "A fully charged 3S LiPo shall measure ≥ 12.6 V at pack terminals."),
    ("REQ-OA-022-01", "OA", "A hardware inspection shall be performed after every operating session involving terrain traverse."),
    ("REQ-OA-022-02", "OA", "Any loose fastener shall be re-torqued before the next mission."),
    ("REQ-OA-022-03", "OA", "Worn or damaged components shall be replaced before rover is returned to service."),
    ("REQ-OA-023-01", "OA", "Software updates shall be deployed via SSH without requiring physical disassembly."),
    ("REQ-OA-023-02", "OA", "After any update, all ROS nodes shall be verified running before returning rover to service."),
    ("REQ-OA-023-03", "OA", "Post-update functional test shall include ≥ 0.5 m commanded forward motion and full stop."),
    # OAct-03
    ("REQ-OA-031-01", "OA", "All sourced components shall meet or exceed BOM specifications."),
    ("REQ-OA-031-02", "OA", "Builder shall verify received quantities against BOM before beginning assembly."),
    ("REQ-OA-031-03", "OA", "Substitute components shall be verified compatible before use."),
    ("REQ-OA-032-01", "OA", "Mechanical assembly shall be completable using only standard hand tools."),
    ("REQ-OA-032-02", "OA", "All pivot joints shall use flanged bearings."),
    ("REQ-OA-032-03", "OA", "All structural fasteners shall be tightened to finger-tight plus 1/4 turn unless otherwise specified."),
    ("REQ-OA-032-04", "OA", "Completed chassis shall support rover total mass without visible deflection."),
    ("REQ-OA-033-01", "OA", "A continuity check shall be performed on all power rails before applying battery power for the first time."),
    ("REQ-OA-033-02", "OA", "Wire gauges shall meet or exceed the minimum specified in the harness guide."),
    ("REQ-OA-033-03", "OA", "An in-line fuse (≤ 30 A) shall be installed between battery and PCB input."),
    ("REQ-OA-033-04", "OA", "All motor and servo connectors shall be secured with positive-retention connectors."),
    ("REQ-OA-034-01", "OA", "Software installation shall be completable following the documented guide without prior ROS expertise."),
    ("REQ-OA-034-02", "OA", "All ROS nodes shall start without errors on first launch after fresh installation."),
    ("REQ-OA-034-03", "OA", "Rover shall respond to /cmd_vel within 5 minutes of completing software installation."),
    ("REQ-OA-034-04", "OA", "Wi-Fi connectivity and SSH access shall be confirmed before launching ROS."),
    # OAct-04
    ("REQ-OA-041-01", "OA", "Payload designs shall not exceed power budget allocations."),
    ("REQ-OA-041-02", "OA", "Mechanical payload attachments shall use the standard M3 bolt pattern without permanent chassis modification."),
    ("REQ-OA-041-03", "OA", "Design package shall include a defined ROS data interface (topic name, message type, update rate)."),
    ("REQ-OA-041-04", "OA", "Payload mass shall be documented; total rover mass with payload shall not exceed 10 kg."),
    ("REQ-OA-042-01", "OA", "Payload integration shall not require removal or permanent modification of any baseline rover component."),
    ("REQ-OA-042-02", "OA", "All payload wiring shall be routed clear of rotating and articulating components."),
    ("REQ-OA-042-03", "OA", "Payload integration shall be reversible using only a standard Allen key set."),
    ("REQ-OA-043-01", "OA", "Custom ROS nodes shall be added to OSR catkin workspace without modifying existing baseline nodes."),
    ("REQ-OA-043-02", "OA", "New ROS topics shall follow the OSR naming convention."),
    ("REQ-OA-043-03", "OA", "All custom nodes shall handle startup and shutdown gracefully."),
    ("REQ-OA-043-04", "OA", "A README shall document all new topics, configurable parameters, and their data types."),
]

SF_REQUIREMENTS: list[tuple[str, str, str]] = [
    ("REQ-SF-01-01", "SF", "System shall accept motion commands as geometry_msgs/Twist on /cmd_vel."),
    ("REQ-SF-01-02", "SF", "System shall apply a 1-second command watchdog, outputting zero velocity on timeout."),
    ("REQ-SF-01-03", "SF", "System shall discard command messages containing NaN or Inf values."),
    ("REQ-SF-01-04", "SF", "System shall process command messages at a minimum rate of 10 Hz."),
    ("REQ-SF-02-01", "SF", "System shall compute per-wheel speed setpoints using the OSR rocker-bogie kinematic model."),
    ("REQ-SF-02-02", "SF", "Drive wheel setpoints shall be updated at ≥ 20 Hz."),
    ("REQ-SF-02-03", "SF", "System shall clamp drive setpoints to motor controller rated maximum speed."),
    ("REQ-SF-02-04", "SF", "System shall position corner steering servos to Ackermann-correct angles within 250 ms."),
    ("REQ-SF-02-05", "SF", "Upon halt signal from SF-06, SF-02 shall set all drive motor setpoints to zero within ≤ 50 ms."),
    ("REQ-SF-03-01", "SF", "System shall provide regulated 5V ± 5% to RPi and logic peripherals."),
    ("REQ-SF-03-02", "SF", "System shall read and publish battery voltage and current at ≥ 1 Hz."),
    ("REQ-SF-03-03", "SF", "System shall compute and publish state-of-charge as a percentage from LiPo discharge curve."),
    ("REQ-SF-03-04", "SF", "System shall trigger safe stop when any motor current exceeds 10 A."),
    ("REQ-SF-03-05", "SF", "System shall publish low-battery warning when voltage falls below 11.0 V."),
    ("REQ-SF-03-06", "SF", "System shall trigger safe stop when battery voltage falls below 10.5 V."),
    ("REQ-SF-04-01", "SF", "System shall sample wheel encoder counts at ≥ 20 Hz per wheel."),
    ("REQ-SF-04-02", "SF", "System shall sample IMU acceleration and gyroscope at ≥ 50 Hz."),
    ("REQ-SF-04-03", "SF", "System shall publish odometry (/odom) at ≥ 10 Hz."),
    ("REQ-SF-04-04", "SF", "System shall publish attitude (/imu) at ≥ 20 Hz."),
    ("REQ-SF-04-05", "SF", "System shall publish telemetry topics to ground station at ≥ 5 Hz."),
    ("REQ-SF-04-06", "SF", "Telemetry latency from sensor read to Wi-Fi transmission shall not exceed 200 ms."),
    ("REQ-SF-05-01", "SF", "System shall capture and publish video at ≥ 15 fps at 640x480 when camera is installed."),
    ("REQ-SF-05-02", "SF", "System shall publish compressed video on /camera/image_raw/compressed."),
    ("REQ-SF-05-03", "SF", "Video stream latency shall not exceed 500 ms over local Wi-Fi."),
    ("REQ-SF-05-04", "SF", "System shall start without error when camera is absent; SF-05 shall be inactive without affecting other functions."),
    ("REQ-SF-06-01", "SF", "System shall monitor motor channel current at ≥ 10 Hz."),
    ("REQ-SF-06-02", "SF", "System shall trigger safe stop within 100 ms of any motor current exceeding 10 A."),
    ("REQ-SF-06-03", "SF", "System shall publish battery warning at < 11.0 V and trigger safe stop at < 10.5 V."),
    ("REQ-SF-06-04", "SF", "System shall monitor rover roll and pitch at ≥ 10 Hz."),
    ("REQ-SF-06-05", "SF", "System shall trigger safe stop within 100 ms of roll or pitch exceeding 35°."),
    ("REQ-SF-06-06", "SF", "Upon safe stop, system shall zero all drive motor setpoints and publish fault event to /diagnostics."),
    ("REQ-SF-06-07", "SF", "Safe stop shall latch; rover shall not resume motion until operator clear command is received and fault resolved."),
    ("REQ-SF-07-01", "SF", "System shall provide switchable 5V @ ≥ 2 A and 12V @ ≥ 2 A to payload connector."),
    ("REQ-SF-07-02", "SF", "System shall monitor payload current and disable rail if exceeding configured limit (default 2 A)."),
    ("REQ-SF-07-03", "SF", "System shall provide USB, I2C, and UART connectivity to payload from Raspberry Pi."),
    ("REQ-SF-07-04", "SF", "Payload power enable/disable shall be controllable via software (GPIO)."),
    ("REQ-SF-07-05", "SF", "Payload power rail switching shall not interrupt or reset any other system power rail."),
]

LC_REQUIREMENTS: list[tuple[str, str, str]] = [
    ("REQ-LC-01-01", "LC", "LC-01 shall receive motion commands from ground station on /cmd_vel."),
    ("REQ-LC-01-02", "LC", "LC-01 shall detect command stream timeout and notify LC-02 to command zero velocity."),
    ("REQ-LC-01-03", "LC", "LC-01 shall relay all outbound telemetry topics to ground station at their respective publish rates."),
    ("REQ-LC-01-04", "LC", "LC-01 shall relay video stream from LC-08 when SF-05 is active."),
    ("REQ-LC-01-05", "LC", "LC-01 shall not drop or reorder command packets at distances ≤ 50 m."),
    ("REQ-LC-02-01", "LC", "LC-02 shall parse geometry_msgs/Twist and extract linear.x and angular.z."),
    ("REQ-LC-02-02", "LC", "LC-02 shall discard messages containing NaN or Inf values."),
    ("REQ-LC-02-03", "LC", "LC-02 shall clamp linear.x to ±0.4 m/s and angular.z to ±1.0 rad/s."),
    ("REQ-LC-02-04", "LC", "LC-02 shall output zero velocity to LC-03 immediately upon halt command from LC-05."),
    ("REQ-LC-02-05", "LC", "LC-02 shall output zero velocity to LC-03 when LC-01 signals watchdog timeout."),
    ("REQ-LC-03-01", "LC", "LC-03 shall compute per-wheel speed setpoints using the OSR rocker-bogie kinematic model."),
    ("REQ-LC-03-02", "LC", "LC-03 shall compute Ackermann steering angles for all four corner wheels."),
    ("REQ-LC-03-03", "LC", "LC-03 shall update drive wheel setpoints at ≥ 20 Hz."),
    ("REQ-LC-03-04", "LC", "LC-03 shall update steering servo angles within 250 ms of angular velocity change."),
    ("REQ-LC-03-05", "LC", "LC-03 shall clamp wheel speed setpoints to motor controller rated maximum."),
    ("REQ-LC-03-06", "LC", "LC-03 shall clamp steering angles to each servo's mechanical range (±30°)."),
    ("REQ-LC-03-07", "LC", "LC-03 shall output zero speed to all wheels immediately upon halt command."),
    ("REQ-LC-04-01", "LC", "LC-04 shall read wheel encoder counts from all six wheels at ≥ 20 Hz."),
    ("REQ-LC-04-02", "LC", "LC-04 shall read IMU acceleration and angular velocity at ≥ 50 Hz."),
    ("REQ-LC-04-03", "LC", "LC-04 shall read per-channel motor currents at ≥ 10 Hz."),
    ("REQ-LC-04-04", "LC", "LC-04 shall publish nav_msgs/Odometry at ≥ 10 Hz."),
    ("REQ-LC-04-05", "LC", "LC-04 shall publish sensor_msgs/Imu at ≥ 20 Hz."),
    ("REQ-LC-04-06", "LC", "LC-04 shall publish per-motor current readings to LC-05 at ≥ 10 Hz."),
    ("REQ-LC-04-07", "LC", "Odometry position error shall not exceed 10% of distance travelled in straight-line test."),
    ("REQ-LC-05-01", "LC", "LC-05 shall monitor motor currents at ≥ 10 Hz and trigger safe stop within 100 ms of 10 A threshold."),
    ("REQ-LC-05-02", "LC", "LC-05 shall monitor battery voltage at ≥ 1 Hz, warn at < 11.0 V, and stop at < 10.5 V."),
    ("REQ-LC-05-03", "LC", "LC-05 shall monitor roll and pitch at ≥ 10 Hz and trigger safe stop within 100 ms of 35° threshold."),
    ("REQ-LC-05-04", "LC", "All critical faults shall latch; halt persists until clear_fault service call is received."),
    ("REQ-LC-05-05", "LC", "LC-05 shall verify fault condition resolved before responding to clear_fault."),
    ("REQ-LC-05-06", "LC", "LC-05 shall publish all fault events with timestamp and classification to /diagnostics."),
    ("REQ-LC-06-01", "LC", "LC-06 shall read battery voltage and current from INA219 at ≥ 1 Hz."),
    ("REQ-LC-06-02", "LC", "LC-06 shall publish sensor_msgs/BatteryState on /battery_state."),
    ("REQ-LC-06-03", "LC", "LC-06 shall compute SoC% using 3S LiPo discharge curve (100% at ≥ 12.6 V, 0% at ≤ 10.5 V)."),
    ("REQ-LC-06-04", "LC", "LC-06 shall provide software-controllable enable/disable for payload power rail."),
    ("REQ-LC-06-05", "LC", "LC-06 voltage measurement accuracy shall be within ±0.1 V of multimeter reference."),
    ("REQ-LC-07-01", "LC", "LC-07 shall publish aggregated diagnostic summary at ≥ 5 Hz."),
    ("REQ-LC-07-02", "LC", "LC-07 shall include battery state, fault flags, odometry, attitude, and motor currents in telemetry."),
    ("REQ-LC-07-03", "LC", "LC-07 shall relay video frames from LC-08 when SF-05 is active."),
    ("REQ-LC-07-04", "LC", "LC-07 shall not introduce more than 50 ms of additional latency to sensor topic data."),
    ("REQ-LC-08-01", "LC", "LC-08 shall provide GPIO-controlled 5V and 12V power rails to payload connector."),
    ("REQ-LC-08-02", "LC", "LC-08 shall monitor payload current at ≥ 1 Hz and disable rail if exceeding limit (default 2 A)."),
    ("REQ-LC-08-03", "LC", "LC-08 shall publish a fault event to /diagnostics on payload overcurrent."),
    ("REQ-LC-08-04", "LC", "LC-08 shall provide USB, I2C, and UART pass-through from payload connector to RPi."),
    ("REQ-LC-08-05", "LC", "Payload power switching shall not affect any other power rail or reset the Raspberry Pi."),
]

# Layer definitions: (module_id_key, display_name, requirements_list)
MODULES = [
    ("OSR-OA-MODULE",  "Operational Analysis Requirements",  OA_REQUIREMENTS),
    ("OSR-SF-MODULE",  "System Function Requirements",       SF_REQUIREMENTS),
    ("OSR-LC-MODULE",  "Logical Component Requirements",     LC_REQUIREMENTS),
]

# ---------------------------------------------------------------------------
# ReqIF XML generation
# ---------------------------------------------------------------------------

def _spec_object(req_id: str, statement: str, layer: str, status: str = "DRAFT") -> str:
    return (
        f'      <SPEC-OBJECT IDENTIFIER="{req_id}" LAST-CHANGE="{TIMESTAMP}"'
        f' LONG-NAME="{req_id}">\n'
        f'        <TYPE><SPEC-OBJECT-TYPE-REF>SOT-REQUIREMENT</SPEC-OBJECT-TYPE-REF></TYPE>\n'
        f'        <VALUES>\n'
        f'          <ATTRIBUTE-VALUE-STRING THE-VALUE="{xml_escape(req_id)}">\n'
        f'            <DEFINITION><ATTRIBUTE-DEFINITION-STRING-REF>AD-ID</ATTRIBUTE-DEFINITION-STRING-REF></DEFINITION>\n'
        f'          </ATTRIBUTE-VALUE-STRING>\n'
        f'          <ATTRIBUTE-VALUE-STRING THE-VALUE="{xml_escape(statement)}">\n'
        f'            <DEFINITION><ATTRIBUTE-DEFINITION-STRING-REF>AD-TEXT</ATTRIBUTE-DEFINITION-STRING-REF></DEFINITION>\n'
        f'          </ATTRIBUTE-VALUE-STRING>\n'
        f'          <ATTRIBUTE-VALUE-STRING THE-VALUE="{xml_escape(layer)}">\n'
        f'            <DEFINITION><ATTRIBUTE-DEFINITION-STRING-REF>AD-LAYER</ATTRIBUTE-DEFINITION-STRING-REF></DEFINITION>\n'
        f'          </ATTRIBUTE-VALUE-STRING>\n'
        f'          <ATTRIBUTE-VALUE-STRING THE-VALUE="{xml_escape(status)}">\n'
        f'            <DEFINITION><ATTRIBUTE-DEFINITION-STRING-REF>AD-STATUS</ATTRIBUTE-DEFINITION-STRING-REF></DEFINITION>\n'
        f'          </ATTRIBUTE-VALUE-STRING>\n'
        f'        </VALUES>\n'
        f'      </SPEC-OBJECT>'
    )


def _spec_hierarchy(req_id: str, depth: int = 3) -> str:
    pad = "  " * depth
    hier_id = _id(f"sh:{req_id}")
    return (
        f'{pad}<SPEC-HIERARCHY IDENTIFIER="{hier_id}" LAST-CHANGE="{TIMESTAMP}">\n'
        f'{pad}  <OBJECT><SPEC-OBJECT-REF>{req_id}</SPEC-OBJECT-REF></OBJECT>\n'
        f'{pad}</SPEC-HIERARCHY>'
    )


def generate_reqif() -> str:
    all_reqs = OA_REQUIREMENTS + SF_REQUIREMENTS + LC_REQUIREMENTS

    # ── SPEC-OBJECTS (all requirements) ─────────────────────────────────────
    spec_objects = "\n".join(
        _spec_object(rid, stmt, layer)
        for rid, layer, stmt in all_reqs
    )

    # ── SPECIFICATIONS (one per module / layer) ──────────────────────────────
    specs = []
    for module_id, module_name, reqs in MODULES:
        children = "\n".join(_spec_hierarchy(rid) for rid, _, _ in reqs)
        specs.append(
            f'      <SPECIFICATION IDENTIFIER="{module_id}" LAST-CHANGE="{TIMESTAMP}"'
            f' LONG-NAME="{xml_escape(module_name)}">\n'
            f'        <TYPE><SPECIFICATION-TYPE-REF>SPEC-TYPE-MODULE</SPECIFICATION-TYPE-REF></TYPE>\n'
            f'        <CHILDREN>\n'
            f'{children}\n'
            f'        </CHILDREN>\n'
            f'      </SPECIFICATION>'
        )
    specifications = "\n".join(specs)

    total = len(all_reqs)
    return f"""\
<?xml version="1.0" encoding="UTF-8"?>
<!--
  OSR Requirements — ReqIF 1.0
  Generated by generate_reqif.py
  Total requirements: {total}
  Modules: {len(MODULES)} (OA, SF, LC)

  Import into Capella Requirements Viewpoint:
    1. Install Requirements Viewpoint add-on for Capella 6.1
       https://download.eclipse.org/capella/addons/requirements/updates/releases/0.13.1
    2. File > Import > Requirements > Import ReqIF
    3. Select this file

  Standalone use:
    Also importable into IBM DOORS, Polarion, Jama Connect (ReqIF 1.0 compatible).
-->
<REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd">

  <THE-HEADER>
    <REQ-IF-HEADER IDENTIFIER="OSR-REQIF-HEADER"
                   CREATION-TIME="{TIMESTAMP}"
                   TITLE="JPL Open Source Rover — Requirements Register"
                   REQ-IF-TOOL-ID="generate_reqif.py"
                   REQ-IF-VERSION="1.0"
                   SOURCE-TOOL-ID="OSR MBSE — Arcadia/Capella 6.1"/>
  </THE-HEADER>

  <CORE-CONTENT>
    <REQ-IF-CONTENT>

      <!-- ─── Data types ─────────────────────────────────────────────────── -->
      <DATATYPES>
        <DATATYPE-DEFINITION-STRING IDENTIFIER="DT-STRING-1024"
            LAST-CHANGE="{TIMESTAMP}" MAX-LENGTH="1024" NAME="String1024"/>
      </DATATYPES>

      <!-- ─── Spec types ─────────────────────────────────────────────────── -->
      <SPEC-TYPES>
        <SPEC-OBJECT-TYPE IDENTIFIER="SOT-REQUIREMENT"
            LAST-CHANGE="{TIMESTAMP}" LONG-NAME="Requirement">
          <SPEC-ATTRIBUTES>
            <ATTRIBUTE-DEFINITION-STRING IDENTIFIER="AD-ID"
                LAST-CHANGE="{TIMESTAMP}" LONG-NAME="ID">
              <TYPE><DATATYPE-DEFINITION-STRING-REF>DT-STRING-1024</DATATYPE-DEFINITION-STRING-REF></TYPE>
            </ATTRIBUTE-DEFINITION-STRING>
            <ATTRIBUTE-DEFINITION-STRING IDENTIFIER="AD-TEXT"
                LAST-CHANGE="{TIMESTAMP}" LONG-NAME="Text">
              <TYPE><DATATYPE-DEFINITION-STRING-REF>DT-STRING-1024</DATATYPE-DEFINITION-STRING-REF></TYPE>
            </ATTRIBUTE-DEFINITION-STRING>
            <ATTRIBUTE-DEFINITION-STRING IDENTIFIER="AD-LAYER"
                LAST-CHANGE="{TIMESTAMP}" LONG-NAME="Layer">
              <TYPE><DATATYPE-DEFINITION-STRING-REF>DT-STRING-1024</DATATYPE-DEFINITION-STRING-REF></TYPE>
            </ATTRIBUTE-DEFINITION-STRING>
            <ATTRIBUTE-DEFINITION-STRING IDENTIFIER="AD-STATUS"
                LAST-CHANGE="{TIMESTAMP}" LONG-NAME="Status">
              <TYPE><DATATYPE-DEFINITION-STRING-REF>DT-STRING-1024</DATATYPE-DEFINITION-STRING-REF></TYPE>
            </ATTRIBUTE-DEFINITION-STRING>
          </SPEC-ATTRIBUTES>
        </SPEC-OBJECT-TYPE>
        <SPECIFICATION-TYPE IDENTIFIER="SPEC-TYPE-MODULE"
            LAST-CHANGE="{TIMESTAMP}" LONG-NAME="Module"/>
      </SPEC-TYPES>

      <!-- ─── Spec objects (one per requirement) ─────────────────────────── -->
      <SPEC-OBJECTS>
{spec_objects}
      </SPEC-OBJECTS>

      <!-- ─── Specifications (one per Arcadia layer) ─────────────────────── -->
      <SPECIFICATIONS>
{specifications}
      </SPECIFICATIONS>

    </REQ-IF-CONTENT>
  </CORE-CONTENT>

</REQ-IF>
"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(
        description="Generate OSR_requirements.reqif from the requirements register"
    )
    p.add_argument("--out", "-o", default=None,
                   help="Output path (default: OSR_requirements.reqif next to this script)")
    args = p.parse_args()

    out = Path(args.out) if args.out else Path(__file__).parent / "OSR_requirements.reqif"
    content = generate_reqif()
    out.write_text(content, encoding="utf-8")

    total = len(OA_REQUIREMENTS) + len(SF_REQUIREMENTS) + len(LC_REQUIREMENTS)
    print(f"Written: {out}")
    print(f"  {total} requirements across {len(MODULES)} modules (OA, SF, LC)")
    print(f"  ReqIF 1.0 — importable into Capella Requirements Viewpoint 0.13.1")


if __name__ == "__main__":
    main()
