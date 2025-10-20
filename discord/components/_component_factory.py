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

from typing import TYPE_CHECKING

from .action_row import ActionRow
from .button import Button
from .channel_select_menu import ChannelSelect
from .component import Component, StateComponentMixin
from .container import Container
from .file_component import FileComponent
from .file_upload import FileUpload
from .input_text import TextInput
from .label import Label
from .media_gallery import MediaGallery
from .mentionable_select_menu import MentionableSelect
from .role_select_menu import RoleSelect
from .section import Section
from .separator import Separator
from .string_select_menu import StringSelect
from .text_display import TextDisplay
from .thumbnail import Thumbnail
from .types import P
from .unknown_component import UnknownComponent
from .user_select_menu import UserSelect

if TYPE_CHECKING:
    from ..state import ConnectionState


COMPONENT_MAPPINGS = {
    1: ActionRow,
    2: Button,
    3: StringSelect,
    4: TextInput,
    5: UserSelect,
    6: RoleSelect,
    7: MentionableSelect,
    8: ChannelSelect,
    9: Section,
    10: TextDisplay,
    11: Thumbnail,
    12: MediaGallery,
    13: FileComponent,
    14: Separator,
    17: Container,
    18: Label,
    19: FileUpload,
}

STATE_COMPONENTS = (Section, Container, Thumbnail, MediaGallery, FileComponent)


def _component_factory(data: P, state: ConnectionState | None = None) -> Component[P]:
    component_type = data["type"]
    if cls := COMPONENT_MAPPINGS.get(component_type):
        if issubclass(cls, StateComponentMixin):
            return cls.from_payload(data, state=state)  # pyright: ignore[ reportReturnType, reportArgumentType]
        else:
            return cls.from_payload(data)  # pyright: ignore[reportArgumentType,  reportReturnType]
    else:
        return UnknownComponent.from_payload(data)  # pyright: ignore[reportReturnType]


__all__ = ("_component_factory",)
