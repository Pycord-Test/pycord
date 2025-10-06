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

from collections.abc import Sequence
from typing import TYPE_CHECKING, ClassVar, Literal

from typing_extensions import override

from ..enums import ComponentType
from ..types.component_types import MediaGalleryComponent as MediaGalleryComponentPayload
from .component import Component, StateComponentMixin
from .media_gallery_item import MediaGalleryItem

if TYPE_CHECKING:
    from typing_extensions import Self

    from ..state import ConnectionState


class MediaGallery(StateComponentMixin[MediaGalleryComponentPayload], Component[MediaGalleryComponentPayload]):
    """Represents a Media Gallery from Components V2.

    This is a component that displays up to 10 different :class:`MediaGalleryItem` objects.

    This inherits from :class:`Component`.

    .. versionadded:: 2.7
    .. versionchanged:: 3.0

    Attributes
    ----------
    type: Literal[:data:`ComponentType.media_gallery`]
        The type of component.
    items: List[:class:`MediaGalleryItem`]
        The media this gallery contains.
    id: :class:`int` | :data:`None`
        The media gallery's ID.

    Parameters
    ----------
    items:
        The media gallery items this gallery contains.
        Has to be passed unpacked (e.g. ``*items``).
    id:
        The component's ID. If not provided by the user, it is set sequentially by
        Discord. The ID `0` is treated as if no ID was provided.
    """

    __slots__: tuple[str, ...] = ("items",)

    __repr_info__: ClassVar[tuple[str, ...]] = __slots__
    versions: tuple[int, ...] = (2,)
    type: Literal[ComponentType.media_gallery] = ComponentType.media_gallery  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(self, *items: MediaGalleryItem, id: int | None = None):
        self.items: list[MediaGalleryItem] = list(items)
        super().__init__(id=id)

    @classmethod
    @override
    def from_payload(cls, payload: MediaGalleryComponentPayload, state: ConnectionState | None = None) -> Self:
        items = [MediaGalleryItem.from_payload(d, state=state) for d in payload.get("items", [])]
        return cls(*items, id=payload.get("id"))

    @override
    def to_dict(self) -> MediaGalleryComponentPayload:
        return {  # pyright: ignore[reportReturnType]
            "type": int(self.type),
            "id": self.id,
            "items": [i.to_dict() for i in self.items],
        }
