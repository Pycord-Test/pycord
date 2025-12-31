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

from typing import TYPE_CHECKING, ClassVar, Literal

from typing_extensions import override

from ..enums import ComponentType
from ..types.component_types import TextDisplayComponent as TextDisplayComponentPayload
from .component import Component, ModalComponentMixin

if TYPE_CHECKING:
    from typing_extensions import Self


class TextDisplay(ModalComponentMixin[TextDisplayComponentPayload], Component[TextDisplayComponentPayload]):
    """Represents a Text Display from Components V2.

    This is a component that displays text.

    This inherits from :class:`Component`.

    .. versionadded:: 2.7
    .. versionchanged:: 3.0

    Attributes
    ----------
    type: Literal[:data:`ComponentType.text_display`]
        The type of component.
    content: :class:`str`
        The component's text content.
    id: :class:`int` | :data:`None`
        The text display's ID.

    Parameters
    ----------
    content:
        The text content of the component. Can be markdown formatted.
    id:
        The text display's ID. If not provided, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.
    """

    __slots__: tuple[str, ...] = ("content",)  # pyright: ignore[reportIncompatibleUnannotatedOverride]

    __repr_info__: ClassVar[tuple[str, ...]] = __slots__
    versions: tuple[int, ...] = (2,)
    type: Literal[ComponentType.text_display] = ComponentType.text_display  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(self, content: str, id: int | None = None):
        self.content: str = content
        super().__init__(id=id)

    @classmethod
    @override
    def from_payload(cls, payload: TextDisplayComponentPayload) -> Self:
        return cls(
            content=payload["content"],
            id=payload.get("id"),
        )

    @override
    def to_dict(self, modal: bool = False) -> TextDisplayComponentPayload:
        return {"type": int(self.type), "id": self.id, "content": self.content}  # pyright: ignore[reportReturnType]
