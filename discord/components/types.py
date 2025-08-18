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

from typing import TYPE_CHECKING, TypeVar, TypeAlias, Literal

from ..types.components import (
    StringSelect as StringSelectPayload,
    ChannelSelect as ChannelSelectPayload,
    RoleSelect as RoleSelectPayload,
    MentionableSelect as MentionableSelectPayload,
    UserSelect as UserSelectPayload,
    Component as ComponentPayload,
)

if TYPE_CHECKING:
    from ..emoji import AppEmoji, GuildEmoji
    from ..partial_emoji import PartialEmoji
    from .component import Component
    from .action_row import ActionRow
    from .button import Button
    from .string_select_menu import StringSelectMenu
    from .input_text import InputText
    from .user_select_menu import UserSelectMenu
    from .role_select_menu import RoleSelectMenu
    from .mentionable_select_menu import MentionableSelectMenu
    from .channel_select_menu import ChannelSelectMenu
    from .section import Section
    from .text_display import TextDisplay
    from .thumbnail import Thumbnail
    from .media_gallery import MediaGallery
    from .file_component import FileComponent
    from .separator import Separator
    from .container import Container
    from .unknown_component import UnknownComponent


AnyEmoji: TypeAlias = "GuildEmoji | AppEmoji | PartialEmoji"


P = TypeVar("P", bound="ComponentPayload", covariant=True)
C = TypeVar("C", bound="Component[ComponentPayload]", covariant=True)
DT = TypeVar("DT", bound='Literal["user", "role", "channel"]')

SelectMenuTypes: TypeAlias = (
    StringSelectPayload | ChannelSelectPayload | RoleSelectPayload | MentionableSelectPayload | UserSelectPayload
)

T = TypeVar("T", bound="SelectMenuTypes")

AnyComponent: TypeAlias = "ActionRow | Button | StringSelectMenu | InputText | UserSelectMenu | RoleSelectMenu | MentionableSelectMenu | ChannelSelectMenu | Section | TextDisplay | Thumbnail | MediaGallery | FileComponent | Separator | Container | UnknownComponent"
