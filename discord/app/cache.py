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

from collections import OrderedDict, defaultdict, deque
from typing import TYPE_CHECKING, Deque, Protocol, TypeVar

from discord import utils
from discord.member import Member
from discord.message import Message
from discord.soundboard import SoundboardSound

from ..channel import DMChannel
from ..emoji import AppEmoji, GuildEmoji
from ..guild import Guild
from ..poll import Poll
from ..sticker import GuildSticker, Sticker
from ..types.channel import DMChannel as DMChannelPayload
from ..types.emoji import Emoji as EmojiPayload
from ..types.message import Message as MessagePayload
from ..types.sticker import GuildSticker as GuildStickerPayload
from ..types.user import User as UserPayload
from ..ui.modal import Modal
from ..ui.view import View
from ..user import User

if TYPE_CHECKING:
    from discord.app.state import ConnectionState

    from ..abc import MessageableChannel, PrivateChannel

T = TypeVar("T")


class Cache(Protocol):
    def __init__(self):
        self.__state: ConnectionState | None = None

    @property
    def _state(self) -> "ConnectionState":
        if self.__state is None:
            raise RuntimeError("Cache state has not been initialized.")
        return self.__state

    @_state.setter
    def _state(self, state: "ConnectionState") -> None:
        self.__state = state

    # users
    async def get_all_users(self) -> list[User]: ...

    async def store_user(self, payload: UserPayload) -> User: ...

    async def delete_user(self, user_id: int) -> None: ...

    async def get_user(self, user_id: int) -> User | None: ...

    # stickers

    async def get_all_stickers(self) -> list[GuildSticker]: ...

    async def get_sticker(self, sticker_id: int) -> GuildSticker: ...

    async def store_sticker(self, guild: Guild, data: GuildStickerPayload) -> GuildSticker: ...

    async def delete_sticker(self, sticker_id: int) -> None: ...

    # interactions

    async def store_view(self, view: View, message_id: int | None) -> None: ...

    async def delete_view_on(self, message_id: int) -> None: ...

    async def get_all_views(self) -> list[View]: ...

    async def store_modal(self, modal: Modal, user_id: int) -> None: ...

    async def delete_modal(self, custom_id: str) -> None: ...

    async def get_all_modals(self) -> list[Modal]: ...

    # guilds

    async def get_all_guilds(self) -> list[Guild]: ...

    async def get_guild(self, id: int) -> Guild | None: ...

    async def add_guild(self, guild: Guild) -> None: ...

    async def delete_guild(self, guild: Guild) -> None: ...

    # emojis

    async def store_guild_emoji(self, guild: Guild, data: EmojiPayload) -> GuildEmoji: ...

    async def store_app_emoji(self, application_id: int, data: EmojiPayload) -> AppEmoji: ...

    async def get_all_emojis(self) -> list[GuildEmoji | AppEmoji]: ...

    async def get_emoji(self, emoji_id: int | None) -> GuildEmoji | AppEmoji | None: ...

    async def delete_emoji(self, emoji: GuildEmoji | AppEmoji) -> None: ...

    # polls

    async def get_all_polls(self) -> list[Poll]: ...

    async def get_poll(self, message_id: int) -> Poll: ...

    async def store_poll(self, poll: Poll, message_id: int) -> None: ...

    # private channels

    async def get_private_channels(self) -> "list[PrivateChannel]": ...

    async def get_private_channel(self, channel_id: int) -> "PrivateChannel": ...

    async def get_private_channel_by_user(self, user_id: int) -> "PrivateChannel | None": ...

    async def store_private_channel(self, channel: "PrivateChannel") -> None: ...

    # messages

    async def store_message(self, message: MessagePayload, channel: "MessageableChannel") -> Message: ...

    async def store_built_message(self, message: Message) -> None: ...

    async def upsert_message(self, message: Message) -> None: ...

    async def delete_message(self, message_id: int) -> None: ...

    async def get_message(self, message_id: int) -> Message | None: ...

    async def get_all_messages(self) -> list[Message]: ...

    # guild members

    async def store_member(self, member: Member) -> None: ...

    async def get_member(self, guild_id: int, user_id: int) -> Member | None: ...

    async def delete_member(self, guild_id: int, user_id: int) -> None: ...

    async def delete_guild_members(self, guild_id: int) -> None: ...

    async def get_guild_members(self, guild_id: int) -> list[Member]: ...

    async def get_all_members(self) -> list[Member]: ...

    async def clear(self, views: bool = True) -> None: ...

    async def store_sound(self, sound: SoundboardSound) -> None: ...

    async def get_sound(self, sound_id: int) -> SoundboardSound | None: ...

    async def get_all_sounds(self) -> list[SoundboardSound]: ...

    async def delete_sound(self, sound_id: int) -> None: ...


class MemoryCache(Cache):
    def __init__(self, max_messages: int | None = None) -> None:
        self.__state: ConnectionState | None = None
        self.max_messages = max_messages
        self._users: dict[int, User] = {}
        self._guilds: dict[int, Guild] = {}
        self._polls: dict[int, Poll] = {}
        self._stickers: dict[int, list[GuildSticker]] = {}
        self._views: dict[str, View] = {}
        self._modals: dict[str, Modal] = {}
        self._sounds: dict[int, SoundboardSound] = {}
        self._messages: Deque[Message] = deque(maxlen=self.max_messages)

        self._emojis: dict[int, list[GuildEmoji | AppEmoji]] = {}

        self._private_channels: OrderedDict[int, PrivateChannel] = OrderedDict()
        self._private_channels_by_user: dict[int, DMChannel] = {}

        self._guild_members: dict[int, dict[int, Member]] = defaultdict(dict)

    def _flatten(self, matrix: list[list[T]]) -> list[T]:
        return [item for row in matrix for item in row]

    async def clear(self, views: bool = True) -> None:
        self._users: dict[int, User] = {}
        self._guilds: dict[int, Guild] = {}
        self._polls: dict[int, Poll] = {}
        self._stickers: dict[int, list[GuildSticker]] = {}
        if views:
            self._views: dict[str, View] = {}
        self._modals: dict[str, Modal] = {}
        self._messages: Deque[Message] = deque(maxlen=self.max_messages)

        self._emojis: dict[int, list[GuildEmoji | AppEmoji]] = {}

        self._private_channels: OrderedDict[int, PrivateChannel] = OrderedDict()
        self._private_channels_by_user: dict[int, DMChannel] = {}

        self._guild_members: dict[int, dict[int, Member]] = defaultdict(dict)

    # users
    async def get_all_users(self) -> list[User]:
        return list(self._users.values())

    async def store_user(self, payload: UserPayload) -> User:
        user_id = int(payload["id"])
        try:
            return self._users[user_id]
        except KeyError:
            user = User(state=self._state, data=payload)
            if user.discriminator != "0000":
                self._users[user_id] = user
                user._stored = True
            return user

    async def delete_user(self, user_id: int) -> None:
        self._users.pop(user_id, None)

    async def get_user(self, user_id: int) -> User | None:
        return self._users.get(user_id)

    # stickers

    async def get_all_stickers(self) -> list[GuildSticker]:
        return self._flatten(list(self._stickers.values()))

    async def get_sticker(self, sticker_id: int) -> GuildSticker | None:
        stickers = self._flatten(list(self._stickers.values()))
        for sticker in stickers:
            if sticker.id == sticker_id:
                return sticker

    async def store_sticker(self, guild: Guild, data: GuildStickerPayload) -> GuildSticker:
        sticker = GuildSticker(state=self._state, data=data)
        try:
            self._stickers[guild.id].append(sticker)
        except KeyError:
            self._stickers[guild.id] = [sticker]
        return sticker

    async def delete_sticker(self, sticker_id: int) -> None:
        self._stickers.pop(sticker_id, None)

    # interactions

    async def delete_view_on(self, message_id: int) -> View | None:
        for view in await self.get_all_views():
            if view.message and view.message.id == message_id:
                return view

    async def store_view(self, view: View, message_id: int) -> None:
        self._views[str(message_id or view.id)] = view

    async def get_all_views(self) -> list[View]:
        return list(self._views.values())

    async def store_modal(self, modal: Modal) -> None:
        self._modals[modal.custom_id] = modal

    async def get_all_modals(self) -> list[Modal]:
        return list(self._modals.values())

    # guilds

    async def get_all_guilds(self) -> list[Guild]:
        return list(self._guilds.values())

    async def get_guild(self, id: int) -> Guild | None:
        return self._guilds.get(id)

    async def add_guild(self, guild: Guild) -> None:
        self._guilds[guild.id] = guild

    async def delete_guild(self, guild: Guild) -> None:
        self._guilds.pop(guild.id, None)

    # emojis

    async def store_guild_emoji(self, guild: Guild, data: EmojiPayload) -> GuildEmoji:
        emoji = GuildEmoji(guild=guild, state=self._state, data=data)
        try:
            self._emojis[guild.id].append(emoji)
        except KeyError:
            self._emojis[guild.id] = [emoji]
        return emoji

    async def store_app_emoji(self, application_id: int, data: EmojiPayload) -> AppEmoji:
        emoji = AppEmoji(application_id=application_id, state=self._state, data=data)
        try:
            self._emojis[application_id].append(emoji)
        except KeyError:
            self._emojis[application_id] = [emoji]
        return emoji

    async def get_all_emojis(self) -> list[GuildEmoji | AppEmoji]:
        return self._flatten(list(self._emojis.values()))

    async def get_emoji(self, emoji_id: int | None) -> GuildEmoji | AppEmoji | None:
        emojis = self._flatten(list(self._emojis.values()))
        for emoji in emojis:
            if emoji.id == emoji_id:
                return emoji

    async def delete_emoji(self, emoji: GuildEmoji | AppEmoji) -> None:
        if isinstance(emoji, AppEmoji):
            self._emojis[emoji.application_id].remove(emoji)
        else:
            self._emojis[emoji.guild_id].remove(emoji)

    # polls

    async def get_all_polls(self) -> list[Poll]:
        return list(self._polls.values())

    async def get_poll(self, message_id: int) -> Poll | None:
        return self._polls.get(message_id)

    async def store_poll(self, poll: Poll, message_id: int) -> None:
        self._polls[message_id] = poll

    # private channels

    async def get_private_channels(self) -> "list[PrivateChannel]":
        return list(self._private_channels.values())

    async def get_private_channel(self, channel_id: int) -> "PrivateChannel | None":
        try:
            channel = self._private_channels[channel_id]
        except KeyError:
            return None
        else:
            self._private_channels.move_to_end(channel_id)
            return channel

    async def store_private_channel(self, channel: "PrivateChannel") -> None:
        channel_id = channel.id
        self._private_channels[channel_id] = channel

        if len(self._private_channels) > 128:
            _, to_remove = self._private_channels.popitem(last=False)
            if isinstance(to_remove, DMChannel) and to_remove.recipient:
                self._private_channels_by_user.pop(to_remove.recipient.id, None)

        if isinstance(channel, DMChannel) and channel.recipient:
            self._private_channels_by_user[channel.recipient.id] = channel

    async def get_private_channel_by_user(self, user_id: int) -> "PrivateChannel | None":
        return self._private_channels_by_user.get(user_id)

    # messages

    async def upsert_message(self, message: Message) -> None:
        self._messages.append(message)

    async def store_message(self, message: MessagePayload, channel: "MessageableChannel") -> Message:
        msg = await Message._from_data(state=self._state, channel=channel, data=message)
        self.store_built_message(msg)
        return msg

    async def store_built_message(self, message: Message) -> None:
        self._messages.append(message)

    async def delete_message(self, message_id: int) -> None:
        self._messages.remove(utils.find(lambda m: m.id == message_id, reversed(self._messages)))

    async def get_message(self, message_id: int) -> Message | None:
        return utils.find(lambda m: m.id == message_id, reversed(self._messages))

    async def get_all_messages(self) -> list[Message]:
        return list(self._messages)

    async def delete_modal(self, custom_id: str) -> None:
        self._modals.pop(custom_id, None)

    # guild members

    async def store_member(self, member: Member) -> None:
        self._guild_members[member.guild.id][member.id] = member

    async def get_member(self, guild_id: int, user_id: int) -> Member | None:
        return self._guild_members[guild_id].get(user_id)

    async def delete_member(self, guild_id: int, user_id: int) -> None:
        self._guild_members[guild_id].pop(user_id, None)

    async def delete_guild_members(self, guild_id: int) -> None:
        self._guild_members.pop(guild_id, None)

    async def get_guild_members(self, guild_id: int) -> list[Member]:
        return list(self._guild_members.get(guild_id, {}).values())

    async def get_all_members(self) -> list[Member]:
        return self._flatten([list(members.values()) for members in self._guild_members.values()])

    async def store_sound(self, sound: SoundboardSound) -> None:
        self._sounds[sound.id] = sound

    async def get_sound(self, sound_id: int) -> SoundboardSound | None:
        return self._sounds.get(sound_id)

    async def get_all_sounds(self) -> list[SoundboardSound]:
        return list(self._sounds.values())

    async def delete_sound(self, sound_id: int) -> None:
        self._sounds.pop(sound_id, None)
