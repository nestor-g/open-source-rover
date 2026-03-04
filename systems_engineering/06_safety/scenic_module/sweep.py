"""
scenic_module.sweep
====================
Parametric sweep engine for the OSR OA/OE parameter space.

Supports three sampling strategies:

``grid``
    Full factorial grid over a subset of parameters (exponential, use with ≤4 params).

``montecarlo``
    Uniform random sampling across the physical range of each parameter.

``lhs``
    Latin Hypercube Sampling — stratified random sampling that guarantees
    better coverage of the parameter space than pure Monte Carlo.

Usage::

    from scenic_module.sweep import SweepEngine, SweepConfig

    cfg = SweepConfig(
        method  = "lhs",
        n       = 500,
        params  = ["motor_current_peak", "battery_voltage", "roll_deg"],
        seed    = 42,
    )
    engine = SweepEngine(cfg)
    result = engine.run()

    print(f"Hazardous points: {len(result.hazardous_points)}")
    print(f"Boundary points:  {len(result.boundary_points)}")
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Optional

from .constraint_oracle import (
    ConstraintResult,
    evaluate_all,
    any_violated,
    hazard_level,
    SWEEP_CONSTRAINTS,
)
from .parameter_space import ALL_PARAMETERS, OAParameter


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class ScenarioPoint:
    """A single sample point in the OA/OE parameter space."""

    # Parameter values at this point (key → value)
    params: dict[str, float]

    # Constraint evaluation results
    constraint_results: list[ConstraintResult]

    # Derived hazard score [0, 1]
    hazard_level: float

    # True if any constraint is violated
    is_hazardous: bool

    # True if this point is near (within `boundary_margin_frac`) a safety threshold
    is_boundary: bool

    # Which constraint IDs are violated
    violated_constraints: list[str]

    # Index in the sweep for reproducibility
    index: int = 0


@dataclass
class SweepResult:
    """Aggregated outcome of a full parametric sweep."""

    config:           "SweepConfig"
    points:           list[ScenarioPoint]

    # Derived subsets (populated after sweep completes)
    hazardous_points: list[ScenarioPoint] = field(default_factory=list)
    boundary_points:  list[ScenarioPoint] = field(default_factory=list)
    safe_points:      list[ScenarioPoint] = field(default_factory=list)

    # Per-constraint violation counts
    violation_counts: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.points:
            self._classify()

    def _classify(self) -> None:
        self.hazardous_points = [p for p in self.points if p.is_hazardous]
        self.boundary_points  = [p for p in self.points if p.is_boundary and not p.is_hazardous]
        self.safe_points      = [p for p in self.points if not p.is_hazardous and not p.is_boundary]

        self.violation_counts = {}
        for p in self.hazardous_points:
            for cid in p.violated_constraints:
                self.violation_counts[cid] = self.violation_counts.get(cid, 0) + 1

    @property
    def n_total(self) -> int:
        return len(self.points)

    @property
    def n_hazardous(self) -> int:
        return len(self.hazardous_points)

    @property
    def n_boundary(self) -> int:
        return len(self.boundary_points)

    @property
    def hazard_rate(self) -> float:
        """Fraction of sampled points that violate at least one constraint."""
        if not self.points:
            return 0.0
        return self.n_hazardous / self.n_total

    def top_hazardous(self, n: int = 10) -> list[ScenarioPoint]:
        """Return the n points with the highest hazard_level scores."""
        return sorted(self.hazardous_points, key=lambda p: p.hazard_level, reverse=True)[:n]

    def worst_per_constraint(self) -> dict[str, ScenarioPoint]:
        """Return the worst-margin point for each violated constraint."""
        worst: dict[str, ScenarioPoint] = {}
        for pt in self.hazardous_points:
            for r in pt.constraint_results:
                if not r.is_safe:
                    if r.constraint_id not in worst or r.margin < worst[r.constraint_id].constraint_results[0].margin:
                        worst[r.constraint_id] = pt
        return worst


# ---------------------------------------------------------------------------
# Sweep configuration
# ---------------------------------------------------------------------------

@dataclass
class SweepConfig:
    """Configuration for a single sweep run."""

    # Sampling method
    method: str = "lhs"           # "grid" | "montecarlo" | "lhs"

    # Number of samples (ignored for "grid" — see grid_steps instead)
    n: int = 500

    # Parameter keys to sweep (defaults to all in ALL_PARAMETERS)
    params: Optional[list[str]] = None

    # For grid method: number of steps per parameter axis
    grid_steps: int = 10

    # Fraction of threshold distance that counts as "boundary"
    boundary_margin_frac: float = 0.10   # 10% of threshold value

    # Random seed for reproducibility
    seed: Optional[int] = 42

    # Constraint IDs to evaluate at each point
    constraint_ids: tuple[str, ...] = SWEEP_CONSTRAINTS

    # If True, fix OE parameters at their nominal values (sweep OA only)
    oa_only: bool = False

    def resolved_params(self) -> list[OAParameter]:
        """Return the list of OAParameter objects to sweep."""
        from .parameter_space import OA_PARAMETERS, OE_PARAMETERS
        if self.params:
            return [ALL_PARAMETERS[k] for k in self.params if k in ALL_PARAMETERS]
        if self.oa_only:
            return list(OA_PARAMETERS.values())
        return list(ALL_PARAMETERS.values())


# ---------------------------------------------------------------------------
# Sampling strategies
# ---------------------------------------------------------------------------

def _sample_grid(params: list[OAParameter], steps: int) -> list[dict[str, float]]:
    """Full factorial grid.  WARNING: scales as steps^len(params)."""
    axes: list[list[float]] = []
    for p in params:
        lo, hi = p.phys_min, p.phys_max
        step_size = (hi - lo) / max(steps - 1, 1)
        axes.append([lo + i * step_size for i in range(steps)])

    def _product(axes: list[list[float]]) -> list[list[float]]:
        result: list[list[float]] = [[]]
        for axis in axes:
            result = [prev + [v] for prev in result for v in axis]
        return result

    combos = _product(axes)
    return [{p.key: combo[i] for i, p in enumerate(params)} for combo in combos]


def _sample_montecarlo(
    params: list[OAParameter], n: int, rng: random.Random
) -> list[dict[str, float]]:
    """Uniform random sampling across physical range."""
    samples = []
    for _ in range(n):
        pt = {p.key: rng.uniform(p.phys_min, p.phys_max) for p in params}
        samples.append(pt)
    return samples


def _sample_lhs(
    params: list[OAParameter], n: int, rng: random.Random
) -> list[dict[str, float]]:
    """
    Latin Hypercube Sampling.

    Each parameter axis is divided into n equal-width strata; one sample
    is drawn uniformly from each stratum; strata are then independently
    shuffled per parameter.  This guarantees that no two samples occupy
    the same stratum on any axis.
    """
    k = len(params)
    # Build stratum assignments: k × n matrix
    strata = [list(range(n)) for _ in range(k)]
    for col in strata:
        rng.shuffle(col)

    samples: list[dict[str, float]] = []
    for i in range(n):
        pt: dict[str, float] = {}
        for j, p in enumerate(params):
            lo, hi = p.phys_min, p.phys_max
            span   = hi - lo
            stratum_lo = lo + strata[j][i] / n * span
            stratum_hi = stratum_lo + span / n
            pt[p.key] = rng.uniform(stratum_lo, stratum_hi)
        samples.append(pt)
    return samples


# ---------------------------------------------------------------------------
# Boundary detection
# ---------------------------------------------------------------------------

def _is_boundary(
    constraint_results: list[ConstraintResult],
    margin_frac: float,
) -> bool:
    """Return True if any safe constraint is within `margin_frac` of its threshold."""
    for r in constraint_results:
        if r.is_safe and r.threshold != 0.0:
            headroom_frac = abs(r.margin) / abs(r.threshold)
            if headroom_frac <= margin_frac:
                return True
    return False


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

class SweepEngine:
    """Runs a parametric sweep and collects :class:`ScenarioPoint` results."""

    def __init__(self, config: SweepConfig) -> None:
        self.cfg = config
        self._rng = random.Random(config.seed)

    # ------------------------------------------------------------------
    def run(self) -> SweepResult:
        """Execute the configured sweep and return a :class:`SweepResult`."""
        param_list = self.cfg.resolved_params()
        samples    = self._generate_samples(param_list)
        points     = [self._evaluate(i, s) for i, s in enumerate(samples)]
        return SweepResult(config=self.cfg, points=points)

    # ------------------------------------------------------------------
    def run_focused(
        self,
        hazard_id: str,
        n_extra: int = 200,
    ) -> SweepResult:
        """Focused sweep: normal run + extra samples near threshold.

        Adds *n_extra* Monte Carlo samples whose primary parameter values
        are drawn from a narrow band (±20 % of threshold) around each
        threshold defined in parameters that reference *hazard_id*.
        """
        base_result  = self.run()

        # Find relevant parameters
        from .parameter_space import ALL_PARAMETERS
        relevant = [p for p in ALL_PARAMETERS.values() if hazard_id in p.hazard_refs]
        if not relevant:
            return base_result

        extra_samples: list[dict[str, float]] = []
        param_list = self.cfg.resolved_params()

        for _ in range(n_extra):
            # Start from nominal values
            pt = {p.key: p.nominal for p in param_list}
            # Perturb the primary parameter(s) for this hazard near threshold
            for rp in relevant:
                for thresh_val in rp.thresholds.values():
                    width = abs(thresh_val) * 0.20 if thresh_val != 0.0 else 0.5
                    lo = max(rp.phys_min, thresh_val - width)
                    hi = min(rp.phys_max, thresh_val + width)
                    pt[rp.key] = self._rng.uniform(lo, hi)
            extra_samples.append(pt)

        n_base   = len(base_result.points)
        extra_pts = [self._evaluate(n_base + i, s) for i, s in enumerate(extra_samples)]

        all_pts = base_result.points + extra_pts
        return SweepResult(config=self.cfg, points=all_pts)

    # ------------------------------------------------------------------
    def _generate_samples(self, param_list: list[OAParameter]) -> list[dict[str, float]]:
        method = self.cfg.method.lower()
        if method == "grid":
            return _sample_grid(param_list, self.cfg.grid_steps)
        elif method == "montecarlo":
            return _sample_montecarlo(param_list, self.cfg.n, self._rng)
        elif method == "lhs":
            return _sample_lhs(param_list, self.cfg.n, self._rng)
        else:
            raise ValueError(
                f"Unknown sweep method '{method}'. Choose: grid, montecarlo, lhs"
            )

    def _evaluate(self, index: int, params: dict[str, float]) -> ScenarioPoint:
        results   = evaluate_all(params, self.cfg.constraint_ids)
        is_haz    = any_violated(results)
        haz_level = hazard_level(results)
        boundary  = _is_boundary(results, self.cfg.boundary_margin_frac)
        violated  = [r.constraint_id for r in results if not r.is_safe]
        return ScenarioPoint(
            params               = params,
            constraint_results   = results,
            hazard_level         = haz_level,
            is_hazardous         = is_haz,
            is_boundary          = boundary,
            violated_constraints = violated,
            index                = index,
        )


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def quick_sweep(
    method:    str = "lhs",
    n:         int = 300,
    hazard_id: Optional[str] = None,
    seed:      int = 42,
) -> SweepResult:
    """One-liner sweep over the full OA/OE parameter space.

    Parameters
    ----------
    method:
        ``"lhs"``, ``"montecarlo"``, or ``"grid"``.
    n:
        Number of samples (for grid: steps per axis).
    hazard_id:
        If supplied, run :meth:`SweepEngine.run_focused` for the given hazard.
    seed:
        Random seed for reproducibility.
    """
    cfg    = SweepConfig(method=method, n=n, seed=seed)
    engine = SweepEngine(cfg)
    if hazard_id:
        return engine.run_focused(hazard_id)
    return engine.run()
