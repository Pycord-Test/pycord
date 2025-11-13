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
from functools import lru_cache
from typing import Any, TypeVar, cast

from typing_extensions import Self, override

from discord.abc import PrivateChannel
from discord.app.event_emitter import Event
from discord.app.state import ConnectionState
from discord.channel import GroupChannel, GuildChannel, _channel_factory
from discord.channel.thread import Thread
from discord.enums import ChannelType, try_enum
from discord.utils.private import get_as_snowflake, parse_time

T = TypeVar("T")


@lru_cache(maxsize=128)
def _create_event_channel_class(event_cls: type[Event], channel_cls: type[GuildChannel]) -> type[GuildChannel]:
    """
    Dynamically create a class that inherits from both an Event and a Channel type.

    This allows the event to have the correct channel type while also being an Event.
    Results are cached to avoid recreating the same class multiple times.

    Parameters
    ----------
    event_cls: type[Event]
        The event class (e.g., ChannelCreate)
    channel_cls: type[GuildChannel]
        The channel class (e.g., TextChannel, VoiceChannel)

    Returns
    -------
    type[GuildChannel]
        A new class that inherits from both the event and channel
    """

    class EventChannel(event_cls, channel_cls):  # type: ignore
        __slots__ = ()

    EventChannel.__name__ = f"{event_cls.__name__}_{channel_cls.__name__}"
    EventChannel.__qualname__ = f"{event_cls.__qualname__}_{channel_cls.__name__}"

    return EventChannel  # type: ignore


class ChannelCreate(Event, GuildChannel):
    """Called when a guild channel is created.

    This requires :attr:`Intents.guilds` to be enabled.

    This event inherits from the actual channel type that was created
    (e.g., :class:`TextChannel`, :class:`VoiceChannel`, :class:`ForumChannel`, etc.).
    You can access all channel attributes directly on the event object.

    .. note::
        While this class shows :class:`GuildChannel` in the signature, at runtime
        the event will be an instance of the specific channel type that was created.
    """

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
        # Create the real channel object to be stored in the guild
        channel = await factory._from_data(guild=guild, state=state, data=data)  # type: ignore
        guild._add_channel(channel)  # type: ignore

        # Create a dynamic event class that combines this event type with the specific channel type
        event_channel_cls = _create_event_channel_class(cls, factory)  # type: ignore
        # Instantiate it using the event's stub __init__ (no arguments)
        self = event_channel_cls()  # type: ignore
        # Populate the event instance with data from the real channel
        self._populate_from_slots(channel)
        return self  # type: ignore


class PrivateChannelUpdate(Event, PrivateChannel):
    """Called whenever a private group DM is updated (e.g., changed name or topic).

    This requires :attr:`Intents.messages` to be enabled.

    This event inherits from :class:`GroupChannel`.

    Attributes
    ----------
    old: :class:`GroupChannel` | None
        The channel's old info before the update, or None if not in cache.
    """

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
    """Called whenever a guild channel is updated (e.g., changed name, topic, permissions).

    This requires :attr:`Intents.guilds` to be enabled.

    This event inherits from the actual channel type that was updated
    (e.g., :class:`TextChannel`, :class:`VoiceChannel`, :class:`ForumChannel`, etc.).

    .. note::
        While this class shows :class:`GuildChannel` in the signature, at runtime
        the event will be an instance of the specific channel type that was updated.

    Attributes
    ----------
    old: :class:`TextChannel` | :class:`VoiceChannel` | :class:`CategoryChannel` | :class:`StageChannel` | :class:`ForumChannel` | None
        The channel's old info before the update, or None if not in cache.
        This will be the same type as the event itself.
    """

    __event_name__: str = "GUILD_CHANNEL_UPDATE"

    old: GuildChannel | None

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: tuple[GuildChannel | None, GuildChannel], state: ConnectionState) -> Self | None:
        channel = data[1]
        # Create a dynamic event class that combines this event type with the specific channel type
        event_channel_cls = _create_event_channel_class(cls, type(channel))  # type: ignore
        # Instantiate it using the event's stub __init__ (no arguments)
        self = event_channel_cls()  # type: ignore
        # Set the old channel and populate from the new channel
        self.old = data[0]
        self._populate_from_slots(channel)
        return self  # type: ignore


class ChannelUpdate(Event, GuildChannel):
    """Internal event that dispatches to either :class:`PrivateChannelUpdate` or :class:`GuildChannelUpdate`.

    This event is not directly received by user code. It automatically routes to the appropriate
    specific channel update event based on the channel type.
    """

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
                old_channel = copy(channel)
                await channel._update(data)  # type: ignore
                await state.emitter.emit("GUILD_CHANNEL_UPDATE", (old_channel, channel))


class ChannelDelete(Event, GuildChannel):
    """Called when a guild channel is deleted.

    This requires :attr:`Intents.guilds` to be enabled.

    This event inherits from the actual channel type that was deleted
    (e.g., :class:`TextChannel`, :class:`VoiceChannel`, :class:`ForumChannel`, etc.).
    You can access all channel attributes directly on the event object.

    .. note::
        While this class shows :class:`GuildChannel` in the signature, at runtime
        the event will be an instance of the specific channel type that was deleted.
    """

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
                # Create a dynamic event class that combines this event type with the specific channel type
                event_channel_cls = _create_event_channel_class(cls, type(channel))  # type: ignore
                # Instantiate it using the event's stub __init__ (no arguments)
                self = event_channel_cls()  # type: ignore
                # Populate the event instance with data from the real channel
                self._populate_from_slots(channel)
                return self  # type: ignore


class ChannelPinsUpdate(Event):
    """Called whenever a message is pinned or unpinned from a channel.

    Attributes
    ----------
    channel: :class:`abc.PrivateChannel` | :class:`TextChannel` | :class:`VoiceChannel` | :class:`StageChannel` | :class:`ForumChannel` | :class:`Thread`
        The channel that had its pins updated. Can be any messageable channel type.
    last_pin: :class:`datetime.datetime` | None
        The latest message that was pinned as an aware datetime in UTC, or None if no pins exist.
    """

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
