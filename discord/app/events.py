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

from abc import ABC
from asyncio import Future
import asyncio
from typing import Any, Callable, Self, Type, TypeVar

from .state import ConnectionState

T = TypeVar('T')


class Event(ABC):
    __event_name__: str

    @classmethod
    async def __load__(cls, data: dict[str, Any], state: ConnectionState) -> Self:
        ...


class EventEmitter:
    def __init__(self, state: ConnectionState) -> None:
        self._listeners: dict[Type[Event], list[Callable]] = {}
        self._events: dict[str, list[Type[Event]]]
        self._wait_fors: dict[Type[Event], list[Future]] = {}
        self._state = state

    def add_event(self, event: Type[Event]) -> None:
        try:
            self._events[event.__event_name__].append(event)
        except KeyError:
            self._events[event.__event_name__] = [event]

    def remove_event(self, event: Type[Event]) -> list[Type[Event]] | None:
        return self._events.pop(event.__event_name__, None)

    def add_listener(self, event: Type[Event], listener: Callable) -> None:
        try:
            self._listeners[event].append(listener)
        except KeyError:
            self.add_event(event)
            self._listener[event] = [listener]

    def remove_listener(self, event: Type[Event], listener: Callable) -> None:
        self._listeners[event].remove(listener)

    def add_wait_for(self, event: Type[T]) -> Future[T]:
        fut = Future()

        try:
            self._wait_fors[event].append(fut)
        except KeyError:
            self._wait_fors[event] = [fut]

        return fut

    def remove_wait_for(self, event: Type[Event], fut: Future) -> None:
        self._wait_fors[event].remove(fut)

    async def publish(self, event_str: str, data: dict[str, Any]) -> None:
        items = list(self.events.items())

        for event, funcs in items:
            if event._name == event_str:
                eve = event()

                await eve.__load__(data)

                for func in funcs:
                    asyncio.create_task(func(eve))

                wait_fors = self.wait_fors.get(event)

                if wait_fors is not None:
                    for wait_for in wait_fors:
                        wait_for.set_result(eve)
                    self.wait_fors.pop(event)
