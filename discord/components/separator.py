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

from typing import TYPE_CHECKING, ClassVar, Literal, override

from discord.enums import ComponentType, SeparatorSpacingSize, try_enum
from discord.types.components import SeparatorComponent as SeparatorComponentPayload
from .component import Component

if TYPE_CHECKING:
    from typing_extensions import Self


class Separator(Component[SeparatorComponentPayload]):
    """Represents a Separator from Components V2.

    This is a component that visually separates components.

    This inherits from :class:`Component`.

    .. versionadded:: 2.7
    .. versionchanged:: 3.0

    Attributes
    ----------
    divider: :class:`bool`
        Whether the separator will show a horizontal line in addition to vertical spacing.
    spacing: Optional[:class:`SeparatorSpacingSize`]
        The separator's spacing size.
    """

    __slots__: tuple[str, ...] = (
        "divider",
        "spacing",
    )

    __repr_info__: ClassVar[tuple[str, ...]] = __slots__
    versions: tuple[int, ...] = (2,)
    type: Literal[ComponentType.separator] = ComponentType.separator  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(
        self, divider: bool = True, spacing: SeparatorSpacingSize = SeparatorSpacingSize.small, id: int | None = None
    ) -> None:
        self.divider: bool = divider
        self.spacing: SeparatorSpacingSize = spacing
        super().__init__(id=id)

    @classmethod
    @override
    def from_payload(cls, payload: SeparatorComponentPayload) -> Self:
        self = cls(
            divider=payload.get("divider", False), spacing=try_enum(SeparatorSpacingSize, payload.get("spacing", 1))
        )
        self.id = payload.get("id")
        return self

    @override
    def to_dict(self) -> SeparatorComponentPayload:
        return {  # pyright: ignore[reportReturnType]
            "type": int(self.type),
            "id": self.id,
            "divider": self.divider,
            "spacing": int(self.spacing),
        }  # type: ignore
