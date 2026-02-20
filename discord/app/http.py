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

import logging
from typing import TYPE_CHECKING

from ..appinfo import AppInfo, PartialAppInfo
from ..application_role_connection import ApplicationRoleConnectionMetadata
from ..banners import print_banner, start_logging
from ..channel import _threaded_channel_factory
from ..channel.thread import Thread
from ..emoji import AppEmoji
from ..enums import ChannelType
from ..errors import *
from ..flags import ApplicationFlags
from ..gateway import *
from ..guild import Guild
from ..invite import Invite
from ..iterators import EntitlementIterator, GuildIterator
from ..monetization import SKU
from ..object import Object
from ..soundboard import SoundboardSound
from ..stage_instance import StageInstance
from ..sticker import (GuildSticker, StandardSticker, StickerPack,
                       _sticker_factory)
from ..template import Template
from ..user import ClientUser, User
from ..utils.private import (bytes_to_base64_data, resolve_invite,
                             resolve_template)
from ..webhook import Webhook
from ..widget import Widget
from .base import BaseApp

if TYPE_CHECKING:
    from ..abc import PrivateChannel, Snowflake, SnowflakeTime
    from ..channel import DMChannel, GuildChannel
    from ..member import Member
    from ..soundboard import SoundboardSound
    from ..voice_client import VoiceProtocol

_log = logging.getLogger(__name__)


class HTTPApp(BaseApp):
    @property
    def voice_clients(self) -> list[VoiceProtocol]:
        """Represents a list of voice connections.

        These are usually :class:`.VoiceClient` instances.
        """
        return self._connection.voice_clients

    @property
    def application_id(self) -> int | None:
        """The client's application ID.

        If this is not passed via ``__init__`` then this is retrieved
        through the gateway when an event contains the data. Usually
        after :func:`~discord.on_connect` is called.

        .. versionadded:: 2.0
        """
        return self._connection.application_id

    @property
    def application_flags(self) -> ApplicationFlags:
        """The client's application flags.

        .. versionadded:: 2.0
        """
        return self._connection.application_flags  # type: ignore

    async def login(self, token: str) -> None:
        """|coro|

        Logs in the client with the specified credentials.

        Parameters
        ----------
        token: :class:`str`
            The authentication token. Do not prefix this token with
            anything as the library will do it for you.

        Raises
        ------
        TypeError
            The token was in invalid type.
        :exc:`LoginFailure`
            The wrong credentials are passed.
        :exc:`HTTPException`
            An unknown HTTP related error occurred,
            usually when it isn't 200 or the known incorrect credentials
            passing status code.
        """
        if not isinstance(token, str):
            raise TypeError(f"token must be of type str, not {token.__class__.__name__}")

        _log.info("logging in using static token")

        data = await self.http.static_login(token.strip())
        self._connection.user = ClientUser(state=self._connection, data=data)

        print_banner(
            bot_name=self._connection.user.display_name,
            module=self._banner_module or "discord",
        )
        start_logging(self._flavor, debug=self._debug)

    async def is_owner(self, user: User | Member) -> bool:
        """|coro|

        Checks if a :class:`~discord.User` or :class:`~discord.Member` is the owner of
        this bot.

        If an :attr:`owner_id` is not set, it is fetched automatically
        through the use of :meth:`~.Bot.application_info`.

        .. versionchanged:: 1.3
            The function also checks if the application is team-owned if
            :attr:`owner_ids` is not set.

        Parameters
        ----------
        user: Union[:class:`.abc.User`, :class:`.member.Member`]
            The user to check for.

        Returns
        -------
        :class:`bool`
            Whether the user is the owner.
        """

        if self.owner_id:
            return user.id == self.owner_id
        elif self.owner_ids:
            return user.id in self.owner_ids
        else:
            app = await self.application_info()  # type: ignore
            if app.team:
                self.owner_ids = ids = {m.id for m in app.team.members}
                return user.id in ids
            else:
                self.owner_id = owner_id = app.owner.id
                return user.id == owner_id

    async def fetch_application(self, application_id: int, /) -> PartialAppInfo:
        """|coro|
        Retrieves a :class:`.PartialAppInfo` from an application ID.

        Parameters
        ----------
        application_id: :class:`int`
            The application ID to retrieve information from.

        Returns
        -------
        :class:`.PartialAppInfo`
            The application information.

        Raises
        ------
        NotFound
            An application with this ID does not exist.
        HTTPException
            Retrieving the application failed.
        """
        data = await self.http.get_application(application_id)
        return PartialAppInfo(state=self._connection, data=data)

    def fetch_guilds(
        self,
        *,
        limit: int | None = 100,
        before: SnowflakeTime = None,
        after: SnowflakeTime = None,
        with_counts: bool = True,
    ) -> GuildIterator:
        """Retrieves an :class:`.AsyncIterator` that enables receiving your guilds.

        .. note::

            Using this, you will only receive :attr:`.Guild.owner`, :attr:`.Guild.icon`,
            :attr:`.Guild.id`, and :attr:`.Guild.name` per :class:`.Guild`.

        .. note::

            This method is an API call. For general usage, consider :attr:`guilds` instead.

        Parameters
        ----------
        limit: Optional[:class:`int`]
            The number of guilds to retrieve.
            If ``None``, it retrieves every guild you have access to. Note, however,
            that this would make it a slow operation.
            Defaults to ``100``.
        before: Union[:class:`.abc.Snowflake`, :class:`datetime.datetime`]
            Retrieves guilds before this date or object.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
        after: Union[:class:`.abc.Snowflake`, :class:`datetime.datetime`]
            Retrieve guilds after this date or object.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
        with_counts: :class:`bool`
            Whether to include member count information in guilds. This fills the
            :attr:`.Guild.approximate_member_count` and :attr:`.Guild.approximate_presence_count`
            fields.
            Defaults to ``True``.

        Yields
        ------
        :class:`.Guild`
            The guild with the guild data parsed.

        Raises
        ------
        :exc:`HTTPException`
            Getting the guilds failed.

        Examples
        --------

        Usage ::

            async for guild in client.fetch_guilds(limit=150):
                print(guild.name)

        Flattening into a list ::

            guilds = await client.fetch_guilds(limit=150).flatten()
            # guilds is now a list of Guild...

        All parameters are optional.
        """
        return GuildIterator(self, limit=limit, before=before, after=after, with_counts=with_counts)

    async def fetch_template(self, code: Template | str) -> Template:
        """|coro|

        Gets a :class:`.Template` from a discord.new URL or code.

        Parameters
        ----------
        code: Union[:class:`.Template`, :class:`str`]
            The Discord Template Code or URL (must be a discord.new URL).

        Returns
        -------
        :class:`.Template`
            The template from the URL/code.

        Raises
        ------
        :exc:`NotFound`
            The template is invalid.
        :exc:`HTTPException`
            Getting the template failed.
        """
        code = resolve_template(code)
        data = await self.http.get_template(code)
        return await Template.from_data(data=data, state=self._connection)  # type: ignore

    async def fetch_guild(self, guild_id: int, /, *, with_counts=True) -> Guild:
        """|coro|

        Retrieves a :class:`.Guild` from an ID.

        .. note::

            Using this, you will **not** receive :attr:`.Guild.channels`, :attr:`.Guild.members`,
            :attr:`.Member.activity` and :attr:`.Member.voice` per :class:`.Member`.

        .. note::

            This method is an API call. For general usage, consider :meth:`get_guild` instead.

        Parameters
        ----------
        guild_id: :class:`int`
            The guild's ID to fetch from.

        with_counts: :class:`bool`
            Whether to include count information in the guild. This fills the
            :attr:`.Guild.approximate_member_count` and :attr:`.Guild.approximate_presence_count`
            fields.

            .. versionadded:: 2.0

        Returns
        -------
        :class:`.Guild`
            The guild from the ID.

        Raises
        ------
        :exc:`Forbidden`
            You do not have access to the guild.
        :exc:`HTTPException`
            Getting the guild failed.
        """
        data = await self.http.get_guild(guild_id, with_counts=with_counts)
        return await Guild._from_data(guild=data, state=self._connection)

    async def fetch_stage_instance(self, channel_id: int, /) -> StageInstance:
        """|coro|

        Gets a :class:`.StageInstance` for a stage channel id.

        .. versionadded:: 2.0

        Parameters
        ----------
        channel_id: :class:`int`
            The stage channel ID.

        Returns
        -------
        :class:`.StageInstance`
            The stage instance from the stage channel ID.

        Raises
        ------
        :exc:`NotFound`
            The stage instance or channel could not be found.
        :exc:`HTTPException`
            Getting the stage instance failed.
        """
        data = await self.http.get_stage_instance(channel_id)
        guild = self.get_guild(int(data["guild_id"]))
        return StageInstance(guild=guild, state=self._connection, data=data)  # type: ignore

    # Invite management

    async def fetch_invite(
        self,
        url: Invite | str,
        *,
        with_counts: bool = True,
        with_expiration: bool = True,
        event_id: int | None = None,
    ) -> Invite:
        """|coro|

        Gets an :class:`.Invite` from a discord.gg URL or ID.

        .. note::

            If the invite is for a guild you have not joined, the guild and channel
            attributes of the returned :class:`.Invite` will be :class:`.PartialInviteGuild` and
            :class:`.PartialInviteChannel` respectively.

        Parameters
        ----------
        url: Union[:class:`.Invite`, :class:`str`]
            The Discord invite ID or URL (must be a discord.gg URL).
        with_counts: :class:`bool`
            Whether to include count information in the invite. This fills the
            :attr:`.Invite.approximate_member_count` and :attr:`.Invite.approximate_presence_count`
            fields.
        with_expiration: :class:`bool`
            Whether to include the expiration date of the invite. This fills the
            :attr:`.Invite.expires_at` field.

            .. versionadded:: 2.0
        event_id: Optional[:class:`int`]
            The ID of the scheduled event to be associated with the event.

            See :meth:`Invite.set_scheduled_event` for more
            info on event invite linking.

            .. versionadded:: 2.0

        Returns
        -------
        :class:`.Invite`
            The invite from the URL/ID.

        Raises
        ------
        :exc:`NotFound`
            The invite has expired or is invalid.
        :exc:`HTTPException`
            Getting the invite failed.
        """

        invite_id = resolve_invite(url)
        data = await self.http.get_invite(
            invite_id,
            with_counts=with_counts,
            with_expiration=with_expiration,
            guild_scheduled_event_id=event_id,
        )
        return await Invite.from_incomplete(state=self._connection, data=data)

    async def delete_invite(self, invite: Invite | str) -> None:
        """|coro|

        Revokes an :class:`.Invite`, URL, or ID to an invite.

        You must have the :attr:`~.Permissions.manage_channels` permission in
        the associated guild to do this.

        Parameters
        ----------
        invite: Union[:class:`.Invite`, :class:`str`]
            The invite to revoke.

        Raises
        ------
        :exc:`Forbidden`
            You do not have permissions to revoke invites.
        :exc:`NotFound`
            The invite is invalid or expired.
        :exc:`HTTPException`
            Revoking the invite failed.
        """

        invite_id = resolve_invite(invite)
        await self.http.delete_invite(invite_id)

    # Miscellaneous stuff

    async def fetch_widget(self, guild_id: int, /) -> Widget:
        """|coro|

        Gets a :class:`.Widget` from a guild ID.

        .. note::

            The guild must have the widget enabled to get this information.

        Parameters
        ----------
        guild_id: :class:`int`
            The ID of the guild.

        Returns
        -------
        :class:`.Widget`
            The guild's widget.

        Raises
        ------
        :exc:`Forbidden`
            The widget for this guild is disabled.
        :exc:`HTTPException`
            Retrieving the widget failed.
        """
        data = await self.http.get_widget(guild_id)

        return Widget(state=self._connection, data=data)

    async def application_info(self) -> AppInfo:
        """|coro|

        Retrieves the bot's application information.

        Returns
        -------
        :class:`.AppInfo`
            The bot's application information.

        Raises
        ------
        :exc:`HTTPException`
            Retrieving the information failed somehow.
        """
        data = await self.http.application_info()
        if "rpc_origins" not in data:
            data["rpc_origins"] = None
        return AppInfo(self._connection, data)

    async def fetch_user(self, user_id: int, /) -> User:
        """|coro|

        Retrieves a :class:`~discord.User` based on their ID.
        You do not have to share any guilds with the user to get this information,
        however many operations do require that you do.

        .. note::

            This method is an API call. If you have :attr:`discord.Intents.members` and member cache enabled,
            consider :meth:`get_user` instead.

        Parameters
        ----------
        user_id: :class:`int`
            The user's ID to fetch from.

        Returns
        -------
        :class:`~discord.User`
            The user you requested.

        Raises
        ------
        :exc:`NotFound`
            A user with this ID does not exist.
        :exc:`HTTPException`
            Fetching the user failed.
        """
        data = await self.http.get_user(user_id)
        return User(state=self._connection, data=data)

    async def fetch_channel(self, channel_id: int, /) -> GuildChannel | PrivateChannel | Thread:
        """|coro|

        Retrieves a :class:`.abc.GuildChannel`, :class:`.abc.PrivateChannel`, or :class:`.Thread` with the specified ID.

        .. note::

            This method is an API call. For general usage, consider :meth:`get_channel` instead.

        .. versionadded:: 1.2

        Returns
        -------
        Union[:class:`.abc.GuildChannel`, :class:`.abc.PrivateChannel`, :class:`.Thread`]
            The channel from the ID.

        Raises
        ------
        :exc:`InvalidData`
            An unknown channel type was received from Discord.
        :exc:`HTTPException`
            Retrieving the channel failed.
        :exc:`NotFound`
            Invalid Channel ID.
        :exc:`Forbidden`
            You do not have permission to fetch this channel.
        """
        data = await self.http.get_channel(channel_id)

        factory, ch_type = _threaded_channel_factory(data["type"])
        if factory is None:
            raise InvalidData("Unknown channel type {type} for channel ID {id}.".format_map(data))

        if ch_type in (ChannelType.group, ChannelType.private):
            # the factory will be a DMChannel or GroupChannel here
            return factory(me=self.user, data=data, state=self._connection)
        # the factory can't be a DMChannel or GroupChannel here
        guild_id = int(data["guild_id"])  # type: ignore
        guild = self.get_guild(guild_id) or Object(id=guild_id)
        # GuildChannels expect a Guild, we may be passing an Object
        return factory(guild=guild, state=self._connection, data=data)

    async def fetch_webhook(self, webhook_id: int, /) -> Webhook:
        """|coro|

        Retrieves a :class:`.Webhook` with the specified ID.

        Returns
        -------
        :class:`.Webhook`
            The webhook you requested.

        Raises
        ------
        :exc:`HTTPException`
            Retrieving the webhook failed.
        :exc:`NotFound`
            Invalid webhook ID.
        :exc:`Forbidden`
            You do not have permission to fetch this webhook.
        """
        data = await self.http.get_webhook(webhook_id)
        return Webhook.from_state(data, state=self._connection)

    async def fetch_sticker(self, sticker_id: int, /) -> StandardSticker | GuildSticker:
        """|coro|

        Retrieves a :class:`.Sticker` with the specified ID.

        .. versionadded:: 2.0

        Returns
        -------
        Union[:class:`.StandardSticker`, :class:`.GuildSticker`]
            The sticker you requested.

        Raises
        ------
        :exc:`HTTPException`
            Retrieving the sticker failed.
        :exc:`NotFound`
            Invalid sticker ID.
        """
        data = await self.http.get_sticker(sticker_id)
        cls, _ = _sticker_factory(data["type"])  # type: ignore
        return cls(state=self._connection, data=data)  # type: ignore

    async def fetch_premium_sticker_packs(self) -> list[StickerPack]:
        """|coro|

        Retrieves all available premium sticker packs.

        .. versionadded:: 2.0

        Returns
        -------
        List[:class:`.StickerPack`]
            All available premium sticker packs.

        Raises
        ------
        :exc:`HTTPException`
            Retrieving the sticker packs failed.
        """
        data = await self.http.list_premium_sticker_packs()
        return [StickerPack(state=self._connection, data=pack) for pack in data["sticker_packs"]]

    async def create_dm(self, user: Snowflake) -> DMChannel:
        """|coro|

        Creates a :class:`.DMChannel` with this user.

        This should be rarely called, as this is done transparently for most
        people.

        .. versionadded:: 2.0

        Parameters
        ----------
        user: :class:`~discord.abc.Snowflake`
            The user to create a DM with.

        Returns
        -------
        :class:`.DMChannel`
            The channel that was created.
        """
        state = self._connection
        found = await state._get_private_channel_by_user(user.id)
        if found:
            return found

        data = await state.http.start_private_message(user.id)
        return await state.add_dm_channel(data)

    async def fetch_role_connection_metadata_records(
        self,
    ) -> list[ApplicationRoleConnectionMetadata]:
        """|coro|

        Fetches the bot's role connection metadata records.

        .. versionadded:: 2.4

        Returns
        -------
        List[:class:`.ApplicationRoleConnectionMetadata`]
            The bot's role connection metadata records.
        """
        data = await self._connection.http.get_application_role_connection_metadata_records(self.application_id)
        return [ApplicationRoleConnectionMetadata.from_dict(r) for r in data]

    async def update_role_connection_metadata_records(
        self, *role_connection_metadata
    ) -> list[ApplicationRoleConnectionMetadata]:
        """|coro|

        Updates the bot's role connection metadata records.

        .. versionadded:: 2.4

        Parameters
        ----------
        *role_connection_metadata: :class:`ApplicationRoleConnectionMetadata`
            The new metadata records to send to Discord.

        Returns
        -------
        List[:class:`.ApplicationRoleConnectionMetadata`]
            The updated role connection metadata records.
        """
        payload = [r.to_dict() for r in role_connection_metadata]
        data = await self._connection.http.update_application_role_connection_metadata_records(
            self.application_id, payload
        )
        return [ApplicationRoleConnectionMetadata.from_dict(r) for r in data]

    async def fetch_skus(self) -> list[SKU]:
        """|coro|

        Fetches the bot's SKUs.

        .. versionadded:: 2.5

        Returns
        -------
        List[:class:`.SKU`]
            The bot's SKUs.
        """
        data = await self._connection.http.list_skus(self.application_id)
        return [SKU(state=self._connection, data=s) for s in data]

    def entitlements(
        self,
        user: Snowflake | None = None,
        skus: list[Snowflake] | None = None,
        before: SnowflakeTime | None = None,
        after: SnowflakeTime | None = None,
        limit: int | None = 100,
        guild: Snowflake | None = None,
        exclude_ended: bool = False,
    ) -> EntitlementIterator:
        """Returns an :class:`.AsyncIterator` that enables fetching the application's entitlements.

        .. versionadded:: 2.6

        Parameters
        ----------
        user: :class:`.abc.Snowflake` | None
            Limit the fetched entitlements to entitlements owned by this user.
        skus: list[:class:`.abc.Snowflake`] | None
            Limit the fetched entitlements to entitlements that are for these SKUs.
        before: :class:`.abc.Snowflake` | :class:`datetime.datetime` | None
            Retrieves guilds before this date or object.
            If a datetime is provided, it is recommended to use a UTC-aware datetime.
            If the datetime is naive, it is assumed to be local time.
        after: :class:`.abc.Snowflake` | :class:`datetime.datetime` | None
            Retrieve guilds after this date or object.
            If a datetime is provided, it is recommended to use a UTC-aware datetime.
            If the datetime is naive, it is assumed to be local time.
        limit: Optional[:class:`int`]
            The number of entitlements to retrieve.
            If ``None``, retrieves every entitlement, which may be slow.
            Defaults to ``100``.
        guild: :class:`.abc.Snowflake` | None
            Limit the fetched entitlements to entitlements owned by this guild.
        exclude_ended: :class:`bool`
            Whether to limit the fetched entitlements to those that have not ended.
            Defaults to ``False``.

        Yields
        ------
        :class:`.Entitlement`
            The application's entitlements.

        Raises
        ------
        :exc:`HTTPException`
            Retrieving the entitlements failed.

        Examples
        --------

        Usage ::

            async for entitlement in client.entitlements():
                print(entitlement.user_id)

        Flattening into a list ::

            entitlements = await user.entitlements().flatten()

        All parameters are optional.
        """
        return EntitlementIterator(
            self._connection,
            user_id=user.id if user else None,
            sku_ids=[sku.id for sku in skus] if skus else None,
            before=before,
            after=after,
            limit=limit,
            guild_id=guild.id if guild else None,
            exclude_ended=exclude_ended,
        )

    @property
    def store_url(self) -> str:
        """:class:`str`: The URL that leads to the application's store page for monetization.

        .. versionadded:: 2.6
        """
        return f"https://discord.com/application-directory/{self.application_id}/store"

    async def fetch_emojis(self) -> list[AppEmoji]:
        r"""|coro|

        Retrieves all custom :class:`AppEmoji`\s from the application.

        Raises
        ---------
        HTTPException
            An error occurred fetching the emojis.

        Returns
        --------
        List[:class:`AppEmoji`]
            The retrieved emojis.
        """
        data = await self._connection.http.get_all_application_emojis(self.application_id)
        return [await self._connection.maybe_store_app_emoji(self.application_id, d) for d in data["items"]]

    async def fetch_emoji(self, emoji_id: int, /) -> AppEmoji:
        """|coro|

        Retrieves a custom :class:`AppEmoji` from the application.

        Parameters
        ----------
        emoji_id: :class:`int`
            The emoji's ID.

        Returns
        -------
        :class:`AppEmoji`
            The retrieved emoji.

        Raises
        ------
        NotFound
            The emoji requested could not be found.
        HTTPException
            An error occurred fetching the emoji.
        """
        data = await self._connection.http.get_application_emoji(self.application_id, emoji_id)
        return await self._connection.maybe_store_app_emoji(self.application_id, data)

    async def create_emoji(
        self,
        *,
        name: str,
        image: bytes,
    ) -> AppEmoji:
        r"""|coro|

        Creates a custom :class:`AppEmoji` for the application.

        There is currently a limit of 2000 emojis per application.

        Parameters
        -----------
        name: :class:`str`
            The emoji name. Must be at least 2 characters.
        image: :class:`bytes`
            The :term:`py:bytes-like object` representing the image data to use.
            Only JPG, PNG and GIF images are supported.

        Raises
        -------
        HTTPException
            An error occurred creating an emoji.

        Returns
        --------
        :class:`AppEmoji`
            The created emoji.
        """

        img = bytes_to_base64_data(image)
        data = await self._connection.http.create_application_emoji(self.application_id, name, img)
        return await self._connection.maybe_store_app_emoji(self.application_id, data)

    async def delete_emoji(self, emoji: Snowflake) -> None:
        """|coro|

        Deletes the custom :class:`AppEmoji` from the application.

        Parameters
        ----------
        emoji: :class:`abc.Snowflake`
            The emoji you are deleting.

        Raises
        ------
        HTTPException
            An error occurred deleting the emoji.
        """

        await self._connection.http.delete_application_emoji(self.application_id, emoji.id)
        if self._connection.cache_app_emojis and await self._connection.get_emoji(emoji.id):
            await self._connection._remove_emoji(emoji)

    async def fetch_default_sounds(self) -> list[SoundboardSound]:
        """|coro|

        Fetches the bot's default sounds.

        .. versionadded:: 2.7

        Returns
        -------
        List[:class:`.SoundboardSound`]
            The bot's default sounds.
        """
        data = await self._connection.http.get_default_sounds()
        return [SoundboardSound(http=self.http, state=self._connection, data=s) for s in data]
