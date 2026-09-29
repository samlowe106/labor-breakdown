"""Point-factory helpers shared across test_*.py. Plain functions, not pytest
fixtures: each test calls these directly to build its own specific series.
"""

from datetime import date

from labor_breakdown import DataPoint


def monthly(*values: float, start: date = date(2020, 1, 1)) -> list[DataPoint]:
    # one point per month, starting at `start`, in the order given
    first = start.year * 12 + start.month - 1
    return [
        DataPoint(date((first + i) // 12, (first + i) % 12 + 1, 1), v)
        for i, v in enumerate(values)
    ]


def constant(value: float, months: int) -> list[DataPoint]:
    return monthly(*([value] * months))
