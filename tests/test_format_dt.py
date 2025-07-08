import datetime
import random
import pytest
from discord.utils import format_dt

# Fix seed so that time tests are reproducible
random.seed(42)

ALL_STYLES = ["t", "T", "d", "D", "f", "F", "R", None]

DATETIME_CASES = [
    (datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc), 0),
    (datetime.datetime(2000, 2, 29, 12, 0, 0, tzinfo=datetime.timezone.utc), 951825600),
    (datetime.datetime(1999, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc), 946684799),
    (datetime.datetime(2023, 1, 2, 3, 4, 5, tzinfo=datetime.timezone.utc), 1672628645),
    (datetime.datetime(2050, 6, 15, 7, 30, 0, tzinfo=datetime.timezone.utc), 2538891000),
]


def random_time():
    return datetime.time(
        random.randint(0, 23),
        random.randint(0, 59),
        random.randint(0, 59),
    )


@pytest.mark.parametrize(("dt", "expected_ts"), DATETIME_CASES)
@pytest.mark.parametrize("style", ALL_STYLES)
def test_format_dt_formats_datetime(dt, expected_ts, style):
    """
    For each (dt, expected_ts) pair and each style,
    format_dt should produce the correct Discord timestamp.
    """
    if style is None:
        expected = f"<t:{expected_ts}>"
    else:
        expected = f"<t:{expected_ts}:{style}>"
    result = format_dt(dt, style=style)
    assert result == expected


@pytest.mark.parametrize("style", ALL_STYLES)
def test_format_dt_formats_time_equivalence(style):
    """
    For a time-only input, format_dt(time, style) should equal
    format_dt(datetime.combine(today, time), style).
    """
    tm = random_time()
    today = datetime.datetime.now().date()
    result_time = format_dt(tm, style=style)
    dt = datetime.datetime.combine(today, tm)
    result_dt = format_dt(dt, style=style)
    assert result_time == result_dt
