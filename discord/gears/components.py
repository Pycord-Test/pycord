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
from functools import wraps
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Coroutine, ParamSpec, Protocol, TypeAlias, TypeVar, Unpack

from ..events import InteractionCreate
from ..interactions import ComponentInteraction, ModalInteraction
from ..utils import MISSING, Undefined
from ..utils.private import hybridmethod, maybe_awaitable
from .base import GearBase

ComponentPredicate: TypeAlias = Callable[[str], bool | Awaitable[bool]]


class ComponentListener(Protocol):
    async def __call__(self, interaction: ComponentInteraction[Any]) -> Any: ...


CL_t = TypeVar("CL_t", bound=ComponentListener)


class ModalListener(Protocol):
    async def __call__(self, interaction: ModalInteraction[Unpack[tuple[Any, ...]]]) -> Any: ...


ML_t = TypeVar("ML_t", bound=ModalListener)

T = TypeVar("T", bound="ComponentListener | ModalListener")
MG_t = TypeVar("MG_t", bound="ModalGearMixin")


def _unwrap_predicate(
    maybe_predicate: Callable[[str], bool | Awaitable[bool]] | str,
) -> Callable[[str], bool | Awaitable[bool]]:
    return lambda x: x == maybe_predicate if isinstance(maybe_predicate, str) else maybe_predicate


P = ParamSpec("P")
R = TypeVar("R")


def _listener_factory(
    listener: Callable[P, Awaitable[R]],
    interaction_type: type[ModalInteraction | ComponentInteraction],
    predicate: ComponentPredicate,
) -> Callable[P, Coroutine[Any, Any, R | None]]:
    @wraps(listener)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:
        # Assume last positional arg is the interaction
        if args:
            interaction: Any = args[-1]
            if isinstance(interaction, interaction_type) and await maybe_awaitable(predicate, interaction.custom_id):
                return await listener(*args, **kwargs)
        return None

    return wrapper


CG_t = TypeVar("CG_t", bound="ComponentGearMixin")


class ComponentGearMixin(GearBase, ABC):
    """A mixin that provides component handling for a :class:`discord.Gear`.

    This mixin is used to handle components such as buttons, select menus, and other interactive elements.
    """

    def add_component_listener(
        self, predicate: Callable[[str], bool | Awaitable[bool]] | str, listener: ComponentListener
    ) -> Callable[[InteractionCreate], Awaitable[None]]:
        """Registers a component interaction listener.

        This method can be used to register a function that will be called
        when a component interaction occurs that matches the provided predicate.

        .. versionadded:: 3.0

        Parameters
        ----------
        predicate:
            A (potentially async) function that takes a string (the component's custom ID) and returns a boolean indicating whether the
            function should be called for that component. Alternatively, a string can be provided, which will match
            the component's custom ID exactly.

        listener:
            The interaction callback to call when a component interaction occurs that matches the predicate.

        Returns
        -------
        Callable[[InteractionCreate], Awaitable[None]]
            The registered listener. Use this to unregister the listener.
        """
        actual_predicate: Callable[[str], bool | Awaitable[bool]] = _unwrap_predicate(predicate)
        actual_listener = _listener_factory(listener, ComponentInteraction, actual_predicate)
        self.add_listener(actual_listener, event=InteractionCreate)
        return actual_listener

    if TYPE_CHECKING:

        @classmethod
        def listen_component(
            cls: type[CG_t],
            predicate: Callable[[str], bool | Awaitable[bool]] | str,
        ) -> Callable[
            [Callable[[ComponentListener], Awaitable[None]] | Callable[[Any, ComponentListener], Awaitable[None]]],
            Callable[[InteractionCreate], Awaitable[None]],
        ]:
            """A shortcut decorator that registers a component interaction listener.

            This decorator can be used to register a function that will be called
            when a component interaction occurs that matches the provided predicate.

            .. versionadded:: 3.0

            Parameters
            ----------
            predicate:
                A (potentially async) function that takes a string (the component's custom ID) and returns a boolean indicating whether the
                function should be called for that component. Alternatively, a string can be provided, which will match
                the component's custom ID exactly.
            """
            ...
    else:
        # Instance function listeners (but not bound to an instance)
        @hybridmethod
        def listen_component(
            cls: type[CG_t],  # noqa: N805
            predicate: Callable[[str], bool | Awaitable[bool]] | str,
        ) -> Callable[
            [Callable[[Any, ComponentInteraction[Any]], Awaitable[None]]],
            Callable[[Any, ComponentInteraction[Any]], Awaitable[None]],
        ]:
            def decorator(
                func: Callable[[Any, ComponentInteraction[Any]], Awaitable[None]],
            ) -> Callable[[Any, ComponentInteraction[Any]], Awaitable[None]]:
                actual_predicate: Callable[[str], bool | Awaitable[bool]] = _unwrap_predicate(predicate)

                actual_listener = _listener_factory(func, ComponentInteraction, actual_predicate)

                # Use parent's listen to register for InteractionCreate
                return cls.listen(InteractionCreate)(actual_listener)

            return decorator

        # Bare listeners (everything else)
        @listen_component.instancemethod
        def listen_component(
            self,
            predicate: Callable[[str], bool | Awaitable[bool]] | str,
        ) -> Callable[[ComponentListener], Callable[[InteractionCreate], Awaitable[None]]]:
            def decorator(
                func: ComponentListener,
            ) -> Callable[[InteractionCreate], Awaitable[None]]:
                return self.add_component_listener(predicate, func)

            return decorator


MG_t = TypeVar("MG_t", bound="ModalGearMixin")


class ModalGearMixin(GearBase, ABC):
    """A mixin that provides modal handling for a :class:`discord.Gear`.

    This mixin is used to handle modals interactions.
    """

    def add_modal_listener(
        self, predicate: Callable[[str], bool | Awaitable[bool]] | str, listener: ModalListener
    ) -> Callable[[InteractionCreate], Awaitable[None]]:
        """Registers a modal interaction listener.

        This method can be used to register a function that will be called
        when a modal interaction occurs that matches the provided predicate.

        .. versionadded:: 3.0

        Parameters
        ----------
        predicate:
            A (potentially async) function that takes a string (the modal's custom ID) and returns a boolean indicating whether the
            function should be called for that modal. Alternatively, a string can be provided, which will match
            the modal's custom ID exactly.

        listener:
            The interaction callback to call when a modal interaction occurs that matches the predicate.

        Returns
        -------
        Callable[[InteractionCreate], Awaitable[None]]
            The registered listener. Use this to unregister the listener.
        """
        actual_predicate: Callable[[str], bool | Awaitable[bool]] = _unwrap_predicate(predicate)
        actual_listener = _listener_factory(listener, ModalInteraction, actual_predicate)
        self.add_listener(actual_listener, event=InteractionCreate)
        return actual_listener

    if TYPE_CHECKING:

        @classmethod
        def listen_modal(
            cls: type[MG_t],
            predicate: Callable[[str], bool | Awaitable[bool]] | str,
        ) -> Callable[
            [Callable[[ModalListener], Awaitable[None]] | Callable[[Any, ModalListener], Awaitable[None]]],
            Callable[[InteractionCreate], Awaitable[None]],
        ]:
            """A shortcut decorator that registers a modal interaction listener.

            This decorator can be used to register a function that will be called
            when a modal interaction occurs that matches the provided predicate.

            .. versionadded:: 3.0

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
            Callable[[Any, ModalInteraction[Unpack[tuple[Any, ...]]]], Awaitable[None]],
        ]:
            def decorator(
                func: Callable[[Any, ModalInteraction[Unpack[tuple[Any, ...]]]], Awaitable[None]],
            ) -> Callable[[Any, ModalInteraction[Unpack[tuple[Any, ...]]]], Awaitable[None]]:
                actual_predicate: Callable[[str], bool | Awaitable[bool]] = _unwrap_predicate(predicate)

                actual_listener = _listener_factory(func, ModalInteraction, actual_predicate)

                # Use parent's listen to register for InteractionCreate
                return cls.listen(InteractionCreate)(actual_listener)

            return decorator

        # Bare listeners (everything else)
        @listen_modal.instancemethod
        def listen_modal(
            self,
            predicate: Callable[[str], bool | Awaitable[bool]] | str,
        ) -> Callable[[ModalListener], Callable[[InteractionCreate], Awaitable[None]]]:
            def decorator(
                func: ModalListener,
            ) -> Callable[[InteractionCreate], Awaitable[None]]:
                return self.add_modal_listener(predicate, func)

            return decorator
