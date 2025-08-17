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

from .allowed_types import AnyComponent
from collections.abc import MutableSequence
from .component import WalkableComponent
from typing import Iterator


class ComponentsSequence(MutableSequence[AnyComponent]):
    """A sequence of components that can be used in Discord Bot UI Kit.

    This is a mutable sequence that allows adding, removing, and modifying components.
    It is used to represent a collection of components in a message.

    .. versionadded:: 3.0
    """

    def __init__(self, *components: AnyComponent):
        self._components = list(components)

    def __getitem__(self, index: int) -> AnyComponent:
        return self._components[index]

    def __len__(self) -> int:
        return len(self._components)

    def __setitem__(self, index: int, value: AnyComponent) -> None:
        self._components[index] = value

    def __delitem__(self, index: int) -> None:
        del self._components[index]

    def insert(self, index: int, value: AnyComponent) -> None:
        self._components.insert(index, value)

    def get_by_id(self, component_id: str | int) -> AnyComponent | None:
        """Get a component by its custom ID.

        Parameters
        ----------
        component_id: :class:`str`
            The custom ID of the component to find.

        Returns
        -------
        Optional[AnyComponent]
            The component with the specified custom ID, or None if not found.
        """
        for component in self._components:
            if isinstance(component_id, str) and getattr(component, "custom_id", None) == component_id:
                return component
            elif isinstance(component_id, int) and getattr(component, "id", None) == component_id:
                return component

            if isinstance(component, WalkableComponent):
                if found := component.get_by_id(component_id):
                    return found
        return None

    def __iter__(self) -> Iterator[AnyComponent]:
        yield from self._components
