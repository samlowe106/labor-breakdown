"""Shared data types for the labor breakdown.

A DataPoint is one monthly observation of a Current Population Survey series
(e.g. the employment level for a given month). A Band is one slice of the
population the breakdown splits into, and a Breakdown is the whole result:
every band's value for every month, plus the totals behind them.

Deliberately just data, no I/O: nothing here knows about FRED, HTTP, or file
formats. That's the caller's job (e.g. a site's own fetch script) -- this
package only answers "given these series, how does the population split up?"
"""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class DataPoint:
    date: date
    value: float


@dataclass(frozen=True)
class Band:
    """One slice of the population.

    `in_labor_force` is BLS's own definition (employed + unemployed), so only
    the first three bands have it. `approximate` marks the bands derived from
    a fixed annual ratio or a held-flat snapshot (see Assumptions) instead of
    a live monthly series, so a chart can flag them as less precise.
    """

    key: str
    short_name: str
    name: str
    in_labor_force: bool
    approximate: bool


# Bottom-to-top stacking order. The first three sum to exactly the official
# civilian labor force (employed + unemployed); everything else is outside it.
BANDS: tuple[Band, ...] = (
    Band("employed", "Employed", "Employed, adequately", True, False),
    Band(
        "underemployed",
        "Underemployed",
        "Underemployed (part-time for economic reasons)",
        True,
        False,
    ),
    Band(
        "unemployed",
        "Unemployed",
        "Unemployed, searched in last 4 weeks",
        True,
        False,
    ),
    Band(
        "discouraged",
        "Discouraged",
        "Discouraged (gave up searching), 12-month avg",
        False,
        False,
    ),
    Band("retired", "Retired", "Retired", False, True),
    Band(
        "other-nilf",
        "Not in labor force, other",
        "Not in labor force, other reasons",
        False,
        True,
    ),
    Band(
        "incarcerated-working",
        "Incarcerated, working",
        "Incarcerated, doing wage labor",
        False,
        True,
    ),
    Band(
        "incarcerated-not-working",
        "Incarcerated, not working",
        "Incarcerated, not working",
        False,
        True,
    ),
)


@dataclass(frozen=True)
class Breakdown:
    """Every band's value for every month in `dates`.

    `bands` maps each Band.key to one value per date, in the same unit as the
    input series (FRED's CPS levels are in thousands of people).
    `total_population` is the civilian noninstitutional population plus the
    incarcerated, i.e. the sum of every band. `labor_force_participation_rate`
    is in percent and uses the official formula, labor force / civilian
    population, so the incarcerated are not in its denominator.
    """

    dates: list[date]
    bands: dict[str, list[float]]
    total_population: list[float]
    labor_force_participation_rate: list[float]
