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
from discord.enums import VoiceChannelEffectAnimationType, try_enum
from discord.member import Member, VoiceState
from discord.raw_models import RawVoiceChannelStatusUpdateEvent
from discord.utils.private import get_as_snowflake

if TYPE_CHECKING:
    from discord.emoji import PartialEmoji
    from discord.guild import Guild
    from discord.soundboard import PartialSoundboardSound, SoundboardSound

    from ..channel import VoiceChannel
    from ..types.channel import VoiceChannelEffectSendEvent as VoiceChannelEffectSendEventPayload

_log = logging.getLogger(__name__)


async def logging_coroutine(coroutine, *, info: str) -> None:
    """Helper to log exceptions in coroutines."""
    try:
        await coroutine
    except Exception:
        _log.exception("Exception occurred during %s", info)


class VoiceStateUpdate(Event):
    """Called when a member changes their voice state.

    The following, but not limited to, examples illustrate when this event is called:
    - A member joins a voice or stage channel.
    - A member leaves a voice or stage channel.
    - A member is muted or deafened by their own accord.
    - A member is muted or deafened by a guild administrator.

    This requires :attr:`Intents.voice_states` to be enabled.

    Attributes
    ----------
    member: :class:`Member`
        The member whose voice states changed.
    before: :class:`VoiceState`
        The voice state prior to the changes.
    after: :class:`VoiceState`
        The voice state after the changes.
    """

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
    """Called when the voice server is updated.

    .. note::
        This is an internal event used by the voice protocol.
        It is not dispatched to user code.
    """

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
    """Called when someone updates a voice channel status.

    Attributes
    ----------
    raw: :class:`RawVoiceChannelStatusUpdateEvent`
        The raw voice channel status update payload.
    channel: :class:`VoiceChannel` | :class:`StageChannel`
        The channel where the voice channel status update originated from.
    old_status: :class:`str` | None
        The old voice channel status.
    new_status: :class:`str` | None
        The new voice channel status.
    """

    __event_name__: str = "VOICE_CHANNEL_STATUS_UPDATE"

    raw: RawVoiceChannelStatusUpdateEvent
    channel: "VoiceChannel"
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


class VoiceChannelEffectSend(Event):
    """Called when a voice channel effect is sent.

    Attributes
    ----------
    animation_type: :class:`VoiceChannelEffectAnimationType`
        The type of animation that is being sent.
    animation_id: :class:`int`
        The ID of the animation that is being sent.
    sound: :class:`SoundboardSound` | :class:`PartialSoundboardSound` | None
        The sound that is being sent, could be ``None`` if the effect is not a sound effect.
    guild: :class:`Guild`
        The guild in which the sound is being sent.
    user: :class:`Member`
        The member that sent the sound.
    channel: :class:`VoiceChannel` | :class:`StageChannel`
        The voice channel in which the sound is being sent.
    emoji: :class:`PartialEmoji` | None
        The emoji associated with the effect, if any.
    """

    __event_name__: str = "VOICE_CHANNEL_EFFECT_SEND"

    def __init__(
        self,
        *,
        animation_type: VoiceChannelEffectAnimationType,
        animation_id: int,
        sound: "SoundboardSound | PartialSoundboardSound | None",
        guild: "Guild",
        user: Member,
        channel: "VoiceChannel",
        emoji: "PartialEmoji | None",
    ) -> None:
        self.animation_type = animation_type
        self.animation_id = animation_id
        self.sound = sound
        self.guild = guild
        self.user = user
        self.channel = channel
        self.emoji = emoji

    @classmethod
    @override
    async def __load__(cls, data: "VoiceChannelEffectSendEventPayload", state: ConnectionState) -> Self | None:
        from discord.emoji import PartialEmoji
        from discord.soundboard import PartialSoundboardSound

        channel_id = int(data["channel_id"])
        user_id = int(data["user_id"])
        guild_id = int(data["guild_id"])

        guild = await state._get_guild(guild_id)
        if guild is None:
            _log.debug(
                "VOICE_CHANNEL_EFFECT_SEND referencing unknown guild ID: %s. Discarding.",
                guild_id,
            )
            return

        channel = guild.get_channel(channel_id)
        if channel is None:
            _log.debug(
                "VOICE_CHANNEL_EFFECT_SEND referencing an unknown channel ID: %s. Discarding.",
                channel_id,
            )
            return

        user = guild.get_member(user_id)
        if user is None:
            _log.debug(
                "VOICE_CHANNEL_EFFECT_SEND referencing an unknown user ID: %s. Discarding.",
                user_id,
            )
            return

        # Create sound if present
        sound = None
        if data.get("sound_id"):
            sound = PartialSoundboardSound(data, state, state.http)

        # Create emoji if present
        emoji = None
        if raw_emoji := data.get("emoji"):
            emoji = PartialEmoji(
                name=raw_emoji.get("name"),
                animated=raw_emoji.get("animated", False),
                id=int(raw_emoji["id"]) if raw_emoji.get("id") else None,
            )

        return cls(
            animation_type=try_enum(VoiceChannelEffectAnimationType, data["animation_type"]),
            animation_id=int(data["animation_id"]),
            sound=sound,
            guild=guild,
            user=user,
            channel=channel,  # type: ignore
            emoji=emoji,
        )
