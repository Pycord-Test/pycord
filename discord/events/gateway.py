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

from typing import Any, cast

from typing_extensions import Self, override

from discord.emoji import Emoji
from discord.flags import ApplicationFlags
from discord.guild import Guild
from discord.member import Member
from discord.role import Role
from discord.sticker import Sticker
from discord.types.user import User as UserPayload
from discord.user import ClientUser, User
from discord.utils.private import get_as_snowflake

from ..app.event_emitter import Event
from ..app.state import ConnectionState
from ..enums import ApplicationCommandPermissionType
from ..types.guild import Guild as GuildPayload
from ..types.interactions import (
    ApplicationCommandPermissions as ApplicationCommandPermissionsPayload,
)
from ..types.interactions import (
    GuildApplicationCommandPermissions,
)


class Resumed(Event):
    """Called when the client has resumed a session."""

    __event_name__: str = "RESUMED"

    @classmethod
    async def __load__(cls, _data: Any, _state: ConnectionState) -> Self | None:
        return cls()


class Ready(Event):
    """Called when the client is done preparing the data received from Discord.

    Usually after login is successful and the client's guilds and cache are filled up.

    .. warning::
        This event is not guaranteed to be the first event called.
        Likewise, this event is **not** guaranteed to only be called once.
        This library implements reconnection logic and thus will end up calling
        this event whenever a RESUME request fails.

    Attributes
    ----------
    user: :class:`ClientUser`
        An instance representing the connected application user.
    application_id: :class:`int`
        A snowflake of the application's ID.
    application_flags: :class:`ApplicationFlags`
        An instance representing the application flags.
    guilds: list[:class:`Guild`]
        A list of guilds received in this event. Note it may have incomplete data
        as ``GUILD_CREATE`` fills up other parts of guild data.
    """

    __event_name__: str = "READY"

    user: ClientUser
    application_id: int
    application_flags: ApplicationFlags
    guilds: list[Guild]

    @classmethod
    @override
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
                self.application_id = get_as_snowflake(application, "id")  # type: ignore
                # flags will always be present here
                self.application_flags = ApplicationFlags._from_value(application["flags"])  # type: ignore
                state.application_id = self.application_id
                state.application_flags = self.application_flags

        self.guilds = []

        for guild_data in data["guilds"]:
            guild = await Guild._from_data(guild_data, state)
            self.guilds.append(guild)
            await state._add_guild(guild)

        await state.emitter.emit("CACHE_APP_EMOJIS", None)

        return self


class _CacheAppEmojis(Event):
    __event_name__: str = "CACHE_APP_EMOJIS"

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        if state.cache_app_emojis and state.application_id:
            data = await state.http.get_all_application_emojis(state.application_id)
            for e in data.get("items", []):
                await state.maybe_store_app_emoji(state.application_id, e)


class ApplicationCommandPermission:
    def __init__(self, data: ApplicationCommandPermissionsPayload) -> None:
        self.id = int(data["id"])
        """The id of the user, role, or channel affected by this permission"""
        self.type = ApplicationCommandPermissionType(data["type"])
        """Represents what this permission affects"""
        self.permission = data["permission"]
        """Represents whether the permission is allowed or denied"""


class ApplicationCommandPermissionsUpdate(Event):
    """Called when application command permissions are updated for a guild.

    This requires :attr:`Intents.guilds` to be enabled.

    Attributes
    ----------
    id: :class:`int`
        The ID of the command or application.
    application_id: :class:`int`
        The application ID.
    guild_id: :class:`int`
        The ID of the guild where permissions were updated.
    permissions: list[:class:`ApplicationCommandPermission`]
        The updated permissions for this application command.
    """

    __event_name__: str = "APPLICATION_COMMAND_PERMISSIONS_UPDATE"

    id: int
    application_id: int
    guild_id: int
    permissions: list[ApplicationCommandPermission]

    @classmethod
    @override
    async def __load__(cls, data: GuildApplicationCommandPermissions, state: ConnectionState) -> Self:
        self = cls()
        self.id = int(data["id"])
        self.application_id = int(data["application_id"])
        self.guild_id = int(data["guild_id"])
        self.permissions = [ApplicationCommandPermission(data) for data in data["permissions"]]
        return self


class PresenceUpdate(Event):
    """Called when a member updates their presence.

    This is called when one or more of the following things change:
    - status
    - activity

    This requires :attr:`Intents.presences` and :attr:`Intents.members` to be enabled.

    Attributes
    ----------
    old: :class:`Member`
        The member's old presence info.
    new: :class:`Member`
        The member's updated presence info.
    """

    __event_name__: str = "PRESENCE_UPDATE"

    old: Member
    new: Member

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        self = cls()
        guild_id = get_as_snowflake(data, "guild_id")
        guild = await state._get_guild(guild_id)
        if guild is None:
            return

        user = data["user"]
        member_id = int(user["id"])
        member = await guild.get_member(member_id)
        if member is None:
            return

        self.old = Member._copy(member)
        self.new = member
        user_update = member._presence_update(data=data, user=user)
        await state.emitter.emit("USER_UPDATE", user_update)
        return self


class UserUpdate(Event, User):
    """Called when a user updates their profile.

    This is called when one or more of the following things change:
    - avatar
    - username
    - discriminator
    - global_name

    This requires :attr:`Intents.members` to be enabled.

    This event inherits from :class:`User`.

    Attributes
    ----------
    old: :class:`User`
        The user's old info before the update.
    """

    __event_name__: str = "USER_UPDATE"

    old: User

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: tuple[User, User] | Any, state: ConnectionState) -> Self | None:
        self = cls()
        if isinstance(data, tuple):
            self.old = data[0]
            self.__dict__.update(data[1].__dict__)
            return self
        else:
            user = cast(ClientUser, state.user)
            await user._update(data)  # type: ignore
            ref = await state.cache.get_user(user.id)
            if ref is not None:
                ref._update(data)
