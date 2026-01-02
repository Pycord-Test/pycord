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

from __future__ import annotations

import datetime
from typing import Literal

from typing_extensions import Self, overload, override

DISCORD_EPOCH = 1420070400000
TimestampStyle = Literal["f", "F", "d", "D", "t", "T", "R"]


class DiscordTime(datetime.datetime):
    """A subclass of :class:`datetime.datetime` that offers additional utility methods

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
        return cls.now(datetime.timezone.utc)

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
        .. code-block:: python

            # Generate realistic snowflake
            snowflake = DateTime.utcnow().generate_snowflake()

            # Generate boundary snowflakes
            lower_bound = DateTime.utcnow().generate_snowflake(mode="boundary", high=False)
            upper_bound = DateTime.utcnow().generate_snowflake(mode="boundary", high=True)

            # For inclusive ranges:
            # Lower:
            DateTime.utcnow().generate_snowflake(mode="boundary", high=False) - 1
            # Upper:
            DateTime.utcnow().generate_snowflake(mode="boundary", high=True) + 1

        """
        discord_millis = int(self.timestamp() * 1000 - DISCORD_EPOCH)

        if mode == "realistic":
            return (discord_millis << 22) | 0x3FFFFF
        elif mode == "boundary":
            return (discord_millis << 22) + (2**22 - 1 if high else 0)
        else:
            raise ValueError(f"Invalid mode '{mode}'. Must be 'realistic' or 'boundary'")

    @classmethod
    def from_datetime(cls, dt: datetime.datetime | datetime.time) -> Self:
        """Converts a datetime or time object to a UTC-aware datetime object.

        Parameters
        ----------
        dt: :class:`datetime.datetime` | :class:`datetime.time`
            A datetime or time object to generate a DiscordTime from.
        """
        if isinstance(dt, datetime.time):
            dt = datetime.datetime.combine(cls.utcnow(), dt)
        return cls(
            day=dt.day,
            month=dt.month,
            year=dt.year,
            hour=dt.hour,
            minute=dt.minute,
            second=dt.second,
            microsecond=dt.microsecond,
            tzinfo=dt.tzinfo,
        )

    @classmethod
    def from_snowflake(cls, id: int) -> Self:
        """Converts a Discord snowflake ID to a UTC-aware datetime object.

        Parameters
        ----------
        id: :class:`int`
            The snowflake ID.

        Returns
        -------
        :class:`discord.DiscordTime`
            An aware datetime in UTC representing the creation time of the snowflake.
        """
        timestamp = ((id >> 22) + DISCORD_EPOCH) / 1000
        return DiscordTime.fromtimestamp(timestamp, tz=datetime.timezone.utc)

    def format(self, /, style: TimestampStyle | None = None) -> str:
        """A method to format this :class:`discord.DiscordTime` for presentation within Discord.

        This allows for a locale-independent way of presenting data using Discord specific Markdown.

        +-------------+----------------------------+-----------------+
        |    Style    |       Example Output       |   Description   |
        +=============+============================+=================+
        | t           | 22:57                      | Short Time      |
        +-------------+----------------------------+-----------------+
        | T           | 22:57:58                   | Long Time       |
        +-------------+----------------------------+-----------------+
        | d           | 17/05/2016                 | Short Date      |
        +-------------+----------------------------+-----------------+
        | D           | 17 May 2016                | Long Date       |
        +-------------+----------------------------+-----------------+
        | f (default) | 17 May 2016 22:57          | Short Date Time |
        +-------------+----------------------------+-----------------+
        | F           | Tuesday, 17 May 2016 22:57 | Long Date Time  |
        +-------------+----------------------------+-----------------+
        | R           | 5 years ago                | Relative Time   |
        +-------------+----------------------------+-----------------+

        Note that the exact output depends on the user's locale setting in the client. The example output
        presented is using the ``en-GB`` locale.

        .. versionadded:: 2.0

        Parameters
        ----------
        style: :class:`str`
            The style to format the datetime with.

        Returns
        -------
        :class:`str`
            The formatted string.
        """
        if style is None:
            return f"<t:{int(self.timestamp())}>"
        return f"<t:{int(self.timestamp())}:{style}>"

    @overload
    @classmethod
    def parse_time(cls, timestamp: None) -> None: ...

    @overload
    @classmethod
    def parse_time(cls, timestamp: str) -> DiscordTime: ...

    @classmethod
    def parse_time(cls, timestamp: str | None) -> DiscordTime | None:
        """A helper function to convert an ISO 8601 timestamp to a discord datetime object.

        Parameters
        ----------
        timestamp: Optional[:class:`str`]
            The timestamp to convert.

        Returns
        -------
        Optional[:class:`discord.DiscordTime`]
            The converted datetime object.
        """
        if timestamp:
            return DiscordTime.fromisoformat(timestamp)
        return None
