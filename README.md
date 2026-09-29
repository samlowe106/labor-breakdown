# labor-breakdown

A rough estimate of how the U.S. population splits into eight bands, computed from plain monthly Current Population Survey series:

- **Employed**, **underemployed** (part-time for economic reasons), and **unemployed**: together exactly the official civilian labor force.
- **Discouraged** workers, smoothed with a 12-month trailing average since the series is only published not seasonally adjusted.
- **Retired** and **other not in labor force**: the live not-in-labor-force total (minus the discouraged), split by one fixed annual ratio from CPS ASEC.
- **Incarcerated, working** and **incarcerated, not working**: a single BJS prison + jail headcount, split by the ACLU's estimated share doing wage labor, held flat across every month.

The last four bands are the approximate part: their inputs are hand-entered in [`assumptions.py`](src/labor_breakdown/assumptions.py), each with its source, and each band is marked `approximate` so a chart can flag it. Pass your own `Assumptions` to override them.

The civilian noninstitutional population excludes incarcerated people by definition, so the incarcerated bands are added on top of it as extra population. The labor force participation rate uses the official formula (labor force / civilian population), so it doesn't count them either.

Everything is a pure function over `DataPoint(date, value)` sequences: fetching the data (e.g. from [FRED](https://fred.stlouisfed.org/), which needs no API key for its CSV export) is up to you. See [samlowe.dev/tools/labor-breakdown](https://samlowe.dev/tools/labor-breakdown/) for a chart built on top of this package.

## Usage

```python
from datetime import date
from labor_breakdown import BANDS, breakdown

# Each a list of DataPoint(date, value), monthly, in thousands of people.
result = breakdown(
    employed=ce16ov,                  # FRED CE16OV
    underemployed=lns12032194,        # FRED LNS12032194
    unemployed=unemploy,              # FRED UNEMPLOY
    discouraged=lnu05026645,          # FRED LNU05026645, raw (smoothed for you)
    not_in_labor_force=lns15000000,   # FRED LNS15000000
    civilian_population=cnp16ov,      # FRED CNP16OV
    start=date(2012, 1, 1),
)

for band in BANDS:
    print(band.name, result.bands[band.key][-1])
print("LFPR", result.labor_force_participation_rate[-1])
```

## Development

Uses [uv](https://docs.astral.sh/uv/), so no separate venv/pip setup is needed.

```bash
uv run --group dev pytest --verbose
```

[pre-commit](https://pre-commit.com/) runs ruff (lint + import order), black, and [ty](https://github.com/astral-sh/ty) (type checking) on every commit:

```bash
uv run pre-commit install   # once, per checkout
uv run pre-commit run --all-files
```

## License

[GNU AGPLv3](LICENSE).
