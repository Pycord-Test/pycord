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

from copy import copy
from datetime import datetime
from typing import Any, TypeVar, cast

from typing_extensions import override, Self

from discord.abc import GuildChannel, PrivateChannel
from discord.app.event_emitter import Event
from discord.app.state import ConnectionState
from discord.channel import GroupChannel, _channel_factory
from discord.enums import ChannelType, try_enum
from discord.threads import Thread
from discord.utils.private import get_as_snowflake, parse_time

T = TypeVar("T")


class ChannelCreate(Event, GuildChannel):
    __event_name__: str = "CHANNEL_CREATE"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: dict[str, Any], state: ConnectionState) -> Self | None:
        factory, _ = _channel_factory(data["type"])
        if factory is None:
            return

        guild_id = get_as_snowflake(data, "guild_id")
        guild = await state._get_guild(guild_id)
        if guild is None:
            return
        # the factory can't be a DMChannel or GroupChannel here
        channel = factory(guild=guild, state=state, data=data)  # type: ignore
        guild._add_channel(channel)  # type: ignore
        self = cls()
        self._populate_from_slots(channel)
        return self


class PrivateChannelUpdate(Event, PrivateChannel):
    __event_name__: str = "PRIVATE_CHANNEL_UPDATE"

    old: PrivateChannel | None

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: tuple[PrivateChannel | None, PrivateChannel], state: ConnectionState) -> Self | None:
        self = cls()
        self.old = data[0]
        self._populate_from_slots(data[1])
        return self


class GuildChannelUpdate(Event, PrivateChannel):
    __event_name__: str = "GUILD_CHANNEL_UPDATE"

    old: GuildChannel | None

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: tuple[GuildChannel | None, GuildChannel], state: ConnectionState) -> Self | None:
        self = cls()
        self.old = data[0]
        self._populate_from_slots(data[1])
        return self


class ChannelUpdate(Event, GuildChannel):
    __event_name__: str = "CHANNEL_UPDATE"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: dict[str, Any], state: ConnectionState) -> Self | None:
        channel_type = try_enum(ChannelType, data.get("type"))
        channel_id = int(data["id"])
        if channel_type is ChannelType.group:
            channel = await state._get_private_channel(channel_id)
            old_channel = copy(channel)
            # the channel is a GroupChannel
            await cast(GroupChannel, channel)._update_group(data)
            await state.emitter.emit("PRIVATE_CHANNEL_UPDATE", (old_channel, channel))
            return

        guild_id = get_as_snowflake(data, "guild_id")
        guild = await state._get_guild(guild_id)
        if guild is not None:
            channel = guild.get_channel(channel_id)
            if channel is not None:
                old_channel = copy.copy(channel)
                await channel._update(data)  # type: ignore
                await state.emitter.emit("GUILD_CHANNEL_UPDATE", (old_channel, channel))


class ChannelDelete(Event, GuildChannel):
    __event_name__: str = "CHANNEL_DELETE"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: dict[str, Any], state: ConnectionState) -> Self | None:
        guild = await state._get_guild(get_as_snowflake(data, "guild_id"))
        channel_id = int(data["id"])
        if guild is not None:
            channel = guild.get_channel(channel_id)
            if channel is not None:
                guild._remove_channel(channel)
                self = cls()
                self._populate_from_slots(channel)
                return self


class ChannelPinsUpdate(Event):
    __event_name__: str = "CHANNEL_PINS_UPDATE"
    channel: PrivateChannel | GuildChannel | Thread
    last_pin: datetime | None

    @classmethod
    @override
    async def __load__(cls, data: dict[str, Any], state: ConnectionState) -> Self | None:
        channel_id = int(data["channel_id"])
        try:
            guild = await state._get_guild(int(data["guild_id"]))
        except KeyError:
            guild = None
            channel = await state._get_private_channel(channel_id)
        else:
            channel = guild and guild._resolve_channel(channel_id)

        if channel is None:
            return

        self = cls()
        self.channel = channel
        self.last_pin = parse_time(data["last_pin_timestamp"]) if data["last_pin_timestamp"] else None
        return self
