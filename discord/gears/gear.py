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

from collections import defaultdict
from collections.abc import Awaitable, Callable, Collection, Sequence
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    Protocol,
    TypeAlias,
    TypeVar,
    cast,
    runtime_checkable,
)

from ..app.event_emitter import Event
from ..utils import MISSING, Undefined
from ..utils.annotations import get_annotations
from ..utils.private import hybridmethod

_T = TypeVar("_T", bound="Gear")
E = TypeVar("E", bound="Event", covariant=True)
E_contra = TypeVar("E_contra", bound="Event", contravariant=True)


@runtime_checkable
class AttributedEventCallback(Protocol):
    __event__: type[Event]
    __once__: bool


@runtime_checkable
class StaticAttributedEventCallback(AttributedEventCallback, Protocol):
    __staticmethod__: bool


EventCallback: TypeAlias = Callable[[E], Awaitable[None]]


class Gear:
    """A gear is a modular component that can listen to and handle events.

    You can subclass this class to create your own gears and attach them to your bot or other gears.

    Example
    -------
    .. code-block:: python3
        class MyGear(Gear):
            @Gear.listen()
            async def listen(self, event: Ready) -> None:
                print(f"Received event on instance: {event.__class__.__name__}")


        my_gear = MyGear()


        @my_gear.listen()
        async def on_event(event: Ready) -> None:
            print(f"Received event on bare: {event.__class__.__name__}")


        bot.add_gear(my_gear)
    """

    def __init__(self) -> None:
        self._listeners: dict[type[Event], set[EventCallback[Event]]] = defaultdict(set)
        self._once_listeners: set[EventCallback[Event]] = set()
        self._init_called: bool = True

        self._gears: set[Gear] = set()

        for name in dir(type(self)):
            attr = getattr(type(self), name, None)
            if not callable(attr):
                continue
            if isinstance(attr, StaticAttributedEventCallback):
                callback = attr
                event = attr.__event__
                once = attr.__once__
            elif isinstance(attr, AttributedEventCallback):
                callback = partial(attr, self)
                event = attr.__event__
                once = attr.__once__
            else:
                continue
            self.add_listener(cast("EventCallback[Event]", callback), event=event, once=once)
            setattr(self, name, callback)

    def _handle_event(self, event: Event) -> Collection[Awaitable[Any]]:
        tasks: list[Awaitable[None]] = []

        for listener in self._listeners[type(event)]:
            if listener in self._once_listeners:
                self._once_listeners.remove(listener)
            tasks.append(listener(event))

        for gear in self._gears:
            tasks.extend(gear._handle_event(event))

        return tasks

    def attach_gear(self, gear: "Gear") -> None:
        """Attaches a gear to this gear.

        This will propagate all events from the attached gear to this gear.

        Parameters
        ----------
        gear:
            The gear to attach.
        """
        if not getattr(gear, "_init_called", False):
            raise RuntimeError(
                "Cannot attach gear before __init__ has been called. Maybe you forgot to call super().__init__()?"
            )
        self._gears.add(gear)

    def detach_gear(self, gear: "Gear") -> None:
        """Detaches a gear from this gear.

        Parameters
        ----------
        gear:
            The gear to detach.

        Raises
        ------
        KeyError
            If the gear is not attached.
        """
        self._gears.remove(gear)

    @staticmethod
    def _parse_listener_signature(
        callback: Callable[[E], Awaitable[None]], is_instance_function: bool = False
    ) -> type[E]:
        params = get_annotations(
            callback,
            expected_types={0: type(Event)},
            custom_error="""Type annotation mismatch for parameter "{parameter}": expected <class 'Event'>, got {got}.""",
        )
        if is_instance_function:
            event = list(params.values())[1]
        else:
            event = next(iter(params.values()))
        return cast(type[E], event)

    def add_listener(
        self,
        callback: Callable[[E], Awaitable[None]],
        *,
        event: type[E] | Undefined = MISSING,
        is_instance_function: bool = False,
        once: bool = False,
    ) -> None:
        """
        Adds an event listener to the gear.

        Parameters
        ----------
        callback:
            The callback function to be called when the event is emitted.
        event:
            The type of event to listen for. If not provided, it will be inferred from the callback signature.
        once:
            Whether the listener should be removed after being called once.
        is_instance_function:
            Whether the callback is an instance method (i.e., it takes the gear instance as the first argument).

        Raises
        ------
        TypeError
            If the event type cannot be inferred from the callback signature.
        """
        if event is MISSING:
            event = self._parse_listener_signature(callback, is_instance_function)
        if once:
            self._once_listeners.add(cast("EventCallback[Event]", callback))
        self._listeners[event].add(cast("EventCallback[Event]", callback))

    def remove_listener(
        self, callback: EventCallback[E], event: type[E] | Undefined = MISSING, is_instance_function: bool = False
    ) -> None:
        """
        Removes an event listener from the gear.

        Parameters
        ----------
        callback:
            The callback function to be removed.
        event:
            The type of event the listener was registered for. If not provided, it will be inferred from the callback signature.
        is_instance_function:
            Whether the callback is an instance method (i.e., it takes the gear instance as the first argument).

        Raises
        ------
        TypeError
            If the event type cannot be inferred from the callback signature.
        KeyError
            If the listener is not found.
        """
        if event is MISSING:
            event = self._parse_listener_signature(callback)
        self._listeners[event].remove(cast("EventCallback[Event]", callback))

    if TYPE_CHECKING:

        @classmethod
        def listen(
            cls: type[_T],
            event: type[E] | Undefined = MISSING,  # pyright: ignore[reportUnusedParameter]
            once: bool = False,
        ) -> Callable[
            [Callable[[E], Awaitable[None]] | Callable[[Any, E], Awaitable[None]]],
            EventCallback[E],
        ]:
            """
            A decorator that registers an event listener.

            Parameters
            ----------
            event:
                The type of event to listen for. If not provided, it will be inferred from the callback signature.
            once:
                Whether the listener should be removed after being called once.

            Returns
            -------
            A decorator that registers the decorated function as an event listener.

            Raises
            ------
            TypeError
                If the event type cannot be inferred from the callback signature.
            """
            ...
    else:
        # Instance function events (but not bound to an instance, this is why we have to manually pass self with partial above)
        @hybridmethod
        def listen(
            cls: type[_T],  # noqa: N805 # Ruff complains of our shenanigans here
            event: type[E] | Undefined = MISSING,
            once: bool = False,
        ) -> Callable[[Callable[[Any, E], Awaitable[None]]], Callable[[Any, E], Awaitable[None]]]:
            def decorator(func: Callable[[Any, E], Awaitable[None]]) -> Callable[[Any, E], Awaitable[None]]:
                if isinstance(func, staticmethod):
                    func.__func__.__event__ = event
                    func.__func__.__once__ = once
                    func.__func__.__staticmethod__ = True
                else:
                    func.__event__ = event
                    func.__once__ = once
                return func

            return decorator

        # Bare events (everything else)
        @listen.instancemethod
        def listen(
            self, event: type[E] | Undefined = MISSING, once: bool = False
        ) -> Callable[[Callable[[E], Awaitable[None]]], EventCallback[E]]:
            def decorator(func: Callable[[E], Awaitable[None]]) -> EventCallback[E]:
                self.add_listener(func, event=event, is_instance_function=False, once=once)
                return cast(EventCallback[E], func)

            return decorator
