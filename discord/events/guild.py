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

from typing_extensions import Self

from discord import Role
from discord.app.event_emitter import Event
from discord.app.state import ConnectionState
from discord.emoji import Emoji
from discord.guild import Guild
from discord.member import Member
from discord.raw_models import RawMemberRemoveEvent
from discord.sticker import Sticker

if TYPE_CHECKING:
    from ..types.member import MemberWithUser

_log = logging.getLogger(__name__)


class GuildMemberJoin(Event, Member):
    __event_name__ = "GUILD_MEMBER_JOIN"

    def __init__(self) -> None: ...

    @classmethod
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "GUILD_MEMBER_ADD referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        member = Member(guild=guild, data=data, state=state)
        if state.member_cache_flags.joined:
            await guild._add_member(member)

        if guild._member_count is not None:
            guild._member_count += 1

        self = cls()
        self.__dict__.update(member.__dict__)
        return self


class GuildMemberRemove(Event, Member):
    __event_name__ = "GUILD_MEMBER_REMOVE"

    def __init__(self) -> None: ...

    @classmethod
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
                guild._remove_member(member)  # type: ignore
                self = cls()
                self.__dict__.update(member.__dict__)
                return self
        else:
            _log.debug(
                "GUILD_MEMBER_REMOVE referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )


class GuildMemberUpdate(Event, Member):
    __event_name__ = "GUILD_MEMBER_UPDATE"

    old: Member

    def __init__(self) -> None: ...

    @classmethod
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
            self.__dict__.update(member.__dict__)
            self.old = old_member
            return self
        else:
            if state.member_cache_flags.joined:
                member = Member(data=data, guild=guild, state=state)

                # Force an update on the inner user if necessary
                user_update = member._update_inner_user(user)
                if user_update:
                    await state.emitter.emit("USER_UPDATE", user_update)

                await guild._add_member(member)
            _log.debug(
                "GUILD_MEMBER_UPDATE referencing an unknown member ID: %s. Discarding.",
                user_id,
            )


class GuildEmojisUpdate(Event):
    __event_name__ = "GUILD_EMOJIS_UPDATE"
    guild: Guild
    emojis: list[Emoji]
    old_emojis: list[Emoji]

    @classmethod
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


class GuildStickersUpdate(Event):
    __event_name__ = "GUILD_STICKERS_UPDATE"

    guild: Guild
    stickers: list[Sticker]
    old_stickers: list[Sticker]

    @classmethod
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


class GuildAvailable(Event, Guild):
    __event_name__ = "GUILD_AVAILABLE"

    def __init__(self) -> None: ...

    @classmethod
    async def __load__(cls, data: Guild, _: ConnectionState) -> Self:
        self = cls()
        self.__dict__.update(data.__dict__)
        return self


class GuildUnavailable(Event, Guild):
    __event_name__ = "GUILD_UNAVAILABLE"

    def __init__(self) -> None: ...

    @classmethod
    async def __load__(cls, data: Guild, _: ConnectionState) -> Self:
        self = cls()
        self.__dict__.update(data.__dict__)
        return self


class GuildJoin(Event, Guild):
    __event_name__ = "GUILD_JOIN"

    def __init__(self) -> None: ...

    @classmethod
    async def __load__(cls, data: Guild, _: ConnectionState) -> Self:
        self = cls()
        self.__dict__.update(data.__dict__)
        return self


class GuildCreate(Event, Guild):
    __event_name__ = "GUILD_CREATE"

    def __init__(self) -> None: ...

    @classmethod
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
        self.__dict__.update(data.__dict__)
        return self


class GuildUpdate(Event, Guild):
    __event_name__ = "GUILD_UPDATE"

    old: Guild

    def __init__(self) -> None: ...

    @classmethod
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["id"]))
        if guild is not None:
            old_guild = copy.copy(guild)
            guild = await guild._from_data(data, state)
            self = cls()
            self.__dict__.update(guild.__dict__)
            self.old = old_guild
            return self
        else:
            _log.debug(
                "GUILD_UPDATE referencing an unknown guild ID: %s. Discarding.",
                data["id"],
            )


class GuildDelete(Event, Guild):
    __event_name__ = "GUILD_DELETE"

    old: Guild

    def __init__(self) -> None: ...

    @classmethod
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
        self.__dict__.update(guild.__dict__)
        return self


class GuildBanAdd(Event, Member):
    __event_name__ = "GUILD_BAN_ADD"

    def __init__(self) -> None: ...

    @classmethod
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
            member = Member(guild=guild, data=fake_data, state=state)

        self = cls()
        self.__dict__.update(member.__dict__)
        return self


class GuildBanRemove(Event, Member):
    __event_name__ = "GUILD_BAN_REMOVE"

    def __init__(self) -> None: ...

    @classmethod
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
            member = Member(guild=guild, data=fake_data, state=state)

        self = cls()
        self.__dict__.update(member.__dict__)
        return self


class GuildRoleCreate(Event, Role):
    __event_name__ = "GUILD_ROLE_CREATE"

    def __init__(self) -> None: ...

    @classmethod
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
        self.__dict__.update(role.__dict__)
        return self


class GuildRoleUpdate(Event, Role):
    __event_name__ = "GUILD_ROLE_UPDATE"

    old: Role

    def __init__(self) -> None: ...

    @classmethod
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "GUILD_ROLE_UPDATE referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        role_id: int = int(data["role"]["id"])
        role = guild.get_role(role_id)
        if role is None:
            _log.debug(
                "GUILD_ROLE_UPDATE referencing an unknown role ID: %s. Discarding.",
                data["role"]["id"],
            )
            return

        old_role = copy.copy(role)
        await role._update(data["role"])

        self = cls()
        self.__dict__.update(role.__dict__)
        self.old = old_role
        return self


class GuildRoleDelete(Event, Role):
    __event_name__ = "GUILD_ROLE_DELETE"

    def __init__(self) -> None: ...

    @classmethod
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
        self.__dict__.update(role.__dict__)
        return self
