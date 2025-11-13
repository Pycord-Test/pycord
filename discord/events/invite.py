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

from typing import Any

from typing_extensions import Self, override

from discord.app.event_emitter import Event
from discord.app.state import ConnectionState
from discord.channel.base import GuildChannel
from discord.guild import Guild
from discord.invite import Invite, PartialInviteChannel, PartialInviteGuild
from discord.types.invite import GatewayInvite, VanityInvite
from discord.types.invite import Invite as InvitePayload


class InviteCreate(Event, Invite):
    """Called when an invite is created.

    You must have :attr:`~Permissions.manage_channels` permission to receive this.

    .. note::
        There is a rare possibility that the :attr:`Invite.guild` and :attr:`Invite.channel`
        attributes will be of :class:`Object` rather than the respective models.

    This requires :attr:`Intents.invites` to be enabled.

    This event inherits from :class:`Invite`.
    """

    __event_name__: str = "INVITE_CREATE"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: GatewayInvite, state: ConnectionState) -> Self | None:
        invite = await Invite.from_gateway(state=state, data=data)
        self = cls()
        self.__dict__.update(invite.__dict__)


class InviteDelete(Event, Invite):
    """Called when an invite is deleted.

    You must have :attr:`~Permissions.manage_channels` permission to receive this.

    .. note::
        There is a rare possibility that the :attr:`Invite.guild` and :attr:`Invite.channel`
        attributes will be of :class:`Object` rather than the respective models.

        Outside of those two attributes, the only other attribute guaranteed to be
        filled by the Discord gateway for this event is :attr:`Invite.code`.

    This requires :attr:`Intents.invites` to be enabled.

    This event inherits from :class:`Invite`.
    """

    __event_name__: str = "INVITE_DELETE"

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: GatewayInvite, state: ConnectionState) -> Self | None:
        invite = await Invite.from_gateway(state=state, data=data)
        self = cls()
        self.__dict__.update(invite.__dict__)
