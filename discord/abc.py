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
import time
from typing import (
    TYPE_CHECKING,
    Callable,
    Iterable,
    Protocol,
    Sequence,
    TypeAlias,
    TypeVar,
    Union,
    overload,
    runtime_checkable,
)

from . import utils
from .context_managers import Typing
from .errors import ClientException, InvalidArgument
from .file import File, VoiceMessage
from .flags import MessageFlags
from .iterators import HistoryIterator, MessagePinIterator
from .mentions import AllowedMentions
from .sticker import GuildSticker, StickerItem
from .utils.private import warn_deprecated
from .voice_client import VoiceClient, VoiceProtocol

__all__ = (
    "Snowflake",
    "User",
    "PrivateChannel",
    "Messageable",
    "Connectable",
    "Mentionable",
)

T = TypeVar("T", bound=VoiceProtocol)

if TYPE_CHECKING:
    from datetime import datetime

    from .app.state import ConnectionState
    from .asset import Asset
    from .channel import (
        DMChannel,
        GroupChannel,
        PartialMessageable,
        StageChannel,
        TextChannel,
        VoiceChannel,
    )
    from .channel.thread import Thread
    from .client import Client
    from .embeds import Embed
    from .message import Message, MessageReference, PartialMessage
    from .poll import Poll
    from .types.channel import OverwriteType
    from .types.channel import PermissionOverwrite as PermissionOverwritePayload
    from .ui.view import View
    from .user import ClientUser

    PartialMessageableChannel = TextChannel | VoiceChannel | StageChannel | Thread | DMChannel | PartialMessageable
    MessageableChannel = PartialMessageableChannel | GroupChannel
SnowflakeTime: TypeAlias = "Snowflake | datetime"

MISSING = utils.MISSING


async def _single_delete_strategy(messages: Iterable[Message], *, reason: str | None = None):
    for m in messages:
        await m.delete(reason=reason)


async def _purge_messages_helper(
    channel: TextChannel | StageChannel | Thread | VoiceChannel,
    *,
    limit: int | None = 100,
    check: Callable[[Message], bool] | utils.Undefined = MISSING,
    before: SnowflakeTime | None = None,
    after: SnowflakeTime | None = None,
    around: SnowflakeTime | None = None,
    oldest_first: bool | None = False,
    bulk: bool = True,
    reason: str | None = None,
) -> list[Message]:
    if check is MISSING:
        check = lambda m: True

    iterator = channel.history(
        limit=limit,
        before=before,
        after=after,
        oldest_first=oldest_first,
        around=around,
    )
    ret: list[Message] = []
    count = 0

    minimum_time = int((time.time() - 14 * 24 * 60 * 60) * 1000.0 - 1420070400000) << 22
    strategy = channel.delete_messages if bulk else _single_delete_strategy

    async for message in iterator:
        if count == 100:
            to_delete = ret[-100:]
            await strategy(to_delete, reason=reason)
            count = 0
            await asyncio.sleep(1)

        if not check(message):
            continue

        if message.id < minimum_time:
            # older than 14 days old
            if count == 1:
                await ret[-1].delete(reason=reason)
            elif count >= 2:
                to_delete = ret[-count:]
                await strategy(to_delete, reason=reason)

            count = 0
            strategy = _single_delete_strategy

        count += 1
        ret.append(message)

    # Some messages remaining to poll
    if count >= 2:
        # more than 2 messages -> bulk delete
        to_delete = ret[-count:]
        await strategy(to_delete, reason=reason)
    elif count == 1:
        # delete a single message
        await ret[-1].delete(reason=reason)

    return ret


@runtime_checkable
class Snowflake(Protocol):
    """An ABC that details the common operations on a Discord model.

    Almost all :ref:`Discord models <discord_api_models>` meet this
    abstract base class.

    If you want to create a snowflake on your own, consider using
    :class:`.Object`.

    Attributes
    ----------
    id: :class:`int`
        The model's unique ID.
    """

    __slots__ = ()
    id: int


@runtime_checkable
class User(Snowflake, Protocol):
    """An ABC that details the common operations on a Discord user.

    The following implement this ABC:

    - :class:`~discord.User`
    - :class:`~discord.ClientUser`
    - :class:`~discord.Member`

    This ABC must also implement :class:`~discord.abc.Snowflake`.

    Attributes
    ----------
    name: :class:`str`
        The user's username.
    discriminator: :class:`str`
        The user's discriminator.

        .. note::

            If the user has migrated to the new username system, this will always be "0".
    global_name: :class:`str`
        The user's global name.

        .. versionadded:: 2.5
    avatar: :class:`~discord.Asset`
        The avatar asset the user has.
    bot: :class:`bool`
        If the user is a bot account.
    """

    __slots__ = ()

    name: str
    discriminator: str
    global_name: str | None
    avatar: Asset
    bot: bool

    @property
    def display_name(self) -> str:
        """Returns the user's display name."""
        raise NotImplementedError

    @property
    def mention(self) -> str:
        """Returns a string that allows you to mention the given user."""
        raise NotImplementedError


@runtime_checkable
class PrivateChannel(Snowflake, Protocol):
    """An ABC that details the common operations on a private Discord channel.

    The following implement this ABC:

    - :class:`~discord.DMChannel`
    - :class:`~discord.GroupChannel`

    This ABC must also implement :class:`~discord.abc.Snowflake`.

    Attributes
    ----------
    me: :class:`~discord.ClientUser`
        The user presenting yourself.
    """

    __slots__ = ()

    me: ClientUser


class _Overwrites:
    __slots__ = ("id", "allow", "deny", "type")

    ROLE = 0
    MEMBER = 1

    def __init__(self, data: PermissionOverwritePayload):
        self.id: int = int(data["id"])
        self.allow: int = int(data.get("allow", 0))
        self.deny: int = int(data.get("deny", 0))
        self.type: OverwriteType = data["type"]

    def _asdict(self) -> PermissionOverwritePayload:
        return {
            "id": self.id,
            "allow": str(self.allow),
            "deny": str(self.deny),
            "type": self.type,
        }

    def is_role(self) -> bool:
        return self.type == self.ROLE

    def is_member(self) -> bool:
        return self.type == self.MEMBER


class Messageable:
    """An ABC that details the common operations on a model that can send messages.

    The following implement this ABC:

    - :class:`~discord.TextChannel`
    - :class:`~discord.VoiceChannel`
    - :class:`~discord.StageChannel`
    - :class:`~discord.DMChannel`
    - :class:`~discord.GroupChannel`
    - :class:`~discord.User`
    - :class:`~discord.Member`
    - :class:`~discord.ext.commands.Context`
    - :class:`~discord.Thread`
    - :class:`~discord.ApplicationContext`
    """

    __slots__ = ()
    _state: ConnectionState

    async def _get_channel(self) -> MessageableChannel:
        raise NotImplementedError

    @overload
    async def send(
        self,
        content: str | None = ...,
        *,
        tts: bool = ...,
        embed: Embed = ...,
        file: File = ...,
        stickers: Sequence[GuildSticker | StickerItem] = ...,
        delete_after: float = ...,
        nonce: int | str = ...,
        enforce_nonce: bool = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Message | MessageReference | PartialMessage = ...,
        mention_author: bool = ...,
        view: View = ...,
        poll: Poll = ...,
        suppress: bool = ...,
        silent: bool = ...,
    ) -> Message: ...

    @overload
    async def send(
        self,
        content: str | None = ...,
        *,
        tts: bool = ...,
        embed: Embed = ...,
        files: list[File] = ...,
        stickers: Sequence[GuildSticker | StickerItem] = ...,
        delete_after: float = ...,
        nonce: int | str = ...,
        enforce_nonce: bool = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Message | MessageReference | PartialMessage = ...,
        mention_author: bool = ...,
        view: View = ...,
        poll: Poll = ...,
        suppress: bool = ...,
        silent: bool = ...,
    ) -> Message: ...

    @overload
    async def send(
        self,
        content: str | None = ...,
        *,
        tts: bool = ...,
        embeds: list[Embed] = ...,
        file: File = ...,
        stickers: Sequence[GuildSticker | StickerItem] = ...,
        delete_after: float = ...,
        nonce: int | str = ...,
        enforce_nonce: bool = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Message | MessageReference | PartialMessage = ...,
        mention_author: bool = ...,
        view: View = ...,
        poll: Poll = ...,
        suppress: bool = ...,
        silent: bool = ...,
    ) -> Message: ...

    @overload
    async def send(
        self,
        content: str | None = ...,
        *,
        tts: bool = ...,
        embeds: list[Embed] = ...,
        files: list[File] = ...,
        stickers: Sequence[GuildSticker | StickerItem] = ...,
        delete_after: float = ...,
        nonce: int | str = ...,
        enforce_nonce: bool = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Message | MessageReference | PartialMessage = ...,
        mention_author: bool = ...,
        view: View = ...,
        poll: Poll = ...,
        suppress: bool = ...,
        silent: bool = ...,
    ) -> Message: ...

    async def send(
        self,
        content=None,
        *,
        tts=None,
        embed=None,
        embeds=None,
        file=None,
        files=None,
        stickers=None,
        delete_after=None,
        nonce=None,
        enforce_nonce=None,
        allowed_mentions=None,
        reference=None,
        mention_author=None,
        view=None,
        poll=None,
        suppress=None,
        silent=None,
    ):
        """|coro|

        Sends a message to the destination with the content given.

        The content must be a type that can convert to a string through ``str(content)``.
        If the content is set to ``None`` (the default), then the ``embed`` parameter must
        be provided.

        To upload a single file, the ``file`` parameter should be used with a
        single :class:`~discord.File` object. To upload multiple files, the ``files``
        parameter should be used with a :class:`list` of :class:`~discord.File` objects.
        **Specifying both parameters will lead to an exception**.

        To upload a single embed, the ``embed`` parameter should be used with a
        single :class:`~discord.Embed` object. To upload multiple embeds, the ``embeds``
        parameter should be used with a :class:`list` of :class:`~discord.Embed` objects.
        **Specifying both parameters will lead to an exception**.

        Parameters
        ----------
        content: Optional[:class:`str`]
            The content of the message to send.
        tts: :class:`bool`
            Indicates if the message should be sent using text-to-speech.
        embed: :class:`~discord.Embed`
            The rich embed for the content.
        file: :class:`~discord.File`
            The file to upload.
        files: List[:class:`~discord.File`]
            A list of files to upload. Must be a maximum of 10.
        nonce: Union[:class:`str`, :class:`int`]
            The nonce to use for sending this message. If the message was successfully sent,
            then the message will have a nonce with this value.
        enforce_nonce: Optional[:class:`bool`]
            Whether :attr:`nonce` is enforced to be validated.

            .. versionadded:: 2.5
        delete_after: :class:`float`
            If provided, the number of seconds to wait in the background
            before deleting the message we just sent. If the deletion fails,
            then it is silently ignored.
        allowed_mentions: :class:`~discord.AllowedMentions`
            Controls the mentions being processed in this message. If this is
            passed, then the object is merged with :attr:`~discord.Client.allowed_mentions`.
            The merging behaviour only overrides attributes that have been explicitly passed
            to the object, otherwise it uses the attributes set in :attr:`~discord.Client.allowed_mentions`.
            If no object is passed at all then the defaults given by :attr:`~discord.Client.allowed_mentions`
            are used instead.

            .. versionadded:: 1.4

        reference: Union[:class:`~discord.Message`, :class:`~discord.MessageReference`, :class:`~discord.PartialMessage`]
            A reference to the :class:`~discord.Message` being replied to or forwarded. This can be created using
            :meth:`~discord.Message.to_reference`.
            When replying, you can control whether this mentions the author of the referenced message using the
            :attr:`~discord.AllowedMentions.replied_user` attribute of ``allowed_mentions`` or by
            setting ``mention_author``.

            .. versionadded:: 1.6

        mention_author: Optional[:class:`bool`]
            If set, overrides the :attr:`~discord.AllowedMentions.replied_user` attribute of ``allowed_mentions``.

            .. versionadded:: 1.6
        view: :class:`discord.ui.View`
            A Discord UI View to add to the message.
        embeds: List[:class:`~discord.Embed`]
            A list of embeds to upload. Must be a maximum of 10.

            .. versionadded:: 2.0
        stickers: Sequence[Union[:class:`~discord.GuildSticker`, :class:`~discord.StickerItem`]]
            A list of stickers to upload. Must be a maximum of 3.

            .. versionadded:: 2.0
        suppress: :class:`bool`
            Whether to suppress embeds for the message.
        silent: :class:`bool`
            Whether to suppress push and desktop notifications for the message.

            .. versionadded:: 2.4
        poll: :class:`Poll`
            The poll to send.

            .. versionadded:: 2.6

        Returns
        -------
        :class:`~discord.Message`
            The message that was sent.

        Raises
        ------
        ~discord.HTTPException
            Sending the message failed.
        ~discord.Forbidden
            You do not have the proper permissions to send the message.
        ~discord.InvalidArgument
            The ``files`` list is not of the appropriate size,
            you specified both ``file`` and ``files``,
            or you specified both ``embed`` and ``embeds``,
            or the ``reference`` object is not a :class:`~discord.Message`,
            :class:`~discord.MessageReference` or :class:`~discord.PartialMessage`.
        """

        channel = await self._get_channel()
        state = self._state
        content = str(content) if content is not None else None

        if embed is not None and embeds is not None:
            raise InvalidArgument("cannot pass both embed and embeds parameter to send()")

        if embed is not None:
            embed = embed.to_dict()

        elif embeds is not None:
            if len(embeds) > 10:
                raise InvalidArgument("embeds parameter must be a list of up to 10 elements")
            embeds = [embed.to_dict() for embed in embeds]

        flags = MessageFlags(
            suppress_embeds=bool(suppress),
            suppress_notifications=bool(silent),
        )

        if stickers is not None:
            stickers = [sticker.id for sticker in stickers]

        if allowed_mentions is None:
            allowed_mentions = state.allowed_mentions and state.allowed_mentions.to_dict()
        elif state.allowed_mentions is not None:
            allowed_mentions = state.allowed_mentions.merge(allowed_mentions).to_dict()
        else:
            allowed_mentions = allowed_mentions.to_dict()

        if mention_author is not None:
            allowed_mentions = allowed_mentions or AllowedMentions().to_dict()
            allowed_mentions["replied_user"] = bool(mention_author)

        _reference = None
        if reference is not None:
            try:
                _reference = reference.to_message_reference_dict()
                from .message import MessageReference

                if not isinstance(reference, MessageReference):
                    warn_deprecated(
                        f"Passing {type(reference).__name__} to reference",
                        "MessageReference",
                        "2.7",
                        "3.0",
                    )
            except AttributeError:
                raise InvalidArgument(
                    "reference parameter must be Message, MessageReference, or PartialMessage"
                ) from None

        if view:
            if not hasattr(view, "__discord_ui_view__"):
                raise InvalidArgument(f"view parameter must be View not {view.__class__!r}")

            components = view.to_components()
            if view.is_components_v2():
                if embeds or content:
                    raise TypeError("cannot send embeds or content with a view using v2 component logic")
                flags.is_components_v2 = True
        else:
            components = None

        if poll:
            poll = poll.to_dict()

        if file is not None and files is not None:
            raise InvalidArgument("cannot pass both file and files parameter to send()")

        if file is not None:
            if not isinstance(file, File):
                raise InvalidArgument("file parameter must be File")
            files = [file]
        elif files is not None:
            if len(files) > 10:
                raise InvalidArgument("files parameter must be a list of up to 10 elements")
            elif not all(isinstance(file, File) for file in files):
                raise InvalidArgument("files parameter must be a list of File")

        if files is not None:
            flags = flags + MessageFlags(is_voice_message=any(isinstance(f, VoiceMessage) for f in files))
            try:
                data = await state.http.send_files(
                    channel.id,
                    files=files,
                    content=content,
                    tts=tts,
                    embed=embed,
                    embeds=embeds,
                    nonce=nonce,
                    enforce_nonce=enforce_nonce,
                    allowed_mentions=allowed_mentions,
                    message_reference=_reference,
                    stickers=stickers,
                    components=components,
                    flags=flags.value,
                    poll=poll,
                )
            finally:
                for f in files:
                    f.close()
        else:
            data = await state.http.send_message(
                channel.id,
                content,
                tts=tts,
                embed=embed,
                embeds=embeds,
                nonce=nonce,
                enforce_nonce=enforce_nonce,
                allowed_mentions=allowed_mentions,
                message_reference=_reference,
                stickers=stickers,
                components=components,
                flags=flags.value,
                poll=poll,
            )

        ret = state.create_message(channel=channel, data=data)
        if view:
            if view.is_dispatchable():
                await state.store_view(view, ret.id)
            view.message = ret
            view.refresh(ret.components)

        if delete_after is not None:
            await ret.delete(delay=delete_after)
        return ret

    async def trigger_typing(self) -> None:
        """|coro|

        Triggers a *typing* indicator to the destination.

        *Typing* indicator will go away after 10 seconds, or after a message is sent.
        """

        channel = await self._get_channel()
        await self._state.http.send_typing(channel.id)

    def typing(self) -> Typing:
        """Returns a context manager that allows you to type for an indefinite period of time.

        This is useful for denoting long computations in your bot.

        .. note::

            This is both a regular context manager and an async context manager.
            This means that both ``with`` and ``async with`` work with this.

        Example Usage: ::

            async with channel.typing():
                # simulate something heavy
                await asyncio.sleep(10)

            await channel.send("done!")
        """
        return Typing(self)

    async def fetch_message(self, id: int, /) -> Message:
        """|coro|

        Retrieves a single :class:`~discord.Message` from the destination.

        Parameters
        ----------
        id: :class:`int`
            The message ID to look for.

        Returns
        -------
        :class:`~discord.Message`
            The message asked for.

        Raises
        ------
        ~discord.NotFound
            The specified message was not found.
        ~discord.Forbidden
            You do not have the permissions required to get a message.
        ~discord.HTTPException
            Retrieving the message failed.
        """

        channel = await self._get_channel()
        data = await self._state.http.get_message(channel.id, id)
        return self._state.create_message(channel=channel, data=data)

    def pins(
        self,
        *,
        limit: int | None = 50,
        before: SnowflakeTime | None = None,
    ) -> MessagePinIterator:
        """Returns a :class:`~discord.MessagePinIterator` that enables receiving the destination's pinned messages.

        You must have :attr:`~discord.Permissions.read_message_history` permissions to use this.

        .. warning::

            Starting from version 3.0, `await channel.pins()` will no longer return a list of :class:`Message`. See examples below for new usage instead.

        Parameters
        ----------
        limit: Optional[:class:`int`]
            The number of pinned messages to retrieve.
            If ``None``, retrieves every pinned message in the channel.
        before: Optional[Union[:class:`~discord.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve messages pinned before this datetime.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.

        Yields
        ------
        :class:`~discord.MessagePin`
            The pinned message.

        Raises
        ------
        ~discord.Forbidden
            You do not have permissions to get pinned messages.
        ~discord.HTTPException
            The request to get pinned messages failed.

        Examples
        --------

        Usage ::

            counter = 0
            async for pin in channel.pins(limit=250):
                if pin.message.author == client.user:
                    counter += 1

        Flattening into a list: ::

            pins = await channel.pins(limit=None).flatten()
            # pins is now a list of MessagePin...

        All parameters are optional.
        """
        return MessagePinIterator(
            self,
            limit=limit,
            before=before,
        )

    def can_send(self, *objects) -> bool:
        """Returns a :class:`bool` indicating whether you have the permissions to send the object(s).

        Returns
        -------
        :class:`bool`
            Indicates whether you have the permissions to send the object(s).

        Raises
        ------
        TypeError
            An invalid type has been passed.
        """
        mapping = {
            "Message": "send_messages",
            "Embed": "embed_links",
            "File": "attach_files",
            "GuildEmoji": "use_external_emojis",
            "GuildSticker": "use_external_stickers",
        }
        # Can't use channel = await self._get_channel() since its async
        if hasattr(self, "permissions_for"):
            channel = self
        elif hasattr(self, "channel") and type(self.channel).__name__ not in (
            "DMChannel",
            "GroupChannel",
        ):
            channel = self.channel
        else:
            return True  # Permissions don't exist for User DMs

        objects = (None,) + objects  # Makes sure we check for send_messages first

        for obj in objects:
            try:
                if obj is None:
                    permission = mapping["Message"]
                else:
                    permission = mapping.get(type(obj).__name__) or mapping[obj.__name__]

                if type(obj).__name__ == "GuildEmoji":
                    if obj._to_partial().is_unicode_emoji or obj.guild_id == channel.guild.id:
                        continue
                elif type(obj).__name__ == "GuildSticker":
                    if obj.guild_id == channel.guild.id:
                        continue

            except (KeyError, AttributeError) as e:
                raise TypeError(f"The object {obj} is of an invalid type.") from e

            if not getattr(channel.permissions_for(channel.guild.me), permission):
                return False

        return True

    def history(
        self,
        *,
        limit: int | None = 100,
        before: SnowflakeTime | None = None,
        after: SnowflakeTime | None = None,
        around: SnowflakeTime | None = None,
        oldest_first: bool | None = None,
    ) -> HistoryIterator:
        """Returns an :class:`~discord.AsyncIterator` that enables receiving the destination's message history.

        You must have :attr:`~discord.Permissions.read_message_history` permissions to use this.

        Parameters
        ----------
        limit: Optional[:class:`int`]
            The number of messages to retrieve.
            If ``None``, retrieves every message in the channel. Note, however,
            that this would make it a slow operation.
        before: Optional[Union[:class:`~discord.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve messages before this date or message.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
        after: Optional[Union[:class:`~discord.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve messages after this date or message.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
        around: Optional[Union[:class:`~discord.abc.Snowflake`, :class:`datetime.datetime`]]
            Retrieve messages around this date or message.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
            When using this argument, the maximum limit is 101. Note that if the limit is an
            even number, then this will return at most limit + 1 messages.
        oldest_first: Optional[:class:`bool`]
            If set to ``True``, return messages in oldest->newest order. Defaults to ``True`` if
            ``after`` is specified, otherwise ``False``.

        Yields
        ------
        :class:`~discord.Message`
            The message with the message data parsed.

        Raises
        ------
        ~discord.Forbidden
            You do not have permissions to get channel message history.
        ~discord.HTTPException
            The request to get message history failed.

        Examples
        --------

        Usage ::

            counter = 0
            async for message in channel.history(limit=200):
                if message.author == client.user:
                    counter += 1

        Flattening into a list: ::

            messages = await channel.history(limit=123).flatten()
            # messages is now a list of Message...

        All parameters are optional.
        """
        return HistoryIterator(
            self,
            limit=limit,
            before=before,
            after=after,
            around=around,
            oldest_first=oldest_first,
        )


class Connectable(Protocol):
    """An ABC that details the common operations on a channel that can
    connect to a voice server.

    The following implement this ABC:

    - :class:`~discord.VoiceChannel`
    - :class:`~discord.StageChannel`

    Note
    ----
    This ABC is not decorated with :func:`typing.runtime_checkable`, so will fail :func:`isinstance`/:func:`issubclass`
    checks.
    """

    __slots__ = ()
    _state: ConnectionState

    def _get_voice_client_key(self) -> tuple[int, str]:
        raise NotImplementedError

    def _get_voice_state_pair(self) -> tuple[int, int]:
        raise NotImplementedError

    async def connect(
        self,
        *,
        timeout: float = 60.0,
        reconnect: bool = True,
        cls: Callable[[Client, Connectable], T] = VoiceClient,
    ) -> T:
        """|coro|

        Connects to voice and creates a :class:`VoiceClient` to establish
        your connection to the voice server.

        This requires :attr:`Intents.voice_states`.

        Parameters
        ----------
        timeout: :class:`float`
            The timeout in seconds to wait for the voice endpoint.
        reconnect: :class:`bool`
            Whether the bot should automatically attempt
            a reconnect if a part of the handshake fails
            or the gateway goes down.
        cls: Type[:class:`VoiceProtocol`]
            A type that subclasses :class:`~discord.VoiceProtocol` to connect with.
            Defaults to :class:`~discord.VoiceClient`.

        Returns
        -------
        :class:`~discord.VoiceProtocol`
            A voice client that is fully connected to the voice server.

        Raises
        ------
        asyncio.TimeoutError
            Could not connect to the voice channel in time.
        ~discord.ClientException
            You are already connected to a voice channel.
        ~discord.opus.OpusNotLoaded
            The opus library has not been loaded.
        """

        key_id, _ = self._get_voice_client_key()
        state = self._state

        if state._get_voice_client(key_id):
            raise ClientException("Already connected to a voice channel.")

        client = state._get_client()
        voice = cls(client, self)

        if not isinstance(voice, VoiceProtocol):
            raise TypeError("Type must meet VoiceProtocol abstract base class.")

        state._add_voice_client(key_id, voice)

        try:
            await voice.connect(timeout=timeout, reconnect=reconnect)
        except asyncio.TimeoutError:
            try:
                await voice.disconnect(force=True)
            except Exception:
                # we don't care if disconnect failed because connection failed
                pass
            raise  # re-raise

        return voice


@runtime_checkable
class Mentionable(Protocol):
    """An ABC that details the common operations on an object that can
    be mentioned.
    """

    def mention(self) -> str: ...
