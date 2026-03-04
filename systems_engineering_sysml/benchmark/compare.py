#!/usr/bin/env python3
"""
benchmark/compare.py — Arcadia/Capella vs SysML v2 model comparison
=====================================================================
Counts model elements in both parallel artefact trees and produces a
side-by-side benchmark table.

Usage:
    cd systems_engineering_sysml/benchmark
    python3 compare.py
    python3 compare.py --json          # machine-readable output
    python3 compare.py --md            # GitHub markdown table

Counts compared:
    Requirements   : REQ- IDs (Arcadia) vs requirement def blocks (SysML v2)
    satisfy links  : PVG reqIDs strings (Arcadia) vs satisfy statements (SysML v2)
    Components     : LA part defs in Capella XML vs part def blocks (SysML v2)
    Functions      : SF entries in markdown vs action def blocks (SysML v2)
    Constraints    : Hazard rows in markdown vs constraint def blocks (SysML v2)
    Safety reqs    : SafetyCriticalReq defs (SysML v2 — new formalism, no Arcadia equiv)
    Verify links   : verify statements (SysML v2 — no Arcadia equiv)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]   # repo root
ARCADIA = ROOT / "systems_engineering"
SYSML   = ROOT / "systems_engineering_sysml"


# ── Arcadia counters ──────────────────────────────────────────────────────────

def count_arcadia_requirements() -> int:
    """Unique REQ-* IDs across all markdown and reqif files."""
    ids: set[str] = set()
    for path in ARCADIA.rglob("*.md"):
        ids.update(re.findall(r"REQ-[A-Z0-9-]+", path.read_text(encoding="utf-8")))
    reqif = ARCADIA / "MBSE_workspace" / "OSR_requirements.reqif"
    if reqif.exists():
        ids.update(re.findall(r"REQ-[A-Z0-9-]+", reqif.read_text(encoding="utf-8")))
    return len(ids)


def count_arcadia_pvg_links() -> int:
    """Count ownedPropertyValueGroups with name='Requirements' in Capella model."""
    capella = ARCADIA / "MBSE_workspace" / "OSR_capella_model" / "OSR_capella_model.capella"
    if not capella.exists():
        return 0
    text = capella.read_text(encoding="utf-8")
    return len(re.findall(r'name="Requirements"', text))


def count_arcadia_logical_components() -> int:
    """Count LC-xx entries in logical_components.md."""
    lc = ARCADIA / "03_logical_architecture" / "logical_components.md"
    if not lc.exists():
        return 0
    return len(re.findall(r"^## LC-\d+", lc.read_text(encoding="utf-8"), re.MULTILINE))


def count_arcadia_system_functions() -> int:
    """Count SF-xx entries in system_functions.md."""
    sf = ARCADIA / "02_system_analysis" / "system_functions.md"
    if not sf.exists():
        return 0
    return len(re.findall(r"^## SF-\d+", sf.read_text(encoding="utf-8"), re.MULTILINE))


def count_arcadia_hazards() -> int:
    """Count hazard rows in hazard_log.md."""
    hl = ARCADIA / "06_safety" / "hazard_log.md"
    if not hl.exists():
        return 0
    return len(re.findall(r"^\| H-\d+", hl.read_text(encoding="utf-8"), re.MULTILINE))


def count_arcadia_fmea_rows() -> int:
    """Count FM- entries in fmea_system.md."""
    fmea = ARCADIA / "06_safety" / "fmea_system.md"
    if not fmea.exists():
        return 0
    return len(re.findall(r"^\| FM-", fmea.read_text(encoding="utf-8"), re.MULTILINE))


# ── SysML v2 counters ─────────────────────────────────────────────────────────

def _scan_sysml(pattern: str) -> int:
    """Count pattern occurrences across all .sysml files."""
    count = 0
    for path in SYSML.rglob("*.sysml"):
        count += len(re.findall(pattern, path.read_text(encoding="utf-8")))
    return count


def count_sysml_requirement_defs() -> int:
    return _scan_sysml(r"\brequirement\s+def\b")


def count_sysml_safety_critical_reqs() -> int:
    """requirement defs that specialise SafetyCriticalReq."""
    return _scan_sysml(r":>\s*SafetyCriticalReq\b")


def count_sysml_satisfy_statements() -> int:
    return _scan_sysml(r"\bsatisfy\b")


def count_sysml_verify_statements() -> int:
    return _scan_sysml(r"\bverify\b")


def count_sysml_part_defs() -> int:
    return _scan_sysml(r"\bpart\s+def\b")


def count_sysml_action_defs() -> int:
    return _scan_sysml(r"\baction\s+def\b")


def count_sysml_constraint_defs() -> int:
    return _scan_sysml(r"\bconstraint\s+def\b")


def count_sysml_assert_constraints() -> int:
    return _scan_sysml(r"\bassert\s+constraint\b")


def count_sysml_files() -> int:
    return len(list(SYSML.rglob("*.sysml")))


# ── Report ────────────────────────────────────────────────────────────────────

def build_rows() -> list[dict]:
    return [
        {
            "metric":     "Requirements (total unique IDs)",
            "arcadia":    count_arcadia_requirements(),
            "sysml":      count_sysml_requirement_defs(),
            "note":       "Arcadia: REQ-* grep; SysML: requirement def count",
            "sysml_wins": True,   # first-class, formal, typed
        },
        {
            "metric":     "Safety-critical requirements",
            "arcadia":    "—",   # no formal distinction in Arcadia
            "sysml":      count_sysml_safety_critical_reqs(),
            "note":       "SysML only — SafetyCriticalReq specialisation with hazardRef + responseMs",
            "sysml_wins": True,
        },
        {
            "metric":     "satisfy/trace links",
            "arcadia":    count_arcadia_pvg_links(),
            "sysml":      count_sysml_satisfy_statements(),
            "note":       "Arcadia: PVG reqIDs strings; SysML: formal satisfy keyword",
            "sysml_wins": True,
        },
        {
            "metric":     "verify links",
            "arcadia":    "—",   # no verify in Arcadia without ATICA4Capella
            "sysml":      count_sysml_verify_statements(),
            "note":       "SysML only — first-class verify with testMethod metadata",
            "sysml_wins": True,
        },
        {
            "metric":     "Logical components / part defs",
            "arcadia":    count_arcadia_logical_components(),
            "sysml":      count_sysml_part_defs(),
            "note":       "Arcadia: LC-xx in markdown; SysML: part def with typed attributes",
            "sysml_wins": None,  # comparable
        },
        {
            "metric":     "System functions / action defs",
            "arcadia":    count_arcadia_system_functions(),
            "sysml":      count_sysml_action_defs(),
            "note":       "Arcadia: SF-xx markdown sections; SysML: action def with in/out ports",
            "sysml_wins": True,
        },
        {
            "metric":     "Safety constraints (hazards)",
            "arcadia":    count_arcadia_hazards(),
            "sysml":      count_sysml_constraint_defs(),
            "note":       "Arcadia: prose hazard table rows; SysML: evaluable constraint def",
            "sysml_wins": True,
        },
        {
            "metric":     "Asserted constraints",
            "arcadia":    "—",
            "sysml":      count_sysml_assert_constraints(),
            "note":       "SysML only — assert constraint ties hazard def to system scope",
            "sysml_wins": True,
        },
        {
            "metric":     "FMEA failure modes (rows)",
            "arcadia":    count_arcadia_fmea_rows(),
            "sysml":      "—",   # FMEA still in HTML dashboard; SysML v2 extension pending
            "note":       "Arcadia: safety_report.html; SysML extension planned (06_safety/fmea.sysml)",
            "sysml_wins": False,
        },
        {
            "metric":     "Model source files",
            "arcadia":    len(list(ARCADIA.rglob("*.md"))) + len(list(ARCADIA.rglob("*.capella"))),
            "sysml":      count_sysml_files(),
            "note":       "Arcadia: markdown + Capella XML; SysML: .sysml text files (git-diff friendly)",
            "sysml_wins": None,
        },
    ]


def print_table(rows: list[dict]) -> None:
    col_w = [40, 12, 12, 52]
    header = ["Metric", "Arcadia", "SysML v2", "Note"]
    sep    = ["-" * w for w in col_w]
    fmt    = "  ".join(f"{{:<{w}}}" for w in col_w)
    print()
    print("OSR MBSE Benchmark — Arcadia/Capella vs SysML v2")
    print("=" * (sum(col_w) + 3 * 2))
    print(fmt.format(*header))
    print(fmt.format(*sep))
    for r in rows:
        win = " ✓" if r["sysml_wins"] is True else (" ✗" if r["sysml_wins"] is False else "  ")
        print(fmt.format(
            r["metric"],
            str(r["arcadia"]),
            str(r["sysml"]) + win,
            r["note"][:col_w[3]],
        ))
    print()
    sysml_wins  = sum(1 for r in rows if r["sysml_wins"] is True)
    arcadia_wins = sum(1 for r in rows if r["sysml_wins"] is False)
    print(f"SysML v2 advantage: {sysml_wins} metrics  |  "
          f"Arcadia advantage: {arcadia_wins} metrics  |  "
          f"Comparable: {len(rows) - sysml_wins - arcadia_wins} metrics")
    print()


def print_markdown(rows: list[dict]) -> None:
    print("| Metric | Arcadia/Capella | SysML v2 | Note |")
    print("|---|---|---|---|")
    for r in rows:
        win = " ✓" if r["sysml_wins"] is True else (" ✗" if r["sysml_wins"] is False else "")
        print(f"| {r['metric']} | {r['arcadia']} | {r['sysml']}{win} | {r['note']} |")


def main() -> None:
    ap = argparse.ArgumentParser(description="OSR MBSE benchmark: Arcadia vs SysML v2")
    ap.add_argument("--json", action="store_true", help="Output JSON")
    ap.add_argument("--md",   action="store_true", help="Output GitHub markdown table")
    args = ap.parse_args()

    rows = build_rows()

    if args.json:
        print(json.dumps(rows, indent=2))
    elif args.md:
        print_markdown(rows)
    else:
        print_table(rows)


if __name__ == "__main__":
    main()
