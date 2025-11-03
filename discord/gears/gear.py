import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable, Sequence
from typing import TYPE_CHECKING, Any, Generic, Literal, Protocol, TypeVar, cast, overload, override

from ..app.event_emitter import Event
from ..utils.private import hybridmethod

E = TypeVar("E", bound="Event")
_T = TypeVar("_T", bound="Gear")


class BareEventCallback(Protocol, Generic[E]):
    __is_instance_method__: Literal[False]
    __event__: type[E]

    async def __call__(self, event: E) -> None: ...


class InstanceEventCallback(Protocol, Generic[E]):
    __is_instance_method__: Literal[True]
    __event__: type[E]

    async def __call__(self, self_: Any, event: E) -> None: ...


EventCallback = BareEventCallback[E] | InstanceEventCallback[E]


class Gear:
    def __init__(self) -> None:
        self._listeners: dict[
            type[Event], tuple[list[InstanceEventCallback[Event]], list[BareEventCallback[Event]]]
        ] = defaultdict(lambda: ([], []))
        self._gears: list[Gear] = []

        for name in dir(self):
            attr = getattr(type(self), name, None)
            if callable(attr) and getattr(attr, "__is_instance_method__", False):
                if event_type := getattr(attr, "__event__", None):
                    self._listeners[event_type][0].append(cast(InstanceEventCallback[Event], attr))

    def _handle_event(self, event: Event) -> Sequence[Awaitable[Any]]:
        tasks: list[Awaitable[None]] = []

        instance_listeners, bare_listeners = self._listeners[type(event)]

        tasks.extend(listener(event) for listener in bare_listeners)

        tasks.extend(listener(self, event) for listener in instance_listeners)

        for gear in self._gears:
            gear_tasks = gear._handle_event(event)
            if gear_tasks:
                tasks.extend(gear_tasks)

        return tasks

    def add_gear(self, gear: "Gear") -> None:
        self._gears.append(gear)

    def remove_gear(self, gear: "Gear") -> None:
        self._gears.remove(gear)

    def add_listener(self, event: type[E], callback: Callable[[E], Awaitable[None]]) -> None:
        callback.__is_instance_method__ = False  # pyright: ignore[reportFunctionMemberAccess]
        callback.__event__ = event  # pyright: ignore[reportFunctionMemberAccess]
        self._listeners[event][1].append(cast(BareEventCallback[Event], callback))

    def remove_listener(self, callback: Callable[[E], Awaitable[None]] | EventCallback[E]) -> None:
        event_type: type[Event] | None = getattr(callback, "__event__", None)
        if event_type is None:
            raise TypeError("callback is not a listener")

        is_instance_method = getattr(callback, "__is_instance_method__", False)
        if is_instance_method:
            self._listeners[event_type][0].remove(cast(InstanceEventCallback[Event], callback))
        else:
            self._listeners[event_type][1].remove(cast(BareEventCallback[Event], callback))

    if TYPE_CHECKING:

        @classmethod
        def listen(
            cls: type[_T],
            event: type[E],  # pyright: ignore[reportUnusedParameter]
        ) -> Callable[
            [Callable[[E], Awaitable[None]] | Callable[[Any, E], Awaitable[None]]],
            InstanceEventCallback[E] | BareEventCallback[E],
        ]: ...
    else:
        # Instance events
        @hybridmethod
        def listen(
            cls: type[_T],
            event: type[E],  # noqa: N805
        ) -> Callable[[Callable[[Any, E], Awaitable[None]]], InstanceEventCallback[E]]:
            def decorator(func: Callable[[Any, E], Awaitable[None]]) -> InstanceEventCallback[E]:
                func.__is_instance_method__ = True
                func.__event__ = event
                return cast(InstanceEventCallback[E], func)

            return decorator

        # Bare events
        @listen.instancemethod
        def listen(self, event: type[E]) -> Callable[[Callable[[E], Awaitable[None]]], BareEventCallback[E]]:
            def decorator(func: Callable[[E], Awaitable[None]]) -> BareEventCallback[E]:
                func.__is_instance_method__ = False
                func.__event__ = event
                self._listeners[event][1].append(cast(BareEventCallback[Event], func))
                return cast(BareEventCallback[E], func)

            return decorator
