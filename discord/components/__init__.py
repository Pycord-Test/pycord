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

from ._component_factory import _component_factory  # pyright: ignore[reportPrivateUsage]
from .action_row import ActionRow
from .button import Button
from .channel_select_menu import ChannelSelect
from .component import Component, ModalComponentMixin, StateComponentMixin, WalkableComponent
from .components_holder import ComponentsHolder
from .container import Container
from .default_select_option import DefaultSelectOption
from .file_component import FileComponent
from .file_upload import FileUpload
from .input_text import TextInput
from .label import Label
from .media_gallery import MediaGallery
from .media_gallery_item import MediaGalleryItem
from .mentionable_select_menu import MentionableSelect
from .modal import Modal
from .partial_components import (
    PartialButton,
    PartialChannelSelect,
    PartialComponent,
    PartialFileUpload,
    PartialLabel,
    PartialMentionableSelect,
    PartialRoleSelect,
    PartialSelect,
    PartialStringSelect,
    PartialTextDisplay,
    PartialTextInput,
    PartialUserSelect,
    PartialWalkableComponent,
    UnknownPartialComponent,
    _partial_component_factory,  # pyright: ignore[reportPrivateUsage]
)
from .role_select_menu import RoleSelect
from .section import Section
from .select_menu import Select
from .select_option import SelectOption
from .separator import Separator
from .string_select_menu import StringSelect
from .text_display import TextDisplay
from .thumbnail import Thumbnail

# Don't change the import order
from .type_aliases import (
    AnyComponent,
    AnyMessagePartialComponent,
    AnyPartialComponent,
    AnyTopLevelMessageComponent,
    AnyTopLevelModalComponent,
    AnyTopLevelModalPartialComponent,
)
from .unfurled_media_item import UnfurledMediaItem
from .unknown_component import UnknownComponent
from .user_select_menu import UserSelect

__all__ = (
    "Component",
    "StateComponentMixin",
    "WalkableComponent",
    "ModalComponentMixin",
    "ComponentsHolder",
    "ActionRow",
    "Button",
    "Select",
    "StringSelect",
    "UserSelect",
    "RoleSelect",
    "MentionableSelect",
    "ChannelSelect",
    "AnyMessagePartialComponent",
    "SelectOption",
    "DefaultSelectOption",
    "TextInput",
    "Section",
    "TextDisplay",
    "Thumbnail",
    "MediaGallery",
    "MediaGalleryItem",
    "UnfurledMediaItem",
    "FileComponent",
    "FileUpload",
    "Separator",
    "Container",
    "Label",
    "Modal",
    "UnknownComponent",
    "_component_factory",
    "PartialLabel",
    "PartialComponent",
    "PartialSelect",
    "PartialStringSelect",
    "PartialUserSelect",
    "PartialButton",
    "PartialRoleSelect",
    "PartialMentionableSelect",
    "PartialChannelSelect",
    "PartialTextInput",
    "PartialTextDisplay",
    "UnknownPartialComponent",
    "PartialFileUpload",
    "_partial_component_factory",
    "AnyComponent",
    "AnyTopLevelModalComponent",
    "AnyTopLevelMessageComponent",
    "AnyPartialComponent",
    "AnyTopLevelModalPartialComponent",
    "PartialWalkableComponent",
)
