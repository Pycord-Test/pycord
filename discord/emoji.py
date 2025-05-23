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

from typing import TYPE_CHECKING, Any, Iterator

from .asset import Asset, AssetMixin
from .partial_emoji import PartialEmoji, _EmojiTag
from .user import User
from .utils import MISSING, SnowflakeList, Undefined, snowflake_time

__all__ = (
    "Emoji",
    "GuildEmoji",
    "AppEmoji",
)

if TYPE_CHECKING:
    from datetime import datetime

    from .abc import Snowflake
    from .guild import Guild
    from .role import Role
    from .state import ConnectionState
    from .types.emoji import Emoji as EmojiPayload


class BaseEmoji(_EmojiTag, AssetMixin):

    __slots__: tuple[str, ...] = (
        "require_colons",
        "animated",
        "managed",
        "id",
        "name",
        "_state",
        "user",
        "available",
    )

    def __init__(self, *, state: ConnectionState, data: EmojiPayload):
        self._state: ConnectionState = state
        self._from_data(data)

    def _from_data(self, emoji: EmojiPayload):
        self.require_colons: bool = emoji.get("require_colons", False)
        self.managed: bool = emoji.get("managed", False)
        self.id: int = int(emoji["id"])  # type: ignore
        self.name: str = emoji["name"]  # type: ignore
        self.animated: bool = emoji.get("animated", False)
        self.available: bool = emoji.get("available", True)
        user = emoji.get("user")
        self.user: User | None = User(state=self._state, data=user) if user else None

    def _to_partial(self) -> PartialEmoji:
        return PartialEmoji(name=self.name, animated=self.animated, id=self.id)

    def __iter__(self) -> Iterator[tuple[str, Any]]:
        for attr in self.__slots__:
            if attr[0] != "_":
                value = getattr(self, attr, None)
                if value is not None:
                    yield attr, value

    def __str__(self) -> str:
        if self.animated:
            return f"<a:{self.name}:{self.id}>"
        return f"<:{self.name}:{self.id}>"

    def __repr__(self) -> str:
        return f"<BaseEmoji id={self.id} name={self.name!r} animated={self.animated}>"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, _EmojiTag) and self.id == other.id

    def __hash__(self) -> int:
        return self.id >> 22

    @property
    def created_at(self) -> datetime:
        """Returns the emoji's creation time in UTC."""
        return snowflake_time(self.id)

    @property
    def url(self) -> str:
        """Returns the URL of the emoji."""
        fmt = "gif" if self.animated else "png"
        return f"{Asset.BASE}/emojis/{self.id}.{fmt}"


class GuildEmoji(BaseEmoji):
    """Represents a custom emoji in a guild.

    Depending on the way this object was created, some attributes can
    have a value of ``None``.

    .. container:: operations

        .. describe:: x == y

            Checks if two emoji are the same.

        .. describe:: x != y

            Checks if two emoji are not the same.

        .. describe:: hash(x)

            Return the emoji's hash.

        .. describe:: iter(x)

            Returns an iterator of ``(field, value)`` pairs. This allows this class
            to be used as an iterable in list/dict/etc constructions.

        .. describe:: str(x)

            Returns the emoji rendered for discord.

    Attributes
    ----------
    name: :class:`str`
        The name of the emoji.
    id: :class:`int`
        The emoji's ID.
    require_colons: :class:`bool`
        If colons are required to use this emoji in the client (:PJSalt: vs PJSalt).
    animated: :class:`bool`
        Whether an emoji is animated or not.
    managed: :class:`bool`
        If this emoji is managed by a Twitch integration.
    guild_id: :class:`int`
        The guild ID the emoji belongs to.
    available: :class:`bool`
        Whether the emoji is available for use.
    user: Optional[:class:`User`]
        The user that created the emoji. This can only be retrieved using :meth:`Guild.fetch_emoji` and
        having the :attr:`~Permissions.manage_emojis` permission.
    """

    __slots__: tuple[str, ...] = (
        "_roles",
        "guild_id",
    )

    def __init__(self, *, guild: Guild, state: ConnectionState, data: EmojiPayload):
        self.guild_id: int = guild.id
        self._roles: SnowflakeList = SnowflakeList(map(int, data.get("roles", [])))
        super().__init__(state=state, data=data)

    def __repr__(self) -> str:
        return (
            "<GuildEmoji"
            f" id={self.id} name={self.name!r} animated={self.animated} managed={self.managed}>"
        )

    @property
    def roles(self) -> list[Role]:
        """A :class:`list` of roles that is allowed to use this emoji.

        If roles is empty, the emoji is unrestricted.
        """
        guild = self.guild
        if guild is None:
            return []

        return [role for role in guild.roles if self._roles.has(role.id)]

    @property
    def guild(self) -> Guild:
        """The guild this emoji belongs to."""
        return self._state._get_guild(self.guild_id)

    def is_usable(self) -> bool:
        """Whether the bot can use this emoji.

        .. versionadded:: 1.3
        """
        if not self.available:
            return False
        if not self._roles:
            return True
        emoji_roles, my_roles = self._roles, self.guild.me._roles
        return any(my_roles.has(role_id) for role_id in emoji_roles)

    async def delete(self, *, reason: str | None = None) -> None:
        """|coro|

        Deletes the custom emoji.

        You must have :attr:`~Permissions.manage_emojis` permission to
        do this.

        Parameters
        ----------
        reason: Optional[:class:`str`]
            The reason for deleting this emoji. Shows up on the audit log.

        Raises
        ------
        Forbidden
            You are not allowed to delete emojis.
        HTTPException
            An error occurred deleting the emoji.
        """

        await self._state.http.delete_custom_emoji(
            self.guild.id, self.id, reason=reason
        )

    async def edit(
        self,
        *,
        name: str | Undefined = MISSING,
        roles: list[Snowflake] | Undefined = MISSING,
        reason: str | None = None,
    ) -> GuildEmoji:
        r"""|coro|

        Edits the custom emoji.

        You must have :attr:`~Permissions.manage_emojis` permission to
        do this.

        .. versionchanged:: 2.0
            The newly updated emoji is returned.

        Parameters
        -----------
        name: :class:`str`
            The new emoji name.
        roles: Optional[List[:class:`~discord.abc.Snowflake`]]
            A list of roles that can use this emoji. An empty list can be passed to make it available to everyone.
        reason: Optional[:class:`str`]
            The reason for editing this emoji. Shows up on the audit log.

        Raises
        -------
        Forbidden
            You are not allowed to edit emojis.
        HTTPException
            An error occurred editing the emoji.

        Returns
        --------
        :class:`GuildEmoji`
            The newly updated emoji.
        """

        payload = {}
        if name is not MISSING:
            payload["name"] = name
        if roles is not MISSING:
            payload["roles"] = [role.id for role in roles]

        data = await self._state.http.edit_custom_emoji(
            self.guild.id, self.id, payload=payload, reason=reason
        )
        return GuildEmoji(guild=self.guild, data=data, state=self._state)


Emoji = GuildEmoji


class AppEmoji(BaseEmoji):
    """Represents a custom emoji from an application.

    Depending on the way this object was created, some attributes can
    have a value of ``None``.

        .. versionadded:: 2.7

    .. container:: operations

        .. describe:: x == y

            Checks if two emoji are the same.

        .. describe:: x != y

            Checks if two emoji are not the same.

        .. describe:: hash(x)

            Return the emoji's hash.

        .. describe:: iter(x)

            Returns an iterator of ``(field, value)`` pairs. This allows this class
            to be used as an iterable in list/dict/etc constructions.

        .. describe:: str(x)

            Returns the emoji rendered for discord.

    Attributes
    ----------
    name: :class:`str`
        The name of the emoji.
    id: :class:`int`
        The emoji's ID.
    require_colons: :class:`bool`
        If colons are required to use this emoji in the client (:PJSalt: vs PJSalt).
    animated: :class:`bool`
        Whether an emoji is animated or not.
    managed: :class:`bool`
        If this emoji is managed by a Twitch integration.
    application_id: Optional[:class:`int`]
        The application ID the emoji belongs to, if available.
    available: :class:`bool`
        Whether the emoji is available for use.
    user: Optional[:class:`User`]
        The user that created the emoji.
    """

    __slots__: tuple[str, ...] = ("application_id",)

    def __init__(
        self, *, application_id: int, state: ConnectionState, data: EmojiPayload
    ):
        self.application_id: int = application_id
        super().__init__(state=state, data=data)

    def __repr__(self) -> str:
        return "<AppEmoji" f" id={self.id} name={self.name!r} animated={self.animated}>"

    @property
    def guild(self) -> Guild:
        """The guild this emoji belongs to. This is always `None` for :class:`AppEmoji`."""
        return None

    @property
    def roles(self) -> list[Role]:
        """A :class:`list` of roles that is allowed to use this emoji. This is always empty for :class:`AppEmoji`."""
        return []

    def is_usable(self) -> bool:
        """Whether the bot can use this emoji."""
        return self.application_id == self._state.application_id

    async def delete(self) -> None:
        """|coro|

        Deletes the application emoji.

        You must own the emoji to do this.

        Raises
        ------
        Forbidden
            You are not allowed to delete the emoji.
        HTTPException
            An error occurred deleting the emoji.
        """

        await self._state.http.delete_application_emoji(self.application_id, self.id)
        if self._state.cache_app_emojis and self._state.get_emoji(self.id):
            self._state._remove_emoji(self)

    async def edit(
        self,
        *,
        name: str | Undefined = MISSING,
    ) -> AppEmoji:
        r"""|coro|

        Edits the application emoji.

        You must own the emoji to do this.

        Parameters
        -----------
        name: :class:`str`
            The new emoji name.

        Raises
        -------
        Forbidden
            You are not allowed to edit the emoji.
        HTTPException
            An error occurred editing the emoji.

        Returns
        --------
        :class:`AppEmoji`
            The newly updated emoji.
        """

        payload = {}
        if name is not MISSING:
            payload["name"] = name

        data = await self._state.http.edit_application_emoji(
            self.application_id, self.id, payload=payload
        )
        return self._state.maybe_store_app_emoji(self.application_id, data)
