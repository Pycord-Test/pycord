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

from discord.enums import ComponentType
from discord.types.components import ActionRow as ActionRowPayload
from .component import WalkableComponent
from .allowed_types import AllowedActionRowComponents

if TYPE_CHECKING:
    from typing_extensions import Self


class ActionRow(WalkableComponent["ActionRowPayload", "AllowedActionRowComponents"]):
    """Represents a Discord Bot UI Kit Action Row.

    This is a component that holds up to 5 children components in a row.

    This inherits from :class:`Component`.

    .. versionadded:: 2.0
    .. versionchanged:: 3.0

    Attributes
    ----------
    type: :class:`ComponentType`
        The type of component.
    components: List[:class:`AllowedActionRowComponents`]
        The components that this ActionRow holds, if any.
    id: Optional[:class:`int`]
        The action row's ID. If not provided, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.

    Parameters
    ----------
    components: Sequence[:class:`AllowedActionRowComponents`]

    """

    __slots__: tuple[str, ...] = ("components",)

    __repr_info__: ClassVar[tuple[str, ...]] = __slots__
    versions: tuple[int, ...] = (1, 2)
    type: Literal[ComponentType.action_row] = ComponentType.action_row  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(self, *components: Sequence[AllowedActionRowComponents], id: int | None = None) -> None:
        self.components: list[AllowedActionRowComponents] = list(components)
        super().__init__(id=id)

    @classmethod
    @override
    def from_payload(cls, payload: ActionRowPayload) -> Self:
        from ._component_factory import _component_factory  # noqa: PLC0415

        components: list[AllowedActionRowComponents] = cast(
            "list[AllowedActionRowComponents]", [_component_factory(d) for d in payload.get("", [])]
        )
        return cls(*components, id=payload.get("id"))

    @property
    def width(self):
        """Return the sum of the components' widths."""
        return sum(getattr(c, "width", 0) for c in self.components)

    @override
    def to_dict(self) -> ActionRowPayload:
        return {  # pyright: ignore[reportReturnType]
            "type": int(self.type),
            "id": self.id,
            "components": [component.to_dict() for component in self.components],
        }  # type: ignore
