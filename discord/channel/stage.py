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
from ..enums import ChannelType, StagePrivacyLevel, VideoQualityMode, VoiceRegion, try_enum
from ..utils import MISSING, Undefined
from .base import GuildMessageableChannel, GuildTopLevelChannel

if TYPE_CHECKING:
    from ..abc import Snowflake
    from ..member import Member
    from ..permissions import PermissionOverwrite
    from ..role import Role
    from ..stage_instance import StageInstance
    from ..types.channel import StageChannel as StageChannelPayload
    from .category import CategoryChannel

__all__ = ("StageChannel",)


class StageChannel(
    GuildTopLevelChannel["StageChannelPayload"],
    GuildMessageableChannel,
    Connectable,
):
    """Represents a Discord guild stage channel.

    .. versionadded:: 1.7

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
    topic: :class:`str` | None
        The channel's topic. ``None`` if it isn't set.
    category_id: :class:`int` | None
        The category channel ID this channel belongs to, if applicable.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0.
    bitrate: :class:`int`
        The channel's preferred audio bitrate in bits per second.
    user_limit: :class:`int`
        The channel's limit for number of members that can be in a stage channel.
        A value of ``0`` indicates no limit.
    rtc_region: :class:`VoiceRegion` | None
        The region for the stage channel's voice communication.
        A value of ``None`` indicates automatic voice region detection.
    video_quality_mode: :class:`VideoQualityMode`
        The camera video quality for the stage channel's participants.
    last_message_id: :class:`int` | None
        The ID of the last message sent to this channel. It may not always point to an existing or valid message.
    slowmode_delay: :class:`int`
        Specifies the slowmode rate limit for users in this channel, in seconds.
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
    )

    @override
    async def _update(self, data: StageChannelPayload) -> None:
        await super()._update(data)
        self.bitrate: int = data.get("bitrate", 64000)
        self.user_limit: int = data.get("user_limit", 0)
        rtc = data.get("rtc_region")
        self.rtc_region: VoiceRegion | None = try_enum(VoiceRegion, rtc) if rtc is not None else None
        self.video_quality_mode: VideoQualityMode = try_enum(VideoQualityMode, data.get("video_quality_mode", 1))

    @property
    @override
    def _sorting_bucket(self) -> int:
        return ChannelType.stage_voice.value

    @property
    def requesting_to_speak(self) -> list[Member]:
        """A list of members who are requesting to speak in the stage channel."""
        return [member for member in self.members if member.voice and member.voice.requested_to_speak_at is not None]

    @property
    def speakers(self) -> list[Member]:
        """A list of members who have been permitted to speak in the stage channel.

        .. versionadded:: 2.0
        """
        return [member for member in self.members if member.voice and not member.voice.suppress]

    @property
    def listeners(self) -> list[Member]:
        """A list of members who are listening in the stage channel.

        .. versionadded:: 2.0
        """
        return [member for member in self.members if member.voice and member.voice.suppress]

    def __repr__(self) -> str:
        attrs = [
            ("id", self.id),
            ("name", self.name),
            ("topic", self.topic),
            ("rtc_region", self.rtc_region),
            ("position", self.position),
            ("bitrate", self.bitrate),
            ("video_quality_mode", self.video_quality_mode),
            ("user_limit", self.user_limit),
            ("category_id", self.category_id),
        ]
        joined = " ".join(f"{k}={v!r}" for k, v in attrs)
        return f"<StageChannel {joined}>"

    @property
    def instance(self) -> StageInstance | None:
        """Returns the currently running stage instance if any.

        .. versionadded:: 2.0

        Returns
        -------
        :class:`StageInstance` | None
            The stage instance or ``None`` if not active.
        """
        return self.guild.get_stage_instance(self.id)

    @property
    def moderators(self) -> list[Member]:
        """Returns a list of members who have stage moderator permissions.

        .. versionadded:: 2.0

        Returns
        -------
        list[:class:`Member`]
            The members with stage moderator permissions.
        """
        from ..permissions import Permissions

        required = Permissions.stage_moderator()
        return [m for m in self.members if (self.permissions_for(m) & required) == required]

    async def edit(
        self,
        *,
        name: str | Undefined = MISSING,
        topic: str | Undefined = MISSING,
        position: int | Undefined = MISSING,
        sync_permissions: bool | Undefined = MISSING,
        category: CategoryChannel | None | Undefined = MISSING,
        overwrites: Mapping[Role | Member | Snowflake, PermissionOverwrite] | Undefined = MISSING,
        rtc_region: VoiceRegion | None | Undefined = MISSING,
        video_quality_mode: VideoQualityMode | Undefined = MISSING,
        reason: str | None = None,
    ) -> Self:
        """|coro|

        Edits the stage channel.

        You must have :attr:`~Permissions.manage_channels` permission to use this.

        Parameters
        ----------
        name: :class:`str`
            The new channel's name.
        topic: :class:`str`
            The new channel's topic.
        position: :class:`int`
            The new channel's position.
        sync_permissions: :class:`bool`
            Whether to sync permissions with the channel's new or pre-existing category.
        category: :class:`CategoryChannel` | None
            The new category for this channel. Can be ``None`` to remove the category.
        overwrites: Mapping[:class:`Role` | :class:`Member` | :class:`~discord.abc.Snowflake`, :class:`PermissionOverwrite`]
            The overwrites to apply to channel permissions.
        rtc_region: :class:`VoiceRegion` | None
            The new region for the stage channel's voice communication.
        video_quality_mode: :class:`VideoQualityMode`
            The camera video quality for the stage channel's participants.
        reason: :class:`str` | None
            The reason for editing this channel. Shows up on the audit log.

        Returns
        -------
        :class:`.StageChannel`
            The newly edited stage channel.

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
        if topic is not MISSING:
            options["topic"] = topic
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

        payload = await self._edit(options, reason=reason)
        if payload is not None:
            return await self.__class__._from_data(data=payload, state=self._state, guild=self.guild)  # type: ignore

    async def create_instance(
        self,
        *,
        topic: str,
        privacy_level: StagePrivacyLevel = StagePrivacyLevel.guild_only,
        reason: str | None = None,
        send_notification: bool = False,
    ) -> StageInstance:
        """|coro|

        Creates a stage instance.

        You must have :attr:`~Permissions.manage_channels` permission to do this.

        Parameters
        ----------
        topic: :class:`str`
            The stage instance's topic.
        privacy_level: :class:`StagePrivacyLevel`
            The stage instance's privacy level.
        send_notification: :class:`bool`
            Whether to send a notification to everyone in the server that the stage is starting.
        reason: :class:`str` | None
            The reason for creating the stage instance. Shows up on the audit log.

        Returns
        -------
        :class:`StageInstance`
            The created stage instance.

        Raises
        ------
        Forbidden
            You do not have permissions to create a stage instance.
        HTTPException
            Creating the stage instance failed.
        """
        from ..stage_instance import StageInstance

        payload = await self._state.http.create_stage_instance(
            self.id,
            topic=topic,
            privacy_level=int(privacy_level),
            send_start_notification=send_notification,
            reason=reason,
        )
        return StageInstance(guild=self.guild, state=self._state, data=payload)

    async def fetch_instance(self) -> StageInstance | None:
        """|coro|

        Fetches the currently running stage instance.

        Returns
        -------
        :class:`StageInstance` | None
            The stage instance or ``None`` if not active.

        Raises
        ------
        NotFound
            The stage instance is not active or was deleted.
        HTTPException
            Fetching the stage instance failed.
        """
        from ..stage_instance import StageInstance

        try:
            payload = await self._state.http.get_stage_instance(self.id)
            return StageInstance(guild=self.guild, state=self._state, data=payload)
        except Exception:
            return None
