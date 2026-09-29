"""The hand-entered figures behind the breakdown's approximate bands.

Only employed, underemployed, unemployed, and discouraged have a live monthly
national series. "Retired" and "other not in labor force" split the live
not-in-labor-force total by one fixed annual ratio, and the two incarcerated
bands are a single snapshot held flat across every month. That's what makes
the breakdown a rough estimate, and these are the numbers to update (or
override, by passing your own Assumptions) when newer sources come out.
"""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Source:
    label: str
    url: str


@dataclass(frozen=True)
class Assumptions:
    # Share of the not-in-labor-force total (minus the discouraged) who are
    # retired, applied uniformly to every month.
    retired_share_of_other_nilf: float
    retired_share_source: Source
    # Combined prison + jail headcount, in people (not thousands).
    incarcerated_total: float
    incarcerated_as_of: date
    incarcerated_source: Source
    # Share of the incarcerated doing wage labor.
    incarcerated_working_share: float
    incarcerated_working_source: Source


DEFAULT_ASSUMPTIONS = Assumptions(
    # Of 93.6M people who neither worked nor looked for work at any point in
    # 2023 (CPS ASEC), 48.6M cited retirement.
    retired_share_of_other_nilf=48.6 / 93.6,
    retired_share_source=Source(
        "BLS Monthly Labor Review (2024), CPS ASEC 2023: 48.6M of 93.6M "
        "non-working-age-eligible adults cited retirement",
        "https://www.bls.gov/opub/mlr/2024/article/why-did-labor-force-nonparticipation-increase-from-1999-to-2022.htm",
    ),
    # State/federal prison + local jail, reconciled to one reference date.
    incarcerated_total=1_852_900,
    incarcerated_as_of=date(2023, 12, 31),
    incarcerated_source=Source(
        "BJS, Correctional Populations in the United States, 2023",
        "https://bjs.ojp.gov/library/publications/correctional-populations-united-states-2023-statistical-tables",
    ),
    # ~65% of state and federal prisoners report working. Measured against the
    # prison population specifically, applied to the combined prison + jail
    # total for simplicity.
    incarcerated_working_share=0.65,
    incarcerated_working_source=Source(
        'ACLU/University of Chicago Global Human Rights Clinic, "Captive Labor" (2022)',
        "https://www.aclu.org/publications/captive-labor-exploitation-incarcerated-workers",
    ),
)
