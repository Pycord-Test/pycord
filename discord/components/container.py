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

from typing import TYPE_CHECKING, ClassVar, Literal, TypeAlias, cast

from typing_extensions import override

from ..colour import Colour
from ..enums import ComponentType
from ..types.components import ContainerComponent as ContainerComponentPayload
from .component import WalkableComponent

if TYPE_CHECKING:
    from typing_extensions import Self

    from ..state import ConnectionState
    from .action_row import ActionRow
    from .file_component import FileComponent
    from .media_gallery import MediaGallery
    from .section import Section
    from .separator import Separator
    from .text_display import TextDisplay


AllowedContainerComponents: TypeAlias = "ActionRow | TextDisplay | Section | MediaGallery | Separator | FileComponent"


class Container(WalkableComponent["ContainerComponentPayload", "AllowedContainerComponents"]):
    """Represents a Container from Components V2.

    This is a component that contains different :class:`Component` objects.
    It may only contain:

    - :class:`ActionRow`
    - :class:`TextDisplay`
    - :class:`Section`
    - :class:`MediaGallery`
    - :class:`Separator`
    - :class:`FileComponent`

    This inherits from :class:`Component`.

    .. versionadded:: 2.7
    .. versionchanged:: 3.0

    Attributes
    ----------
    type: Literal[:data:`ComponentType.container`]
        The type of component.
    components: List[:class:`AllowedContainerComponents`]
        The components contained in this container.
    accent_color: :class:`Colour` | :data:`None`
        The accent color of the container.
    spoiler: :class:`bool` | :data:`None`
        Whether the entire container has a spoiler overlay.
    id: :class:`int` | :data:`None`
        The container's ID.

    Parameters
    ----------
    components:
        The components to include in this container. Has to be passed unpacked (e.g. ``*components``).
    accent_color:
        The accent color of the container. If not provided, it defaults to :data:`None`.
    spoiler:
        Whether the entire container has the spoiler overlay. If not provided, it defaults to :data:`False`.
    id:
        The container's ID. If not provided, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.
    """

    __slots__: tuple[str, ...] = (
        "accent_color",
        "spoiler",
        "components",
    )

    __repr_info__: ClassVar[tuple[str, ...]] = __slots__
    versions: tuple[int, ...] = (2,)
    type: Literal[ComponentType.container] = ComponentType.container  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(
        self,
        *components: AllowedContainerComponents,
        accent_color: Colour | None = None,
        spoiler: bool | None = False,
        id: int | None = None,
    ) -> None:
        self.accent_color: Colour | None = accent_color
        self.spoiler: bool | None = spoiler
        self.components: list[AllowedContainerComponents] = list(components)
        super().__init__(id=id)

    @override
    def to_dict(self) -> ContainerComponentPayload:
        payload: ContainerComponentPayload = {
            "type": int(self.type),  # pyright: ignore[reportAssignmentType]
            "id": self.id,
            "components": [c.to_dict() for c in self.components],
        }
        if self.accent_color:
            payload["accent_color"] = self.accent_color.value
        if self.spoiler is not None:
            payload["spoiler"] = self.spoiler
        return payload

    @classmethod
    @override
    def from_payload(cls, payload: ContainerComponentPayload, state: ConnectionState | None = None) -> Self:
        from ._component_factory import _component_factory  # noqa: PLC0415  # pyright: ignore[reportPrivateUsage]

        components: list[AllowedContainerComponents] = cast(
            "list[AllowedContainerComponents]",
            [_component_factory(d, state=state) for d in payload.get("", [])],
        )
        accent_color = Colour(c) if (c := payload.get("accent_color") is not None) else None
        return cls(
            *components,
            accent_color=accent_color,
            spoiler=payload.get("spoiler"),
            id=payload.get("id"),
        )
