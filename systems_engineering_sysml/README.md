# OSR SysML v2 Model

Parallel MBSE model of the JPL Open Source Rover in **SysML v2 textual notation**.
Maintained alongside the Arcadia/Capella model in `../systems_engineering/` for direct comparison.

## Structure

```
systems_engineering_sysml/
├── core/
│   ├── types.sysml          # OSR scalar types, safety thresholds, ROS topic defs
│   └── relations.sysml      # Base requirement stereotypes: OSRRequirement,
│                            #   SafetyCriticalReq, PerformanceReq, InterfaceReq
│                            #   + SatisfyLink / VerifyLink metadata
├── requirements/
│   ├── oa_requirements.sysml  # 53 OA requirement defs (operational analysis)
│   ├── sf_requirements.sysml  # 34 SF requirement defs (system functions)
│   ├── lc_requirements.sysml  # 44 LC requirement defs (logical components)
│   └── pf_requirements.sysml  # 35 PF requirement defs (physical functions)
├── 01_operational_analysis/   # (actors.sysml — stakeholder part defs)
├── 02_system_analysis/
│   └── system_functions.sysml # SF-01..SF-07 as action defs with in/out ports
├── 03_logical_architecture/
│   └── components.sysml     # LC-01..LC-08 as part defs with satisfy statements
├── 04_physical_architecture/  # (components.sysml — RPi, RoboClaw, PCB parts)
├── 06_safety/
│   └── constraints.sysml    # H-01..H-10 hazard constraints + RPN constraint
├── traceability/
│   └── satisfy_matrix.sysml # Cross-layer satisfy/verify links (OA→SF, SF→LC)
└── benchmark/
    ├── compare.py           # Element count comparison: Arcadia vs SysML v2
    └── benchmark.md         # Latest benchmark results (regenerate with compare.py)
```

## Key differences vs Arcadia/Capella

| Concept | Arcadia/Capella | SysML v2 (this model) |
|---|---|---|
| Requirements | Markdown prose + REQ-* IDs | `requirement def` — typed, with `subject` |
| Requirement types | No formal distinction | `OSRRequirement`, `SafetyCriticalReq`, `PerformanceReq`, `InterfaceReq` |
| Safety thresholds | Strings in markdown + Scenic | `constraint def` — evaluable predicates |
| Traceability | `PropertyValueGroup` XML strings | `satisfy` / `verify` — language keywords |
| Components | Capella `.capella` XML | `part def` — plain text, git-diffable |
| Functions | SF prose sections | `action def` with typed `in`/`out` parameters |
| Tooling | Eclipse Capella GUI | Any SysML v2 tool or plain text editor |

## Running the benchmark

```bash
cd benchmark
python3 compare.py          # console table
python3 compare.py --md     # GitHub markdown
python3 compare.py --json   # machine-readable JSON
```

## SysML v2 tooling options

| Tool | Type | Cost |
|---|---|---|
| [SysML v2 Pilot Implementation](https://github.com/Systems-Modeling/SysML-v2-Release) | Jupyter + VS Code | Free/OSS |
| MagicDraw / Cameo 2024+ | GUI (preview) | Commercial |
| Eclipse SysON | Web browser GUI | Free/OSS (alpha) |

The `.sysml` files in this model follow the **OMG SysML v2 standard textual notation**
and should parse with any conformant tool.

## Arcadia parallel

Each file documents its Arcadia counterpart in the file-level docstring.
The mapping is 1:1 at the package level:

| SysML v2 package | Arcadia equivalent |
|---|---|
| `OSR::Requirements::OA` | `requirements_register.md § OA` |
| `OSR::Requirements::SF` | `requirements_register.md § SF` |
| `OSR::Requirements::LC` | `requirements_register.md § LC` |
| `OSR::Requirements::PF` | `requirements_register.md § PF` |
| `OSR::SA::SystemFunctions` | `02_system_analysis/system_functions.md` |
| `OSR::LA::Components` | `03_logical_architecture/logical_components.md` |
| `OSR::Safety::Constraints` | `06_safety/hazard_log.md` |
| `OSR::Traceability::SatisfyMatrix` | `traceability.md` + Capella PVG reqIDs |
