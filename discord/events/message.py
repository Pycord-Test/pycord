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

from typing import Any, Self
from discord.app.state import ConnectionState
from discord.channel import StageChannel, TextChannel, VoiceChannel
from discord.raw_models import RawBulkMessageDeleteEvent, RawMessageDeleteEvent
from discord.threads import Thread
from ..message import Message
from ..app.event_emitter import Event


class MessageCreate(Event, Message):
    __event_name__ = "MESSAGE_CREATE"

    @classmethod
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        channel, _ = await state._get_guild_channel(data)
        message = await Message._from_data(channel=channel, data=data, state=state)
        self = cls()
        self.__dict__.update(message.__dict__)

        await state.cache.store_message(data, channel)
        # we ensure that the channel is either a TextChannel, VoiceChannel, StageChannel, or Thread
        if channel and channel.__class__ in (
            TextChannel,
            VoiceChannel,
            StageChannel,
            Thread,
        ):
            channel.last_message_id = message.id  # type: ignore

        return self


class MessageDelete(Event, Message):
    __event_name__ = "MESSAGE_DELETE"

    raw: RawMessageDeleteEvent

    @classmethod
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        self = cls()
        raw = RawMessageDeleteEvent(data)
        msg = await state._get_message(raw.message_id)
        raw.cached_message = msg
        self.raw = raw
        if msg is not None:
            await state.cache.delete_message(raw.message_id)
            self.__dict__.update(msg.__dict__)

        return self


class MessageDeleteBulk(Event):
    __event_name__ = "MESSAGE_DELETE_BULK"

    raw: RawBulkMessageDeleteEvent
    messages: list[Message]

    @classmethod
    async def __load__(cls, data: Any, state: ConnectionState) -> Self :
        self = cls()
        raw = RawBulkMessageDeleteEvent(data)
        messages = await state.cache.get_all_messages()
        found_messages = [message for message in messages if message.id in raw.message_ids]
        raw.cached_messages = found_messages
        self.messages = found_messages
        for message in messages:
            await state.cache.delete_message(message.id)
        return self
