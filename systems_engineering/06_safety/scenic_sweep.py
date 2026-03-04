#!/usr/bin/env python3
"""
scenic_sweep.py — OSR parametric sweep CLI
==========================================
Runs a parametric sweep through the OSR OA/OE parameter space,
evaluates safety constraints, generates optional ``.scenic`` files,
and writes a report.

Usage examples
--------------

Basic LHS sweep, 500 samples, print summary::

    python scenic_sweep.py

Monte Carlo sweep, 1000 samples, write HTML + JSON reports::

    python scenic_sweep.py --method montecarlo --n 1000 \\
        --out sweep_out/ --html --json

Focus on a specific hazard (adds extra near-threshold samples)::

    python scenic_sweep.py --hazard H-02 --n 300

Generate Scenic files for the boundary/hazardous points::

    python scenic_sweep.py --generate-scenarios

Grid sweep over a specific parameter subset (small n!)::

    python scenic_sweep.py --method grid --grid-steps 8 \\
        --params motor_current_peak roll_deg

List all parameters in the space::

    python scenic_sweep.py --list-params

Evaluate a single parameter vector::

    python scenic_sweep.py --eval motor_current_peak=11.5,roll_deg=30.0

Options
-------
Run ``python scenic_sweep.py --help`` for the full option list.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running from this directory without installing the package
_THIS = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS))

from scenic_module import (
    ALL_PARAMETERS,
    SweepConfig,
    SweepEngine,
    SweepReport,
    evaluate_all,
    generate_scenarios,
    quick_sweep,
)
from scenic_module.constraint_oracle import SWEEP_CONSTRAINTS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_params(param_str: str) -> dict[str, float]:
    """Parse ``key=val,key2=val2`` into a dict of floats."""
    result: dict[str, float] = {}
    for token in param_str.split(","):
        token = token.strip()
        if "=" not in token:
            continue
        key, val = token.split("=", 1)
        result[key.strip()] = float(val.strip())
    return result


def _list_params(args: argparse.Namespace) -> None:
    from scenic_module import OA_PARAMETERS, OE_PARAMETERS
    print("\n  OA Parameters (rover state — controlled by system):")
    print(f"  {'Key':<25} {'Name':<30} {'Unit':<8} {'Nominal':>8}  Thresholds")
    print("  " + "-" * 90)
    for p in OA_PARAMETERS.values():
        thr = ", ".join(f"{k}={v}" for k, v in p.thresholds.items())
        print(f"  {p.key:<25} {p.name:<30} {p.unit:<8} {p.nominal:>8.3f}  {thr}")

    print("\n  OE Parameters (operational environment — not controlled):")
    print(f"  {'Key':<25} {'Name':<30} {'Unit':<8} {'Nominal':>8}  Thresholds")
    print("  " + "-" * 90)
    for p in OE_PARAMETERS.values():
        thr = ", ".join(f"{k}={v}" for k, v in p.thresholds.items())
        print(f"  {p.key:<25} {p.name:<30} {p.unit:<8} {p.nominal:>8.3f}  {thr}")
    print()


def _eval_point(args: argparse.Namespace) -> None:
    params = _parse_params(args.eval)
    print(f"\n  Evaluating parameter point: {params}\n")
    results = evaluate_all(params)
    print(f"  {'Constraint':<14} {'Status':<10} {'Primary value':>15}  {'Threshold':>10}  {'Margin':>10}  Note")
    print("  " + "-" * 90)
    all_safe = True
    for r in results:
        status = "SAFE" if r.is_safe else "VIOLATED"
        color  = "" if r.is_safe else "  ← !"
        print(
            f"  {r.constraint_id:<14} {status:<10} {r.primary_value:>15.4f}  "
            f"{r.threshold:>10.4f}  {r.margin:>+10.4f}  {r.note}{color}"
        )
        if not r.is_safe:
            all_safe = False
    print()
    if all_safe:
        print("  Result: ALL CONSTRAINTS SATISFIED\n")
    else:
        print("  Result: ONE OR MORE CONSTRAINTS VIOLATED\n")
        sys.exit(2)


def _run_sweep(args: argparse.Namespace) -> None:
    # Build config
    param_list = args.params.split() if args.params else None
    constraints = tuple(args.constraints.split()) if args.constraints else SWEEP_CONSTRAINTS

    cfg = SweepConfig(
        method               = args.method,
        n                    = args.n,
        params               = param_list,
        grid_steps           = args.grid_steps,
        boundary_margin_frac = args.boundary_margin,
        seed                 = args.seed,
        constraint_ids       = constraints,
        oa_only              = args.oa_only,
    )
    engine = SweepEngine(cfg)

    print(f"\n  Running {cfg.method.upper()} sweep — {cfg.n} samples, seed={cfg.seed} ...")
    if args.hazard:
        result = engine.run_focused(args.hazard.upper())
        print(f"  (focused on hazard {args.hazard.upper()} — extra near-threshold samples added)")
    else:
        result = engine.run()

    report = SweepReport(result)
    print(report.summary())

    # Output directory
    out_dir = Path(args.out) if args.out else None

    if args.json or out_dir:
        dest = (out_dir or Path(".")) / "sweep_results.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        report.write_json(dest)
        print(f"  JSON  → {dest}")

    if args.csv or out_dir:
        dest = (out_dir or Path(".")) / "sweep_results.csv"
        dest.parent.mkdir(parents=True, exist_ok=True)
        report.write_csv(dest)
        print(f"  CSV   → {dest}")

    if args.html or out_dir:
        dest = (out_dir or Path(".")) / "sweep_report.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        report.write_html(dest)
        print(f"  HTML  → {dest}")

    if args.generate_scenarios:
        written = generate_scenarios(
            result,
            max_boundary = args.max_boundary,
            max_haz      = args.max_haz,
        )
        print(f"\n  Generated {len(written)} Scenic file(s):")
        for p in written:
            print(f"    {p}")
    print()

    # Exit non-zero if hazard rate exceeds threshold (useful for CI)
    if args.fail_rate is not None and result.hazard_rate > args.fail_rate:
        print(
            f"  FAIL: hazard rate {result.hazard_rate*100:.1f}% exceeds "
            f"threshold {args.fail_rate*100:.1f}%\n"
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# CLI definition
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog        = "scenic_sweep.py",
        description = "OSR parametric OA/OE sweep and Scenic scenario generator",
        formatter_class = argparse.RawDescriptionHelpFormatter,
        epilog = __doc__,
    )

    # ── Mode flags (mutually exclusive groups) ──────────────────────────
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument(
        "--list-params", action="store_true",
        help="Print all OA/OE parameters and exit",
    )
    mode.add_argument(
        "--eval", metavar="KEY=VAL,...",
        help="Evaluate constraints at a single point (e.g. motor_current_peak=11.5,roll_deg=30.0)",
    )

    # ── Sweep options ───────────────────────────────────────────────────
    ap.add_argument(
        "--method", choices=["grid", "montecarlo", "lhs"], default="lhs",
        help="Sampling method (default: lhs)",
    )
    ap.add_argument(
        "--n", type=int, default=500, metavar="N",
        help="Number of samples (default: 500)",
    )
    ap.add_argument(
        "--grid-steps", type=int, default=10, metavar="S",
        help="Steps per axis for grid sweep (default: 10)",
    )
    ap.add_argument(
        "--params", metavar="KEY ...",
        help="Space-separated list of parameter keys to sweep (default: all)",
    )
    ap.add_argument(
        "--oa-only", action="store_true",
        help="Sweep only OA parameters (rover state), fix OE at nominal",
    )
    ap.add_argument(
        "--hazard", metavar="H-XX",
        help="Focus extra samples near threshold of this hazard (e.g. H-02)",
    )
    ap.add_argument(
        "--constraints", metavar="H-XX ...",
        help="Space-separated list of constraint IDs to evaluate (default: all sweep constraints)",
    )
    ap.add_argument(
        "--boundary-margin", type=float, default=0.10, metavar="F",
        help="Fraction of threshold defining 'boundary' zone (default: 0.10)",
    )
    ap.add_argument(
        "--seed", type=int, default=42, metavar="S",
        help="Random seed (default: 42)",
    )

    # ── Output options ──────────────────────────────────────────────────
    ap.add_argument(
        "--out", metavar="DIR",
        help="Output directory (writes JSON + CSV + HTML automatically)",
    )
    ap.add_argument("--json", action="store_true", help="Write sweep_results.json")
    ap.add_argument("--csv",  action="store_true", help="Write sweep_results.csv")
    ap.add_argument("--html", action="store_true", help="Write sweep_report.html")

    # ── Scenario generation ─────────────────────────────────────────────
    ap.add_argument(
        "--generate-scenarios", action="store_true",
        help="Write .scenic files for boundary and hazardous points",
    )
    ap.add_argument(
        "--max-boundary", type=int, default=20, metavar="N",
        help="Max boundary .scenic files to write (default: 20)",
    )
    ap.add_argument(
        "--max-haz", type=int, default=20, metavar="N",
        help="Max hazardous .scenic files to write (default: 20)",
    )

    # ── CI gate ─────────────────────────────────────────────────────────
    ap.add_argument(
        "--fail-rate", type=float, default=None, metavar="F",
        help="Exit 1 if hazard rate > F (e.g. 0.05 for 5%%). Useful in CI.",
    )

    return ap


def main() -> None:
    ap = build_parser()
    args = ap.parse_args()

    if args.list_params:
        from scenic_module import OA_PARAMETERS, OE_PARAMETERS
        # Inject into args namespace for list helper
        args._oa = OA_PARAMETERS
        args._oe = OE_PARAMETERS
        _list_params(args)
        return

    if args.eval:
        _eval_point(args)
        return

    _run_sweep(args)


if __name__ == "__main__":
    main()
