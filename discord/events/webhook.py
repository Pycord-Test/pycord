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

import logging
from typing import TYPE_CHECKING, Any

from typing_extensions import Self, override

from discord.app.event_emitter import Event
from discord.app.state import ConnectionState

if TYPE_CHECKING:
    from discord.channel.base import GuildChannel

_log = logging.getLogger(__name__)


class WebhooksUpdate(Event):
    """Called whenever a webhook is created, modified, or removed from a guild channel.

    This requires :attr:`Intents.webhooks` to be enabled.

    Attributes
    ----------
    channel: :class:`TextChannel` | :class:`VoiceChannel` | :class:`ForumChannel` | :class:`StageChannel`
        The channel that had its webhooks updated.
    """

    __event_name__: str = "WEBHOOKS_UPDATE"

    channel: "GuildChannel"

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "WEBHOOKS_UPDATE referencing an unknown guild ID: %s. Discarding",
                data["guild_id"],
            )
            return

        channel_id = data["channel_id"]
        if channel_id is None:
            _log.debug(
                "WEBHOOKS_UPDATE channel ID was null for guild: %s. Discarding.",
                data["guild_id"],
            )
            return

        channel = guild.get_channel(int(channel_id))
        if channel is None:
            _log.debug(
                "WEBHOOKS_UPDATE referencing an unknown channel ID: %s. Discarding.",
                data["channel_id"],
            )
            return

        self = cls()
        self.channel = channel  # type: ignore
        return self
