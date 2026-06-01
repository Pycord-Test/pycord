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

import asyncio
import logging
import signal
from typing import Any, AsyncGenerator, Sequence

import aiohttp

from ..abc import PartialMessageable, PrivateChannel
from ..activity import ActivityTypes, BaseActivity, create_activity
from ..backoff import ExponentialBackoff
from ..channel import GuildChannel, Thread
from ..emoji import AppEmoji, GuildEmoji
from ..enums import ChannelType, Status
from ..errors import (ConnectionClosed, GatewayNotFound, HTTPException,
                      PrivilegedIntentsRequired)
from ..flags import Intents
from ..gateway import DiscordWebSocket, ReconnectWebSocket
from ..guild import Guild
from ..member import Member
from ..mentions import AllowedMentions
from ..message import Message
from ..poll import Poll
from ..soundboard import SoundboardSound
from ..stage_instance import StageInstance
from ..sticker import GuildSticker
from ..user import User
from ..utils.private import SequenceProxy
from .http import HTTPApp

_log = logging.getLogger(__name__)


def _cancel_tasks(loop: asyncio.AbstractEventLoop) -> None:
    tasks = {t for t in asyncio.all_tasks(loop=loop) if not t.done()}

    if not tasks:
        return

    _log.info("Cleaning up after %d tasks.", len(tasks))
    for task in tasks:
        task.cancel()

    loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
    _log.info("All tasks finished cancelling.")

    for task in tasks:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler(
                {
                    "message": "Unhandled exception during Client.run shutdown.",
                    "exception": task.exception(),
                    "task": task,
                }
            )


def _cleanup_loop(loop: asyncio.AbstractEventLoop) -> None:
    try:
        _cancel_tasks(loop)
        loop.run_until_complete(loop.shutdown_asyncgens())
    finally:
        _log.info("Closing the event loop.")
        loop.close()


class GatewayApp(HTTPApp):
    async def get_guilds(self) -> list[Guild]:
        """The guilds that the connected client is a member of."""
        return await self._connection.get_guilds()

    async def get_emojis(self) -> list[GuildEmoji | AppEmoji]:
        """The emojis that the connected client has.

        .. note::

            This only includes the application's emojis if `cache_app_emojis` is ``True``.
        """
        return await self._connection.get_emojis()

    async def get_guild_emojis(self) -> list[GuildEmoji]:
        """The :class:`~discord.GuildEmoji` that the connected client has."""
        return [e for e in await self.get_emojis() if isinstance(e, GuildEmoji)]

    async def get_app_emojis(self) -> list[AppEmoji]:
        """The :class:`~discord.AppEmoji` that the connected client has.

        .. note::

            This is only available if `cache_app_emojis` is ``True``.
        """
        return [e for e in await self.get_emojis() if isinstance(e, AppEmoji)]

    async def get_stickers(self) -> list[GuildSticker]:
        """The stickers that the connected client has.

        .. versionadded:: 2.0
        """
        return await self._connection.get_stickers()

    async def get_polls(self) -> list[Poll]:
        """The polls that the connected client has.

        .. versionadded:: 2.6
        """
        return await self._connection.get_polls()

    async def get_cached_messages(self) -> Sequence[Message]:
        """Read-only list of messages the connected client has cached.

        .. versionadded:: 1.1
        """
        return SequenceProxy(await self._connection.cache.get_all_messages())

    async def get_private_channels(self) -> list[PrivateChannel]:
        """The private channels that the connected client is participating on.

        .. note::

            This returns only up to 128 most recent private channels due to an internal working
            on how Discord deals with private channels.
        """
        return await self._connection.get_private_channels()

    # hooks

    async def _call_before_identify_hook(self, shard_id: int | None, *, initial: bool = False) -> None:
        # This hook is an internal hook that actually calls the public one.
        # It allows the library to have its own hook without stepping on the
        # toes of those who need to override their own hook.
        await self.before_identify_hook(shard_id, initial=initial)

    async def before_identify_hook(self, shard_id: int | None, *, initial: bool = False) -> None:
        """|coro|

        A hook that is called before IDENTIFYing a session. This is useful
        if you wish to have more control over the synchronization of multiple
        IDENTIFYing clients.

        The default implementation sleeps for 5 seconds.

        .. versionadded:: 1.4

        Parameters
        ----------
        shard_id: :class:`int`
            The shard ID that requested being IDENTIFY'd
        initial: :class:`bool`
            Whether this IDENTIFY is the first initial IDENTIFY.
        """

        if not initial:
            await asyncio.sleep(5.0)

    async def connect(self, *, reconnect: bool = True) -> None:
        """|coro|

        Creates a WebSocket connection and lets the WebSocket listen
        to messages from Discord. This is a loop that runs the entire
        event system and miscellaneous aspects of the library. Control
        is not resumed until the WebSocket connection is terminated.

        Parameters
        ----------
        reconnect: :class:`bool`
            If we should attempt reconnecting, either due to internet
            failure or a specific failure on Discord's part. Certain
            disconnects that lead to bad state will not be handled (such as
            invalid sharding payloads or bad tokens).

        Raises
        ------
        :exc:`GatewayNotFound`
            The gateway to connect to Discord is not found. Usually if this
            is thrown then there is a Discord API outage.
        :exc:`ConnectionClosed`
            The WebSocket connection has been terminated.
        """

        backoff = ExponentialBackoff()
        ws_params = {
            "initial": True,
            "shard_id": self.shard_id,
        }
        while not self.is_closed():
            try:
                coro = DiscordWebSocket.from_client(self, **ws_params)
                self.ws = await asyncio.wait_for(coro, timeout=60.0)
                ws_params["initial"] = False
                while True:
                    await self.ws.poll_event()
            except ReconnectWebSocket as e:
                _log.info("Got a request to %s the websocket.", e.op)
                # self.dispatch("disconnect") # TODO: dispatch event
                ws_params.update(
                    sequence=self.ws.sequence,
                    resume=e.resume,
                    session=self.ws.session_id,
                )
                continue
            except (
                OSError,
                HTTPException,
                GatewayNotFound,
                ConnectionClosed,
                aiohttp.ClientError,
                asyncio.TimeoutError,
            ) as exc:
                self.dispatch("disconnect")
                if not reconnect:
                    await self.close()
                    if isinstance(exc, ConnectionClosed) and exc.code == 1000:
                        # clean close, don't re-raise this
                        return
                    raise

                if self.is_closed():
                    return

                # If we get connection reset by peer then try to RESUME
                if isinstance(exc, OSError) and exc.errno in (54, 10054):
                    ws_params.update(
                        sequence=self.ws.sequence,
                        initial=False,
                        resume=True,
                        session=self.ws.session_id,
                    )
                    continue

                # We should only get this when an unhandled close code happens,
                # such as a clean disconnect (1000) or a bad state (bad token, no sharding, etc)
                # sometimes, discord sends us 1000 for unknown reasons, so we should reconnect
                # regardless and rely on is_closed instead
                if isinstance(exc, ConnectionClosed):
                    if exc.code == 4014:
                        raise PrivilegedIntentsRequired(exc.shard_id) from None
                    if exc.code != 1000:
                        await self.close()
                        raise

                retry = backoff.delay()
                _log.exception("Attempting a reconnect in %.2fs", retry)
                await asyncio.sleep(retry)
                # Always try to RESUME the connection
                # If the connection is not RESUME-able then the gateway will invalidate the session.
                # This is apparently what the official Discord client does.
                if self.ws is None:
                    continue
                ws_params.update(sequence=self.ws.sequence, resume=True, session=self.ws.session_id)

    async def close(self) -> None:
        """|coro|

        Closes the connection to Discord.
        """
        if self._closed:
            return

        await self.http.close()
        self._closed = True

        for voice in self.voice_clients:
            try:
                await voice.disconnect(force=True)
            except Exception:
                # if an error happens during disconnects, disregard it.
                pass

        if self.ws is not None and self.ws.open:
            await self.ws.close(code=1000)

        self._ready.clear()

    async def start(self, token: str, *, reconnect: bool = True) -> None:
        """|coro|

        A shorthand coroutine for :meth:`login` + :meth:`connect`.

        Raises
        ------
        TypeError
            An unexpected keyword argument was received.
        """
        await self.login(token)
        await self.connect(reconnect=reconnect)

    def run(self, *args: Any, **kwargs: Any) -> None:
        """A blocking call that abstracts away the event loop
        initialization from you.

        If you want more control over the event loop then this
        function should not be used. Use :meth:`start` coroutine
        or :meth:`connect` + :meth:`login`.

        Roughly Equivalent to: ::

            try:
                loop.run_until_complete(start(*args, **kwargs))
            except KeyboardInterrupt:
                loop.run_until_complete(close())
                # cancel all tasks lingering
            finally:
                loop.close()

        .. warning::

            This function must be the last function to call due to the fact that it
            is blocking. That means that registration of events or anything being
            called after this function call will not execute until it returns.
        """
        loop = self.loop

        try:
            loop.add_signal_handler(signal.SIGINT, loop.stop)
            loop.add_signal_handler(signal.SIGTERM, loop.stop)
        except (NotImplementedError, RuntimeError):
            pass

        async def runner():
            try:
                await self.start(*args, **kwargs)
            finally:
                if not self.is_closed():
                    await self.close()

        def stop_loop_on_completion(f):
            loop.stop()

        future = asyncio.ensure_future(runner(), loop=loop)
        future.add_done_callback(stop_loop_on_completion)
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            _log.info("Received signal to terminate bot and event loop.")
        finally:
            future.remove_done_callback(stop_loop_on_completion)
            _log.info("Cleaning up tasks.")
            _cleanup_loop(loop)

        if not future.cancelled():
            try:
                return future.result()
            except KeyboardInterrupt:
                # I am unsure why this gets raised here but suppress it anyway
                return None

    # properties

    def is_closed(self) -> bool:
        """Indicates if the WebSocket connection is closed."""
        return self._closed

    @property
    def activity(self) -> ActivityTypes | None:
        """The activity being used upon logging in.

        Returns
        -------
        Optional[:class:`.BaseActivity`]
        """
        return create_activity(self._connection._activity)

    @activity.setter
    def activity(self, value: ActivityTypes | None) -> None:
        if value is None:
            self._connection._activity = None
        elif isinstance(value, BaseActivity):
            # ConnectionState._activity is typehinted as ActivityPayload, we're passing Dict[str, Any]
            self._connection._activity = value.to_dict()  # type: ignore
        else:
            raise TypeError("activity must derive from BaseActivity.")

    @property
    def status(self) -> Status:
        """The status being used upon logging on to Discord.

        .. versionadded: 2.0
        """
        if self._connection._status in {state.value for state in Status}:
            return Status(self._connection._status)
        return Status.online

    @status.setter
    def status(self, value: Status) -> None:
        if value is Status.offline:
            self._connection._status = "invisible"
        elif isinstance(value, Status):
            self._connection._status = str(value)
        else:
            raise TypeError("status must derive from Status.")

    @property
    def allowed_mentions(self) -> AllowedMentions | None:
        """The allowed mention configuration.

        .. versionadded:: 1.4
        """
        return self._connection.allowed_mentions

    @allowed_mentions.setter
    def allowed_mentions(self, value: AllowedMentions | None) -> None:
        if value is None or isinstance(value, AllowedMentions):
            self._connection.allowed_mentions = value
        else:
            raise TypeError(f"allowed_mentions must be AllowedMentions not {value.__class__!r}")

    @property
    def intents(self) -> Intents:
        """The intents configured for this connection.

        .. versionadded:: 1.5
        """
        return self._connection.intents

    async def get_users(self) -> list[User]:
        """Returns a list of all the users the bot can see."""
        return await self._connection.cache.get_all_users()

    async def get_channel(self, id: int, /) -> GuildChannel | Thread | PrivateChannel | None:
        """Returns a channel or thread with the given ID.

        Parameters
        ----------
        id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[Union[:class:`.abc.GuildChannel`, :class:`.Thread`, :class:`.abc.PrivateChannel`]]
            The returned channel or ``None`` if not found.
        """
        return await self._connection.get_channel(id)

    async def get_message(self, id: int, /) -> Message | None:
        """Returns a message the given ID.

        This is useful if you have a message_id but don't want to do an API call
        to access the message.

        Parameters
        ----------
        id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`.Message`]
            The returned message or ``None`` if not found.
        """
        return await self._connection._get_message(id)

    def get_partial_messageable(self, id: int, *, type: ChannelType | None = None) -> PartialMessageable:
        """Returns a partial messageable with the given channel ID.

        This is useful if you have a channel_id but don't want to do an API call
        to send messages to it.

        .. versionadded:: 2.0

        Parameters
        ----------
        id: :class:`int`
            The channel ID to create a partial messageable for.
        type: Optional[:class:`.ChannelType`]
            The underlying channel type for the partial messageable.

        Returns
        -------
        :class:`.PartialMessageable`
            The partial messageable
        """
        return PartialMessageable(state=self._connection, id=id, type=type)

    async def get_stage_instance(self, id: int, /) -> StageInstance | None:
        """Returns a stage instance with the given stage channel ID.

        .. versionadded:: 2.0

        Parameters
        ----------
        id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`.StageInstance`]
            The stage instance or ``None`` if not found.
        """
        from ..channel import StageChannel

        channel = await self._connection.get_channel(id)

        if isinstance(channel, StageChannel):
            return channel.instance

    async def get_guild(self, id: int, /) -> Guild | None:
        """Returns a guild with the given ID.

        Parameters
        ----------
        id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`.Guild`]
            The guild or ``None`` if not found.
        """
        return await self._connection._get_guild(id)

    async def get_user(self, id: int, /) -> User | None:
        """Returns a user with the given ID.

        Parameters
        ----------
        id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`~discord.User`]
            The user or ``None`` if not found.
        """
        return await self._connection.get_user(id)

    async def get_emoji(self, id: int, /) -> GuildEmoji | AppEmoji | None:
        """Returns an emoji with the given ID.

        Parameters
        ----------
        id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`.GuildEmoji` | :class:`.AppEmoji`]
            The custom emoji or ``None`` if not found.
        """
        return await self._connection.get_emoji(id)

    async def get_sticker(self, id: int, /) -> GuildSticker | None:
        """Returns a guild sticker with the given ID.

        .. versionadded:: 2.0

        .. note::

            To retrieve standard stickers, use :meth:`.fetch_sticker`.
            or :meth:`.fetch_premium_sticker_packs`.

        Returns
        -------
        Optional[:class:`.GuildSticker`]
            The sticker or ``None`` if not found.
        """
        return await self._connection.get_sticker(id)

    async def get_poll(self, id: int, /) -> Poll | None:
        """Returns a poll attached to the given message ID.

        Parameters
        ----------
        id: :class:`int`
            The message ID of the poll to search for.

        Returns
        -------
        Optional[:class:`.Poll`]
            The poll or ``None`` if not found.
        """
        return await self._connection.get_poll(id)

    async def get_all_channels(self) -> AsyncGenerator[GuildChannel]:
        """A generator that retrieves every :class:`.abc.GuildChannel` the client can 'access'.

        This is equivalent to: ::

            for guild in await client.get_guilds():
                for channel in guild.channels:
                    yield channel

        .. note::

            Just because you receive a :class:`.abc.GuildChannel` does not mean that
            you can communicate in said channel. :meth:`.abc.GuildChannel.permissions_for` should
            be used for that.

        Yields
        ------
        :class:`.abc.GuildChannel`
            A channel the client can 'access'.
        """

        for guild in await self.get_guilds():
            for channel in guild.channels:
                yield channel

    async def get_all_members(self) -> AsyncGenerator[Member]:
        """Returns a generator with every :class:`.Member` the client can see.

        This is equivalent to: ::

            for guild in await client.get_guilds():
                for member in guild.members:
                    yield member

        Yields
        ------
        :class:`.Member`
            A member the client can see.
        """
        for guild in await self.get_guilds():
            for member in guild.members:
                yield member

    async def wait_until_ready(self) -> None:
        """|coro|

        Waits until the client's internal cache is all ready.
        """
        await self._ready.wait()

    async def change_presence(
        self,
        *,
        activity: BaseActivity | None = None,
        status: Status | None = None,
    ):
        """|coro|

        Changes the client's presence.

        Parameters
        ----------
        activity: Optional[:class:`.BaseActivity`]
            The activity being done. ``None`` if no currently active activity is done.
        status: Optional[:class:`.Status`]
            Indicates what status to change to. If ``None``, then
            :attr:`.Status.online` is used.

        Raises
        ------
        :exc:`InvalidArgument`
            If the ``activity`` parameter is not the proper type.

        Example
        -------

        .. code-block:: python3

            game = discord.Game("with the API")
            await client.change_presence(status=discord.Status.idle, activity=game)

        .. versionchanged:: 2.0
            Removed the ``afk`` keyword-only parameter.
        """

        if status is None:
            status_str = "online"
            status = Status.online
        elif status is Status.offline:
            status_str = "invisible"
            status = Status.offline
        else:
            status_str = str(status)

        await self.ws.change_presence(activity=activity, status=status_str)

        for guild in await self._connection.get_guilds():
            me = guild.me
            if me is None:
                continue

            me.activities = (activity,) if activity is not None else ()
            me.status = status

    def get_sound(self, sound_id: int) -> SoundboardSound | None:
        """Gets a :class:`.Sound` from the bot's sound cache.

        .. versionadded:: 2.7

        Parameters
        ----------
        sound_id: :class:`int`
            The ID of the sound to get.

        Returns
        -------
        Optional[:class:`.SoundboardSound`]
            The sound with the given ID.
        """
        return self._connection._get_sound(sound_id)

    @property
    def sounds(self) -> list[SoundboardSound]:
        """A list of all the sounds the bot can see.

        .. versionadded:: 2.7
        """
        return self._connection.sounds
