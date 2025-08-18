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

from typing import TYPE_CHECKING

from discord.types.components import MediaGalleryItem as MediaGalleryItemPayload
from .unfurled_media_item import UnfurledMediaItem

if TYPE_CHECKING:
    from discord.state import ConnectionState


class MediaGalleryItem:
    """Represents an item used in the :class:`MediaGallery` component.

    .. versionadded:: 2.7
    .. versionchanged:: 3.0

    Attributes
    ----------
    media: :class:`UnfurledMediaItem`
        The :class:`UnfurledMediaItem` associated with this media gallery item.
    description: :class:`str` | :class:`None`
        The gallery item's description, up to 1024 characters.
    spoiler: :class:`bool`
        Whether the gallery item is a spoiler.

    Parameters
    ----------
    url: :class:`str`
        The URL of this media gallery item. This can either be an arbitrary URL or an ``attachment://`` URL to work with local files.
    description:
        The description of this media gallery item, up to 1024 characters. Defaults to :data:`None`.
    spoiler:
        Whether this media gallery item has a spoiler overlay. Defaults to :data:`False`.
    """

    def __init__(self, url: str | UnfurledMediaItem, *, description: str | None = None, spoiler: bool = False):
        self._state: ConnectionState | None = None
        self.media: UnfurledMediaItem = UnfurledMediaItem(url) if isinstance(url, str) else url
        self.description: str | None = description
        self.spoiler: bool = spoiler

    @property
    def url(self) -> str:
        """Returns the URL of this gallery's underlying media item."""
        return self.media.url

    def is_dispatchable(self) -> bool:
        return False

    @classmethod
    def from_payload(cls, data: MediaGalleryItemPayload, state: ConnectionState | None = None) -> MediaGalleryItem:
        media = (umi := data.get("media")) and UnfurledMediaItem.from_dict(umi, state=state)
        description = data.get("description")
        spoiler = data.get("spoiler", False)

        r = cls(
            url=media,
            description=description,
            spoiler=spoiler,
        )
        r._state = state
        return r

    def to_dict(self) -> MediaGalleryItemPayload:
        payload: MediaGalleryItemPayload = {"media": self.media.to_dict()}
        if self.description:
            payload["description"] = self.description
        payload["spoiler"] = self.spoiler
        return payload
