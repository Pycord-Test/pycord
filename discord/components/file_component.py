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
from ..types.component_types import FileComponent as FileComponentPayload
from .component import Component, StateComponentMixin
from .unfurled_media_item import UnfurledMediaItem

if TYPE_CHECKING:
    from typing_extensions import Self

    from ..state import ConnectionState


class FileComponent(StateComponentMixin[FileComponentPayload], Component[FileComponentPayload]):
    """Represents a File from Components V2.

    This component displays a downloadable file in a message.

    This inherits from :class:`Component`.

    .. versionadded:: 2.7
    .. versionchanged:: 3.0

    Attributes
    ----------
    type: Literal[:data:`ComponentType.file`]
        The type of component.
    file: :class:`UnfurledMediaItem`
        The file's media item.
    name: :class:`str`
        The file's name.
    size: :class:`int`
        The file's size in bytes.
    spoiler: :class:`bool` | :data:`None`
        Whether the file has the spoiler overlay.

    Parameters
    ----------
    url: :class:`str`
        The URL of this media gallery item. This HAS to be an ``attachment://`` URL to work with local files.
    spoiler:
        Whether the file has the spoiler overlay. Defaults to :data:`False`.
    id:
        The component's ID. If not provided by the user, it is set sequentially by Discord.
        The ID `0` is treated as if no ID was provided.
    size:
        The file's size in bytes. If not provided, it is set to :data:`None`.
    name:
        The file's name. If not provided, it is set to :data:`None`.
    """

    __slots__: tuple[str, ...] = (
        "file",
        "spoiler",
        "name",
        "size",
    )

    __repr_info__: ClassVar[tuple[str, ...]] = __slots__
    versions: tuple[int, ...] = (2,)
    type: Literal[ComponentType.file] = ComponentType.file  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(
        self,
        url: str | UnfurledMediaItem,
        *,
        spoiler: bool | None = False,
        id: int | None = None,
        size: int | None = None,
        name: str | None = None,
    ) -> None:
        self.file: UnfurledMediaItem = url if isinstance(url, UnfurledMediaItem) else UnfurledMediaItem(url)
        self.spoiler: bool | None = bool(spoiler) if spoiler is not None else None
        self.size: int | None = size
        self.name: str | None = name
        super().__init__(id=id)

    @classmethod
    @override
    def from_payload(cls, payload: FileComponentPayload, state: ConnectionState | None = None) -> Self:
        file = UnfurledMediaItem.from_dict(payload.get("file", {}), state=state)
        return cls(
            file, spoiler=payload.get("spoiler"), id=payload.get("id"), size=payload["size"], name=payload["name"]
        )

    @override
    def to_dict(self) -> FileComponentPayload:
        payload = {"type": int(self.type), "id": self.id, "file": self.file.to_dict()}
        if self.spoiler is not None:
            payload["spoiler"] = self.spoiler
        return payload  # type: ignore  # pyright: ignore[reportReturnType]

    @property
    def url(self) -> str:
        return self.file.url

    @url.setter
    def url(self, url: str) -> None:
        self.file = UnfurledMediaItem(url)
