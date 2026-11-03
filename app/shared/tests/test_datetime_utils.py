from datetime import date, datetime, timezone

from app.shared.datetime_utils import cairo_day_bounds, cairo_today


def test_cairo_day_bounds_start_is_previous_day_2100_utc_in_summer():
    start, end = cairo_day_bounds(date(2026, 10, 14))
    assert start == datetime(2026, 10, 13, 21, 0, tzinfo=timezone.utc)
    assert end == datetime(2026, 10, 14, 21, 0, tzinfo=timezone.utc)


def test_cairo_today_returns_a_date():
    value = cairo_today()
    assert isinstance(value, date) and not isinstance(value, datetime)
