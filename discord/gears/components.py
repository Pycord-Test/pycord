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
from abc import ABC
from collections.abc import Awaitable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Generic, TypeAlias, TypeVar, cast

from typing_extensions import Unpack

from ..events import InteractionCreate
from ..interactions import ComponentInteraction, ModalInteraction
from ..utils.private import hybridmethod, maybe_awaitable
from .base import GearBase

ComponentListenerCallback: TypeAlias = (
    Callable[[ComponentInteraction[Any]], Awaitable[Any]] | Callable[[Any, ComponentInteraction[Any]], Awaitable[Any]]
)

ModalListenerCallback: TypeAlias = (
    Callable[[ModalInteraction[Unpack[tuple[Any, ...]]]], Awaitable[Any]]
    | Callable[[Any, ModalInteraction[Unpack[tuple[Any, ...]]]], Awaitable[Any]]
)

T = TypeVar("T", bound="ComponentListenerCallback | ModalListenerCallback")


def _unwrap_predicate(
    maybe_predicate: Callable[[str], bool | Awaitable[bool]] | str,
) -> Callable[[str], bool | Awaitable[bool]]:
    return (lambda x: x == maybe_predicate) if isinstance(maybe_predicate, str) else maybe_predicate


UiPredicate: TypeAlias = Callable[[str], bool | Awaitable[bool]]


@dataclass(frozen=True)
class UiListener(ABC, Generic[T]):
    callback: T
    predicate: UiPredicate
    _pass_self: bool = False
    once: bool = False


@dataclass(frozen=True)
class ComponentListener(UiListener[ComponentListenerCallback]):
    """A registered component interaction listener.

    This class represents a listener that has been registered to handle
    component interactions based on a predicate.
    """


CG_t = TypeVar("CG_t", bound="ComponentGearMixin")


class ComponentGearMixin(GearBase, ABC):
    """A mixin that provides component handling for a :class:`discord.Gear`.

    This mixin is used to handle components such as buttons, select menus, and other interactive elements.
    """

    def __init__(self) -> None:
        super().__init__()
        self._component_listeners: set[ComponentListener] = set()
        for name in dir(type(self)):
            attr = getattr(type(self), name, None)
            if isinstance(attr, ComponentListener):
                self._component_listeners.add(attr)

        self.add_listener(self._handle_component_interaction, event=InteractionCreate)

    async def _handle_component_interaction(self, event: InteractionCreate) -> None:
        if not isinstance(event.interaction, ComponentInteraction):
            return

        listeners_to_remove: list[ComponentListener] = []
        tasks: list[Awaitable[None]] = []
        for listener in self._component_listeners:
            if not await maybe_awaitable(listener.predicate, event.interaction.custom_id):
                continue

            if listener.once:
                listeners_to_remove.append(listener)

            if listener._pass_self:
                tasks.append(listener.callback(self, event.interaction))
            else:
                tasks.append(listener.callback(event.interaction))

        for listener in listeners_to_remove:
            self._component_listeners.remove(listener)

        await asyncio.gather(*tasks)

    def add_component_listener(
        self,
        predicate: Callable[[str], bool | Awaitable[bool]] | str,
        listener: ComponentListenerCallback,
        once: bool = False,
    ) -> ComponentListener:
        """Registers a component interaction listener.

        This method can be used to register a function that will be called
        when a component interaction occurs that matches the provided predicate.

        Parameters
        ----------
        predicate:
            A (potentially async) function that takes a string (the component's custom ID) and returns a boolean indicating whether the
            function should be called for that component. Alternatively, a string can be provided, which will match
            the component's custom ID exactly.

        listener:
            The interaction callback to call when a component interaction occurs that matches the predicate.

        once:
            Whether to unregister the listener after it has been called once.

        Returns
        -------
        ComponentListener
            The registered listener. Use this to unregister the listener.
        """
        actual_predicate: Callable[[str], bool | Awaitable[bool]] = _unwrap_predicate(predicate)
        component_listener = ComponentListener(callback=listener, predicate=actual_predicate, once=once)
        self._component_listeners.add(component_listener)
        return component_listener

    def remove_component_listener(self, listener: ComponentListener) -> None:
        """Unregisters a component interaction listener.

        This method can be used to unregister a previously registered
        component interaction listener.

        Parameters
        ----------
        listener:
            The listener to unregister.

        Raises
        ------
        KeyError
            If the listener is not registered.
        """
        self._component_listeners.remove(listener)

    if TYPE_CHECKING:

        @classmethod
        def listen_component(
            cls: type[CG_t],
            predicate: Callable[[str], bool | Awaitable[bool]] | str,  # pyright: ignore[reportUnusedParameter]
            once: bool = False,  # pyright: ignore[reportUnusedParameter]
        ) -> Callable[
            [ComponentListenerCallback],
            ComponentListener,
        ]:
            """A shortcut decorator that registers a component interaction listener.

            This decorator can be used to register a function that will be called
            when a component interaction occurs that matches the provided predicate.

            Parameters
            ----------
            predicate:
                A (potentially async) function that takes a string (the component's custom ID) and returns a boolean indicating whether the
                function should be called for that component. Alternatively, a string can be provided, which will match
                the component's custom ID exactly.
            once:
                Whether to unregister the listener after it has been called once.
            """
            ...
    else:
        # Instance function listeners (but not bound to an instance)
        @hybridmethod
        def listen_component(
            cls: type[CG_t],  # noqa: N805
            predicate: Callable[[str], bool | Awaitable[bool]] | str,
            once: bool = False,
        ) -> Callable[
            [Callable[[Any, ComponentInteraction[Any]], Awaitable[None]]],
            ComponentListener,
        ]:
            def decorator(
                func: Callable[[Any, ComponentInteraction[Any]], Awaitable[None]],
            ) -> ComponentListener:
                actual_predicate: Callable[[str], bool | Awaitable[bool]] = _unwrap_predicate(predicate)

                component_listener = ComponentListener(
                    callback=func,
                    predicate=actual_predicate,
                    _pass_self=True,
                    once=once,
                )
                return component_listener

            return decorator

        # Bare listeners (everything else)
        @listen_component.instancemethod
        def listen_component(
            self,
            predicate: Callable[[str], bool | Awaitable[bool]] | str,
            once: bool = False,
        ) -> Callable[[ComponentListenerCallback], ComponentListener]:
            def decorator(
                func: ComponentListenerCallback,
            ) -> ComponentListener:
                return self.add_component_listener(predicate=predicate, listener=func, once=once)

            return decorator


@dataclass(frozen=True)
class ModalListener(UiListener[ModalListenerCallback]):
    """A registered modal interaction listener.

    This class represents a listener that has been registered to handle
    modal interactions based on a predicate.
    """


MG_t = TypeVar("MG_t", bound="ModalGearMixin")


class ModalGearMixin(GearBase, ABC):
    """A mixin that provides modal handling for a :class:`discord.Gear`.

    This mixin is used to handle modals interactions.
    """

    def __init__(self) -> None:
        super().__init__()
        self._modal_listeners: set[ModalListener] = set()
        for name in dir(type(self)):
            attr = getattr(type(self), name, None)
            if isinstance(attr, ModalListener):
                self._modal_listeners.add(attr)

        self.add_listener(self._handle_modal_interaction, event=InteractionCreate)

    async def _handle_modal_interaction(self, event: InteractionCreate) -> None:
        if not isinstance(event.interaction, ModalInteraction):
            return

        listeners_to_remove: list[ModalListener] = []
        tasks: list[Awaitable[None]] = []
        for listener in self._modal_listeners:
            if not await maybe_awaitable(listener.predicate, event.interaction.custom_id):
                continue

            if listener.once:
                listeners_to_remove.append(listener)

            if listener._pass_self:
                tasks.append(listener.callback(self, event.interaction))
            else:
                tasks.append(listener.callback(event.interaction))

        for listener in listeners_to_remove:
            self._modal_listeners.remove(listener)

        await asyncio.gather(*tasks)

    def add_modal_listener(
        self,
        predicate: Callable[[str], bool | Awaitable[bool]] | str,
        listener: ModalListenerCallback,
        once: bool = False,
    ) -> ModalListener:
        """Registers a modal interaction listener.

        This method can be used to register a function that will be called
        when a modal interaction occurs that matches the provided predicate.

        Parameters
        ----------
        predicate:
            A (potentially async) function that takes a string (the modal's custom ID) and returns a boolean indicating whether the
            function should be called for that modal. Alternatively, a string can be provided, which will match
            the modal's custom ID exactly.

        listener:
            The interaction callback to call when a modal interaction occurs that matches the predicate.
        once:
            Whether to unregister the listener after it has been called once.

        Returns
        -------
        ModalListener
            The registered listener. Use this to unregister the listener.
        """
        actual_predicate: Callable[[str], bool | Awaitable[bool]] = _unwrap_predicate(predicate)
        modal_listener = ModalListener(callback=listener, predicate=actual_predicate, once=once)
        self._modal_listeners.add(modal_listener)
        return modal_listener

    def remove_modal_listener(self, listener: ModalListener) -> None:
        """Unregisters a modal interaction listener.

        This method can be used to unregister a previously registered
        modal interaction listener.

        Parameters
        ----------
        listener:
            The listener to unregister.

        Raises
        ------
        KeyError
            If the listener is not registered.
        """
        self._modal_listeners.remove(listener)

    if TYPE_CHECKING:

        @classmethod
        def listen_modal(
            cls: type[MG_t],
            predicate: Callable[[str], bool | Awaitable[bool]] | str,  # pyright: ignore[reportUnusedParameter]
            once: bool = False,  # pyright: ignore[reportUnusedParameter]
        ) -> Callable[
            [ModalListenerCallback],
            ModalListener,
        ]:
            """A shortcut decorator that registers a modal interaction listener.

            This decorator can be used to register a function that will be called
            when a modal interaction occurs that matches the provided predicate.

            Parameters
            ----------
            predicate:
                A (potentially async) function that takes a string (the modal's custom ID) and returns a boolean indicating whether the
                function should be called for that modal. Alternatively, a string can be provided, which will match
                the modal's custom ID exactly.
            """
            ...
    else:
        # Instance function listeners (but not bound to an instance)
        @hybridmethod
        def listen_modal(
            cls: type[MG_t],  # noqa: N805
            predicate: Callable[[str], bool | Awaitable[bool]] | str,
        ) -> Callable[
            [Callable[[Any, ModalInteraction[Unpack[tuple[Any, ...]]]], Awaitable[None]]],
            ModalListener,
        ]:
            def decorator(
                func: Callable[[Any, ModalInteraction[Unpack[tuple[Any, ...]]]], Awaitable[None]],
            ) -> ModalListener:
                actual_predicate: Callable[[str], bool | Awaitable[bool]] = _unwrap_predicate(predicate)

                modal_listener = ModalListener(
                    callback=func,
                    predicate=actual_predicate,
                    _pass_self=True,
                )
                return modal_listener

            return decorator

        # Bare listeners (everything else)
        @listen_modal.instancemethod
        def listen_modal(
            self,
            predicate: Callable[[str], bool | Awaitable[bool]] | str,
            once: bool = False,
        ) -> Callable[[ModalListenerCallback], ModalListener]:
            def decorator(
                func: ModalListenerCallback,
            ) -> ModalListener:
                return self.add_modal_listener(predicate=predicate, listener=func, once=once)

            return decorator
