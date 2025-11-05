from ..enums import ChannelType, try_enum
from ..threads import Thread
from .channel import *
from .dm import DMChannel, GroupDMChannel


def _guild_channel_factory(channel_type: int):
    value = try_enum(ChannelType, channel_type)
    if value is ChannelType.text:
        return TextChannel, value
    elif value is ChannelType.voice:
        return VoiceChannel, value
    elif value is ChannelType.category:
        return CategoryChannel, value
    elif value is ChannelType.news:
        return TextChannel, value
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
        return GroupDMChannel, value
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
