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

import logging
from typing import Any

from typing_extensions import Self, override

from discord.app.event_emitter import Event
from discord.app.state import ConnectionState
from discord.enums import ScheduledEventStatus
from discord.member import Member
from discord.raw_models import RawScheduledEventSubscription
from discord.scheduled_events import ScheduledEvent

_log = logging.getLogger(__name__)


class GuildScheduledEventCreate(Event, ScheduledEvent):
    """Called when a scheduled event is created.

    This requires :attr:`Intents.scheduled_events` to be enabled.

    This event inherits from :class:`ScheduledEvent`.
    """

    __event_name__: str = "GUILD_SCHEDULED_EVENT_CREATE"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "GUILD_SCHEDULED_EVENT_CREATE referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        creator = None if not data.get("creator", None) else await guild.get_member(data.get("creator_id"))
        scheduled_event = ScheduledEvent(state=state, guild=guild, creator=creator, data=data)
        guild._add_scheduled_event(scheduled_event)

        self = cls()
        self.__dict__.update(scheduled_event.__dict__)
        return self


class GuildScheduledEventUpdate(Event, ScheduledEvent):
    """Called when a scheduled event is updated.

    This requires :attr:`Intents.scheduled_events` to be enabled.

    This event inherits from :class:`ScheduledEvent`.

    Attributes
    ----------
    old: :class:`ScheduledEvent`
        The old scheduled event before the update.
    """

    __event_name__: str = "GUILD_SCHEDULED_EVENT_UPDATE"

    old: ScheduledEvent | None

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "GUILD_SCHEDULED_EVENT_UPDATE referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        creator = None if not data.get("creator", None) else await guild.get_member(data.get("creator_id"))
        scheduled_event = ScheduledEvent(state=state, guild=guild, creator=creator, data=data)
        old_event = guild.get_scheduled_event(int(data["id"]))
        guild._add_scheduled_event(scheduled_event)

        self = cls()
        self.old = old_event
        self.__dict__.update(scheduled_event.__dict__)
        return self


class GuildScheduledEventDelete(Event, ScheduledEvent):
    """Called when a scheduled event is deleted.

    This requires :attr:`Intents.scheduled_events` to be enabled.

    This event inherits from :class:`ScheduledEvent`.
    """

    __event_name__: str = "GUILD_SCHEDULED_EVENT_DELETE"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "GUILD_SCHEDULED_EVENT_DELETE referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        creator = None if not data.get("creator", None) else await guild.get_member(data.get("creator_id"))
        scheduled_event = ScheduledEvent(state=state, guild=guild, creator=creator, data=data)
        scheduled_event.status = ScheduledEventStatus.canceled
        guild._remove_scheduled_event(scheduled_event)

        self = cls()
        self.__dict__.update(scheduled_event.__dict__)
        return self


class GuildScheduledEventUserAdd(Event):
    """Called when a user subscribes to a scheduled event.

    This requires :attr:`Intents.scheduled_events` to be enabled.

    Attributes
    ----------
    event: :class:`ScheduledEvent`
        The scheduled event subscribed to.
    member: :class:`Member`
        The member who subscribed.
    raw: :class:`RawScheduledEventSubscription`
        The raw event payload data.
    """

    __event_name__: str = "GUILD_SCHEDULED_EVENT_USER_ADD"

    raw: RawScheduledEventSubscription
    event: ScheduledEvent
    member: Member

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "GUILD_SCHEDULED_EVENT_USER_ADD referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        raw = RawScheduledEventSubscription(data, "USER_ADD")
        raw.guild = guild

        member = await guild.get_member(data["user_id"])
        if member is not None:
            event = guild.get_scheduled_event(data["guild_scheduled_event_id"])
            if event:
                event.subscriber_count += 1
                guild._add_scheduled_event(event)
                self = cls()
                self.raw = raw
                self.event = event
                self.member = member
                return self


class GuildScheduledEventUserRemove(Event):
    """Called when a user unsubscribes from a scheduled event.

    This requires :attr:`Intents.scheduled_events` to be enabled.

    Attributes
    ----------
    event: :class:`ScheduledEvent`
        The scheduled event unsubscribed from.
    member: :class:`Member`
        The member who unsubscribed.
    raw: :class:`RawScheduledEventSubscription`
        The raw event payload data.
    """

    __event_name__: str = "GUILD_SCHEDULED_EVENT_USER_REMOVE"

    raw: RawScheduledEventSubscription
    event: ScheduledEvent
    member: Member

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "GUILD_SCHEDULED_EVENT_USER_REMOVE referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        raw = RawScheduledEventSubscription(data, "USER_REMOVE")
        raw.guild = guild

        member = await guild.get_member(data["user_id"])
        if member is not None:
            event = guild.get_scheduled_event(data["guild_scheduled_event_id"])
            if event:
                event.subscriber_count -= 1
                guild._add_scheduled_event(event)
                self = cls()
                self.raw = raw
                self.event = event
                self.member = member
                return self
