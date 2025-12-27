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

import pytest

from discord.utils import (
    DISCORD_EPOCH,
    generate_snowflake,
    snowflake_time,
)

UTC = datetime.timezone.utc

DATETIME_CASES = [
    (datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=UTC), int(0 * 1000 - DISCORD_EPOCH)),
    (datetime.datetime(2000, 2, 29, 12, 0, 0, tzinfo=UTC), int(951825600 * 1000 - DISCORD_EPOCH)),
    (datetime.datetime(1999, 12, 31, 23, 59, 59, tzinfo=UTC), int(946684799 * 1000 - DISCORD_EPOCH)),
    (datetime.datetime(2023, 1, 2, 3, 4, 5, tzinfo=UTC), int(1672628645 * 1000 - DISCORD_EPOCH)),
    (datetime.datetime(2050, 6, 15, 7, 30, 0, tzinfo=UTC), int(2538891000 * 1000 - DISCORD_EPOCH)),
]


@pytest.mark.parametrize(("dt", "expected_ms"), DATETIME_CASES)
def test_generate_snowflake_realistic(dt: datetime.datetime, expected_ms: int) -> None:
    sf = generate_snowflake(dt, mode="realistic")
    assert (sf >> 22) == expected_ms
    assert (sf & ((1 << 22) - 1)) == 0x3FFFFF


@pytest.mark.parametrize(("dt", "expected_ms"), DATETIME_CASES)
def test_generate_snowflake_boundary_low(dt: datetime.datetime, expected_ms: int) -> None:
    sf = generate_snowflake(dt, mode="boundary", high=False)
    assert (sf >> 22) == expected_ms
    assert (sf & ((1 << 22) - 1)) == 0


@pytest.mark.parametrize(("dt", "expected_ms"), DATETIME_CASES)
def test_generate_snowflake_boundary_high(dt: datetime.datetime, expected_ms: int) -> None:
    sf = generate_snowflake(dt, mode="boundary", high=True)
    assert (sf >> 22) == expected_ms
    assert (sf & ((1 << 22) - 1)) == (2**22 - 1)


@pytest.mark.parametrize(("dt", "_expected_ms"), DATETIME_CASES)
def test_snowflake_time_roundtrip_boundary(dt: datetime.datetime, _expected_ms: int) -> None:
    sf_low = generate_snowflake(dt, mode="boundary", high=False)
    sf_high = generate_snowflake(dt, mode="boundary", high=True)
    assert snowflake_time(sf_low) == dt
    assert snowflake_time(sf_high) == dt


@pytest.mark.parametrize(("dt", "_expected_ms"), DATETIME_CASES)
def test_snowflake_time_roundtrip_realistic(dt: datetime.datetime, _expected_ms: int) -> None:
    sf = generate_snowflake(dt, mode="realistic")
    assert snowflake_time(sf) == dt


def test_generate_snowflake_invalid_mode() -> None:
    with pytest.raises(ValueError, match=r"Invalid mode 'nope'. Must be 'realistic' or 'boundary'"):
        generate_snowflake(datetime.datetime.now(tz=UTC), mode="nope")  # ty: ignore[invalid-argument-type]
