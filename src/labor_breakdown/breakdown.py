"""The breakdown itself: six monthly CPS series in, eight population bands out.

The series (all monthly, BLS Current Population Survey; FRED IDs in
parentheses):
  employed             Employment Level (CE16OV)
  underemployed        Employed, Part Time for Economic Reasons (LNS12032194)
  unemployed           Unemployment Level, U-3 (UNEMPLOY)
  discouraged          Not in Labor Force, Discouraged Workers (LNU05026645, NSA)
  not_in_labor_force   Not in Labor Force, Total (LNS15000000)
  civilian_population  Civilian Noninstitutional Population (CNP16OV)

The civilian noninstitutional population excludes the incarcerated by
definition, so the incarcerated bands are added on top of it as extra
population rather than carved out of an existing band.
"""

from collections.abc import Sequence
from datetime import date

from .assumptions import DEFAULT_ASSUMPTIONS, Assumptions
from .models import BANDS, Breakdown, DataPoint


def trailing_average(points: Sequence[DataPoint], window: int = 12) -> list[DataPoint]:
    """Trailing `window`-observation average, dated at each window's last
    point. The first `window - 1` points have no full window and are dropped.

    Used on the discouraged-workers series, which is only published not
    seasonally adjusted and is noisy month to month: a 12-month window
    removes the seasonality without a separate seasonal-adjustment model.
    """
    ordered = sorted(points, key=lambda p: p.date)
    return [
        DataPoint(
            ordered[i].date,
            sum(p.value for p in ordered[i - window + 1 : i + 1]) / window,
        )
        for i in range(window - 1, len(ordered))
    ]


def breakdown(
    *,
    employed: Sequence[DataPoint],
    underemployed: Sequence[DataPoint],
    unemployed: Sequence[DataPoint],
    discouraged: Sequence[DataPoint],
    not_in_labor_force: Sequence[DataPoint],
    civilian_population: Sequence[DataPoint],
    assumptions: Assumptions = DEFAULT_ASSUMPTIONS,
    start: date | None = None,
    unit: float = 1000,
    discouraged_window: int = 12,
) -> Breakdown:
    """Split the population into BANDS for every month all six series cover.

    `discouraged` is passed raw; it's smoothed here with a trailing
    `discouraged_window`-month average (pass 1 to skip smoothing), which
    drops that many months minus one from the start of the result. `start`
    drops any earlier months after that. `unit` is how many people one unit
    of the input series represents (FRED's CPS levels are in thousands),
    needed to put the incarcerated headcount in the same unit.

    Raises ValueError if the series share no months at or after `start`.
    """
    smoothed = trailing_average(discouraged, discouraged_window)
    by_date = [
        {p.date: p.value for p in series}
        for series in (
            employed,
            underemployed,
            unemployed,
            smoothed,
            not_in_labor_force,
            civilian_population,
        )
    ]
    emp, under, unemp, disc, nilf, civ = by_date
    dates = sorted(set.intersection(*(set(s) for s in by_date)))
    if start is not None:
        dates = [d for d in dates if d >= start]
    if not dates:
        raise ValueError(
            "the series share no months" + (f" on or after {start}" if start else "")
        )

    incarcerated = assumptions.incarcerated_total / unit
    retired_share = assumptions.retired_share_of_other_nilf
    working_share = assumptions.incarcerated_working_share

    bands: dict[str, list[float]] = {band.key: [] for band in BANDS}
    total_population: list[float] = []
    lfpr: list[float] = []
    for d in dates:
        remainder_nilf = nilf[d] - disc[d]
        bands["employed"].append(emp[d] - under[d])
        bands["underemployed"].append(under[d])
        bands["unemployed"].append(unemp[d])
        bands["discouraged"].append(disc[d])
        bands["retired"].append(remainder_nilf * retired_share)
        bands["other-nilf"].append(remainder_nilf * (1 - retired_share))
        bands["incarcerated-working"].append(incarcerated * working_share)
        bands["incarcerated-not-working"].append(incarcerated * (1 - working_share))
        total_population.append(civ[d] + incarcerated)
        lfpr.append((emp[d] + unemp[d]) / civ[d] * 100)

    return Breakdown(
        dates=dates,
        bands=bands,
        total_population=total_population,
        labor_force_participation_rate=lfpr,
    )
