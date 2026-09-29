from dataclasses import replace
from datetime import date

import pytest

from labor_breakdown import BANDS, DEFAULT_ASSUMPTIONS, breakdown, trailing_average

from .conftest import constant, monthly

MONTHS = 14


def series(**overrides):
    # Round, CPS-shaped levels (thousands of people), constant every month
    # unless a test overrides one.
    base = {
        "employed": constant(160_000, MONTHS),
        "underemployed": constant(4_000, MONTHS),
        "unemployed": constant(7_000, MONTHS),
        "discouraged": constant(400, MONTHS),
        "not_in_labor_force": constant(100_000, MONTHS),
        "civilian_population": constant(267_000, MONTHS),
    }
    return base | overrides


class TestTrailingAverage:
    def test_averages_each_full_window(self):
        result = trailing_average(monthly(1, 2, 3, 4, 5), window=3)
        assert [p.value for p in result] == [2, 3, 4]

    def test_dated_at_window_end(self):
        points = monthly(1, 2, 3, 4, 5)
        result = trailing_average(points, window=3)
        assert [p.date for p in result] == [p.date for p in points[2:]]

    def test_unordered_input_is_sorted_by_date(self):
        points = monthly(1, 2, 3, 4, 5)
        assert trailing_average(list(reversed(points)), window=3) == trailing_average(
            points, window=3
        )

    def test_window_of_one_is_identity(self):
        points = monthly(1, 5, 2)
        assert trailing_average(points, window=1) == points


class TestBreakdown:
    def test_bands_sum_to_total_population(self):
        result = breakdown(**series())
        for i in range(len(result.dates)):
            total = sum(result.bands[band.key][i] for band in BANDS)
            assert total == pytest.approx(result.total_population[i])

    def test_labor_force_bands_are_exactly_employed_plus_unemployed(self):
        result = breakdown(**series())
        in_lf = [band.key for band in BANDS if band.in_labor_force]
        assert in_lf == ["employed", "underemployed", "unemployed"]
        assert sum(result.bands[k][-1] for k in in_lf) == pytest.approx(160_000 + 7_000)

    def test_underemployed_is_carved_out_of_employed(self):
        result = breakdown(**series())
        assert result.bands["employed"][-1] == 156_000
        assert result.bands["underemployed"][-1] == 4_000

    def test_participation_rate_excludes_incarcerated_from_denominator(self):
        result = breakdown(**series())
        assert result.labor_force_participation_rate[-1] == pytest.approx(
            167_000 / 267_000 * 100
        )

    def test_incarcerated_rescaled_to_input_unit_and_held_flat(self):
        result = breakdown(**series())
        incarcerated = DEFAULT_ASSUMPTIONS.incarcerated_total / 1000
        share = DEFAULT_ASSUMPTIONS.incarcerated_working_share
        assert result.bands["incarcerated-working"] == pytest.approx(
            [incarcerated * share] * len(result.dates)
        )
        assert result.total_population[-1] == pytest.approx(267_000 + incarcerated)

    def test_retired_split_excludes_discouraged(self):
        assumptions = replace(DEFAULT_ASSUMPTIONS, retired_share_of_other_nilf=0.5)
        result = breakdown(**series(), assumptions=assumptions)
        assert result.bands["retired"][-1] == pytest.approx((100_000 - 400) / 2)
        assert result.bands["other-nilf"][-1] == pytest.approx((100_000 - 400) / 2)

    def test_discouraged_smoothing_drops_first_months(self):
        result = breakdown(**series())
        assert len(result.dates) == MONTHS - 11
        assert result.dates[0] == date(2020, 12, 1)

    def test_discouraged_window_of_one_keeps_every_month(self):
        result = breakdown(**series(), discouraged_window=1)
        assert len(result.dates) == MONTHS

    def test_month_missing_from_any_series_is_skipped(self):
        gappy = [p for p in constant(7_000, MONTHS) if p.date != date(2021, 1, 1)]
        result = breakdown(**series(unemployed=gappy))
        assert date(2021, 1, 1) not in result.dates
        assert len(result.dates) == MONTHS - 11 - 1

    def test_start_drops_earlier_months(self):
        result = breakdown(**series(), start=date(2021, 2, 1))
        assert result.dates == [date(2021, 2, 1)]

    def test_no_shared_months_raises(self):
        with pytest.raises(ValueError, match="share no months"):
            breakdown(**series(), start=date(2030, 1, 1))
