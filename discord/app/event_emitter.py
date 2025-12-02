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

import asyncio
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Awaitable, Coroutine
from typing import TYPE_CHECKING, Any, Callable, Protocol, TypeAlias, TypeVar

from typing_extensions import Self

if TYPE_CHECKING:
    from .state import ConnectionState

T = TypeVar("T", bound="Event")


class Event(ABC):
    __event_name__: str

    @classmethod
    @abstractmethod
    async def __load__(cls, data: Any, state: "ConnectionState") -> Self | None: ...

    def _populate_from_slots(self, obj: Any) -> None:
        """
        Populate this event instance with attributes from another object.

        Handles both __slots__ and __dict__ based objects.

        Parameters
        ----------
        obj: Any
            The object to copy attributes from.
        """
        # Collect all slots from the object's class hierarchy
        slots = set()
        for klass in type(obj).__mro__:
            if hasattr(klass, "__slots__"):
                slots.update(klass.__slots__)

        # Copy slot attributes
        for slot in slots:
            if hasattr(obj, slot):
                try:
                    setattr(self, slot, getattr(obj, slot))
                except AttributeError:
                    # Some slots might be read-only or not settable
                    pass

        # Also copy __dict__ if it exists
        if hasattr(obj, "__dict__"):
            for key, value in obj.__dict__.items():
                try:
                    setattr(self, key, value)
                except AttributeError:
                    pass


ListenerCallback: TypeAlias = Callable[[Event], Any]


class EventReciever(Protocol):
    def __call__(self, event: Event) -> Awaitable[Any]: ...


class EventEmitter:
    def __init__(self, state: "ConnectionState") -> None:
        self._receivers: list[EventReciever] = []
        self._events: dict[str, list[type[Event]]] = defaultdict(list)
        self._state: ConnectionState = state

        from ..events import ALL_EVENTS

        for event_cls in ALL_EVENTS:
            self.add_event(event_cls)

    def add_event(self, event: type[Event]) -> None:
        self._events[event.__event_name__].append(event)

    def remove_event(self, event: type[Event]) -> list[type[Event]] | None:
        return self._events.pop(event.__event_name__, None)

    def add_receiver(self, receiver: EventReciever) -> None:
        self._receivers.append(receiver)

    def remove_receiver(self, receiver: EventReciever) -> None:
        self._receivers.remove(receiver)

    async def emit(self, event_str: str, data: Any) -> None:
        events = self._events.get(event_str, [])

        coros: list[Awaitable[None]] = []
        for event_cls in events:
            event = await event_cls.__load__(data=data, state=self._state)

            if event is None:
                continue

            coros.extend(receiver(event) for receiver in self._receivers)

        await asyncio.gather(*coros)
