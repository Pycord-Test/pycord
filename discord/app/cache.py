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

from collections import OrderedDict, deque
from typing import Deque, Protocol

from discord import utils
from discord.app.state import ConnectionState
from discord.message import Message

from ..abc import MessageableChannel, PrivateChannel
from ..channel import DMChannel
from ..emoji import AppEmoji, GuildEmoji
from ..guild import Guild
from ..poll import Poll
from ..sticker import GuildSticker, Sticker
from ..ui.modal import Modal, ModalStore
from ..ui.view import View, ViewStore
from ..user import User
from ..types.user import User as UserPayload
from ..types.emoji import Emoji as EmojiPayload
from ..types.sticker import GuildSticker as GuildStickerPayload
from ..types.channel import DMChannel as DMChannelPayload
from ..types.message import Message as MessagePayload

class Cache(Protocol):
    # users
    async def get_all_users(self) -> list[User]:
        ...

    async def store_user(self, payload: UserPayload) -> User:
        ...

    async def delete_user(self, user_id: int) -> None:
        ...

    async def get_user(self, user_id: int) -> User | None:
        ...

    # stickers

    async def get_all_stickers(self) -> list[GuildSticker]:
        ...

    async def get_sticker(self, sticker_id: int) -> GuildSticker:
        ...

    async def store_sticker(self, guild: Guild, data: GuildStickerPayload) -> GuildSticker:
        ...

    async def delete_sticker(self, sticker_id: int) -> None:
        ...

    # interactions

    async def store_view(self, view: View, message_id: int | None) -> None:
        ...

    async def delete_view_on(self, message_id: int) -> None:
        ...

    async def get_all_views(self) -> list[View]:
        ...

    async def store_modal(self, modal: Modal, user_id: int) -> None:
        ...

    async def delete_modal(self, custom_id: str) -> None:
        ...

    async def get_all_modals(self) -> list[Modal]:
        ...

    # guilds

    async def get_all_guilds(self) -> list[Guild]:
        ...

    async def get_guild(self, id: int) -> Guild | None:
        ...

    async def add_guild(self, guild: Guild) -> None:
        ...

    async def delete_guild(self, guild: Guild) -> None:
        ...

    # emojis

    async def store_guild_emoji(self, guild: Guild, data: EmojiPayload) -> GuildEmoji:
        ...

    async def store_app_emoji(
        self, application_id: int, data: EmojiPayload
    ) -> AppEmoji:
        ...

    async def get_all_emojis(self) -> list[GuildEmoji | AppEmoji]:
        ...

    async def get_emoji(self, emoji_id: int | None) -> GuildEmoji | AppEmoji | None:
        ...

    async def delete_emoji(self, emoji: GuildEmoji | AppEmoji) -> None:
        ...

    # polls

    async def get_all_polls(self) -> list[Poll]:
        ...

    async def get_poll(self, message_id: int) -> Poll:
        ...

    async def store_poll(self, poll: Poll, message_id: int) -> None:
        ...

    # private channels

    async def get_private_channels(self) -> list[PrivateChannel]:
        ...

    async def get_private_channel(self, channel_id: int) -> PrivateChannel:
        ...

    async def get_private_channel_by_user(self, user_id: int) -> PrivateChannel:
        ...

    async def store_private_channel(self, channel: PrivateChannel) -> None:
        ...

    # messages

    async def store_message(self, message: MessagePayload, channel: MessageableChannel) -> Message:
        ...

    async def upsert_message(self, message: Message) -> None:
        ...

    async def delete_message(self, message_id: int) -> None:
        ...

    async def get_message(self, message_id: int) -> Message | None:
        ...

    async def get_all_messages(self) -> list[Message]:
        ...

    def clear(self, views: bool = True) -> None:
        ...

class MemoryCache(Cache):
    def __init__(self, max_messages: int | None = None, *, state: ConnectionState):
        self._state = state
        self.max_messages = max_messages
        self.clear()

    def clear(self, views: bool = True) -> None:
        self._users: dict[int, User] = {}
        self._guilds: dict[int, Guild] = {}
        self._polls: dict[int, Poll] = {}
        self._stickers: dict[int, list[GuildSticker]] = {}
        if views:
            self._views: dict[str, View] = {}
        self._modals: dict[str, Modal] = {}
        self._messages: Deque[Message] = deque(maxlen=self.max_messages)

        self._emojis = dict[str, GuildEmoji | AppEmoji] = {}

        self._private_channels: OrderedDict[int, PrivateChannel] = OrderedDict()
        self._private_channels_by_user: dict[int, DMChannel] = {}

    # users
    async def get_all_users(self) -> list[User]:
        return list(self._users.values())

    async def store_user(self, payload: UserPayload) -> User:
        user_id = int(payload["id"])
        try:
            return self._users[user_id]
        except KeyError:
            user = User(state=self, data=payload)
            if user.discriminator != "0000":
                self._users[user_id] = user
                user._stored = True
            return user

    async def delete_user(self, user_id: int) -> None:
        self._users.pop(user_id, None)

    async def get_user(self, user_id: int) -> User:
        return self._users.get(user_id)

    # stickers

    async def get_all_stickers(self) -> list[GuildSticker]:
        return list(self._stickers.values())

    async def get_sticker(self, sticker_id: int) -> GuildSticker | None:
        return self._stickers.get(sticker_id)

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

    async def store_app_emoji(
        self, application_id: int, data: EmojiPayload
    ) -> AppEmoji:
        emoji = AppEmoji(application_id=application_id, state=self._state, data=data)
        try:
            self._emojis[application_id].append(emoji)
        except KeyError:
            self._emojis[application_id] = [emoji]
        return emoji

    async def get_all_emojis(self) -> list[GuildEmoji | AppEmoji]:
        return list(self._emojis.values())

    async def get_emoji(self, emoji_id: int | None) -> GuildEmoji | AppEmoji | None:
        return self._emojis.get(emoji_id)

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

    async def get_private_channels(self) -> list[PrivateChannel]:
        return list(self._private_channels.values())

    async def get_private_channel(self, channel_id: int) -> PrivateChannel | None:
        try:
            channel = self._private_channels[channel_id]
        except KeyError:
            return None
        else:
            self._private_channels.move_to_end(channel_id)
            return channel

    async def store_private_channel(self, channel: PrivateChannel) -> None:
        channel_id = channel.id
        self._private_channels[channel_id] = channel

        if len(self._private_channels) > 128:
            _, to_remove = self._private_channels.popitem(last=False)
            if isinstance(to_remove, DMChannel) and to_remove.recipient:
                self._private_channels_by_user.pop(to_remove.recipient.id, None)

        if isinstance(channel, DMChannel) and channel.recipient:
            self._private_channels_by_user[channel.recipient.id] = channel

    async def get_private_channel_by_user(self, user_id: int) -> PrivateChannel | None:
        return self._private_channels_by_user.get(user_id)

    # messages

    async def upsert_message(self, message: Message) -> None:
        self._messages.append(message)

    async def store_message(self, message: MessagePayload, channel: MessageableChannel) -> Message:
        msg = await Message._from_data(state=self._state, channel=channel, data=message)
        self._messages.append(msg)
        return msg

    async def get_message(self, message_id: int) -> Message | None:
        return utils.find(lambda m: m.id == message_id, reversed(self._messages))

    async def get_all_messages(self) -> list[Message]:
        return list(self._messages)

    async def delete_modal(self, custom_id: str) -> None:
        self._modals.pop(custom_id, None)
