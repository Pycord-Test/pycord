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

from __future__ import annotations
from typing import Generic, TypeVar, overload
from .type_aliases import AnyComponent
from collections.abc import MutableSequence, Iterator, Iterable
from .component import WalkableComponent
from typing_extensions import override


T = TypeVar("T", bound=AnyComponent)


class ComponentsSequence(MutableSequence[T], Generic[T]):
    """A sequence of components that can be used in Discord Bot UI Kit.

    This is a mutable sequence that allows adding, removing, and modifying components.
    It is used to represent a collection of components in a message.

    .. versionadded:: 3.0
    """

    def __init__(self, *components: T):
        self._components: list[T] = list(components)

    @overload
    def __getitem__(self, index: int) -> T: ...

    @overload
    def __getitem__(self, index: slice) -> list[T]: ...

    @override
    def __getitem__(self, index: int | slice) -> T | list[T]:
        return self._components[index]

    @override
    def __len__(self) -> int:
        return len(self._components)

    @overload
    def __setitem__(self, index: int, value: T) -> None: ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[T]) -> None: ...

    @override
    def __setitem__(self, index: int | slice, value: T | Iterable[T]) -> None:
        if isinstance(index, int):
            self._components[index] = value  # pyright: ignore[reportArgumentType, reportCallIssue]
        else:
            raise NotImplementedError("Setting multiple items with a slice is not supported in this implementation")

    @overload
    def __delitem__(self, index: int) -> None: ...

    @overload
    def __delitem__(self, index: slice) -> None: ...

    @override
    def __delitem__(self, index: int | slice) -> None:
        del self._components[index]

    @override
    def insert(self, index: int, value: T) -> None:
        """Insert a component at a specific index.

        Parameters
        ----------
        index: :class:`int`
            The index at which to insert the component.
        value:
            The component to insert.
        """
        self._components.insert(index, value)

    def get_by_id(self, component_id: str | int) -> T | None:
        """Get a component by its custom ID.

        Parameters
        ----------
        component_id: :class:`str`
            The custom ID of the component to find.

        Returns
        -------
            The component with the specified custom ID, or None if not found.
        """
        for component in self._components:
            if isinstance(component_id, str) and getattr(component, "custom_id", None) == component_id:
                return component
            elif isinstance(component_id, int) and getattr(component, "id", None) == component_id:
                return component

            if isinstance(component, WalkableComponent):
                if found := component.get_by_id(component_id):
                    return found  # pyright: ignore[reportReturnType]
        return None

    @override
    def __iter__(self) -> Iterator[T]:
        yield from self._components
