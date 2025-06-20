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

from discord.types.monetization import Entitlement as EntitlementPayload

from ..monetization import Entitlement

from ..app.state import ConnectionState
from ..app.event_emitter import Event


class EntitlementCreate(Event, Entitlement):
    __event_name__ = "ENTITLEMENT_CREATE"

    def __init__(self) -> None:
        pass

    @classmethod
    async def __load__(cls, data: Any, state: ConnectionState) -> Self:
        self = cls()
        self.__dict__.update(Entitlement(data=data, state=state).__dict__)
        return self


class EntitlementUpdate(Event, Entitlement):
    __event_name__ = "ENTITLEMENT_UPDATE"

    def __init__(self) -> None:
        pass

    @classmethod
    async def __load__(cls, data: Any, state: ConnectionState) -> Self:
        self = cls()
        self.__dict__.update(Entitlement(data=data, state=state).__dict__)
        return self


class EntitlementDelete(Event, Entitlement):
    __event_name__ = "ENTITLEMENT_DELETE"

    def __init__(self) -> None:
        pass

    @classmethod
    async def __load__(cls, data: Any, state: ConnectionState) -> Self:
        self = cls()
        self.__dict__.update(Entitlement(data=data, state=state).__dict__)
        return self

