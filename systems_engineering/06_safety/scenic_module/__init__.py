"""
scenic_module
=============
OSR parametric OA/OE sweep and Scenic scenario generation module.

Public API
----------

**Parameter space** — :mod:`.parameter_space`

.. code-block:: python

    from scenic_module import OA_PARAMETERS, OE_PARAMETERS, ALL_PARAMETERS
    from scenic_module import get_parameters_for_hazard

**Constraint evaluation** — :mod:`.constraint_oracle`

.. code-block:: python

    from scenic_module import evaluate_all, evaluate_constraint, ConstraintResult

**Parametric sweep** — :mod:`.sweep`

.. code-block:: python

    from scenic_module import SweepEngine, SweepConfig, quick_sweep

**Scenario generation** — :mod:`.scenario_generator`

.. code-block:: python

    from scenic_module import generate_scenarios

**Reporting** — :mod:`.report`

.. code-block:: python

    from scenic_module import SweepReport

One-liner pipeline::

    from scenic_module import quick_sweep, SweepReport, generate_scenarios

    result  = quick_sweep(method="lhs", n=500)
    report  = SweepReport(result)
    print(report.summary())
    report.write_html("sweep_report.html")
    written = generate_scenarios(result)
    print(f"{len(written)} Scenic files written")
"""

from .parameter_space import (
    OAParameter,
    OA_PARAMETERS,
    OE_PARAMETERS,
    ALL_PARAMETERS,
    PARAMETER_GROUPS,
    get_parameters_for_hazard,
    get_parameters_for_scenario,
)

from .constraint_oracle import (
    ConstraintResult,
    CONSTRAINT_MAP,
    SWEEP_CONSTRAINTS,
    evaluate_constraint,
    evaluate_all,
    any_violated,
    hazard_level,
)

from .sweep import (
    ScenarioPoint,
    SweepResult,
    SweepConfig,
    SweepEngine,
    quick_sweep,
)

from .scenario_generator import (
    ScenarioGenerator,
    GeneratorConfig,
    generate_scenarios,
)

from .report import SweepReport

__all__ = [
    # parameter_space
    "OAParameter",
    "OA_PARAMETERS",
    "OE_PARAMETERS",
    "ALL_PARAMETERS",
    "PARAMETER_GROUPS",
    "get_parameters_for_hazard",
    "get_parameters_for_scenario",
    # constraint_oracle
    "ConstraintResult",
    "CONSTRAINT_MAP",
    "SWEEP_CONSTRAINTS",
    "evaluate_constraint",
    "evaluate_all",
    "any_violated",
    "hazard_level",
    # sweep
    "ScenarioPoint",
    "SweepResult",
    "SweepConfig",
    "SweepEngine",
    "quick_sweep",
    # scenario_generator
    "ScenarioGenerator",
    "GeneratorConfig",
    "generate_scenarios",
    # report
    "SweepReport",
]

__version__ = "0.1.0"
