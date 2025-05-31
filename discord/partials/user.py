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
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from discord.errors import MissingApplicationID
from discord.abc import Messageable, Snowflake, SnowflakeTime
from discord.iterators import EntitlementIterator
from discord.mixins import Hashable
from discord.monetization import Entitlement
from discord.utils import snowflake_time
from discord.asset import Asset

if TYPE_CHECKING:
    from typing_extensions import Self

    from ..app.state import ConnectionState
    from ..types.user import PartialUser as PartialUserPayload
    from ..channel import DMChannel
    from ..message import Message
    from ..user import User
    from ..guild import Guild


class PartialUser(Messageable, Hashable):

    __slots__ = (
        "id",
        "name",
        "discriminator",
        "global_name",
        "_avatar",

        "_state",
    )

    if TYPE_CHECKING:
        id: int
        name: str
        discriminator: str
        global_name: str | None
        _avatar: str | None

    async def _get_channel(self):
        return await self.create_dm()

    def __init__(self, state: ConnectionState, id: int) -> None:
        self._state: ConnectionState = state
        self.id = id

    def __hash__(self) -> int:
        return self.id >> 22

    def __default_attrs(self) -> None:
        self.name = ""
        self.discriminator = "0"  # not so sure about this default, but meh
        self.global_name = None
        self._avatar = None

    async def _update(self, data: PartialUserPayload | None) -> Self:
        if data is None:
            self.__default_attrs()
            return self
        self.name = data["username"]
        self.discriminator = data["discriminator"]
        self.global_name = data["global_name"]
        self._avatar = data["avatar"]
        return self

    @classmethod
    async def __load__(cls, state: ConnectionState, id: int, data: PartialUserPayload | None = None) -> Self:
        return await cls(state, id)._update(data)

    def _to_minimal_user_json(self) -> dict[str, Any]:
        return {
            "username": self.name,
            "id": self.id,
            "avatar": self._avatar,
            "discriminator": self.discriminator,
            "global_name": self.global_name,
            "bot": False,
        }

    @property
    def jump_url(self) -> str:
        """Returns a URL that allows the client to jump to the user.

        .. versionadded:: 2.0
        """
        return f"https://discord.com/users/{self.id}"

    @property
    def mention(self) -> str:
        """Returns a string that allows you to mention the given user."""
        return f"<@{self.id}>"

    @property
    def created_at(self) -> datetime.datetime:
        """Returns the user's creation time in UTC.

        This is when the user's Discord account was created.
        """
        return snowflake_time(self.id)

    @property
    def display_name(self) -> str:
        """Returns the user's display name.
        This will be their global name if set, otherwise their username.

        If this is a partial user, the string may be empty.
        """
        return self.global_name or self.name

    @property
    def avatar(self) -> Asset | None:
        """Returns an :class:`Asset` for the avatar the user has.

        If the user does not have a traditional avatar, ``None`` is returned.
        If you want the avatar that a user has displayed, consider :attr:`display_avatar`.

        If this is a partial user, this may be ``None`` even if the user has an avatar set.
        """
        return self._avatar and Asset._from_avatar(self._state, self.id, self._avatar)  # type: ignore

    @property
    def default_avatar(self) -> Asset:
        """Returns the default avatar for a given user.
        This is calculated by the user's ID if they're on the new username system, otherwise their discriminator.
        """
        eq = (self.id >> 2) if self.is_migrated else int(self.discriminator)
        perc = 6 if self.is_migrated else 5
        return Asset._from_default_avatar(self._state, eq % perc)

    def mentioned_in(self, message: Message) -> bool:
        """Checks if a user is mentioned in the specific message.

        Parameters
        ----------
        message: :class:`discord.Message`
            The message to check if the user's mentioned in.

        Returns
        -------
        :class:`bool`
            Indicates if the user is mentioned in the message.
        """

        if message.mention_everyone:
            return True

        return any(user.id == self.id for user in message.mentions)

    async def create_dm(self) -> DMChannel:
        """|coro|

        Creates a :class:`DMChannel` with this user.

        This should be rarely called, as this is done transparently for most
        people.

        Returns
        -------
        :class:`DMChannel`
            The channel that was created.
        """

        found = await self._state._get_private_channel_by_user(self.id)
        if found is not None:
            return found

        data = await self._state.http.start_private_message(self.id)
        return await self._state.add_dm_channel(data)

    async def create_test_entitlement(self, sku: Snowflake, /) -> Entitlement:
        """|coro|

        Creates a test entitlement for the user.

        Parameters
        ----------
        sku: :class:`Snowflake`
            The SKU to create a test entitlement for.

        Returns
        -------
        :class:`Entitlement`
            The created entitlement.
        """
        if not self._state.application_id:
            raise MissingApplicationID

        data = await self._state.http.create_test_entitlement(
            self._state.application_id,
            {
                "owner_id": self.id,
                "owner_type": 2,
                "sku_id": sku.id,
            },
        )
        return Entitlement(data=data, state=self._state)

    def entitlements(
        self,
        *,
        skus: list[Snowflake] | None = None,
        before: SnowflakeTime | None = None,
        after: SnowflakeTime | None = None,
        limit: int | None = 100,
        exclude_ended: bool = False,
    ) -> EntitlementIterator:
        """Returns an :class:`AsyncIterator` that enableds fetching the user's entitlements.

        This is identical to :meth:`Client.entitlements` with the ``user`` parameter.

        .. versionadded:: 2.6

        Parameters
        ----------
        skus: List[:class:`discord.abc.Snowflake`] | None
            Limit the fetched entitlements to entitlements that are for these SKUs.
        before: :class:`discord.abc.Snowflake` | :class:`datetime.datetime` | None
            Retrieves guilds before this date or object. If a datetime is provided,
            it is recommended to use a UTC-aware datetime. If the datetime is naive,
            it is assumed to be local time.
        after: :class:`discord.abc.Snowflake` | :class:`datetime.datetime` | None
            Retrieves guilds after this date or object. If a datetime is provided,
            it is recommended to use a UTC-aware datetime. If the datetime is naive,
            it is assumed to be local time.
        limit: :class:`int` | None
            The number of entitlements to retrieve. If ``None``, retrieves every
            entitlement, which may be slow. Defaults to ``100``.
        exclude_ended: :class:`bool`
            Whether to limit the fetched entitlements to those that have not ended.
            Defaults to ``False``.

        Yields
        ------
        :class:`discord.Entitlement`
            The user's entitlements.

        Raises
        ------
        :exc:`discord.HTTPException`
            Retrieving the entitlements failed.
        """
        return EntitlementIterator(
            self._state,
            self.id,
            sku_ids=[sku.id for sku in skus] if skus else None,
            before=before,
            after=after,
            limit=limit,
            exclude_ended=exclude_ended,
        )

    @property
    def is_migrated(self) -> bool:
        """Checks whether the user is already migrated to global name.

        This may return a wrong value for partial users.
        """
        return self.discriminator in ("0", "0000")

    async def fetch(self) -> User:
        """|coro|

        Fetches this user.

        Returns
        -------
        :class:`discord.User`
            The fetched user.
        """
        data = await self._state.http.get_user(self.id)
        return await self._state.store_user(data)

    async def get_dm_channel(self) -> DMChannel | None:
        """Returns the channel associated with this user if it exists.

        If this return ``None``, you can create a DM channel by calling the
        :meth:`create_dm` coroutine function.
        """
        return await self._state._get_private_channel_by_user(self.id)

    async def get_mutual_guilds(self) -> list[Guild]:
        """The guilds that the user shares with the client.

        .. note::

            This will only return mutual guilds within the client's internal cache.

        .. versionadded:: 1.7
        """
        return [
            guild for guild in await self._state.cache.get_all_guilds()
            if await guild.get_member(self.id)
        ]
