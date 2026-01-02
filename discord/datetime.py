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
from typing import override, Literal

from typing_extensions import Self

__all__ = (
    "DiscordTime",
)

DISCORD_EPOCH = 1420070400000


class DiscordTime(datetime.datetime):
    """A subclass of `datetime.datetime` that offers additional utility methods

    .. versionadded:: 3.0
    """

    @override
    @classmethod
    def utcnow(cls) -> Self:
        """A helper function to return an aware UTC datetime representing the current time.

        This should be preferred to :meth:`datetime.datetime.utcnow` since it is an aware
        datetime, compared to the naive datetime in the standard library.

        Returns
        -------
        :class:`discord.DiscordTime`
            The current aware datetime in UTC.
        """
        return cls.now(datetime.UTC)

    def generate_snowflake(
            self,
            *,
            mode: Literal["boundary", "realistic"] = "boundary",
            high: bool = False,
    ) -> int:
        """Returns a numeric snowflake pretending to be created at the given date.

        This function can generate both realistic snowflakes (for general use) and
        boundary snowflakes (for range queries).

        Parameters
        ----------
        mode: :class:`str`
            The type of snowflake to generate:
            - "realistic": Creates a snowflake with random-like lower bits
            - "boundary": Creates a snowflake for range queries (default)
        high: :class:`bool`
            Only used when mode="boundary". Whether to set the lower 22 bits
            to high (True) or low (False). Default is False.

        Returns
        -------
        :class:`int`
            The snowflake representing the time given.

        Examples
        --------
        # Generate realistic snowflake
        snowflake = DateTime.utcnow().generate_snowflake()

        # Generate boundary snowflakes
        lower_bound = DateTime.utcnow().generate_snowflake(mode="boundary", high=False)
        upper_bound = DateTime.utcnow().generate_snowflake(mode="boundary", high=True)

        # For inclusive ranges:
        # Lower: DateTime.utcnow().generate_snowflake(mode="boundary", high=False) - 1
        # Upper: DateTime.utcnow().generate_snowflake(mode="boundary", high=True) + 1
        """
        discord_millis = int(self.timestamp() * 1000 - DISCORD_EPOCH)

        if mode == "realistic":
            return (discord_millis << 22) | 0x3FFFFF
        elif mode == "boundary":
            return (discord_millis << 22) + (2 ** 22 - 1 if high else 0)
        else:
            raise ValueError(f"Invalid mode '{mode}'. Must be 'realistic' or 'boundary'")

    @classmethod
    def from_datetime(cls, dt: datetime.datetime) -> Self:
        cls(day=dt.day, month=dt.month, year=dt.year, hour=dt.hour, minute=dt.minute, second=dt.second,
            microsecond=dt.microsecond, tzinfo=dt.tzinfo)
