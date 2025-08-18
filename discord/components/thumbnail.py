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

from discord.enums import ComponentType
from discord.types.components import ThumbnailComponent as ThumbnailComponentPayload
from .component import StateComponent
from .unfurled_media_item import UnfurledMediaItem

if TYPE_CHECKING:
    from typing_extensions import Self
    from discord.state import ConnectionState


class Thumbnail(StateComponent[ThumbnailComponentPayload]):
    """Represents a Thumbnail from Components V2.

    This is a component that displays media, such as images and videos.

    This inherits from :class:`Component`.

    .. versionadded:: 2.7
    .. versionchanged:: 3.0

    Attributes
    ----------
    type: Literal[:data:`ComponentType.thumbnail`]
        The type of component.
    media: :class:`UnfurledMediaItem`
        The component's underlying media object.
    description: :class:`str` | :data:`None`
        The thumbnail's description, up to 1024 characters.
    spoiler: :class:`bool` | :data:`None`
        Whether the thumbnail has the spoiler overlay.
    id: :class:`int` | :data:`None`
        The thumbnail's ID.

    Parameters
    ----------
    url:
        The URL of the thumbnail. This can either be an arbitrary URL or an ``attachment://`` URL to work with local files.
    id:
        The thumbnail's ID. If not provided, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.
    description:
        The thumbnail's description, up to 1024 characters.
    spoiler:
        Whether the thumbnail has the spoiler overlay. Defaults to ``False``.
    """

    __slots__: tuple[str, ...] = (
        "file",
        "description",
        "spoiler",
    )

    __repr_info__: ClassVar[tuple[str, ...]] = __slots__
    versions: tuple[int, ...] = (2,)
    type: Literal[ComponentType.thumbnail] = ComponentType.thumbnail  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(
        self,
        url: str | UnfurledMediaItem,
        *,
        id: int | None = None,
        description: str | None = None,
        spoiler: bool | None = False,
    ):
        self.file: UnfurledMediaItem = url if isinstance(url, UnfurledMediaItem) else UnfurledMediaItem(url)
        self.description: str | None = description
        self.spoiler: bool | None = spoiler
        super().__init__(id=id)

    @property
    def url(self) -> str:
        """Returns the URL of this thumbnail's underlying media item."""
        return self.file.url

    @classmethod
    @override
    def from_payload(cls, payload: ThumbnailComponentPayload, state: ConnectionState | None = None) -> Self:
        file = UnfurledMediaItem.from_dict(payload.get("file", {}), state=state)
        return cls(
            url=file,
            id=payload.get("id"),
            description=payload.get("description"),
            spoiler=payload.get("spoiler", False),
        )

    @override
    def to_dict(self) -> ThumbnailComponentPayload:
        payload: ThumbnailComponentPayload = {"type": self.type, "id": self.id, "media": self.file.to_dict()}  # pyright: ignore[reportAssignmentType]
        if self.description:
            payload["description"] = self.description
        if self.spoiler is not None:
            payload["spoiler"] = self.spoiler
        return payload
