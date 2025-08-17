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

from typing import TYPE_CHECKING, override

from discord.asset import AssetMixin
from discord.flags import AttachmentFlags
from discord.types.components import UnfurledMediaItem as UnfurledMediaItemPayload

if TYPE_CHECKING:
    from discord.state import ConnectionState


class UnfurledMediaItem(AssetMixin):
    """Represents an Unfurled Media Item used in Components V2.

    This is used as an underlying component for other media-based components such as :class:`Thumbnail`, :class:`FileComponent`, and :class:`MediaGalleryItem`.

    .. versionadded:: 2.7

    Attributes
    ----------
    url: :class:`str`
        The URL of this media item. This can either be an arbitrary URL or an ``attachment://`` URL to work with local files.
    """

    def __init__(self, url: str):
        self._state: ConnectionState | None = None
        self._url: str = url
        self.proxy_url: str | None = None
        self.height: int | None = None
        self.width: int | None = None
        self.content_type: str | None = None
        self.flags: AttachmentFlags | None = None
        self.attachment_id: int | None = None

    @property
    @override
    def url(self) -> str:  # pyright: ignore[reportIncompatibleVariableOverride]
        """Returns this media item's url."""
        return self._url

    @classmethod
    def from_dict(cls, data: UnfurledMediaItemPayload, state: ConnectionState | None = None) -> UnfurledMediaItem:
        r = cls(data.get("url"))
        r.proxy_url = data.get("proxy_url")
        r.height = data.get("height")
        r.width = data.get("width")
        r.content_type = data.get("content_type")
        r.flags = AttachmentFlags._from_value(data.get("flags", 0))  # pyright: ignore[reportPrivateUsage]
        r.attachment_id = data.get("attachment_id")  # pyright: ignore[reportAttributeAccessIssue]
        r._state = state
        return r

    def to_dict(self) -> UnfurledMediaItemPayload:
        return {"url": self.url}  # pyright: ignore[reportReturnType]
