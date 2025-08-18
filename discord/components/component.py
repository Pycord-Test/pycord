"""
The MIT License (MIT)

Copyright (c) 2015-2021 Rapptz
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

from typing import TYPE_CHECKING, Callable, ClassVar, Generic
from typing_extensions import override
from abc import ABC, abstractmethod
from collections.abc import Iterator

from discord.enums import ComponentType
from .types import P, C

if TYPE_CHECKING:
    from typing_extensions import Self
    from discord.state import ConnectionState


class Component(ABC, Generic[P]):
    """Represents a Discord Bot UI Kit Component.

    The components supported by Discord in messages are as follows:

    - :class:`ActionRow`
    - :class:`Button`
    - :class:`SelectMenu`
    - :class:`Section`
    - :class:`TextDisplay`
    - :class:`Thumbnail`
    - :class:`MediaGallery`
    - :class:`FileComponent`
    - :class:`Separator`
    - :class:`Container`

    This class is abstract and cannot be instantiated.

    .. versionadded:: 2.0

    Attributes
    ----------
    type: :class:`ComponentType`
        The type of component.
    id: :class:`int`
        The component's ID. If not provided by the user, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.
    """

    __slots__: tuple[str, ...] = ("type", "id")  # pyright: ignore[reportIncompatibleUnannotatedOverride]

    __repr_info__: ClassVar[tuple[str, ...]]
    type: ComponentType
    versions: tuple[int, ...]

    def __init__(self, id: int | None = None) -> None:
        self.id: int | None = id

    @override
    def __repr__(self) -> str:
        attrs = " ".join(f"{key}={getattr(self, key)!r}" for key in self.__repr_info__)
        return f"<{self.__class__.__name__} {attrs}>"

    @abstractmethod
    def to_dict(self) -> P: ...

    @classmethod
    @abstractmethod
    def from_payload(cls, payload: P) -> Self: ...  # pyright: ignore[reportGeneralTypeIssues]

    def is_v2(self) -> bool:
        """Whether this component was introduced in Components V2."""
        return bool(self.versions and 1 not in self.versions)

    def any_is_v2(self) -> bool:
        """Whether this component or any of its children were introduced in Components V2."""
        return self.is_v2()

    def is_dispatchable(self) -> bool:
        """Wether this component can be interacted with and lead to a :class:`Interaction`"""
        return False

    def any_is_dispatchable(self) -> bool:
        """Whether this component or any of its children can be interacted with and lead to a :class:`Interaction`"""
        return self.is_dispatchable()


class StateComponent(Component[P], ABC):
    @classmethod
    @abstractmethod
    @override
    def from_payload(cls, payload: P, state: ConnectionState | None = None) -> Self:  # pyright: ignore[reportGeneralTypeIssues]
        ...


class WalkableComponent(Component[P], ABC, Generic[P, C]):
    """A component that can be walked through.

    This is an abstract class and cannot be instantiated directly.
    It is used to represent components that can be walked through, such as :class:`ActionRow`, :class:`Container` and :class:`Section`.
    """

    __slots__: tuple[str, ...] = ("components",)  # pyright: ignore[reportIncompatibleUnannotatedOverride]
    components: list[C]

    def walk_components(self) -> Iterator[C]:
        """Walks through the components in this component."""
        for component in self.components:
            if isinstance(component, WalkableComponent):
                yield from component.walk_components()
            else:
                yield component

    __iter__: Callable[[Self], Iterator[C]] = walk_components

    @override
    def any_is_v2(self) -> bool:
        """Whether this component or any of its children were introduced in Components V2."""
        return self.is_v2() or any(c.any_is_v2() for c in self.walk_components())

    @override
    def any_is_dispatchable(self) -> bool:
        """Whether this component or any of its children can be interacted with and lead to a :class:`Interaction`"""
        return self.is_dispatchable() or any(c.any_is_dispatchable() for c in self.walk_components())

    def get_by_id(self, component_id: str | int) -> C | None:
        for component in self.walk_components():
            if isinstance(component_id, str) and getattr(component, "custom_id", None) == component_id:
                return component
            elif isinstance(component_id, int) and getattr(component, "id", None) == component_id:
                return component
