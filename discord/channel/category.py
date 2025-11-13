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

from typing import TYPE_CHECKING, Any, overload

from typing_extensions import override

if TYPE_CHECKING:
    from collections.abc import Mapping

    from ..app.state import ConnectionState
    from ..guild import Guild
    from ..member import Member
    from ..permissions import PermissionOverwrite
    from ..role import Role
    from . import ForumChannel, StageChannel, TextChannel, VoiceChannel

from ..enums import ChannelType, try_enum
from ..flags import ChannelFlags
from ..types.channel import CategoryChannel as CategoryChannelPayload
from ..utils.private import copy_doc
from .base import GuildChannel, GuildTopLevelChannel


def comparator(channel: GuildChannel):
    # Sorts channels so voice channels (VoiceChannel, StageChannel) appear below non-voice channels
    return isinstance(channel, (VoiceChannel, StageChannel)), (channel.position or -1)


class CategoryChannel(GuildTopLevelChannel[CategoryChannelPayload]):
    """Represents a Discord channel category.

    These are useful to group channels to logical compartments.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the category's hash.

        .. describe:: str(x)

            Returns the category's name.

    Attributes
    ----------
    name: str
        The category name.
    guild: Guild
        The guild the category belongs to.
    id: int
        The category channel ID.
    position: int
        The position in the category list. This is a number that starts at 0. e.g. the
        top category is position 0.
    flags: ChannelFlags
        Extra features of the channel.

        .. versionadded:: 2.0
    """

    __slots__: tuple[str, ...] = ()

    @override
    def __repr__(self) -> str:
        return f"<CategoryChannel id={self.id} name={self.name!r} position={self.position}>"

    @property
    @override
    def _sorting_bucket(self) -> int:
        return ChannelType.category.value

    @property
    def type(self) -> ChannelType:
        """The channel's Discord type."""
        return try_enum(ChannelType, self._type)

    @copy_doc(GuildChannel.clone)
    async def clone(self, *, name: str | None = None, reason: str | None = None) -> CategoryChannel:
        return await self._clone_impl({}, name=name, reason=reason)

    @overload
    async def edit(
        self,
        *,
        name: str = ...,
        position: int = ...,
        overwrites: Mapping[Role | Member, PermissionOverwrite] = ...,
        reason: str | None = ...,
    ) -> CategoryChannel | None: ...

    @overload
    async def edit(self) -> CategoryChannel | None: ...

    async def edit(self, *, reason=None, **options):
        """|coro|

        Edits the channel.

        You must have the :attr:`~Permissions.manage_channels` permission to
        use this.

        .. versionchanged:: 1.3
            The ``overwrites`` keyword-only parameter was added.

        .. versionchanged:: 2.0
            Edits are no longer in-place, the newly edited channel is returned instead.

        Parameters
        ----------
        name: :class:`str`
            The new category's name.
        position: :class:`int`
            The new category's position.
        reason: Optional[:class:`str`]
            The reason for editing this category. Shows up on the audit log.
        overwrites: Dict[Union[:class:`Role`, :class:`Member`, :class:`~discord.abc.Snowflake`], :class:`PermissionOverwrite`]
            The overwrites to apply to channel permissions. Useful for creating secret channels.

        Returns
        -------
        Optional[:class:`.CategoryChannel`]
            The newly edited category channel. If the edit was only positional
            then ``None`` is returned instead.

        Raises
        ------
        InvalidArgument
            If position is less than 0 or greater than the number of categories.
        Forbidden
            You do not have permissions to edit the category.
        HTTPException
            Editing the category failed.
        """

        payload = await self._edit(options, reason=reason)
        if payload is not None:
            # the payload will always be the proper channel payload
            return await self.__class__._from_data(data=payload, state=self._state, guild=self.guild)  # type: ignore

    @copy_doc(GuildTopLevelChannel.move)
    async def move(self, **kwargs):
        kwargs.pop("category", None)
        await super().move(**kwargs)

    @property
    def channels(self) -> list[GuildTopLevelChannel]:
        """Returns the channels that are under this category.

        These are sorted by the official Discord UI, which places voice channels below the text channels.
        """

        ret = [c for c in self.guild.channels if c.category_id == self.id]
        ret.sort(key=comparator)
        return ret

    @property
    def text_channels(self) -> list[TextChannel]:
        """Returns the text channels that are under this category."""
        ret = [c for c in self.guild.channels if c.category_id == self.id and isinstance(c, TextChannel)]
        ret.sort(key=lambda c: (c.position or -1, c.id))
        return ret

    @property
    def voice_channels(self) -> list[VoiceChannel]:
        """Returns the voice channels that are under this category."""
        ret = [c for c in self.guild.channels if c.category_id == self.id and isinstance(c, VoiceChannel)]
        ret.sort(key=lambda c: (c.position or -1, c.id))
        return ret

    @property
    def stage_channels(self) -> list[StageChannel]:
        """Returns the stage channels that are under this category.

        .. versionadded:: 1.7
        """
        ret = [c for c in self.guild.channels if c.category_id == self.id and isinstance(c, StageChannel)]
        ret.sort(key=lambda c: (c.position or -1, c.id))
        return ret

    @property
    def forum_channels(self) -> list[ForumChannel]:
        """Returns the forum channels that are under this category.

        .. versionadded:: 2.0
        """
        ret = [c for c in self.guild.channels if c.category_id == self.id and isinstance(c, ForumChannel)]
        ret.sort(key=lambda c: (c.position or -1, c.id))
        return ret

    async def create_text_channel(self, name: str, **options: Any) -> TextChannel:
        """|coro|

        A shortcut method to :meth:`Guild.create_text_channel` to create a :class:`TextChannel` in the category.

        Returns
        -------
        :class:`TextChannel`
            The channel that was just created.
        """
        return await self.guild.create_text_channel(name, category=self, **options)

    async def create_voice_channel(self, name: str, **options: Any) -> VoiceChannel:
        """|coro|

        A shortcut method to :meth:`Guild.create_voice_channel` to create a :class:`VoiceChannel` in the category.

        Returns
        -------
        :class:`VoiceChannel`
            The channel that was just created.
        """
        return await self.guild.create_voice_channel(name, category=self, **options)

    async def create_stage_channel(self, name: str, **options: Any) -> StageChannel:
        """|coro|

        A shortcut method to :meth:`Guild.create_stage_channel` to create a :class:`StageChannel` in the category.

        .. versionadded:: 1.7

        Returns
        -------
        :class:`StageChannel`
            The channel that was just created.
        """
        return await self.guild.create_stage_channel(name, category=self, **options)

    async def create_forum_channel(self, name: str, **options: Any) -> ForumChannel:
        """|coro|

        A shortcut method to :meth:`Guild.create_forum_channel` to create a :class:`ForumChannel` in the category.

        .. versionadded:: 2.0

        Returns
        -------
        :class:`ForumChannel`
            The channel that was just created.
        """
        return await self.guild.create_forum_channel(name, category=self, **options)
