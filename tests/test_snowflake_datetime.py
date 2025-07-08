# tests/test_snowflake_utils.py

import datetime
import pytest

from discord.utils import generate_snowflake, snowflake_time, DISCORD_EPOCH

UTC = datetime.timezone.utc

DATETIME_CASES = [
    (datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=UTC), int(0 * 1000 - DISCORD_EPOCH)),
    (datetime.datetime(2000, 2, 29, 12, 0, 0, tzinfo=UTC), int(951825600 * 1000 - DISCORD_EPOCH)),
    (datetime.datetime(1999, 12, 31, 23, 59, 59, tzinfo=UTC), int(946684799 * 1000 - DISCORD_EPOCH)),
    (datetime.datetime(2023, 1, 2, 3, 4, 5, tzinfo=UTC), int(1672628645 * 1000 - DISCORD_EPOCH)),
    (datetime.datetime(2050, 6, 15, 7, 30, 0, tzinfo=UTC), int(2538891000 * 1000 - DISCORD_EPOCH)),
]


@pytest.mark.parametrize(("dt", "expected_ms"), DATETIME_CASES)
def test_generate_snowflake_realistic(dt, expected_ms):
    """Realistic mode should set lower 22 bits to 0x3FFFFF."""
    sf = generate_snowflake(dt, mode="realistic")
    # top bits are the timestamp
    assert (sf >> 22) == expected_ms
    # lower 22 bits are all ones in realistic mode
    assert (sf & ((1 << 22) - 1)) == 0x3FFFFF


@pytest.mark.parametrize(("dt", "expected_ms"), DATETIME_CASES)
def test_generate_snowflake_boundary_low(dt, expected_ms):
    """Boundary mode low should zero out lower 22 bits."""
    sf = generate_snowflake(dt, mode="boundary", high=False)
    assert (sf >> 22) == expected_ms
    assert (sf & ((1 << 22) - 1)) == 0


@pytest.mark.parametrize(("dt", "expected_ms"), DATETIME_CASES)
def test_generate_snowflake_boundary_high(dt, expected_ms):
    """Boundary mode high should set lower 22 bits to max."""
    sf = generate_snowflake(dt, mode="boundary", high=True)
    assert (sf >> 22) == expected_ms
    assert (sf & ((1 << 22) - 1)) == (2**22 - 1)


@pytest.mark.parametrize(("dt", "expected_ms"), DATETIME_CASES)
def test_snowflake_time_roundtrip_boundary(dt, expected_ms):
    """Converting boundary snowflake back to datetime yields the original dt."""
    sf_low = generate_snowflake(dt, mode="boundary", high=False)
    sf_high = generate_snowflake(dt, mode="boundary", high=True)
    # snowflake_time ignores low bits, so both should map to dt
    assert snowflake_time(sf_low) == dt
    assert snowflake_time(sf_high) == dt


@pytest.mark.parametrize(("dt", "expected_ms"), DATETIME_CASES)
def test_snowflake_time_roundtrip_realistic(dt, expected_ms):
    """Converting realistic snowflake back to datetime yields the original dt."""
    sf = generate_snowflake(dt, mode="realistic")
    assert snowflake_time(sf) == dt


def test_generate_snowflake_invalid_mode():
    """Passing an invalid mode should raise ValueError."""
    with pytest.raises(ValueError, match="Invalid mode 'nope'. Must be 'realistic' or 'boundary'"):
        generate_snowflake(datetime.datetime.now(tz=UTC), mode="nope")
