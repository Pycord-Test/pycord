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

import datetime
import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic

from typing_extensions import Self, TypeVar, override

from ..abc import Snowflake
from ..enums import ChannelType, try_enum
from ..permissions import Permissions
from ..types.channel import Channel as ChannelPayload
from ..utils import snowflake_time

_log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..app.state import ConnectionState


P = TypeVar("P", bound="ChannelPayload")


class BaseChannel(ABC, Generic[P]):
    __slots__: tuple[str, ...] = ("id", "_type", "_state", "_data")  # pyright: ignore [reportIncompatibleUnannotatedOverride]

    def __init__(self, id: int, state: "ConnectionState"):
        self.id: int = id
        self._state: ConnectionState = state
        self._data: P = {}  # type: ignore

    async def _update(self, data: P) -> None:
        self._type: int = data["type"]
        self._data = self._data | data  # type: ignore

    @classmethod
    async def _from_data(cls, *, data: P, state: "ConnectionState", **kwargs) -> Self:
        if kwargs:
            _log.warning("Unexpected keyword arguments passed to %s._from_data: %r", cls.__name__, kwargs)
        self = cls(int(data["id"]), state)
        await self._update(data)
        return self

    @property
    def type(self) -> ChannelType:
        """The channel's Discord channel type."""
        return try_enum(ChannelType, self._type)

    async def _get_channel(self) -> Self:
        return self

    @property
    def created_at(self) -> datetime.datetime:
        """The channel's creation time in UTC."""
        return snowflake_time(self.id)

    @abstractmethod
    @override
    def __repr__(self) -> str: ...

    @property
    @abstractmethod
    def jump_url(self) -> str: ...

    @abstractmethod
    def permissions_for(self, obj: Snowflake, /) -> Permissions: ...
