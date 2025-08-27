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

from typing import TYPE_CHECKING, TypeAlias

from ..types.components import Modal as ModalPayload

if TYPE_CHECKING:
    from .label import Label
    from .text_display import TextDisplay

AllowedModalComponents: TypeAlias = "Label | TextDisplay"


class Modal:
    """
    Represents a modal. Used when sending modals with :meth:`InteractionResponse.send_modal`

    ..versionadded:: 3.0

    Attributes
    ----------
    title: :class:`str`
        The title of the modal. This is shown at the top of the modal.
    custom_id: :class:`str`
        The custom ID of the modal. This is received during an interaction.
    components: List[:class:`Label` | :class:`TextDisplay`]
        The components in the modal.

    Parameters
    ----------
    components:
        The components this modal holds.
        Has to be passed unpacked (e.g. ``*components``).
    title:
        The title of the modal. This is shown at the top of the modal.
    custom_id:
        The custom ID of the modal. This is received during an interaction.
    """

    def __init__(
        self,
        *components: AllowedModalComponents,
        title: str,
        custom_id: str,
    ) -> None:
        self.title: str = title
        self.custom_id: str = custom_id
        self.components: list[AllowedModalComponents] = list(components)

    def to_dict(self) -> ModalPayload:
        return {
            "title": self.title,
            "custom_id": self.custom_id,
            "components": [component.to_dict(modal=True) for component in self.components],
        }
