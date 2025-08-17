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

from typing import TYPE_CHECKING, override

from discord.enums import ComponentType, try_enum
from discord.types.components import Component as ComponentPayload
from .component import Component

if TYPE_CHECKING:
    from typing_extensions import Self


class UnknownComponent(Component[ComponentPayload]):
    """Represents an unknown component.

    This is used when the component type is not recognized by the library,
    for example if a new component is introduced by Discord.

    .. versionadded:: 3.0

    Attributes
    ----------
    type: :class:`ComponentType`
        The type of the unknown component.

    """

    __slots__: tuple[str, ...] = ("type",)

    def __init__(self, type: ComponentType, id: int | None = None) -> None:
        self.type: ComponentType = type
        super().__init__(id=id)

    @override
    def to_dict(self) -> ComponentPayload:
        return {"type": int(self.type)}  # pyright: ignore[reportReturnType]

    @classmethod
    @override
    def from_payload(cls, payload: ComponentPayload) -> Self:
        type_ = try_enum(ComponentType, payload.pop("type", 0))
        self = cls(type_, id=payload.pop("id", None))
        for key, value in payload.items():
            setattr(self, key, value)
        return self
