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
from collections.abc import Awaitable, Callable, Collection
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    TypeAlias,
    TypeVar,
    cast,
)

from typing_extensions import override

from ..app.event_emitter import Event
from ..utils import MISSING, Undefined
from ..utils.annotations import get_annotations
from ..utils.private import hybridmethod
from .base import GearBase
from .components import ComponentGearMixin, ModalGearMixin

_T = TypeVar("_T", bound="Gear")
E = TypeVar("E", bound="Event", covariant=True)

EventCallback: TypeAlias = Callable[[E], Awaitable[None]] | Callable[[Any, E], Awaitable[None]]


@dataclass
class EventListener(Generic[E]):
    """A registered event listener.

    This class represents a listener that has been registered to handle
    events of a specific type.
    """

    callback: Callable[..., Awaitable[None]]
    event: type[E]
    once: bool = False
    _pass_self: bool = False

    @override
    def __hash__(self) -> int:
        return hash((self.callback, self.event))


class Gear(ModalGearMixin, ComponentGearMixin, GearBase):  # pyright: ignore[reportUnsafeMultipleInheritance]
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
        self._listeners: dict[type[Event], set[EventListener[Event]]] = defaultdict(set)
        self._init_called: bool = True

        self._gears: set[Gear] = set()

        for name in dir(type(self)):
            attr = getattr(type(self), name, None)
            if isinstance(attr, EventListener):
                self._listeners[attr.event.event_type()].add(attr)

        super().__init__()

    def _handle_event(self, event: Event) -> Collection[Awaitable[Any]]:
        tasks: list[Awaitable[None]] = []

        listeners_to_remove: list[EventListener[Event]] = []
        for listener in self._listeners[event.event_type()]:
            if listener.once:
                listeners_to_remove.append(listener)

            if listener._pass_self:
                tasks.append(listener.callback(self, event))
            else:
                tasks.append(listener.callback(event))

        for listener in listeners_to_remove:
            self._listeners[event.event_type()].remove(listener)

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

    @override
    def add_listener(
        self,
        callback: Callable[[E], Awaitable[None]],
        *,
        event: type[E] | Undefined = MISSING,
        is_instance_function: bool = False,
        once: bool = False,
    ) -> EventListener[E]:
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

        Returns
        -------
        EventListener
            The registered listener. Use this to unregister the listener.

        Raises
        ------
        TypeError
            If the event type cannot be inferred from the callback signature.
        """
        if event is MISSING:
            event = self._parse_listener_signature(callback, is_instance_function)

        listener = EventListener(callback=callback, event=event, once=once)
        self._listeners[event.event_type()].add(cast(EventListener[Event], listener))
        return listener

    @override
    def remove_listener(
        self,
        listener: EventListener[E],
        event: type[E] | Undefined = MISSING,
        is_instance_function: bool = False,
    ) -> None:
        """
        Removes an event listener from the gear.

        Parameters
        ----------
        listener:
            The EventListener instance to be removed.
        event:
            The type of event the listener was registered for. If not provided, it will be inferred from the callback signature.
            Only required if passing a callback instead of an EventListener.
        is_instance_function:
            Whether the callback is an instance method (i.e., it takes the gear instance as the first argument).

        Raises
        ------
        TypeError
            If the event type cannot be inferred from the callback signature.
        KeyError
            If the listener is not found.
        """
        if isinstance(listener, EventListener):
            self._listeners[listener.event.event_type()].remove(cast(EventListener[Event], listener))

    if TYPE_CHECKING:

        @classmethod
        @override
        def listen(
            cls: type[_T],
            event: type[E] | Undefined = MISSING,
            once: bool = False,
        ) -> Callable[
            [Callable[[E], Awaitable[None]] | Callable[[Any, E], Awaitable[None]]],
            EventListener[E],
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
            event: type[E] | None = None,
            once: bool = False,
        ) -> Callable[[Callable[[Any, E], Awaitable[None]]], EventListener[E]]:
            def decorator(func: Callable[[Any, E], Awaitable[None]]) -> EventListener[E]:
                is_static = isinstance(func, staticmethod)

                if event is None:
                    inferred_event: type[E] = cls._parse_listener_signature(func, is_instance_function=not is_static)
                else:
                    inferred_event = event

                event_listener = EventListener(
                    callback=func,
                    event=inferred_event,
                    once=once,
                    _pass_self=not is_static,
                )
                return event_listener

            return decorator

        # Bare events (everything else)
        @listen.instancemethod
        def listen(
            self, event: type[E] | Undefined = MISSING, once: bool = False
        ) -> Callable[[Callable[[E], Awaitable[None]]], EventListener[E]]:
            def decorator(func: Callable[[E], Awaitable[None]]) -> EventListener[E]:
                listener = self.add_listener(func, event=event, is_instance_function=False, once=once)
                return listener

            return decorator
