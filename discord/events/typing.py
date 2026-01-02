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

from typing import TYPE_CHECKING, Any

from typing_extensions import Self, override

from discord import utils
from discord.app.event_emitter import Event
from discord.app.state import ConnectionState
from discord.channel import DMChannel, GroupChannel, TextChannel
from discord.channel.thread import Thread
from discord.member import Member
from discord.raw_models import RawTypingEvent
from discord.user import User

from ..datetime import DiscordTime

if TYPE_CHECKING:
    from discord.message import MessageableChannel


class TypingStart(Event):
    """Called when someone begins typing a message.

    The :attr:`channel` can be a :class:`abc.Messageable` instance,
    which could be :class:`TextChannel`, :class:`GroupChannel`, or :class:`DMChannel`.

    If the :attr:`channel` is a :class:`TextChannel` then the :attr:`user` is a :class:`Member`,
    otherwise it is a :class:`User`.

    This requires :attr:`Intents.typing` to be enabled.

    Attributes
    ----------
    raw: :class:`RawTypingEvent`
        The raw event payload data.
    channel: :class:`abc.Messageable`
        The location where the typing originated from.
    user: :class:`User` | :class:`Member`
        The user that started typing.
    when: :class:`discord.DiscordTime`
        When the typing started as an aware datetime in UTC.
    """

    __event_name__: str = "TYPING_START"

    raw: RawTypingEvent
    channel: "MessageableChannel"
    user: User | Member
    when: DiscordTime

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        raw = RawTypingEvent(data)

        member_data = data.get("member")
        if member_data:
            guild = await state._get_guild(raw.guild_id)
            if guild is not None:
                raw.member = Member(data=member_data, guild=guild, state=state)
            else:
                raw.member = None
        else:
            raw.member = None

        channel, guild = await state._get_guild_channel(data)
        if channel is None:
            return

        user = raw.member or await _get_typing_user(state, channel, raw.user_id)
        if user is None:
            return

        self = cls()
        self.raw = raw
        self.channel = channel  # type: ignore
        self.user = user
        self.when = raw.when
        return self


async def _get_typing_user(
    state: ConnectionState, channel: "MessageableChannel | None", user_id: int
) -> User | Member | None:
    """Helper function to get the user who is typing."""
    if isinstance(channel, DMChannel):
        return channel.recipient or await state.get_user(user_id)

    elif isinstance(channel, (Thread, TextChannel)) and channel.guild is not None:
        return await channel.guild.get_member(user_id)  # type: ignore

    elif isinstance(channel, GroupChannel):
        return utils.find(lambda x: x.id == user_id, channel.recipients)

    return await state.get_user(user_id)
