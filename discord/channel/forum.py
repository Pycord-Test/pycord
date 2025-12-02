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

from typing import TYPE_CHECKING, Mapping, overload

from typing_extensions import Self, override

from ..enums import ChannelType, SortOrder
from ..flags import ChannelFlags
from ..utils import MISSING, Undefined
from .base import GuildPostableChannel

if TYPE_CHECKING:
    from ..abc import Snowflake
    from ..emoji import GuildEmoji
    from ..member import Member
    from ..permissions import PermissionOverwrite
    from ..role import Role
    from ..types.channel import ForumChannel as ForumChannelPayload
    from .category import CategoryChannel
    from .channel import ForumTag

__all__ = ("ForumChannel",)


class ForumChannel(GuildPostableChannel["ForumChannelPayload"]):
    """Represents a Discord forum channel.

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
        The channel's topic/guidelines. ``None`` if it doesn't exist.
    category_id: :class:`int` | None
        The category channel ID this channel belongs to, if applicable.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0.
    nsfw: :class:`bool`
        Whether the channel is marked as NSFW.
    slowmode_delay: :class:`int`
        The number of seconds a member must wait between creating posts
        in this channel. A value of `0` denotes that it is disabled.
    last_message_id: :class:`int` | None
        The last message ID sent to this channel. It may not point to an existing or valid message.
    default_auto_archive_duration: :class:`int`
        The default auto archive duration in minutes for posts created in this channel.
    default_thread_slowmode_delay: :class:`int` | None
        The initial slowmode delay to set on newly created posts in this channel.
    available_tags: list[:class:`ForumTag`]
        The set of tags that can be used in this forum channel.
    default_sort_order: :class:`SortOrder` | None
        The default sort order type used to order posts in this channel.
    default_reaction_emoji: :class:`str` | :class:`GuildEmoji` | None
        The default forum reaction emoji.

    .. versionadded:: 3.0
    """

    __slots__: tuple[str, ...] = ()

    @property
    @override
    def _sorting_bucket(self) -> int:
        return ChannelType.forum.value

    def __repr__(self) -> str:
        attrs = [
            ("id", self.id),
            ("name", self.name),
            ("position", self.position),
            ("nsfw", self.nsfw),
            ("category_id", self.category_id),
        ]
        joined = " ".join(f"{k}={v!r}" for k, v in attrs)
        return f"<ForumChannel {joined}>"

    @overload
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
        default_sort_order: SortOrder | Undefined = MISSING,
        default_reaction_emoji: GuildEmoji | int | str | None | Undefined = MISSING,
        available_tags: list[ForumTag] | Undefined = MISSING,
        require_tag: bool | Undefined = MISSING,
        overwrites: Mapping[Role | Member | Snowflake, PermissionOverwrite] | Undefined = MISSING,
        reason: str | None = None,
    ) -> Self: ...

    @overload
    async def edit(self) -> Self: ...

    async def edit(self, *, reason: str | None = None, **options) -> Self:
        """|coro|

        Edits the forum channel.

        You must have :attr:`~Permissions.manage_channels` permission to use this.

        Parameters
        ----------
        name: :class:`str`
            The new channel name.
        topic: :class:`str`
            The new channel's topic/guidelines.
        position: :class:`int`
            The new channel's position.
        nsfw: :class:`bool`
            Whether the channel should be marked as NSFW.
        sync_permissions: :class:`bool`
            Whether to sync permissions with the channel's new or pre-existing category.
        category: :class:`CategoryChannel` | None
            The new category for this channel. Can be ``None`` to remove the category.
        slowmode_delay: :class:`int`
            Specifies the slowmode rate limit for users in this channel, in seconds.
            A value of ``0`` disables slowmode. The maximum value possible is ``21600``.
        default_auto_archive_duration: :class:`int`
            The new default auto archive duration in minutes for posts created in this channel.
            Must be one of ``60``, ``1440``, ``4320``, or ``10080``.
        default_thread_slowmode_delay: :class:`int`
            The new default slowmode delay in seconds for posts created in this channel.
        default_sort_order: :class:`SortOrder`
            The default sort order type to use to order posts in this channel.
        default_reaction_emoji: :class:`GuildEmoji` | :class:`int` | :class:`str` | None
            The default reaction emoji for posts.
            Can be a unicode emoji or a custom emoji.
        available_tags: list[:class:`ForumTag`]
            The set of tags that can be used in this channel. Must be less than ``20``.
        require_tag: :class:`bool`
            Whether a tag should be required to be specified when creating a post in this channel.
        overwrites: Mapping[:class:`Role` | :class:`Member` | :class:`~discord.abc.Snowflake`, :class:`PermissionOverwrite`]
            The overwrites to apply to channel permissions.
        reason: :class:`str` | None
            The reason for editing this channel. Shows up on the audit log.

        Returns
        -------
        :class:`.ForumChannel`
            The newly edited forum channel.

        Raises
        ------
        Forbidden
            You do not have permissions to edit the channel.
        HTTPException
            Editing the channel failed.
        """
        if "require_tag" in options:
            options["flags"] = ChannelFlags._from_value(self.flags.value)
            options["flags"].require_tag = options.pop("require_tag")

        payload = await self._edit(options, reason=reason)
        if payload is not None:
            return await self.__class__._from_data(data=payload, state=self._state, guild=self.guild)  # type: ignore
        return self
