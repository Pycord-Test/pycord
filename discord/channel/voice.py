"""
The MIT License (MIT)

Copyright (c) 2015-2021 Rapptz
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

from __future__ import annotations

from typing import TYPE_CHECKING, Mapping

from typing_extensions import Self, override

from ..abc import Connectable
from ..enums import ChannelType, InviteTarget, VideoQualityMode, VoiceRegion, try_enum
from ..utils import MISSING, Undefined
from .base import GuildMessageableChannel, GuildTopLevelChannel

if TYPE_CHECKING:
    from ..abc import Snowflake
    from ..enums import EmbeddedActivity
    from ..invite import Invite
    from ..member import Member
    from ..permissions import PermissionOverwrite
    from ..role import Role
    from ..soundboard import PartialSoundboardSound
    from ..types.channel import VoiceChannel as VoiceChannelPayload
    from .category import CategoryChannel

__all__ = ("VoiceChannel",)


class VoiceChannel(
    GuildTopLevelChannel["VoiceChannelPayload"],
    GuildMessageableChannel,
    Connectable,
):
    """Represents a Discord guild voice channel.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns the channel's name.

    Attributes
    ----------
    id: :class:`int`
        The channel's ID.
    name: :class:`str`
        The channel's name.
    guild: :class:`Guild`
        The guild the channel belongs to.
    category_id: :class:`int` | None
        The category channel ID this channel belongs to, if applicable.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0.
    bitrate: :class:`int`
        The channel's preferred audio bitrate in bits per second.
    user_limit: :class:`int`
        The channel's limit for number of members that can be in a voice channel.
        A value of ``0`` indicates no limit.
    rtc_region: :class:`VoiceRegion` | None
        The region for the voice channel's voice communication.
        A value of ``None`` indicates automatic voice region detection.
    video_quality_mode: :class:`VideoQualityMode`
        The camera video quality for the voice channel's participants.
    last_message_id: :class:`int` | None
        The ID of the last message sent to this channel. It may not always point to an existing or valid message.
    slowmode_delay: :class:`int`
        The number of seconds a member must wait between sending messages
        in this channel. A value of `0` denotes that it is disabled.
    status: :class:`str` | None
        The channel's status, if set.
    nsfw: :class:`bool`
        Whether the channel is marked as NSFW.

    .. versionadded:: 3.0
    """

    __slots__: tuple[str, ...] = (
        "topic",
        "nsfw",
        "slowmode_delay",
        "last_message_id",
        "bitrate",
        "user_limit",
        "rtc_region",
        "video_quality_mode",
        "status",
    )

    @override
    async def _update(self, data: VoiceChannelPayload) -> None:
        await super()._update(data)
        self.bitrate: int = data.get("bitrate", 64000)
        self.user_limit: int = data.get("user_limit", 0)
        rtc = data.get("rtc_region")
        self.rtc_region: VoiceRegion | None = try_enum(VoiceRegion, rtc) if rtc is not None else None
        self.video_quality_mode: VideoQualityMode = try_enum(VideoQualityMode, data.get("video_quality_mode", 1))
        self.status: str | None = data.get("status")

    @property
    @override
    def _sorting_bucket(self) -> int:
        return ChannelType.voice.value

    def __repr__(self) -> str:
        attrs = [
            ("id", self.id),
            ("name", self.name),
            ("status", self.status),
            ("rtc_region", self.rtc_region),
            ("position", self.position),
            ("bitrate", self.bitrate),
            ("video_quality_mode", self.video_quality_mode),
            ("user_limit", self.user_limit),
            ("category_id", self.category_id),
        ]
        joined = " ".join(f"{k}={v!r}" for k, v in attrs)
        return f"<VoiceChannel {joined}>"

    async def edit(
        self,
        *,
        name: str | Undefined = MISSING,
        bitrate: int | Undefined = MISSING,
        user_limit: int | Undefined = MISSING,
        position: int | Undefined = MISSING,
        sync_permissions: bool | Undefined = MISSING,
        category: CategoryChannel | None | Undefined = MISSING,
        overwrites: Mapping[Role | Member | Snowflake, PermissionOverwrite] | Undefined = MISSING,
        rtc_region: VoiceRegion | None | Undefined = MISSING,
        video_quality_mode: VideoQualityMode | Undefined = MISSING,
        slowmode_delay: int | Undefined = MISSING,
        nsfw: bool | Undefined = MISSING,
        reason: str | None = None,
    ) -> Self:
        """|coro|

        Edits the voice channel.

        You must have :attr:`~Permissions.manage_channels` permission to use this.

        Parameters
        ----------
        name: :class:`str`
            The new channel's name.
        bitrate: :class:`int`
            The new channel's bitrate.
        user_limit: :class:`int`
            The new channel's user limit.
        position: :class:`int`
            The new channel's position.
        sync_permissions: :class:`bool`
            Whether to sync permissions with the channel's new or pre-existing category.
        category: :class:`CategoryChannel` | None
            The new category for this channel. Can be ``None`` to remove the category.
        overwrites: Mapping[:class:`Role` | :class:`Member` | :class:`~discord.abc.Snowflake`, :class:`PermissionOverwrite`]
            The overwrites to apply to channel permissions.
        rtc_region: :class:`VoiceRegion` | None
            The new region for the voice channel's voice communication.
            A value of ``None`` indicates automatic voice region detection.
        video_quality_mode: :class:`VideoQualityMode`
            The camera video quality for the voice channel's participants.
        slowmode_delay: :class:`int`
            Specifies the slowmode rate limit for user in this channel, in seconds.
        nsfw: :class:`bool`
            Whether the channel is marked as NSFW.
        reason: :class:`str` | None
            The reason for editing this channel. Shows up on the audit log.

        Returns
        -------
        :class:`.VoiceChannel`
            The newly edited voice channel. If the edit was only positional then ``None`` is returned.

        Raises
        ------
        Forbidden
            You do not have permissions to edit the channel.
        HTTPException
            Editing the channel failed.
        """
        options = {}
        if name is not MISSING:
            options["name"] = name
        if bitrate is not MISSING:
            options["bitrate"] = bitrate
        if user_limit is not MISSING:
            options["user_limit"] = user_limit
        if position is not MISSING:
            options["position"] = position
        if sync_permissions is not MISSING:
            options["sync_permissions"] = sync_permissions
        if category is not MISSING:
            options["category"] = category
        if overwrites is not MISSING:
            options["overwrites"] = overwrites
        if rtc_region is not MISSING:
            options["rtc_region"] = rtc_region
        if video_quality_mode is not MISSING:
            options["video_quality_mode"] = video_quality_mode
        if slowmode_delay is not MISSING:
            options["slowmode_delay"] = slowmode_delay
        if nsfw is not MISSING:
            options["nsfw"] = nsfw

        payload = await self._edit(options, reason=reason)
        if payload is not None:
            return await self.__class__._from_data(data=payload, state=self._state, guild=self.guild)  # type: ignore

    async def create_activity_invite(self, activity: EmbeddedActivity | int, **kwargs) -> Invite:
        """|coro|

        A shortcut method that creates an instant activity invite.

        You must have :attr:`~discord.Permissions.start_embedded_activities` permission to do this.

        Parameters
        ----------
        activity: :class:`EmbeddedActivity` | :class:`int`
            The embedded activity to create an invite for. Can be an :class:`EmbeddedActivity` enum member
            or the application ID as an integer.
        max_age: :class:`int`
            How long the invite should last in seconds. If it's 0 then the invite doesn't expire.
        max_uses: :class:`int`
            How many uses the invite could be used for. If it's 0 then there are unlimited uses.
        temporary: :class:`bool`
            Denotes that the invite grants temporary membership.
        unique: :class:`bool`
            Indicates if a unique invite URL should be created.
        reason: :class:`str` | None
            The reason for creating this invite. Shows up on the audit log.

        Returns
        -------
        :class:`~discord.Invite`
            The invite that was created.

        Raises
        ------
        HTTPException
            Invite creation failed.
        """
        from ..enums import EmbeddedActivity

        if isinstance(activity, EmbeddedActivity):
            activity = activity.value

        return await self.create_invite(
            target_type=InviteTarget.embedded_application,
            target_application_id=activity,
            **kwargs,
        )

    async def set_status(self, status: str | None, *, reason: str | None = None) -> None:
        """|coro|

        Sets the voice channel status.

        You must have :attr:`~discord.Permissions.manage_channels` and
        :attr:`~discord.Permissions.connect` permissions to do this.

        Parameters
        ----------
        status: :class:`str` | None
            The new voice channel status. Set to ``None`` to remove the status.
        reason: :class:`str` | None
            The reason for setting the voice channel status. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You do not have permissions to set the voice channel status.
        HTTPException
            Setting the voice channel status failed.
        """
        await self._state.http.edit_voice_channel_status(self.id, status, reason=reason)

    async def send_soundboard_sound(self, sound: PartialSoundboardSound) -> None:
        """|coro|

        Sends a soundboard sound to the voice channel.

        Parameters
        ----------
        sound: :class:`PartialSoundboardSound`
            The soundboard sound to send.

        Raises
        ------
        Forbidden
            You do not have proper permissions to send the soundboard sound.
        HTTPException
            Sending the soundboard sound failed.
        """
        await self._state.http.send_soundboard_sound(self.id, sound)
