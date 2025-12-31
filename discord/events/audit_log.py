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
from typing import Any

from typing_extensions import Self, override

from discord.app.event_emitter import Event
from discord.app.state import ConnectionState
from discord.audit_logs import AuditLogEntry
from discord.raw_models import RawAuditLogEntryEvent

_log = logging.getLogger(__name__)


class GuildAuditLogEntryCreate(Event, AuditLogEntry):
    """Called when an audit log entry is created.

    The bot must have :attr:`~Permissions.view_audit_log` to receive this, and
    :attr:`Intents.moderation` must be enabled.

    This event inherits from :class:`AuditLogEntry`.

    Attributes
    ----------
    raw: :class:`RawAuditLogEntryEvent`
        The raw event payload data.
    """

    __event_name__: str = "GUILD_AUDIT_LOG_ENTRY_CREATE"

    raw: RawAuditLogEntryEvent

    def __init__(self) -> None: ...

    @classmethod
    @override
    async def __load__(cls, data: Any, state: ConnectionState) -> Self | None:
        guild = await state._get_guild(int(data["guild_id"]))
        if guild is None:
            _log.debug(
                "GUILD_AUDIT_LOG_ENTRY_CREATE referencing an unknown guild ID: %s. Discarding.",
                data["guild_id"],
            )
            return

        raw = RawAuditLogEntryEvent(data)
        raw.guild = guild

        user = await state.get_user(raw.user_id)
        if user is not None:
            data_copy = data.copy()
            data_copy.pop("guild_id", None)
            entry = AuditLogEntry(users={data_copy["user_id"]: user}, data=data_copy, guild=guild)
            self = cls()
            self.raw = raw
            self.__dict__.update(entry.__dict__)
            return self
