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
from discord.guild import Guild
from discord.integrations import Integration, _integration_factory
from discord.raw_models import RawIntegrationDeleteEvent

_log = logging.getLogger(__name__)


class GuildIntegrationsUpdate(Event):
    """Called whenever an integration is created, modified, or removed from a guild.

    This requires :attr:`Intents.integrations` to be enabled.

    Attributes
    ----------
    guild: :class:`Guild`
        The guild that had its integrations updated.
    """

    __event_name__: str = "GUILD_INTEGRATIONS_UPDATE"

    guild: Guild

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "GUILD_INTEGRATIONS_UPDATE referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        self = cls()
        self.guild = guild
        return self


class IntegrationCreate(Event, Integration):
    """Called when an integration is created.

    This requires :attr:`Intents.integrations` to be enabled.

    This event inherits from :class:`Integration`.
    """

    __event_name__: str = "INTEGRATION_CREATE"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        data_copy = data.copy()
        guild_id = int(data_copy.pop("guild_id"))
        guild = await state._get_guild(guild_id)
        if guild is None:
            _log.debug(
                "INTEGRATION_CREATE referencing an unknown guild ID: %s. Discarding.",
                guild_id,
            )
            return

        integration_cls, _ = _integration_factory(data_copy["type"])
        integration = integration_cls(data=data_copy, guild=guild)

        self = cls()
        self.__dict__.update(integration.__dict__)
        return self


class IntegrationUpdate(Event, Integration):
    """Called when an integration is updated.

    This requires :attr:`Intents.integrations` to be enabled.

    This event inherits from :class:`Integration`.
    """

    __event_name__: str = "INTEGRATION_UPDATE"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        data_copy = data.copy()
        guild_id = int(data_copy.pop("guild_id"))
        guild = await state._get_guild(guild_id)
        if guild is None:
            _log.debug(
                "INTEGRATION_UPDATE referencing an unknown guild ID: %s. Discarding.",
                guild_id,
            )
            return

        integration_cls, _ = _integration_factory(data_copy["type"])
        integration = integration_cls(data=data_copy, guild=guild)

        self = cls()
        self.__dict__.update(integration.__dict__)
        return self


class IntegrationDelete(Event):
    """Called when an integration is deleted.

    This requires :attr:`Intents.integrations` to be enabled.

    Attributes
    ----------
    raw: :class:`RawIntegrationDeleteEvent`
        The raw event payload data.
    """

    __event_name__: str = "INTEGRATION_DELETE"

    raw: RawIntegrationDeleteEvent

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild_id = int(data["guild_id"])
        guild = await state._get_guild(guild_id)
        if guild is None:
            _log.debug(
                "INTEGRATION_DELETE referencing an unknown guild ID: %s. Discarding.",
                guild_id,
            )
            return

        raw = RawIntegrationDeleteEvent(data)

        self = cls()
        self.raw = raw
        return self
