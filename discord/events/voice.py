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
import logging
from typing import TYPE_CHECKING, Any

from typing_extensions import Self, override

from discord.app.event_emitter import Event
from discord.app.state import ConnectionState
from discord.member import Member, VoiceState
from discord.raw_models import RawVoiceChannelStatusUpdateEvent
from discord.utils.private import get_as_snowflake

if TYPE_CHECKING:
    from discord.abc import VocalGuildChannel

_log = logging.getLogger(__name__)


async def logging_coroutine(coroutine, *, info: str) -> None:
    """Helper to log exceptions in coroutines."""
    try:
        await coroutine
    except Exception:
        _log.exception("Exception occurred during %s", info)


class VoiceStateUpdate(Event):
    __event_name__: str = "VOICE_STATE_UPDATE"

    member: Member
    before: VoiceState
    after: VoiceState

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(get_as_snowflake(data, "guild_id"))
        channel_id = get_as_snowflake(data, "channel_id")
        flags = state.member_cache_flags
        # state.user is *always* cached when this is called
        self_id = state.user.id  # type: ignore

        if guild is None:
            return

        if int(data["user_id"]) == self_id:
            voice = state._get_voice_client(guild.id)
            if voice is not None:
                coro = voice.on_voice_state_update(data)
                asyncio.create_task(logging_coroutine(coro, info="Voice Protocol voice state update handler"))

        member, before, after = await guild._update_voice_state(data, channel_id)  # type: ignore
        if member is None:
            _log.debug(
                "VOICE_STATE_UPDATE referencing an unknown member ID: %s. Discarding.",
                data["user_id"],
            )
            return

        if flags.voice:
            if channel_id is None and flags._voice_only and member.id != self_id:
                # Only remove from cache if we only have the voice flag enabled
                # Member doesn't meet the Snowflake protocol currently
                guild._remove_member(member)  # type: ignore
            elif channel_id is not None:
                await guild._add_member(member)

        self = cls()
        self.member = member
        self.before = before
        self.after = after
        return self


class VoiceServerUpdate(Event):
    __event_name__: str = "VOICE_SERVER_UPDATE"

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        try:
            key_id = int(data["guild_id"])
        except KeyError:
            key_id = int(data["channel_id"])

        vc = state._get_voice_client(key_id)
        if vc is not None:
            coro = vc.on_voice_server_update(data)
            asyncio.create_task(logging_coroutine(coro, info="Voice Protocol voice server update handler"))

        # This event doesn't dispatch to user code, it's internal for voice protocol
        return None


class VoiceChannelStatusUpdate(Event):
    __event_name__: str = "VOICE_CHANNEL_STATUS_UPDATE"

    raw: RawVoiceChannelStatusUpdateEvent
    channel: "VocalGuildChannel"
    old_status: str | None
    new_status: str | None

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        raw = RawVoiceChannelStatusUpdateEvent(data)
        guild = await state._get_guild(int(data["guild_id"]))
        channel_id = int(data["id"])

        if guild is None:
            _log.debug(
                "VOICE_CHANNEL_STATUS_UPDATE referencing unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        channel = guild.get_channel(channel_id)
        if channel is None:
            _log.debug(
                "VOICE_CHANNEL_STATUS_UPDATE referencing an unknown channel ID: %s. Discarding.",
                channel_id,
            )
            return

        old_status = channel.status
        channel.status = data.get("status", None)

        self = cls()
        self.raw = raw
        self.channel = channel  # type: ignore
        self.old_status = old_status
        self.new_status = channel.status
        return self
