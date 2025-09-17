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

from collections.abc import Iterator, Sequence
from typing import TYPE_CHECKING, ClassVar, Literal, TypeAlias, cast

from typing_extensions import override

from ..enums import ComponentType
from ..types.components import SectionComponent as SectionComponentPayload
from .component import WalkableComponent

if TYPE_CHECKING:
    from typing_extensions import Self

    from discord.state import ConnectionState

    from .button import Button
    from .text_display import TextDisplay
    from .thumbnail import Thumbnail

    AllowedSectionComponents: TypeAlias = TextDisplay
    AllowedSectionAccessoryComponents: TypeAlias = Button | Thumbnail


class Section(
    WalkableComponent["SectionComponentPayload", "AllowedSectionComponents | AllowedSectionAccessoryComponents"],
):
    """Represents a Section from Components V2.

    This is a component that groups other components together with an additional component to the right as the accessory.

    This inherits from :class:`Component`.

    .. versionadded:: 2.7

    Attributes
    ----------
    type: Literal[:data:`ComponentType.section`]
        The type of component.
    components: List[:class:`Component`]
        The components contained in this section. Currently supports :class:`TextDisplay`.
    accessory: :class:`Component` | :data:`None`
        The accessory attached to this Section. Currently supports :class:`Button` and :class:`Thumbnail`.
    id: :class:`int` | :data:`None`
        The section's ID.

    Parameters
    ----------
    components:
        The components contained in this section. Currently supports :class:`TextDisplay`.
    accessory:
        The accessory attached to this Section. Currently supports :class:`Button` and :class:`Thumbnail`.
    id:
        The section's ID. If not provided, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.
    """

    __slots__: tuple[str, ...] = ("components", "accessory")

    __repr_info__: ClassVar[tuple[str, ...]] = __slots__
    versions: tuple[int, ...] = (2,)
    type: Literal[ComponentType.section] = ComponentType.section  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(
        self,
        components: Sequence[AllowedSectionComponents],
        accessory: AllowedSectionAccessoryComponents | None = None,
        id: int | None = None,
    ):
        self.components: list[AllowedSectionComponents] = list(components)  # pyright: ignore[reportIncompatibleVariableOverride]
        self.accessory: AllowedSectionAccessoryComponents | None = accessory
        super().__init__(id=id)

    @classmethod
    @override
    def from_payload(cls, payload: SectionComponentPayload, state: ConnectionState | None = None) -> Self:
        from ._component_factory import _component_factory  # noqa: PLC0415  # pyright: ignore[reportPrivateUsage]

        # self.id: int = data.get("id")
        components: list[AllowedSectionComponents] = cast(
            "list[AllowedSectionComponents]",
            [_component_factory(d, state=state) for d in payload.get("", [])],
        )
        accessory: AllowedSectionAccessoryComponents | None = None
        if _accessory := payload.get("accessory"):
            accessory = cast("AllowedSectionAccessoryComponents", _component_factory(_accessory, state=state))
        return cls(
            components=components,
            accessory=accessory,
            id=payload.get("id"),
        )

    @override
    def to_dict(self) -> SectionComponentPayload:
        payload: SectionComponentPayload = {  # pyright: ignore[reportAssignmentType]
            "type": int(self.type),
            "id": self.id,
            "components": [c.to_dict() for c in self.components],
        }
        if self.accessory:
            payload["accessory"] = self.accessory.to_dict()
        return payload

    @override
    def walk_components(self) -> Iterator[AllowedSectionComponents | AllowedSectionAccessoryComponents]:
        yield from super().walk_components()
        if self.accessory:
            yield self.accessory
