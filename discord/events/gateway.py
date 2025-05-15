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

from typing import Any, Self

from discord import utils
from discord.emoji import Emoji
from discord.flags import ApplicationFlags
from discord.guild import Guild, GuildChannel
from discord.member import Member
from discord.role import Role
from discord.sticker import Sticker
from discord.user import ClientUser

from ..app.state import ConnectionState
from ..app.event_emitter import Event
from ..types.interactions import ApplicationCommandPermissions as ApplicationCommandPermissionsPayload, GuildApplicationCommandPermissions
from ..types.guild import Guild as GuildPayload
from ..enums import ApplicationCommandPermissionType


class Resumed(Event):
    __event_name__ = "RESUMED"


class Ready(Event):
    __event_name__ = "READY"

    user: ClientUser
    """An instance of :class:`.user.ClientUser` representing the application"""
    application_id: int
    """A snowflake of the application's id"""
    application_flags: ApplicationFlags
    """An instance of :class:`.flags.ApplicationFlags` representing the application flags"""
    guilds: list[Guild]
    """A list of guilds received in this event. Note it may have incomplete data as `GUILD_CREATE` fills up other parts of guild data."""

    @classmethod
    async def __load__(cls, data: dict[str, Any], state: ConnectionState) -> Self:
        self = cls()
        self.user = ClientUser(state=state, data=data["user"])
        state.user = self.user
        await state.store_user(data["user"])

        if state.application_id is None:
            try:
                application = data["application"]
            except KeyError:
                pass
            else:
                self.application_id = utils._get_as_snowflake(application, "id") # type: ignore
                # flags will always be present here
                self.application_flags = ApplicationFlags._from_value(application["flags"])  # type: ignore
                state.application_id = self.application_id
                state.application_flags = self.application_flags

        self.guilds = []

        for guild_data in data["guilds"]:
            guild = await Guild(data=guild_data, state=state)._from_data(guild_data)
            self.guilds.append(guild)
            await state._add_guild(guild)

        await state.emitter.emit("CACHE_APP_EMOJIS", None)

        return self

class _CacheAppEmojis(Event):
    __event_name__ = "CACHE_APP_EMOJIS"

    @classmethod
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        if state.cache_app_emojis and state.application_id:
            data = await state.http.get_all_application_emojis(state.application_id)
            for e in data.get("items", []):
                await state.maybe_store_app_emoji(state.application_id, e)

class GuildCreate(Event, Guild):
    """An event which represents a guild becoming available via the gateway. Trickles down to the more distinct :class:`.GuildJoin` and :class:`.GuildAvailable` events."""

    __event_name__ = "GUILD_CREATE"

    guild: Guild

    def __init__(self) -> None:
        pass

    @classmethod
    async def __load__(cls, data: GuildPayload, state: ConnectionState) -> Self:
        self = cls()
        guild = await state._get_guild(int(data["id"]))
        if guild is None:
            guild = await Guild(data=data, state=state)._from_data(data)
            await state._add_guild(guild)
        self.guild = guild
        self.__dict__.update(self.guild.__dict__)
        if state._guild_needs_chunking(guild):
            await state.chunk_guild(guild)
        if guild.unavailable:
            await state.emitter.emit("GUILD_JOIN", guild)
        else:
            await state.emitter.emit("GUILD_AVAILABLE", guild)
        return self

class GuildJoin(Event, Guild):
    """An event which represents joining a new guild."""

    __event_name__ = "GUILD_JOIN"

    guild: Guild

    def __init__(self) -> None:
        pass

    @classmethod
    async def __load__(cls, data: Guild, _: ConnectionState) -> Self:
        self = cls()
        self.guild = data
        self.__dict__.update(self.guild.__dict__)
        return self

class GuildAvailable(Event, Guild):
    """An event which represents a guild previously joined becoming available."""

    __event_name__ = "GUILD_AVAILABLE"

    guild: Guild

    def __init__(self) -> None:
        pass

    @classmethod
    async def __load__(cls, data: Guild, _: ConnectionState) -> Self:
        self = cls()
        self.guild = data
        self.__dict__.update(self.guild.__dict__)
        return self

class ApplicationCommandPermission:
    def __init__(self, data: ApplicationCommandPermissionsPayload) -> None:
        self.id = int(data["id"])
        """The id of the user, role, or channel affected by this permission"""
        self.type = ApplicationCommandPermissionType(data["type"])
        """Represents what this permission affects"""
        self.permission = data["permission"]
        """Represents whether the permission is allowed or denied"""

class ApplicationCommandPermissionsUpdate(Event):
    """Represents an Application Command having permissions updated in a guild"""

    __event_name__ = "APPLICATION_COMMAND_PERMISSIONS_UPDATE"

    id: int
    """A snowflake of the application command's id"""
    application_id: int
    """A snowflake of the application's id"""
    guild_id: int
    """A snowflake of the guild's id where the permissions have been updated"""
    permissions: list[ApplicationCommandPermission]
    """A list of permissions this Application Command has"""

    @classmethod
    async def __load__(cls, data: GuildApplicationCommandPermissions, state: ConnectionState) -> Self:
        self = cls()
        self.id = int(data["id"])
        self.application_id = int(data["application_id"])
        self.guild_id = int(data["guild_id"])
        self.permissions = [ApplicationCommandPermission(data) for data in data["permissions"]]
        return self
