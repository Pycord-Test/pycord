"""
The MIT License (MIT)

Copyright (c) 2021-present Pycord Development

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

import datetime
import random

import pytest

from discord.datetime import DiscordTime, TimestampStyle

# Fix seed so that time tests are reproducible
random.seed(42)

ALL_STYLES = [
    "t",
    "T",
    "d",
    "D",
    "f",
    "F",
    "R",
    None,
]

DATETIME_CASES = [
    (datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc), 0),
    (datetime.datetime(2000, 2, 29, 12, 0, 0, tzinfo=datetime.timezone.utc), 951825600),
    (datetime.datetime(1999, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc), 946684799),
    (datetime.datetime(2023, 1, 2, 3, 4, 5, tzinfo=datetime.timezone.utc), 1672628645),
    (datetime.datetime(2050, 6, 15, 7, 30, 0, tzinfo=datetime.timezone.utc), 2538891000),
]


def random_time() -> datetime.time:
    return datetime.time(
        random.randint(0, 23),
        random.randint(0, 59),
        random.randint(0, 59),
    )


@pytest.mark.parametrize(("dt", "expected_ts"), DATETIME_CASES)
@pytest.mark.parametrize("style", ALL_STYLES)
def test_format_dt_formats_datetime(
    dt: datetime.datetime,
    expected_ts: int,
    style: TimestampStyle | None,
) -> None:
    if style is None:
        expected = f"<t:{expected_ts}>"
    else:
        expected = f"<t:{expected_ts}:{style}>"
    result = DiscordTime.from_datetime(dt).format(style=style)
    assert result == expected


@pytest.mark.parametrize("style", ALL_STYLES)
def test_format_dt_formats_time_equivalence(
    style: TimestampStyle | None,
) -> None:
    tm = random_time()
    today = datetime.datetime.now().date()
    result_time = DiscordTime.from_datetime(tm).format(style=style)
    dt = datetime.datetime.combine(today, tm)
    result_dt = DiscordTime.from_datetime(dt).format(style=style)
    assert result_time == result_dt
