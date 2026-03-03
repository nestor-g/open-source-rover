# Cross-Layer Traceability

This page visualises the vertical traceability chains that link the OSR MBSE model
across all five Arcadia layers: Operational Analysis → System Analysis →
Logical Architecture → Physical Architecture → EPBS.

For the interactive, clickable version open the
**[Model Viewer](MBSE_workspace/model_viewer.html)** and click the **Graph** button
in the top-right corner.

---

## Layer Stack Overview

```mermaid
flowchart TB
    subgraph OA["🔵 Operational Analysis (OA)"]
        direction LR
        OE["Operational Entities\n(OE-01 … OE-10)"]
        OAct["Operational Activities\n(OAct-01 … OAct-04)"]
    end
    subgraph SA["🟢 System Analysis (SA)"]
        direction LR
        SF["System Functions\n(SF-01 … SF-07)"]
    end
    subgraph LA["🟣 Logical Architecture (LA)"]
        direction LR
        LC["Logical Components\n(LC-01 … LC-08)"]
        LF["Logical Functions\n(LF-01.x … LF-07.x)"]
    end
    subgraph PA["🟠 Physical Architecture (PA)"]
        direction LR
        PC["Physical Components\n(PC-COMP-01 … PC-MECH-04)"]
        PF["Physical Functions\n(PF-01.x … PF-07.x)"]
    end
    subgraph EPBS["🔴 EPBS"]
        CI["Configuration Items\n(CI-01 … CI-05)"]
    end

    OAct -->|"realized by"| SF
    SF   -->|"realized by"| LC
    SF   -->|"decomposed into"| LF
    LC   -->|"realized by"| PC
    LF   -->|"realized by"| PF
    PC   -->|"grouped into"| CI
```

---

## Motion Control Chain

Traces how an operator command flows from the operational world through to physical hardware.

```mermaid
flowchart TD
    OAct012["OAct-01.2\nCommand Rover Motion"]

    SF01["SF-01\nReceive & Decode Command"]
    SF021["SF-02.1\nCompute Drive Commands"]
    SF022["SF-02.2\nDrive Wheels"]
    SF023["SF-02.3\nSteer Corner Wheels"]

    LC01["LC-01\nCommunication Manager"]
    LC02["LC-02\nCommand Processor"]
    LC03["LC-03\nMobility Controller"]

    PCRPI["PC-COMP-01\nRaspberry Pi 4B"]
    PCRC["PC-MCTL-01\nRoboClaw ×3"]
    PCPCA["PC-MCTL-02\nPCA9685 Servo Driver"]

    OAct012 --> SF01
    OAct012 --> SF021
    OAct012 --> SF022
    OAct012 --> SF023

    SF01   --> LC01
    SF01   --> LC02
    SF021  --> LC03
    SF022  --> LC03
    SF023  --> LC03

    LC01   --> PCRPI
    LC02   --> PCRPI
    LC03   --> PCRPI
    LC03   --> PCRC
    LC03   --> PCPCA
```

---

## Telemetry & State Estimation Chain

```mermaid
flowchart TD
    OAct013["OAct-01.3\nMonitor Rover State"]

    SF041["SF-04.1\nSample Sensors"]
    SF042["SF-04.2\nEstimate Rover State"]
    SF043["SF-04.3\nTransmit Telemetry"]

    LC04["LC-04\nState Estimator"]
    LC07["LC-07\nTelemetry Publisher"]

    PCRPI["PC-COMP-01\nRaspberry Pi 4B"]
    PCIMU["PC-SENS-01\nBNO055 IMU"]
    PCENC["PC-SENS-02\nWheel Encoders ×6"]

    OAct013 --> SF041
    OAct013 --> SF042
    OAct013 --> SF043

    SF041 --> LC04
    SF042 --> LC04
    SF043 --> LC07

    LC04 --> PCRPI
    LC04 --> PCIMU
    LC04 --> PCENC
    LC07 --> PCRPI
```

---

## Fault Detection Chain

```mermaid
flowchart TD
    OAct014["OAct-01.4\nRespond to Hazard"]

    SF061["SF-06.1\nMonitor Motor Currents"]
    SF062["SF-06.2\nMonitor Battery Voltage"]
    SF063["SF-06.3\nDetect Tip Risk (IMU)"]
    SF064["SF-06.4\nExecute Safe Stop"]

    LC05["LC-05\nFault Monitor"]

    PCRPI["PC-COMP-01\nRaspberry Pi 4B"]

    OAct014 --> SF061
    OAct014 --> SF062
    OAct014 --> SF063
    OAct014 --> SF064

    SF061 --> LC05
    SF062 --> LC05
    SF063 --> LC05
    SF064 --> LC05

    LC05 --> PCRPI
```

---

## Power Management Chain

```mermaid
flowchart TD
    OAct021["OAct-02.1\nCharge Battery"]

    SF031["SF-03.1\nDistribute Electrical Power"]
    SF032["SF-03.2\nMonitor Battery State"]
    SF033["SF-03.3\nProtect Against Overcurrent"]

    LC06["LC-06\nPower Manager"]

    PCPCB["PC-PCB-01\nCustom OSR PCB"]
    PCPWR["PC-PWR-01\n3S LiPo Battery"]
    PCINA["PC-SENS-03\nINA219 Power Monitor"]

    OAct021 --> SF031
    OAct021 --> SF032
    OAct021 --> SF033

    SF031 --> LC06
    SF032 --> LC06
    SF033 --> LC06

    LC06 --> PCPCB
    LC06 --> PCPWR
    LC06 --> PCINA
```

---

## EPBS Configuration Item Breakdown

```mermaid
flowchart TD
    CI01["CI-01\nOSR Software Stack\n(CSCI)"]
    CI02["CI-02\nCompute Hardware\n(HWCI)"]
    CI03["CI-03\nMotor Drive System\n(HWCI)"]
    CI04["CI-04\nPower & Sensing System\n(HWCI)"]
    CI05["CI-05\nMechanical Structure\n(HWCI)"]

    PCRPI["PC-COMP-01\nRaspberry Pi 4B"]
    PCRC["PC-MCTL-01\nRoboClaw ×3"]
    PCPCA["PC-MCTL-02\nPCA9685"]
    PCPCB["PC-PCB-01\nCustom PCB"]
    PCPWR["PC-PWR-01\n3S LiPo"]
    PCIMU["PC-SENS-01\nBNO055 IMU"]
    PCENC["PC-SENS-02\nEncoders ×6"]
    PCINA["PC-SENS-03\nINA219"]
    PCCAM["PC-CAM-01\nCamera"]
    PCMOT["PC-MECH-01\nDrive Motors ×6"]
    PCSRV["PC-MECH-02\nSteering Servos ×4"]
    PCCHS["PC-MECH-03\nRocker-Bogie Chassis"]
    PCWHL["PC-MECH-04\nWheel Assembly ×6"]

    CI01 --> PCRPI
    CI02 --> PCRPI
    CI03 --> PCRC
    CI03 --> PCPCA
    CI03 --> PCMOT
    CI03 --> PCSRV
    CI04 --> PCPCB
    CI04 --> PCPWR
    CI04 --> PCIMU
    CI04 --> PCENC
    CI04 --> PCINA
    CI04 --> PCCAM
    CI05 --> PCCHS
    CI05 --> PCWHL
```

---

## Reading the Diagrams

| Arrow | Meaning |
|---|---|
| `A --> B` | A is realized by / decomposes into B |
| `A -->|"realized by"| B` | Explicit realization link |

All element IDs match the full MBSE model.
Cross-reference with the [Requirements Register](requirements_register.md) for
the requirements associated with each element.
