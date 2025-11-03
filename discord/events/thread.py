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
from typing import Any, Self, cast

from typing_extensions import override

from discord import utils
from discord.abc import Snowflake
from discord.app.event_emitter import Event
from discord.app.state import ConnectionState
from discord.raw_models import RawThreadDeleteEvent, RawThreadMembersUpdateEvent, RawThreadUpdateEvent
from discord.threads import Thread, ThreadMember
from discord.types.raw_models import ThreadDeleteEvent, ThreadUpdateEvent
from discord.types.threads import ThreadMember as ThreadMemberPayload

_log = logging.getLogger(__name__)


class ThreadMemberJoin(Event, ThreadMember):
    __event_name__: str = "THREAD_MEMBER_JOIN"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: ThreadMember, _: ConnectionState) -> Self:
        self = cls()
        self.__dict__.update(data.__dict__)
        return self


class ThreadJoin(Event, Thread):
    __event_name__: str = "THREAD_JOIN"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Thread, _: ConnectionState) -> Self:
        self = cls()
        self.__dict__.update(data.__dict__)
        return self


class ThreadMemberRemove(Event, ThreadMember):
    __event_name__: str = "THREAD_MEMBER_REMOVE"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: ThreadMember, _: ConnectionState) -> Self:
        self = cls()
        self.__dict__.update(data.__dict__)
        return self


class ThreadRemove(Event, Thread):
    __event_name__: str = "THREAD_REMOVE"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Thread, _: ConnectionState) -> Self:
        self = cls()
        self.__dict__.update(data.__dict__)
        return self


class ThreadCreate(Event, Thread):
    __event_name__: str = "THREAD_CREATE"

    def __init__(self) -> None: ...

    just_joined: bool

    @classmethod
    @override
    async def __load__(cls, data: dict[str, Any], state: ConnectionState) -> Self | None:
        guild_id = int(data["guild_id"])
        guild = await state._get_guild(guild_id)
        if guild is None:
            return

        cached_thread = guild.get_thread(int(data["id"]))
        self = cls()
        if not cached_thread:
            thread = Thread(guild=guild, state=guild._state, data=data)  # type: ignore
            guild._add_thread(thread)
            if data.get("newly_created"):
                thread._add_member(
                    ThreadMember(
                        thread,
                        {
                            "id": thread.id,
                            "user_id": data["owner_id"],
                            "join_timestamp": data["thread_metadata"]["create_timestamp"],
                            "flags": utils.MISSING,
                        },
                    )
                )
                self.just_joined = False
            self.__dict__.update(thread.__dict__)
        else:
            self.__dict__.update(cached_thread.__dict__)
            self.just_joined = True

        if self.just_joined:
            await state.emitter.emit("THREAD_JOIN", self)
        else:
            return self


class ThreadUpdate(Event, Thread):
    __event_name__: str = "THREAD_UPDATE"

    def __init__(self) -> None: ...

    old: Thread

    @classmethod
    @override
    async def __load__(cls, data: ThreadUpdateEvent, state: ConnectionState) -> Self | None:
        guild_id = int(data["guild_id"])
        guild = await state._get_guild(guild_id)
        raw = RawThreadUpdateEvent(data)
        if guild is None:
            return

        self = cls()

        thread = guild.get_thread(raw.thread_id)
        if thread:
            self.old = thread
            await thread._update(thread)
            if thread.archived:
                guild._remove_thread(cast(Snowflake, raw.thread_id))
        else:
            thread = Thread(guild=guild, state=guild._state, data=data)  # type: ignore
            if not thread.archived:
                guild._add_thread(thread)

        self.__dict__.update(thread.__dict__)
        return self


class ThreadDelete(Event, Thread):
    __event_name__: str = "THREAD_DELETE"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: ThreadDeleteEvent, state: ConnectionState) -> Self | None:
        raw = RawThreadDeleteEvent(data)
        guild = await state._get_guild(raw.guild_id)
        if guild is None:
            return

        self = cls()  # TODO: self is unused @VincentRPS # noqa: F841

        thread = guild.get_thread(raw.thread_id)
        if thread:
            guild._remove_thread(cast(Snowflake, thread.id))
            if (msg := await thread.get_starting_message()) is not None:
                msg.thread = None  # type: ignore

        return cast(Self, thread)  # TODO: this is an incorrect rtype @VincentRPS


class ThreadListSync(Event):
    __event_name__: str = "THREAD_LIST_SYNC"

    @classmethod
    @override
    async def __load__(cls, data: dict[str, Any], state) -> Self | None:
        guild_id = int(data["guild_id"])
        guild = await state._get_guild(guild_id)
        if guild is None:
            _log.debug(
                "THREAD_LIST_SYNC referencing an unknown guild ID: %s. Discarding",
                guild_id,
            )
            return

        try:
            channel_ids = set(data["channel_ids"])
        except KeyError:
            # If not provided, then the entire guild is being synced
            # So all previous thread data should be overwritten
            previous_threads = guild._threads.copy()
            guild._clear_threads()
        else:
            previous_threads = guild._filter_threads(channel_ids)

        threads = {d["id"]: guild._store_thread(d) for d in data.get("threads", [])}

        for member in data.get("members", []):
            try:
                # note: member['id'] is the thread_id
                thread = threads[member["id"]]
            except KeyError:
                continue
            else:
                thread._add_member(ThreadMember(thread, member))

        for thread in threads.values():
            old = previous_threads.pop(thread.id, None)
            if old is None:
                await state.emitter.emit("THREAD_JOIN", thread)

        for thread in previous_threads.values():
            await state.emitter.emit("THREAD_REMOVE", thread)


class ThreadMemberUpdate(Event, ThreadMember):
    __event_name__: str = "THREAD_MEMBER_UPDATE"

    def __init__(self): ...

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild_id = int(data["guild_id"])
        guild = await state._get_guild(guild_id)
        if guild is None:
            _log.debug(
                "THREAD_MEMBER_UPDATE referencing an unknown guild ID: %s. Discarding",
                guild_id,
            )
            return

        thread_id = int(data["id"])
        thread: Thread | None = guild.get_thread(thread_id)
        if thread is None:
            _log.debug(
                "THREAD_MEMBER_UPDATE referencing an unknown thread ID: %s. Discarding",
                thread_id,
            )
            return

        member = ThreadMember(thread, data)
        thread.me = member
        thread._add_member(member)
        self = cls()
        self.__dict__.update(member.__dict__)

        return self


class BulkThreadMemberUpdate(Event):
    __event_name__: str = "BULK_THREAD_MEMBER_UPDATE"

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild_id = int(data["guild_id"])
        guild = await state._get_guild(guild_id)
        if guild is None:
            _log.debug(
                "THREAD_MEMBERS_UPDATE referencing an unknown guild ID: %s. Discarding",
                guild_id,
            )
            return

        thread_id = int(data["id"])
        thread: Thread | None = guild.get_thread(thread_id)
        raw = RawThreadMembersUpdateEvent(data)  # TODO: Not used @VincentRPS # noqa: F841
        if thread is None:
            _log.debug(
                ("THREAD_MEMBERS_UPDATE referencing an unknown thread ID: %s. Discarding"),
                thread_id,
            )
            return

        added_members = [ThreadMember(thread, d) for d in data.get("added_members", [])]
        removed_member_ids = [int(x) for x in data.get("removed_member_ids", [])]
        self_id = state.self_id
        for member in added_members:
            thread._add_member(member)
            if member.id != self_id:
                await state.emitter.emit("THREAD_MEMBER_JOIN", member)
            else:
                thread.me = member
                await state.emitter.emit("THREAD_JOIN", thread)

        for member_id in removed_member_ids:
            member = thread._pop_member(member_id)
            if member_id != self_id:
                if member is not None:
                    await state.emitter.emit("thread_member_remove", member)
            else:
                thread.me = None
                await state.emitter.emit("thread_remove", thread)
