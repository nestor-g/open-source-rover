# Safety Analysis

This section contains the safety analysis artifacts for the JPL Open Source Rover,
cross-referenced to the MBSE model elements and requirements register.

## Contents

| File | Description |
|---|---|
| [hazard_log.md](hazard_log.md) | Hazard identification and risk matrix (10 hazards) |
| [fmea_system.md](fmea_system.md) | System-level FMEA — function failure modes and effects |
| [fta.md](fta.md) | Fault tree analysis for top-level hazards (Mermaid diagrams) |
| [scenarios/](scenarios/README.md) | Scenic probabilistic scenario generator for test case generation |

## Relationship to MBSE Model

Safety analysis drives the design of:
- **SF-06** (Detect and Handle Faults) and all sub-functions
- **LC-05** (Fault Monitor) and its monitoring thresholds
- **REQ-SF-06-xxx** and **REQ-LC-05-xxx** in the requirements register
- Configuration Items **CI-01** through **CI-04** (verification criteria)

The thresholds defined here (10 A motor current, 10.5 V battery, 35° tilt) are
*derived from* the hazard log — not arbitrary. Each threshold traces to a hazard.

## Risk Matrix

| Severity → | 1 Negligible | 2 Minor | 3 Moderate | 4 Critical | 5 Catastrophic |
|---|---|---|---|---|---|
| **5 Very likely** | Medium | High | High | Extreme | Extreme |
| **4 Likely** | Low | Medium | High | High | Extreme |
| **3 Possible** | Low | Medium | Medium | High | High |
| **2 Unlikely** | Low | Low | Medium | Medium | High |
| **1 Very unlikely** | Low | Low | Low | Low | Medium |

**Target:** All hazards reduced to Low or Medium risk after mitigation.

## Process

```
Hazard Log (H-xx) → FMEA (FM-xx) → Safety Requirements (REQ-SAF-xx)
                                   → Fault Tree (FTA)
                                   → Scenic Scenarios (test cases)
```
