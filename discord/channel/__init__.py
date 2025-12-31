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

from ..enums import ChannelType, try_enum
from .base import (
    BaseChannel,
    GuildChannel,
    GuildMessageableChannel,
    GuildPostableChannel,
    GuildThreadableChannel,
    GuildTopLevelChannel,
)
from .category import CategoryChannel
from .dm import DMChannel
from .dm import GroupDMChannel as GroupChannel
from .forum import ForumChannel
from .media import MediaChannel
from .news import NewsChannel
from .partial import PartialMessageable
from .stage import StageChannel
from .text import TextChannel
from .thread import Thread
from .voice import VoiceChannel

__all__ = (
    "BaseChannel",
    "CategoryChannel",
    "DMChannel",
    "ForumChannel",
    "GroupChannel",
    "GuildChannel",
    "GuildMessageableChannel",
    "GuildPostableChannel",
    "GuildThreadableChannel",
    "GuildTopLevelChannel",
    "MediaChannel",
    "NewsChannel",
    "PartialMessageable",
    "StageChannel",
    "TextChannel",
    "Thread",
    "VoiceChannel",
)


def _guild_channel_factory(channel_type: int):
    value = try_enum(ChannelType, channel_type)
    if value is ChannelType.text:
        return TextChannel, value
    elif value is ChannelType.voice:
        return VoiceChannel, value
    elif value is ChannelType.category:
        return CategoryChannel, value
    elif value is ChannelType.news:
        return NewsChannel, value
    elif value is ChannelType.stage_voice:
        return StageChannel, value
    elif value is ChannelType.directory:
        return None, value  # todo: Add DirectoryChannel when applicable
    elif value is ChannelType.forum:
        return ForumChannel, value
    elif value is ChannelType.media:
        return MediaChannel, value
    else:
        return None, value


def _channel_factory(channel_type: int):
    cls, value = _guild_channel_factory(channel_type)
    if value is ChannelType.private:
        return DMChannel, value
    elif value is ChannelType.group:
        return GroupChannel, value
    else:
        return cls, value


def _threaded_channel_factory(channel_type: int):
    cls, value = _channel_factory(channel_type)
    if value in (
        ChannelType.private_thread,
        ChannelType.public_thread,
        ChannelType.news_thread,
    ):
        return Thread, value
    return cls, value


def _threaded_guild_channel_factory(channel_type: int):
    cls, value = _guild_channel_factory(channel_type)
    if value in (
        ChannelType.private_thread,
        ChannelType.public_thread,
        ChannelType.news_thread,
    ):
        return Thread, value
    return cls, value
