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

import asyncio
from typing import TYPE_CHECKING, Any, TypeVar

import discord.abc

from .asset import Asset
from .colour import Colour
from .flags import PublicUserFlags
from .iterators import EntitlementIterator
from .monetization import Entitlement
from .utils import MISSING, Undefined, _bytes_to_base64_data, snowflake_time
from .partials import PartialUser

if TYPE_CHECKING:
    from datetime import datetime
    from typing_extensions import Self

    from .abc import Snowflake, SnowflakeTime
    from .channel import DMChannel
    from .guild import Guild
    from .message import Message
    from .app.state import ConnectionState
    from .types.channel import DMChannel as DMChannelPayload
    from .types.user import User as UserPayload


__all__ = (
    "User",
    "ClientUser",
)

BU = TypeVar("BU", bound="BaseUser")


class _UserTag:
    __slots__ = ()
    id: int


class BaseUser(_UserTag, PartialUser):
    __slots__ = (
        "_banner",
        "_accent_colour",
        "bot",
        "system",
        "_public_flags",
        "_avatar_decoration",
        "_state",
    )

    if TYPE_CHECKING:
        bot: bool
        system: bool
        _state: ConnectionState
        _banner: str | None
        _accent_colour: int | None
        _avatar_decoration: dict | None
        _public_flags: int

    def __repr__(self) -> str:
        if self.is_migrated:
            if self.global_name is not None:
                return (
                    "<BaseUser"
                    f" id={self.id} username={self.name!r} global_name={self.global_name!r}"
                    f" bot={self.bot} system={self.system}>"
                )
            return f"<BaseUser id={self.id} username={self.name!r} bot={self.bot} system={self.system}>"
        return (
            "<BaseUser"
            f" id={self.id} name={self.name!r} discriminator={self.discriminator!r}"
            f" bot={self.bot} system={self.system}>"
        )

    def __str__(self) -> str:
        return (
            f"{self.name}#{self.discriminator}"
            if not self.is_migrated
            else (f"{self.name} ({self.global_name})" if self.global_name is not None else self.name)
        )

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, _UserTag) and other.id == self.id

    async def _update(self, data: UserPayload) -> Self:
        await super()._update(data)
        self._banner = data.get("banner", None)
        self._accent_colour = data.get("accent_color", None)
        self._avatar_decoration = data.get("avatar_decoration_data", None)
        self._public_flags = data.get("public_flags", 0)
        self.bot = data.get("bot", False)
        self.system = data.get("system", False)
        return self

    @classmethod
    def _copy(cls: type[BU], user: BU) -> BU:
        self = cls.__new__(cls)  # bypass __init__

        self.name = user.name
        self.id = user.id
        self.discriminator = user.discriminator
        self.global_name = user.global_name
        self._avatar = user._avatar
        self._banner = user._banner
        self._accent_colour = user._accent_colour
        self._avatar_decoration = user._avatar_decoration
        self.bot = user.bot
        self._state = user._state
        self._public_flags = user._public_flags

        return self

    def _to_minimal_user_json(self) -> dict[str, Any]:
        data = super()._to_minimal_user_json()
        data["bot"] = self.bot
        return data

    @property
    def public_flags(self) -> PublicUserFlags:
        """The publicly available flags the user has."""
        return PublicUserFlags._from_value(self._public_flags)

    @property
    def display_avatar(self) -> Asset:
        """Returns the user's display avatar.

        For regular users this is just their default avatar or uploaded avatar.

        .. versionadded:: 2.0
        """
        return self.avatar or self.default_avatar

    @property
    def banner(self) -> Asset | None:
        """Returns the user's banner asset, if available.

        .. versionadded:: 2.0

        .. note::
            This information is only available via :meth:`Client.fetch_user`.
        """
        if self._banner is None:
            return None
        return Asset._from_user_banner(self._state, self.id, self._banner)

    @property
    def avatar_decoration(self) -> Asset | None:
        """Returns the user's avatar decoration, if available.

        .. versionadded:: 2.5
        """
        if self._avatar_decoration is None:
            return None
        return Asset._from_avatar_decoration(self._state, self.id, self._avatar_decoration.get("asset"))

    @property
    def accent_colour(self) -> Colour | None:
        """Returns the user's accent colour, if applicable.

        There is an alias for this named :attr:`accent_color`.

        .. versionadded:: 2.0

        .. note::

            This information is only available via :meth:`Client.fetch_user`.
        """
        if self._accent_colour is None:
            return None
        return Colour(self._accent_colour)

    @property
    def accent_color(self) -> Colour | None:
        """Returns the user's accent color, if applicable.

        There is an alias for this named :attr:`accent_colour`.

        .. versionadded:: 2.0

        .. note::

            This information is only available via :meth:`Client.fetch_user`.
        """
        return self.accent_colour

    @property
    def colour(self) -> Colour:
        """A property that returns a colour denoting the rendered colour
        for the user. This always returns :meth:`Colour.default`.

        There is an alias for this named :attr:`color`.
        """
        return Colour.default()

    @property
    def color(self) -> Colour:
        """A property that returns a color denoting the rendered color
        for the user. This always returns :meth:`Colour.default`.

        There is an alias for this named :attr:`colour`.
        """
        return self.colour


class ClientUser(BaseUser):
    """Represents your Discord user.

    .. container:: operations

        .. describe:: x == y

            Checks if two users are equal.

        .. describe:: x != y

            Checks if two users are not equal.

        .. describe:: hash(x)

            Return the user's hash.

        .. describe:: str(x)

            Returns the user's name with discriminator or global_name.

    Attributes
    ----------
    name: :class:`str`
        The user's username.
    id: :class:`int`
        The user's unique ID.
    discriminator: :class:`str`
        The user's discriminator. This is given when the username has conflicts.

        .. note::

            If the user has migrated to the new username system, this will always be 0.
    global_name: :class:`str`
        The user's global name.

        .. versionadded:: 2.5
    bot: :class:`bool`
        Specifies if the user is a bot account.
    system: :class:`bool`
        Specifies if the user is a system user (i.e. represents Discord officially).

        .. versionadded:: 1.3
    verified: :class:`bool`
        Specifies if the user's email is verified.
    locale: Optional[:class:`str`]
        The IETF language tag used to identify the language the user is using.
    mfa_enabled: :class:`bool`
        Specifies if the user has MFA turned on and working.
    """

    __slots__ = ("locale", "_flags", "verified", "mfa_enabled", "__weakref__")

    if TYPE_CHECKING:
        verified: bool
        locale: str | None
        mfa_enabled: bool
        _flags: int

    def __init__(self, *, state: ConnectionState, id: int) -> None:
        super().__init__(state=state, id=id)

    def __repr__(self) -> str:
        if self.is_migrated:
            if self.global_name is not None:
                return (
                    "<ClientUser"
                    f" id={self.id} username={self.name!r} global_name={self.global_name!r}"
                    f" bot={self.bot} verified={self.verified} mfa_enabled={self.mfa_enabled}>"
                )
            return (
                "<ClientUser"
                f" id={self.id} username={self.name!r}"
                f" bot={self.bot} verified={self.verified} mfa_enabled={self.mfa_enabled}>"
            )
        return (
            "<ClientUser"
            f" id={self.id} name={self.name!r} discriminator={self.discriminator!r}"
            f" bot={self.bot} verified={self.verified} mfa_enabled={self.mfa_enabled}>"
        )

    async def _update(self, data: UserPayload) -> None:
        await super()._update(data)
        # There's actually an Optional[str] phone field as well, but I won't use it
        self.verified = data.get("verified", False)
        self.locale = data.get("locale")
        self._flags = data.get("flags", 0)
        self.mfa_enabled = data.get("mfa_enabled", False)

    # TODO: Username might not be able to edit anymore.
    async def edit(
        self,
        *,
        username: str | Undefined = MISSING,
        avatar: bytes | Undefined = MISSING,
        banner: bytes | Undefined = MISSING,
    ) -> ClientUser:
        """|coro|

        Edits the current profile of the client.

        .. note::

            To upload an avatar or banner, a :term:`py:bytes-like object` must be passed in that
            represents the image being uploaded. If this is done through a file
            then the file must be opened via ``open('some_filename', 'rb')`` and
            the :term:`py:bytes-like object` is given through the use of ``fp.read()``.

            The only image formats supported for uploading are JPEG, PNG, and GIF.

        .. versionchanged:: 2.0
            The edit is no longer in-place, instead the newly edited client user is returned.

        .. versionchanged:: 2.6
            The ``banner`` keyword-only parameter was added.

        Parameters
        ----------
        username: :class:`str`
            The new username you wish to change to.
        avatar: :class:`bytes`
            A :term:`py:bytes-like object` representing the image to upload.
            Could be ``None`` to denote no avatar.
        banner: :class:`bytes`
            A :term:`py:bytes-like object` representing the image to upload.
            Could be ``None`` to denote no banner.

        Returns
        -------
        :class:`ClientUser`
            The newly edited client user.

        Raises
        ------
        HTTPException
            Editing your profile failed.
        InvalidArgument
            Wrong image format passed for ``avatar`` or ``banner``.
        """
        payload: dict[str, Any] = {}
        if username is not MISSING:
            payload["username"] = username

        if avatar is None:
            payload["avatar"] = None
        elif avatar is not MISSING:
            payload["avatar"] = _bytes_to_base64_data(avatar)

        if banner is None:
            payload["banner"] = None
        elif banner is not MISSING:
            payload["banner"] = _bytes_to_base64_data(banner)

        data: UserPayload = await self._state.http.edit_profile(payload)
        return await ClientUser.__load__(self._state, int(data["id"]), data)


class User(BaseUser):
    """Represents a Discord user.

    .. container:: operations

        .. describe:: x == y

            Checks if two users are equal.

        .. describe:: x != y

            Checks if two users are not equal.

        .. describe:: hash(x)

            Return the user's hash.

        .. describe:: str(x)

            Returns the user's name with discriminator or global_name.

    Attributes
    ----------
    name: :class:`str`
        The user's username.
    id: :class:`int`
        The user's unique ID.
    discriminator: :class:`str`
        The user's discriminator. This is given when the username has conflicts.

        .. note::

            If the user has migrated to the new username system, this will always be "0".
    global_name: :class:`str`
        The user's global name.

        .. versionadded:: 2.5
    bot: :class:`bool`
        Specifies if the user is a bot account.
    system: :class:`bool`
        Specifies if the user is a system user (i.e. represents Discord officially).
    """

    __slots__ = ("_stored",)

    def __init__(self, *, state: ConnectionState, id: int) -> None:
        super().__init__(state=state, id=id)
        self._stored: bool = False

    def __repr__(self) -> str:
        if self.is_migrated:
            if self.global_name is not None:
                return f"<User id={self.id} username={self.name!r} global_name={self.global_name!r} bot={self.bot}>"
            return f"<User id={self.id} username={self.name!r} bot={self.bot}>"
        return f"<User id={self.id} name={self.name!r} discriminator={self.discriminator!r} bot={self.bot}>"

    def __del__(self) -> None:
        try:
            if self._stored:
                asyncio.create_task(self._state.deref_user(self.id))
        except Exception:
            pass

    @classmethod
    def _copy(cls, user: User):
        self = super()._copy(user)
        self._stored = False
        return self
