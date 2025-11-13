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

import asyncio
import copy
import logging
from typing import TYPE_CHECKING, Any

from typing_extensions import Self, override

from ..app.event_emitter import Event
from ..app.state import ConnectionState
from ..emoji import Emoji
from ..guild import Guild
from ..member import Member
from ..raw_models import RawMemberRemoveEvent
from ..role import Role
from ..sticker import Sticker

if TYPE_CHECKING:
    from ..types.member import MemberWithUser

_log = logging.getLogger(__name__)


class GuildMemberJoin(Event, Member):
    """Called when a member joins a guild.

    This requires :attr:`Intents.members` to be enabled.

    This event inherits from :class:`Member`.
    """

    __event_name__: str = "GUILD_MEMBER_JOIN"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "GUILD_MEMBER_ADD referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        member = await Member._from_data(guild=guild, data=data, state=state)
        if state.member_cache_flags.joined:
            await guild._add_member(member)

        if guild._member_count is not None:
            guild._member_count += 1

        self = cls()
        self._populate_from_slots(member)
        return self


class GuildMemberRemove(Event, Member):
    """Called when a member leaves a guild.

    This requires :attr:`Intents.members` to be enabled.

    This event inherits from :class:`Member`.
    """

    __event_name__: str = "GUILD_MEMBER_REMOVE"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        user = await state.store_user(data["user"])
        raw = RawMemberRemoveEvent(data, user)

        guild = await state._get_guild(int(data["guild_id"]))
        if guild is not None:
            if guild._member_count is not None:
                guild._member_count -= 1

            member = await guild.get_member(user.id)
            if member is not None:
                raw.user = member
                await state.cache.delete_member(guild.id, member.id)
                self = cls()
                self._populate_from_slots(member)
                return self
        else:
            _log.debug(
                "GUILD_MEMBER_REMOVE referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )


class GuildMemberUpdate(Event, Member):
    """Called when a member updates their profile.

    This is called when one or more of the following things change:
    - nickname
    - roles
    - pending
    - communication_disabled_until
    - timed_out

    This requires :attr:`Intents.members` to be enabled.

    This event inherits from :class:`Member`.

    Attributes
    ----------
    old: :class:`Member`
        The member's old info before the update.
    """

    __event_name__: str = "GUILD_MEMBER_UPDATE"

    old: Member

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["guild_id"]))
        user = data["user"]
        user_id = int(user["id"])
        if guild is None:
            _log.debug(
                "GUILD_MEMBER_UPDATE referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        member = await guild.get_member(user_id)
        if member is not None:
            old_member = Member._copy(member)
            await member._update(data)
            user_update = member._update_inner_user(user)
            if user_update:
                await state.emitter.emit("USER_UPDATE", user_update)

            self = cls()
            self._populate_from_slots(member)
            self.old = old_member
            return self
        else:
            if state.member_cache_flags.joined:
                member = await Member._from_data(data=data, guild=guild, state=state)

                # Force an update on the inner user if necessary
                user_update = member._update_inner_user(user)
                if user_update:
                    await state.emitter.emit("USER_UPDATE", user_update)

                await guild._add_member(member)
            _log.debug(
                "GUILD_MEMBER_UPDATE referencing an unknown member ID: %s. Discarding.",
                user_id,
            )


class GuildMembersChunk(Event):
    """Called when a chunk of guild members is received.

    This is sent when you request offline members via :meth:`Guild.chunk`.
    This requires :attr:`Intents.members` to be enabled.

    Attributes
    ----------
    guild: :class:`Guild`
        The guild the members belong to.
    members: list[:class:`Member`]
        The members in this chunk.
    chunk_index: :class:`int`
        The chunk index in the expected chunks for this response (0 <= chunk_index < chunk_count).
    chunk_count: :class:`int`
        The total number of expected chunks for this response.
    not_found: list[:class:`int`]
        List of user IDs that were not found.
    presences: list[Any]
        List of presence data.
    nonce: :class:`str`
        The nonce used in the request, if any.
    """

    __event_name__: str = "GUILD_MEMBERS_CHUNK"
    guild: Guild
    members: list[Member]
    chunk_index: int
    chunk_count: int
    not_found: list[int]
    presences: list[Any]
    nonce: str

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild_id = int(data["guild_id"])
        guild = state._get_guild(guild_id)
        presences = data.get("presences", [])

        # the guild won't be None here
        member_data_list = data.get("members", [])
        members = await asyncio.gather(
            *[Member._from_data(guild=guild, data=member, state=state) for member in member_data_list]
        )  # type: ignore
        _log.debug("Processed a chunk for %s members in guild ID %s.", len(members), guild_id)

        if presences:
            member_dict = {str(member.id): member for member in members}
            for presence in presences:
                user = presence["user"]
                member_id = user["id"]
                member = member_dict.get(member_id)
                if member is not None:
                    member._presence_update(presence, user)

        complete = data.get("chunk_index", 0) + 1 == data.get("chunk_count")
        state.process_chunk_requests(guild_id, data.get("nonce"), members, complete)
        return None


class GuildEmojisUpdate(Event):
    """Called when a guild adds or removes emojis.

    This requires :attr:`Intents.emojis_and_stickers` to be enabled.

    Attributes
    ----------
    guild: :class:`Guild`
        The guild who got their emojis updated.
    emojis: list[:class:`Emoji`]
        The list of emojis after the update.
    old_emojis: list[:class:`Emoji`]
        The list of emojis before the update.
    """

    __event_name__: str = "GUILD_EMOJIS_UPDATE"
    guild: Guild
    emojis: list[Emoji]
    old_emojis: list[Emoji]

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "GUILD_EMOJIS_UPDATE referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        before_emojis = guild.emojis
        for emoji in before_emojis:
            await state.cache.delete_emoji(emoji)
        # guild won't be None here
        emojis = []
        for emoji in data["emojis"]:
            emojis.append(await state.store_emoji(guild, emoji))
        guild.emojis = emojis
        self = cls()
        self.guild = guild
        self.old_emojis = guild.emojis
        self.emojis = emojis
        return self


class GuildStickersUpdate(Event):
    """Called when a guild adds or removes stickers.

    This requires :attr:`Intents.emojis_and_stickers` to be enabled.

    Attributes
    ----------
    guild: :class:`Guild`
        The guild who got their stickers updated.
    stickers: list[:class:`GuildSticker`]
        The list of stickers after the update.
    old_stickers: list[:class:`GuildSticker`]
        The list of stickers before the update.
    """

    __event_name__: str = "GUILD_STICKERS_UPDATE"

    guild: Guild
    stickers: list[Sticker]
    old_stickers: list[Sticker]

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                ("GUILD_STICKERS_UPDATE referencing an unknown guild ID: %s. Discarding."),
                data["guild_id"],
            )
            return

        before_stickers = guild.stickers
        for emoji in before_stickers:
            await state.cache.delete_sticker(emoji.id)
        stickers = []
        for sticker in data["stickers"]:
            stickers.append(await state.store_sticker(guild, sticker))
        # guild won't be None here
        guild.stickers = stickers
        self = cls()
        self.old_stickers = stickers
        self.stickers = stickers
        self.guild = guild
        return self


class GuildAvailable(Event, Guild):
    """Called when a guild becomes available.

    The guild must have existed in the client's cache.
    This requires :attr:`Intents.guilds` to be enabled.

    This event inherits from :class:`Guild`.
    """

    __event_name__: str = "GUILD_AVAILABLE"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Guild, state: ConnectionState) -> Self:
        self = cls()
        self._populate_from_slots(data)
        return self


class GuildUnavailable(Event, Guild):
    """Called when a guild becomes unavailable.

    The guild must have existed in the client's cache.
    This requires :attr:`Intents.guilds` to be enabled.

    This event inherits from :class:`Guild`.
    """

    __event_name__: str = "GUILD_UNAVAILABLE"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Guild, state: ConnectionState) -> Self:
        self = cls()
        self._populate_from_slots(data)
        return self


class GuildJoin(Event, Guild):
    """Called when the client joins a new guild or when a guild is created.

    This requires :attr:`Intents.guilds` to be enabled.

    This event inherits from :class:`Guild`.
    """

    __event_name__: str = "GUILD_JOIN"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Guild, state: ConnectionState) -> Self:
        self = cls()
        self._populate_from_slots(data)
        return self


class GuildCreate(Event, Guild):
    """Internal event representing a guild becoming available via the gateway.

    This event trickles down to the more distinct :class:`GuildJoin` and :class:`GuildAvailable` events.
    Users should typically listen to those events instead.

    This event inherits from :class:`Guild`.
    """

    __event_name__: str = "GUILD_CREATE"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        unavailable = data.get("unavailable")
        if unavailable is True:
            # joined a guild with unavailable == True so..
            return

        guild = await state._get_create_guild(data)

        try:
            # Notify the on_ready state, if any, that this guild is complete.
            state._ready_state.put_nowait(guild)  # type: ignore
        except AttributeError:
            pass
        else:
            # If we're waiting for the event, put the rest on hold
            return

        # check if it requires chunking
        if state._guild_needs_chunking(guild):
            asyncio.create_task(state._chunk_and_dispatch(guild, unavailable))
            return

        # Dispatch available if newly available
        if unavailable is False:
            await state.emitter.emit("GUILD_AVAILABLE", guild)
        else:
            await state.emitter.emit("GUILD_JOIN", guild)

        self = cls()
        self._populate_from_slots(guild)
        return self


class GuildUpdate(Event, Guild):
    """Called when a guild is updated.

    Examples of when this is called:
    - Changed name
    - Changed AFK channel
    - Changed AFK timeout
    - etc.

    This requires :attr:`Intents.guilds` to be enabled.

    This event inherits from :class:`Guild`.

    Attributes
    ----------
    old: :class:`Guild`
        The guild prior to being updated.
    """

    __event_name__: str = "GUILD_UPDATE"

    old: Guild

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["id"]))
        if guild is not None:
            old_guild = copy.copy(guild)
            guild = await guild._from_data(data, state)
            self = cls()
            self._populate_from_slots(guild)
            self.old = old_guild
            return self
        else:
            _log.debug(
                "GUILD_UPDATE referencing an unknown guild ID: %s. Discarding.",
                data["id"],
            )


class GuildDelete(Event, Guild):
    """Called when a guild is removed from the client.

    This happens through, but not limited to, these circumstances:
    - The client got banned.
    - The client got kicked.
    - The client left the guild.
    - The client or the guild owner deleted the guild.

    In order for this event to be invoked then the client must have been part of the guild
    to begin with (i.e., it is part of :attr:`Client.guilds`).

    This requires :attr:`Intents.guilds` to be enabled.

    This event inherits from :class:`Guild`.

    Attributes
    ----------
    old: :class:`Guild`
        The guild that was removed.
    """

    __event_name__: str = "GUILD_DELETE"

    old: Guild

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["id"]))
        if guild is None:
            _log.debug(
                "GUILD_DELETE referencing an unknown guild ID: %s. Discarding.",
                data["id"],
            )
            return

        if data.get("unavailable", False):
            # GUILD_DELETE with unavailable being True means that the
            # guild that was available is now currently unavailable
            guild.unavailable = True
            await state.emitter.emit("GUILD_UNAVAILABLE", guild)
            return

        # do a cleanup of the messages cache
        messages = await state.cache.get_all_messages()
        await asyncio.gather(*[state.cache.delete_message(message.id) for message in messages])

        await state._remove_guild(guild)
        self = cls()
        self._populate_from_slots(guild)
        return self


class GuildBanAdd(Event, Member):
    """Called when a user gets banned from a guild.

    This requires :attr:`Intents.moderation` to be enabled.

    This event inherits from :class:`Member`.
    """

    __event_name__: str = "GUILD_BAN_ADD"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "GUILD_BAN_ADD referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        member = await guild.get_member(int(data["user"]["id"]))
        if member is None:
            fake_data: MemberWithUser = {
                "user": data["user"],
                "roles": [],
                "joined_at": None,
                "deaf": False,
                "mute": False,
            }
            member = await Member._from_data(guild=guild, data=fake_data, state=state)

        self = cls()
        self._populate_from_slots(member)
        return self


class GuildBanRemove(Event, Member):
    """Called when a user gets unbanned from a guild.

    This requires :attr:`Intents.moderation` to be enabled.

    This event inherits from :class:`Member`.
    """

    __event_name__: str = "GUILD_BAN_REMOVE"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "GUILD_BAN_ADD referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        fake_data: MemberWithUser = {
            "user": data["user"],
            "roles": [],
            "joined_at": None,
            "deaf": False,
            "mute": False,
        }
        member = await Member._from_data(guild=guild, data=fake_data, state=state)

        self = cls()
        self._populate_from_slots(member)
        return self


class GuildRoleCreate(Event, Role):
    """Called when a guild creates a role.

    To get the guild it belongs to, use :attr:`Role.guild`.
    This requires :attr:`Intents.guilds` to be enabled.

    This event inherits from :class:`Role`.
    """

    __event_name__: str = "GUILD_ROLE_CREATE"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "GUILD_ROLE_CREATE referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        role = Role(guild=guild, data=data["role"], state=state)
        guild._add_role(role)

        self = cls()
        self._populate_from_slots(role)
        return self


class GuildRoleUpdate(Event, Role):
    """Called when a role is changed guild-wide.

    This requires :attr:`Intents.guilds` to be enabled.

    This event inherits from :class:`Role`.

    Attributes
    ----------
    old: :class:`Role`
        The updated role's old info.
    """

    __event_name__: str = "GUILD_ROLE_UPDATE"

    old: Role

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "GUILD_ROLE_UPDATE referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return None

        role_id: int = int(data["role"]["id"])
        role = guild.get_role(role_id)
        if role is None:
            _log.debug(
                "GUILD_ROLE_UPDATE referencing an unknown role ID: %s. Discarding.",
                data["role"]["id"],
            )
            return None

        old_role = copy.copy(role)
        role._update(data["role"])

        self = cls()
        self._populate_from_slots(role)
        self.old = old_role
        return self


class GuildRoleDelete(Event, Role):
    """Called when a guild deletes a role.

    To get the guild it belongs to, use :attr:`Role.guild`.
    This requires :attr:`Intents.guilds` to be enabled.

    This event inherits from :class:`Role`.
    """

    __event_name__: str = "GUILD_ROLE_DELETE"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "GUILD_ROLE_DELETE referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        role_id: int = int(data["role_id"])
        role = guild.get_role(role_id)
        if role is None:
            _log.debug(
                "GUILD_ROLE_DELETE referencing an unknown role ID: %s. Discarding.",
                data["role_id"],
            )
            return

        guild._remove_role(role_id)

        self = cls()
        self._populate_from_slots(role)
        return self
