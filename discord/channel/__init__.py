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
