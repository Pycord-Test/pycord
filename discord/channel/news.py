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

from ..enums import ChannelType
from ..utils import MISSING, Undefined
from .base import GuildMessageableChannel, GuildThreadableChannel, GuildTopLevelChannel

if TYPE_CHECKING:
    from ..abc import Snowflake
    from ..member import Member
    from ..permissions import PermissionOverwrite
    from ..role import Role
    from ..types.channel import NewsChannel as NewsChannelPayload
    from ..types.channel import TextChannel as TextChannelPayload
    from .category import CategoryChannel
    from .text import TextChannel
    from .thread import Thread

__all__ = ("NewsChannel",)


class NewsChannel(
    GuildTopLevelChannel["NewsChannelPayload"],
    GuildMessageableChannel,
    GuildThreadableChannel,
):
    """Represents a Discord guild news/announcement channel.

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
    nsfw: :class:`bool`
        Whether the channel is marked as NSFW.
    slowmode_delay: :class:`int`
        The number of seconds a member must wait between sending messages
        in this channel. A value of `0` denotes that it is disabled.
    last_message_id: :class:`int` | None
        The last message ID of the message sent to this channel. It may
        *not* point to an existing or valid message.
    default_auto_archive_duration: :class:`int`
        The default auto archive duration in minutes for threads created in this channel.

    .. versionadded:: 3.0
    """

    __slots__: tuple[str, ...] = (
        "topic",
        "nsfw",
        "slowmode_delay",
        "last_message_id",
        "default_auto_archive_duration",
        "default_thread_slowmode_delay",
    )

    @property
    @override
    def _sorting_bucket(self) -> int:
        return ChannelType.news.value

    def __repr__(self) -> str:
        attrs = [
            ("id", self.id),
            ("name", self.name),
            ("position", self.position),
            ("nsfw", self.nsfw),
            ("category_id", self.category_id),
        ]
        joined = " ".join(f"{k}={v!r}" for k, v in attrs)
        return f"<NewsChannel {joined}>"

    async def edit(
        self,
        *,
        name: str | Undefined = MISSING,
        topic: str | Undefined = MISSING,
        position: int | Undefined = MISSING,
        nsfw: bool | Undefined = MISSING,
        sync_permissions: bool | Undefined = MISSING,
        category: CategoryChannel | None | Undefined = MISSING,
        slowmode_delay: int | Undefined = MISSING,
        default_auto_archive_duration: int | Undefined = MISSING,
        default_thread_slowmode_delay: int | Undefined = MISSING,
        type: ChannelType | Undefined = MISSING,
        overwrites: Mapping[Role | Member | Snowflake, PermissionOverwrite] | Undefined = MISSING,
        reason: str | None = None,
    ) -> Self | TextChannel:
        """|coro|

        Edits the channel.

        You must have :attr:`~Permissions.manage_channels` permission to use this.

        Parameters
        ----------
        name: :class:`str`
            The new channel name.
        topic: :class:`str`
            The new channel's topic.
        position: :class:`int`
            The new channel's position.
        nsfw: :class:`bool`
            Whether the channel is marked as NSFW.
        sync_permissions: :class:`bool`
            Whether to sync permissions with the channel's new or pre-existing category.
        category: :class:`CategoryChannel` | None
            The new category for this channel. Can be ``None`` to remove the category.
        slowmode_delay: :class:`int`
            Specifies the slowmode rate limit for user in this channel, in seconds.
        default_auto_archive_duration: :class:`int`
            The new default auto archive duration in minutes for threads created in this channel.
        default_thread_slowmode_delay: :class:`int`
            The new default slowmode delay in seconds for threads created in this channel.
        type: :class:`ChannelType`
            Change the type of this news channel. Only conversion between text and news is supported.
        overwrites: Mapping[:class:`Role` | :class:`Member` | :class:`~discord.abc.Snowflake`, :class:`PermissionOverwrite`]
            The overwrites to apply to channel permissions.
        reason: :class:`str` | None
            The reason for editing this channel. Shows up on the audit log.

        Returns
        -------
        :class:`.NewsChannel` | :class:`.TextChannel`
            The newly edited channel. If type was changed, the appropriate channel type is returned.

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
        if nsfw is not MISSING:
            options["nsfw"] = nsfw
        if sync_permissions is not MISSING:
            options["sync_permissions"] = sync_permissions
        if category is not MISSING:
            options["category"] = category
        if slowmode_delay is not MISSING:
            options["slowmode_delay"] = slowmode_delay
        if default_auto_archive_duration is not MISSING:
            options["default_auto_archive_duration"] = default_auto_archive_duration
        if default_thread_slowmode_delay is not MISSING:
            options["default_thread_slowmode_delay"] = default_thread_slowmode_delay
        if type is not MISSING:
            options["type"] = type
        if overwrites is not MISSING:
            options["overwrites"] = overwrites

        payload = await self._edit(options, reason=reason)
        if payload is not None:
            if payload.get("type") == ChannelType.text.value:
                from .text import TextChannel

                return await TextChannel._from_data(data=payload, state=self._state, guild=self.guild)  # type: ignore
            return await self.__class__._from_data(data=payload, state=self._state, guild=self.guild)  # type: ignore

    async def create_thread(
        self,
        *,
        name: str,
        message: Snowflake | None = None,
        auto_archive_duration: int | Undefined = MISSING,
        type: ChannelType | None = None,
        slowmode_delay: int | None = None,
        invitable: bool | None = None,
        reason: str | None = None,
    ) -> Thread:
        """|coro|

        Creates a thread in this news channel.

        Parameters
        ----------
        name: :class:`str`
            The name of the thread.
        message: :class:`abc.Snowflake` | None
            A snowflake representing the message to create the thread with.
        auto_archive_duration: :class:`int`
            The duration in minutes before a thread is automatically archived for inactivity.
        type: :class:`ChannelType` | None
            The type of thread to create.
        slowmode_delay: :class:`int` | None
            Specifies the slowmode rate limit for users in this thread, in seconds.
        invitable: :class:`bool` | None
            Whether non-moderators can add other non-moderators to this thread.
        reason: :class:`str` | None
            The reason for creating a new thread.

        Returns
        -------
        :class:`Thread`
            The created thread
        """
        from .thread import Thread

        if type is None:
            type = ChannelType.private_thread

        if message is None:
            data = await self._state.http.start_thread_without_message(
                self.id,
                name=name,
                auto_archive_duration=auto_archive_duration or self.default_auto_archive_duration,
                type=type.value,
                rate_limit_per_user=slowmode_delay or 0,
                invitable=invitable,
                reason=reason,
            )
        else:
            data = await self._state.http.start_thread_with_message(
                self.id,
                message.id,
                name=name,
                auto_archive_duration=auto_archive_duration or self.default_auto_archive_duration,
                rate_limit_per_user=slowmode_delay or 0,
                reason=reason,
            )

        return Thread(guild=self.guild, state=self._state, data=data)
