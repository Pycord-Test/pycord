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
import copy
import inspect
import itertools
import logging
import os
from collections import OrderedDict, deque
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Coroutine,
    Deque,
    Sequence,
    TypeVar,
    Union,
    cast,
)

from discord.soundboard import SoundboardSound

from .. import utils
from ..activity import BaseActivity
from ..automod import AutoModRule
from ..channel import *
from ..channel import _channel_factory
from ..channel.thread import Thread, ThreadMember
from ..emoji import AppEmoji, GuildEmoji
from ..enums import ChannelType, InteractionType, Status, try_enum
from ..flags import ApplicationFlags, Intents, MemberCacheFlags
from ..guild import Guild
from ..interactions import Interaction
from ..invite import Invite
from ..member import Member
from ..mentions import AllowedMentions
from ..message import Message
from ..monetization import Entitlement, Subscription
from ..object import Object
from ..partial_emoji import PartialEmoji
from ..poll import Poll, PollAnswerCount
from ..raw_models import *
from ..role import Role
from ..sticker import GuildSticker
from ..ui.modal import Modal
from ..ui.view import View
from ..user import ClientUser, User
from ..utils.private import get_as_snowflake, parse_time, sane_wait_for
from .cache import Cache
from .event_emitter import EventEmitter

if TYPE_CHECKING:
    from ..abc import PrivateChannel
    from ..client import Client
    from ..gateway import DiscordWebSocket
    from ..guild import GuildChannel, VocalGuildChannel
    from ..http import HTTPClient
    from ..message import MessageableChannel
    from ..types.activity import Activity as ActivityPayload
    from ..types.channel import DMChannel as DMChannelPayload
    from ..types.emoji import Emoji as EmojiPayload
    from ..types.guild import Guild as GuildPayload
    from ..types.message import Message as MessagePayload
    from ..types.poll import Poll as PollPayload
    from ..types.sticker import GuildSticker as GuildStickerPayload
    from ..types.user import User as UserPayload
    from ..voice_client import VoiceClient

    T = TypeVar("T")
    CS = TypeVar("CS", bound="ConnectionState")
    Channel = GuildChannel | VocalGuildChannel | PrivateChannel | PartialMessageable


class ChunkRequest:
    def __init__(
        self,
        guild_id: int,
        loop: asyncio.AbstractEventLoop,
        resolver: Callable[[int], Any],
        *,
        cache: bool = True,
    ) -> None:
        self.guild_id: int = guild_id
        self.resolver: Callable[[int], Any] = resolver
        self.loop: asyncio.AbstractEventLoop = loop
        self.cache: bool = cache
        self.nonce: str = os.urandom(16).hex()
        self.buffer: list[Member] = []
        self.waiters: list[asyncio.Future[list[Member]]] = []

    async def add_members(self, members: list[Member]) -> None:
        self.buffer.extend(members)
        if self.cache:
            guild = self.resolver(self.guild_id)
            if inspect.isawaitable(guild):
                guild = await guild
            if guild is None:
                return

            for member in members:
                existing = await guild.get_member(member.id)
                if existing is None or existing.joined_at is None:
                    await guild._add_member(member)

    async def wait(self) -> list[Member]:
        future = self.loop.create_future()
        self.waiters.append(future)
        try:
            return await future
        finally:
            self.waiters.remove(future)

    def get_future(self) -> asyncio.Future[list[Member]]:
        future = self.loop.create_future()
        self.waiters.append(future)
        return future

    def done(self) -> None:
        for future in self.waiters:
            if not future.done():
                future.set_result(self.buffer)


_log = logging.getLogger(__name__)


async def logging_coroutine(coroutine: Coroutine[Any, Any, T], *, info: str) -> None:
    try:
        await coroutine
    except Exception:
        _log.exception("Exception occurred during %s", info)


class ConnectionState:
    if TYPE_CHECKING:
        _get_websocket: Callable[..., DiscordWebSocket]
        _get_client: Callable[..., Client]
        _parsers: dict[str, Callable[[dict[str, Any]], None]]

    def __init__(
        self,
        *,
        cache: Cache,
        handlers: dict[str, Callable],
        hooks: dict[str, Callable],
        http: HTTPClient,
        loop: asyncio.AbstractEventLoop,
        **options: Any,
    ) -> None:
        self.loop: asyncio.AbstractEventLoop = loop
        self.http: HTTPClient = http
        self.max_messages: int | None = options.get("max_messages", 1000)
        if self.max_messages is not None and self.max_messages <= 0:
            self.max_messages = 1000

        self.handlers: dict[str, Callable] = handlers
        self.hooks: dict[str, Callable] = hooks
        self.shard_count: int | None = None
        self._ready_task: asyncio.Task | None = None
        self.application_id: int | None = get_as_snowflake(options, "application_id")
        self.application_flags: ApplicationFlags | None = None
        self.heartbeat_timeout: float = options.get("heartbeat_timeout", 60.0)
        self.guild_ready_timeout: float = options.get("guild_ready_timeout", 2.0)
        if self.guild_ready_timeout < 0:
            raise ValueError("guild_ready_timeout cannot be negative")

        allowed_mentions = options.get("allowed_mentions")

        if allowed_mentions is not None and not isinstance(allowed_mentions, AllowedMentions):
            raise TypeError("allowed_mentions parameter must be AllowedMentions")

        self.allowed_mentions: AllowedMentions | None = allowed_mentions
        self._chunk_requests: dict[int | str, ChunkRequest] = {}

        activity = options.get("activity", None)
        if activity:
            if not isinstance(activity, BaseActivity):
                raise TypeError("activity parameter must derive from BaseActivity.")

            activity = activity.to_dict()

        status = options.get("status", None)
        if status:
            status = "invisible" if status is Status.offline else str(status)
        intents = options.get("intents", None)
        if intents is None:
            intents = Intents.default()

        elif not isinstance(intents, Intents):
            raise TypeError(f"intents parameter must be Intent not {type(intents)!r}")
        if not intents.guilds:
            _log.warning("Guilds intent seems to be disabled. This may cause state related issues.")

        self._chunk_guilds: bool = options.get("chunk_guilds_at_startup", intents.members)

        # Ensure these two are set properly
        if not intents.members and self._chunk_guilds:
            raise ValueError("Intents.members must be enabled to chunk guilds at startup.")

        cache_flags = options.get("member_cache_flags", None)
        if cache_flags is None:
            cache_flags = MemberCacheFlags.from_intents(intents)
        elif not isinstance(cache_flags, MemberCacheFlags):
            raise TypeError(f"member_cache_flags parameter must be MemberCacheFlags not {type(cache_flags)!r}")

        else:
            cache_flags._verify_intents(intents)

        self.member_cache_flags: MemberCacheFlags = cache_flags
        self._activity: ActivityPayload | None = activity
        self._status: str | None = status
        self._intents: Intents = intents
        self._voice_clients: dict[int, VoiceClient] = {}

        if not intents.members or cache_flags._empty:
            self.store_user = self.create_user_async  # type: ignore
            self.deref_user = self.deref_user_no_intents  # type: ignore

        self.cache_app_emojis: bool = options.get("cache_app_emojis", False)

        self.emitter: EventEmitter = EventEmitter(self)

        self.cache: Cache = cache
        self.cache._state = self

    async def clear(self, *, views: bool = True) -> None:
        self.user: ClientUser | None = None
        await self.cache.clear()
        self._voice_clients = {}

    async def process_chunk_requests(
        self, guild_id: int, nonce: str | None, members: list[Member], complete: bool
    ) -> None:
        removed = []
        for key, request in self._chunk_requests.items():
            if request.guild_id == guild_id and request.nonce == nonce:
                await request.add_members(members)
                if complete:
                    request.done()
                    removed.append(key)

        for key in removed:
            del self._chunk_requests[key]

    def call_handlers(self, key: str, *args: Any, **kwargs: Any) -> None:
        try:
            func = self.handlers[key]
        except KeyError:
            pass
        else:
            func(*args, **kwargs)

    async def call_hooks(self, key: str, *args: Any, **kwargs: Any) -> None:
        try:
            coro = self.hooks[key]
        except KeyError:
            pass
        else:
            await coro(*args, **kwargs)

    @property
    def self_id(self) -> int | None:
        u = self.user
        return u.id if u else None

    @property
    def intents(self) -> Intents:
        ret = Intents.none()
        ret.value = self._intents.value
        return ret

    @property
    def voice_clients(self) -> list[VoiceClient]:
        return list(self._voice_clients.values())

    def _get_voice_client(self, guild_id: int | None) -> VoiceClient | None:
        # the keys of self._voice_clients are ints
        return self._voice_clients.get(guild_id)  # type: ignore

    def _add_voice_client(self, guild_id: int, voice: VoiceClient) -> None:
        self._voice_clients[guild_id] = voice

    def _remove_voice_client(self, guild_id: int) -> None:
        self._voice_clients.pop(guild_id, None)

    def _update_references(self, ws: DiscordWebSocket) -> None:
        for vc in self.voice_clients:
            vc.main_ws = ws  # type: ignore

    async def store_user(self, data: UserPayload) -> User:
        return await self.cache.store_user(data)

    async def deref_user(self, user_id: int) -> None:
        return await self.cache.delete_user(user_id)

    def create_user(self, data: UserPayload) -> User:
        return User(state=self, data=data)

    async def create_user_async(self, data: UserPayload) -> User:
        return User(state=self, data=data)

    def deref_user_no_intents(self, user_id: int) -> None:
        return

    async def get_user(self, id: int | None) -> User | None:
        return await self.cache.get_user(cast(int, id))

    async def store_emoji(self, guild: Guild, data: EmojiPayload) -> GuildEmoji:
        return await self.cache.store_guild_emoji(guild, data)

    async def maybe_store_app_emoji(self, application_id: int, data: EmojiPayload) -> AppEmoji:
        # the id will be present here
        emoji = AppEmoji(application_id=application_id, state=self, data=data)
        if self.cache_app_emojis:
            await self.cache.store_app_emoji(application_id, data)
        return emoji

    async def store_sticker(self, guild: Guild, data: GuildStickerPayload) -> GuildSticker:
        return await self.cache.store_sticker(guild, data)

    async def store_view(self, view: View, message_id: int | None = None) -> None:
        await self.cache.store_view(view, message_id)

    async def store_modal(self, modal: Modal, user_id: int) -> None:
        await self.cache.store_modal(modal, user_id)

    async def prevent_view_updates_for(self, message_id: int) -> View | None:
        return await self.cache.delete_view_on(message_id)

    async def get_persistent_views(self) -> Sequence[View]:
        views = await self.cache.get_all_views()
        persistent_views = {view.id: view for view in views if view.is_persistent()}
        return list(persistent_views.values())

    async def get_guilds(self) -> list[Guild]:
        return await self.cache.get_all_guilds()

    async def _get_guild(self, guild_id: int | None) -> Guild | None:
        return await self.cache.get_guild(cast(int, guild_id))

    async def _add_guild(self, guild: Guild) -> None:
        await self.cache.add_guild(guild)

    async def _remove_guild(self, guild: Guild) -> None:
        await self.cache.delete_guild(guild)

        for emoji in guild.emojis:
            await self.cache.delete_emoji(emoji)

        for sticker in guild.stickers:
            await self.cache.delete_sticker(sticker.id)

        del guild

    async def _add_default_sounds(self) -> None:
        default_sounds = await self.http.get_default_sounds()
        for default_sound in default_sounds:
            sound = SoundboardSound(state=self, http=self.http, data=default_sound)
            await self._add_sound(sound)

    async def _add_sound(self, sound: SoundboardSound) -> None:
        await self.cache.store_sound(sound)

    async def _remove_sound(self, sound: SoundboardSound) -> None:
        await self.cache.delete_sound(sound.id)

    async def get_sounds(self) -> list[SoundboardSound]:
        return list(await self.cache.get_all_sounds())

    async def get_emojis(self) -> list[GuildEmoji | AppEmoji]:
        return await self.cache.get_all_emojis()

    async def get_stickers(self) -> list[GuildSticker]:
        return await self.cache.get_all_stickers()

    async def get_emoji(self, emoji_id: int | None) -> GuildEmoji | AppEmoji | None:
        return await self.cache.get_emoji(emoji_id)

    async def _remove_emoji(self, emoji: GuildEmoji | AppEmoji) -> None:
        await self.cache.delete_emoji(emoji)

    async def get_sticker(self, sticker_id: int | None) -> GuildSticker | None:
        return await self.cache.get_sticker(cast(int, sticker_id))

    async def get_polls(self) -> list[Poll]:
        return await self.cache.get_all_polls()

    async def store_poll(self, poll: Poll, message_id: int):
        await self.cache.store_poll(poll, message_id)

    async def get_poll(self, message_id: int):
        return await self.cache.get_poll(message_id)

    async def get_private_channels(self) -> list[PrivateChannel]:
        return await self.cache.get_private_channels()

    async def _get_private_channel(self, channel_id: int | None) -> PrivateChannel | None:
        return await self.cache.get_private_channel(cast(int, channel_id))

    async def _get_private_channel_by_user(self, user_id: int | None) -> DMChannel | None:
        return cast(DMChannel | None, await self.cache.get_private_channel_by_user(cast(int, user_id)))

    async def _add_private_channel(self, channel: PrivateChannel) -> None:
        await self.cache.store_private_channel(channel)

    async def add_dm_channel(self, data: DMChannelPayload) -> DMChannel:
        # self.user is *always* cached when this is called
        channel = DMChannel(me=self.user, state=self, data=data)  # type: ignore
        await channel._load()
        await self._add_private_channel(channel)
        return channel

    async def _get_message(self, msg_id: int | None) -> Message | None:
        return await self.cache.get_message(cast(int, msg_id))

    def _guild_needs_chunking(self, guild: Guild) -> bool:
        # If presences are enabled then we get back the old guild.large behaviour
        return self._chunk_guilds and not guild.chunked and not (self._intents.presences and not guild.large)

    async def _get_guild_channel(
        self, data: MessagePayload, guild_id: int | None = None
    ) -> tuple[Channel | Thread, Guild | None]:
        channel_id = int(data["channel_id"])
        try:
            # guild_id is in data
            guild = await self._get_guild(int(guild_id or data["guild_id"]))  # type: ignore
        except KeyError:
            channel = DMChannel(id=channel_id, state=self)
            guild = None
        else:
            channel = guild and guild._resolve_channel(channel_id)

        return channel or PartialMessageable(state=self, id=channel_id), guild

    async def chunker(
        self,
        guild_id: int,
        query: str = "",
        limit: int = 0,
        presences: bool = False,
        *,
        nonce: str | None = None,
    ) -> None:
        ws = self._get_websocket(guild_id)  # This is ignored upstream
        await ws.request_chunks(guild_id, query=query, limit=limit, presences=presences, nonce=nonce)

    async def query_members(
        self,
        guild: Guild,
        query: str | None,
        limit: int,
        user_ids: list[int] | None,
        cache: bool,
        presences: bool,
    ):
        guild_id = guild.id
        ws = self._get_websocket(guild_id)
        if ws is None:
            raise RuntimeError("Somehow do not have a websocket for this guild_id")

        request = ChunkRequest(guild.id, self.loop, self._get_guild, cache=cache)
        self._chunk_requests[request.nonce] = request

        try:
            # start the query operation
            await ws.request_chunks(
                guild_id,
                query=query,
                limit=limit,
                user_ids=user_ids,
                presences=presences,
                nonce=request.nonce,
            )
            return await asyncio.wait_for(request.wait(), timeout=30.0)
        except asyncio.TimeoutError:
            _log.warning(
                ("Timed out waiting for chunks with query %r and limit %d for guild_id %d"),
                query,
                limit,
                guild_id,
            )
            raise

    async def _get_create_guild(self, data):
        if data.get("unavailable") is False:
            # GUILD_CREATE with unavailable in the response
            # usually means that the guild has become available
            # and is therefore in the cache
            guild = await self._get_guild(int(data["id"]))
            if guild is not None:
                guild.unavailable = False
                await guild._from_data(data, self)
                return guild

        return self._add_guild_from_data(data)

    def is_guild_evicted(self, guild) -> bool:
        return guild.id not in self._guilds

    async def chunk_guild(self, guild, *, wait=True, cache=None):
        # Note: This method makes an API call without timeout, and should be used in
        #       conjunction with `asyncio.wait_for(..., timeout=...)`.
        cache = cache or self.member_cache_flags.joined
        request = self._chunk_requests.get(guild.id)  # nosec B113
        if request is None:
            self._chunk_requests[guild.id] = request = ChunkRequest(guild.id, self.loop, self._get_guild, cache=cache)
            await self.chunker(guild.id, nonce=request.nonce)

        if wait:
            return await request.wait()
        return request.get_future()

    async def _chunk_and_dispatch(self, guild, unavailable):
        try:
            await asyncio.wait_for(self.chunk_guild(guild), timeout=60.0)
        except asyncio.TimeoutError:
            _log.info("Somehow timed out waiting for chunks.")

        if unavailable is False:
            self.dispatch("guild_available", guild)
        else:
            self.dispatch("guild_join", guild)

    def parse_guild_members_chunk(self, data) -> None:
        guild_id = int(data["guild_id"])
        guild = self._get_guild(guild_id)
        presences = data.get("presences", [])

        # the guild won't be None here
        members = [Member(guild=guild, data=member, state=self) for member in data.get("members", [])]  # type: ignore
        _log.debug("Processed a chunk for %s members in guild ID %s.", len(members), guild_id)

        if presences:
            member_dict = {str(member.id): member for member in members}
            for presence in presences:
                user = presence["user"]
                member_id = user["id"]
                member = member_dict.get(member_id)
                if member is not None:
                    member._presence_update(presence, user)

        complete = data.get("chunk_index", 0) + 1 == data.get("chunk_count")
        self.process_chunk_requests(guild_id, data.get("nonce"), members, complete)

    async def _get_reaction_user(self, channel: MessageableChannel, user_id: int) -> User | Member | None:
        if isinstance(channel, TextChannel):
            return await channel.guild.get_member(user_id)
        return await self.get_user(user_id)

    async def get_reaction_emoji(self, data) -> GuildEmoji | AppEmoji | PartialEmoji:
        emoji_id = get_as_snowflake(data, "id")

        if not emoji_id:
            return data["name"]

        try:
            return await self.cache.get_emoji(emoji_id)
        except KeyError:
            return PartialEmoji.with_state(
                self,
                animated=data.get("animated", False),
                id=emoji_id,
                name=data["name"],
            )

    async def _upgrade_partial_emoji(self, emoji: PartialEmoji) -> GuildEmoji | AppEmoji | PartialEmoji | str:
        emoji_id = emoji.id
        if not emoji_id:
            return emoji.name
        return await self.cache.get_emoji(emoji_id) or emoji

    async def get_channel(self, id: int | None) -> Channel | Thread | None:
        if id is None:
            return None

        pm = await self._get_private_channel(id)
        if pm is not None:
            return pm

        for guild in await self.cache.get_all_guilds():
            channel = guild._resolve_channel(id)
            if channel is not None:
                return channel

    def create_message(
        self,
        *,
        channel: MessageableChannel,
        data: MessagePayload,
    ) -> Message:
        return Message(state=self, channel=channel, data=data)


class AutoShardedConnectionState(ConnectionState):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.shard_ids: list[int] | range = []
        self.shards_launched: asyncio.Event = asyncio.Event()

    def _update_message_references(self) -> None:
        # self._messages won't be None when this is called
        for msg in self._messages:  # type: ignore
            if not msg.guild:
                continue

            new_guild = self._get_guild(msg.guild.id)
            if new_guild is not None and new_guild is not msg.guild:
                channel_id = msg.channel.id
                channel = new_guild._resolve_channel(channel_id) or Object(id=channel_id)
                # channel will either be a TextChannel, Thread or Object
                msg._rebind_cached_references(new_guild, channel)  # type: ignore

    async def chunker(
        self,
        guild_id: int,
        query: str = "",
        limit: int = 0,
        presences: bool = False,
        *,
        shard_id: int | None = None,
        nonce: str | None = None,
    ) -> None:
        ws = self._get_websocket(guild_id, shard_id=shard_id)
        await ws.request_chunks(guild_id, query=query, limit=limit, presences=presences, nonce=nonce)

    async def _delay_ready(self) -> None:
        await self.shards_launched.wait()
        processed = []
        max_concurrency = len(self.shard_ids) * 2
        current_bucket = []
        while True:
            # this snippet of code is basically waiting N seconds
            # until the last GUILD_CREATE was sent
            try:
                guild = await asyncio.wait_for(self._ready_state.get(), timeout=self.guild_ready_timeout)
            except asyncio.TimeoutError:
                break
            else:
                if self._guild_needs_chunking(guild):
                    _log.debug(
                        ("Guild ID %d requires chunking, will be done in the background."),
                        guild.id,
                    )
                    if len(current_bucket) >= max_concurrency:
                        try:
                            await sane_wait_for(current_bucket, timeout=max_concurrency * 70.0)
                        except asyncio.TimeoutError:
                            fmt = "Shard ID %s failed to wait for chunks from a sub-bucket with length %d"
                            _log.warning(fmt, guild.shard_id, len(current_bucket))
                        finally:
                            current_bucket = []

                    # Chunk the guild in the background while we wait for GUILD_CREATE streaming
                    future = asyncio.ensure_future(self.chunk_guild(guild))
                    current_bucket.append(future)
                else:
                    await self._add_default_sounds()
                    future = self.loop.create_future()
                    future.set_result([])

                processed.append((guild, future))

        guilds = sorted(processed, key=lambda g: g[0].shard_id)
        for shard_id, info in itertools.groupby(guilds, key=lambda g: g[0].shard_id):
            children, futures = zip(*info, strict=True)
            # 110 reqs/minute w/ 1 req/guild plus some buffer
            timeout = 61 * (len(children) / 110)
            try:
                await sane_wait_for(futures, timeout=timeout)
            except asyncio.TimeoutError:
                _log.warning(
                    ("Shard ID %s failed to wait for chunks (timeout=%.2f) for %d guilds"),
                    shard_id,
                    timeout,
                    len(guilds),
                )
            for guild in children:
                if guild.unavailable is False:
                    self.dispatch("guild_available", guild)
                else:
                    self.dispatch("guild_join", guild)

            self.dispatch("shard_ready", shard_id)

        if self.cache_app_emojis and self.application_id:
            data = await self.http.get_all_application_emojis(self.application_id)
            for e in data.get("items", []):
                await self.maybe_store_app_emoji(self.application_id, e)

        # remove the state
        try:
            del self._ready_state
        except AttributeError:
            pass  # already been deleted somehow

        # clear the current task
        self._ready_task = None

        # dispatch the event
        self.call_handlers("ready")
        self.dispatch("ready")

    def parse_ready(self, data) -> None:
        if not hasattr(self, "_ready_state"):
            self._ready_state = asyncio.Queue()

        self.user = user = ClientUser(state=self, data=data["user"])
        # self._users is a list of Users, we're setting a ClientUser
        self._users[user.id] = user  # type: ignore

        if self.application_id is None:
            try:
                application = data["application"]
            except KeyError:
                pass
            else:
                self.application_id = get_as_snowflake(application, "id")
                self.application_flags = ApplicationFlags._from_value(application["flags"])

        for guild_data in data["guilds"]:
            self._add_guild_from_data(guild_data)

        if self._messages:
            self._update_message_references()

        self.dispatch("connect")
        self.dispatch("shard_connect", data["__shard_id__"])

        if self._ready_task is None:
            self._ready_task = asyncio.create_task(self._delay_ready())

    def parse_resumed(self, data) -> None:
        self.dispatch("resumed")
        self.dispatch("shard_resumed", data["__shard_id__"])
