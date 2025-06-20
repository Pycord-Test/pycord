from typing import Any, Self
from discord import utils
from discord.app.event_emitter import Event
from discord.app.state import ConnectionState
from discord.threads import Thread, ThreadMember


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
        else:
            self.just_joined = True

        return self
