from typing import Any, Self, cast
from discord import utils
from discord.abc import Snowflake
from discord.app.event_emitter import Event
from discord.app.state import ConnectionState
from discord.raw_models import RawThreadDeleteEvent, RawThreadUpdateEvent
from discord.threads import Thread, ThreadMember
from discord.types.raw_models import ThreadDeleteEvent, ThreadUpdateEvent


class ThreadCreate(Event, Thread):
    __event_name__ = "THREAD_CREATE"

    def __init__(self) -> None:
        ...

    just_joined: bool

    @classmethod
    async def __load__(cls, data: dict[str, Any], state: ConnectionState) -> Self | None:
        guild_id = int(data["guild_id"])
        guild = await state._get_guild(guild_id)
        if guild is None:
            return

        cached_thread = guild.get_thread(int(data["id"]))
        self = cls()
        if not cached_thread:
            thread = Thread(guild=guild, state=guild._state, data=data) # type: ignore
            guild._add_thread(thread)
            if data.get("newly_created"):
                thread._add_member(
                    ThreadMember(
                        thread,
                        {
                            "id": thread.id,
                            "user_id": data["owner_id"],
                            "join_timestamp": data["thread_metadata"][
                                "create_timestamp"
                            ],
                            "flags": utils.MISSING,
                        },
                    )
                )
                self.just_joined = False
            self.__dict__.update(thread.__dict__)
        else:
            self.__dict__.update(cached_thread.__dict__)
            self.just_joined = True

        return self

class ThreadUpdate(Event, Thread):
    __event_name__ = "THREAD_UPDATE"

    def __init__(self) -> None:
        ...

    old: Thread

    @classmethod
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
            thread = Thread(guild=guild, state=guild._state, data=data) # type: ignore
            if not thread.archived:
                guild._add_thread(thread)

        self.__dict__.update(thread.__dict__)
        return self

class ThreadDelete(Event, Thread):
    __event_name__ = "THREAD_DELETE"

    def __init__(self) -> None:
        ...

    @classmethod
    async def __load__(cls, data: ThreadDeleteEvent, state: ConnectionState) -> Self | None:
        raw = RawThreadDeleteEvent(data)
        guild = await state._get_guild(raw.guild_id)
        if guild is None:
            return

        self = cls()

        thread = guild.get_thread(raw.thread_id)
        if thread:
            guild._remove_thread(cast(Snowflake, thread.id))
            if (msg := await thread.get_starting_message()) is not None:
                msg.thread = None # type: ignore

        return cast(Self, thread)
