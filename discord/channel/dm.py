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

from collections.abc import Collection
from typing import TYPE_CHECKING

from typing_extensions import override

from ..abc import Messageable, Snowflake
from ..asset import Asset
from ..permissions import Permissions
from ..types.channel import DMChannel as DMChannelPayload
from ..types.channel import GroupDMChannel as GroupDMChannelPayload
from .base import BaseChannel, P

if TYPE_CHECKING:
    from ..app.state import ConnectionState
    from ..message import Message
    from ..user import User


class DMChannel(BaseChannel[DMChannelPayload], Messageable):
    __slots__: tuple[str, ...] = ("last_message", "recipient")

    def __init__(self, id: int, state: "ConnectionState") -> None:
        super().__init__(id, state)
        self.recipient: User | None = None
        self.last_message: Message | None = None

    @override
    async def _update(self, data: DMChannelPayload) -> None:
        await super()._update(data)
        if last_message_id := data.get("last_message_id", None):
            self.last_message = await self._state.cache.get_message(int(last_message_id))
        if recipients := data.get("recipients"):
            self.recipient = await self._state.cache.store_user(recipients[0])

    @override
    def __repr__(self) -> str:
        return f"<DMChannel id={self.id} recipient={self.recipient}>"

    @property
    @override
    def jump_url(self) -> str:
        """Returns a URL that allows the client to jump to the channel."""
        return f"https://discord.com/channels/@me/{self.id}"


class GroupDMChannel(BaseChannel[GroupDMChannelPayload], Messageable):
    __slots__: tuple[str, ...] = ("recipients", "icon_hash", "owner", "name")

    def __init__(self, id: int, state: "ConnectionState") -> None:
        super().__init__(id, state)
        self.recipients: Collection[User] = set()
        self.icon_hash: str | None = None
        self.owner: User | None = None

    @override
    async def _update(self, data: GroupDMChannelPayload) -> None:
        await super()._update(data)
        self.name: str = data["name"]
        if recipients := data.get("recipients"):
            self.recipients = {await self._state.cache.store_user(recipient_data) for recipient_data in recipients}
        if icon_hash := data.get("icon"):
            self.icon_hash = icon_hash
        if owner_id := data.get("owner_id"):
            self.owner = await self._state.cache.get_user(int(owner_id))

    @override
    def __repr__(self) -> str:
        return f"<GroupDMChannel id={self.id} name={self.name}>"

    @property
    @override
    def jump_url(self) -> str:
        """Returns a URL that allows the client to jump to the channel."""
        return f"https://discord.com/channels/@me/{self.id}"

    @property
    def icon(self) -> Asset | None:
        """Returns the channel's icon asset if available."""
        if self.icon_hash is None:
            return None
        return Asset._from_icon(self._state, self.id, self.icon_hash, path="channel")
