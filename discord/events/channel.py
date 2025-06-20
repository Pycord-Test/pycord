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

from datetime import datetime
from copy import copy
from typing import Any, Self, TypeVar, cast
from discord import utils
from discord.abc import GuildChannel, PrivateChannel
from discord.app.event_emitter import Event
from discord.app.state import ConnectionState
from discord.channel import GroupChannel, _channel_factory
from discord.enums import ChannelType, try_enum
from discord.threads import Thread

T = TypeVar('T')

class ChannelCreate(Event, GuildChannel):
    __event_name__ = "CHANNEL_CREATE"

    def __init__(self) -> None:
        ...

    @classmethod
    async def __load__(cls, data: dict[str, Any], state: ConnectionState) -> Self | None:
        factory, _ = _channel_factory(data["type"])
        if factory is None:
            return

        guild_id = utils._get_as_snowflake(data, "guild_id")
        guild = await state._get_guild(guild_id)
        if guild is not None:
            # the factory can't be a DMChannel or GroupChannel here
            channel = factory(guild=guild, state=self, data=data)  # type: ignore
            guild._add_channel(channel)  # type: ignore
            self = cls()
            self.__dict__.update(channel.__dict__)
            return self
        else:
            return

class PrivateChannelUpdate(Event, PrivateChannel):
    __event_name__ = "PRIVATE_CHANNEL_UPDATE"

    old: PrivateChannel | None

    def __init__(self) -> None:
        ...

    @classmethod
    async def __load__(cls, data: tuple[PrivateChannel | None, PrivateChannel], _: ConnectionState) -> Self | None:
        self = cls()
        self.old = data[0]
        self.__dict__.update(data[1].__dict__)
        return self

class GuildChannelUpdate(Event, PrivateChannel):
    __event_name__ = "GUILD_CHANNEL_UPDATE"

    old: GuildChannel | None

    def __init__(self) -> None:
        ...

    @classmethod
    async def __load__(cls, data: tuple[GuildChannel | None, GuildChannel], _: ConnectionState) -> Self | None:
        self = cls()
        self.old = data[0]
        self.__dict__.update(data[1].__dict__)
        return self

class ChannelUpdate(Event, GuildChannel):
    __event_name__ = "CHANNEL_UPDATE"

    def __init__(self) -> None:
        ...

    @classmethod
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

        guild_id = utils._get_as_snowflake(data, "guild_id")
        guild = await state._get_guild(guild_id)
        if guild is not None:
            channel = guild.get_channel(channel_id)
            if channel is not None:
                old_channel = copy.copy(channel)
                await channel._update(data) # type: ignore
                await state.emitter.emit("GUILD_CHANNEL_UPDATE", (old_channel, channel))

class ChannelDelete(Event, GuildChannel):
    __event_name__ = "CHANNEL_DELETE"

    def __init__(self) -> None:
        ...

    @classmethod
    async def __load__(cls, data: dict[str, Any], state: ConnectionState) -> Self | None:
        guild = await state._get_guild(utils._get_as_snowflake(data, "guild_id"))
        channel_id = int(data["id"])
        if guild is not None:
            channel = guild.get_channel(channel_id)
            if channel is not None:
                guild._remove_channel(channel)
                self = cls()
                self.__dict__.update(channel.__dict__)
                return self

class ChannelPinsUpdate(Event):
    channel: PrivateChannel | GuildChannel | Thread
    last_pin: datetime | None

    @classmethod
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
        self.last_pin = (
            utils.parse_time(data["last_pin_timestamp"])
            if data["last_pin_timestamp"]
            else None
        )
        return self
