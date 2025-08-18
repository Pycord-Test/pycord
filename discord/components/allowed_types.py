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

from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from .text_display import TextDisplay
    from .button import Button
    from .thumbnail import Thumbnail
    from .input_text import InputText
    from .select_menu import SelectMenu
    from .string_select_menu import StringSelectMenu
    from .user_select_menu import UserSelectMenu
    from .role_select_menu import RoleSelectMenu
    from .mentionable_select_menu import MentionableSelectMenu
    from .channel_select_menu import ChannelSelectMenu
    from .action_row import ActionRow
    from .section import Section
    from .media_gallery import MediaGallery
    from .separator import Separator
    from .file_component import FileComponent
    from .container import Container
    from .unknown_component import UnknownComponent
    from .types import SelectMenuTypes

AllowedSectionComponents: TypeAlias = "TextDisplay"
AllowedSectionAccessoryComponents: TypeAlias = "Button | Thumbnail"
AllowedActionRowComponents: TypeAlias = "Button | InputText | SelectMenu[SelectMenuTypes]"
AllowedContainerComponents: TypeAlias = "ActionRow | TextDisplay | Section | MediaGallery | Separator | FileComponent"

AnyComponent: TypeAlias = "ActionRow | Button | StringSelectMenu | InputText | UserSelectMenu | RoleSelectMenu | MentionableSelectMenu | ChannelSelectMenu | Section | TextDisplay | Thumbnail | MediaGallery | FileComponent | Separator | Container | UnknownComponent"
