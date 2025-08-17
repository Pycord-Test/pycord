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

from typing import TYPE_CHECKING, ClassVar, Literal, cast, override
from collections.abc import Sequence

from discord.colour import Colour
from discord.enums import ComponentType
from discord.types.components import ContainerComponent as ContainerComponentPayload
from .component import WalkableComponent
from .allowed_types import AllowedContainerComponents

if TYPE_CHECKING:
    from typing_extensions import Self
    from discord.state import ConnectionState


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
    components: List[:class:`Component`]
        The components contained in this container.
    accent_color: Optional[:class:`Colour`]
        The accent color of the container.
    spoiler: Optional[:class:`bool`]
        Whether the entire container has the spoiler overlay.
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
        *components: Sequence[AllowedContainerComponents],
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
        from ._component_factory import _component_factory  # noqa: PLC0415

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
