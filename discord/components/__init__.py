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
from .channel_select_menu import ChannelSelectMenu
from .component import Component, ModalComponentMixin, StateComponent, WalkableComponent
from .components_sequence import ComponentsHolder
from .container import Container
from .default_select_option import DefaultSelectOption
from .file_component import FileComponent
from .input_text import TextInput
from .interaction_components import (
    InteractionButton,
    InteractionChannelSelect,
    InteractionComponent,
    InteractionLabel,
    InteractionMentionableSelect,
    InteractionRoleSelect,
    InteractionSelect,
    InteractionStringSelect,
    InteractionTextDisplay,
    InteractionTextInput,
    InteractionUserSelect,
    InteractionWalkableComponent,
    UnknownInteractionComponent,
    _interaction_component_factory,  # pyright: ignore[reportPrivateUsage]
)
from .label import Label
from .media_gallery import MediaGallery
from .media_gallery_item import MediaGalleryItem
from .mentionable_select_menu import MentionableSelectMenu
from .modal import Modal
from .role_select_menu import RoleSelectMenu
from .section import Section
from .select_menu import SelectMenu
from .select_option import SelectOption
from .separator import Separator
from .string_select_menu import StringSelectMenu
from .text_display import TextDisplay
from .thumbnail import Thumbnail

# Don't change the import order
from .type_aliases import (
    AnyComponent,
    AnyInteractionComponent,
    AnyMessageInteractionComponent,
    AnyTopLevelMessageComponent,
    AnyTopLevelModalComponent,
    AnyTopLevelModalInteractionComponent,
)
from .unfurled_media_item import UnfurledMediaItem
from .unknown_component import UnknownComponent
from .user_select_menu import UserSelectMenu

__all__ = (
    "Component",
    "StateComponent",
    "WalkableComponent",
    "ModalComponentMixin",
    "ComponentsHolder",
    "ActionRow",
    "Button",
    "SelectMenu",
    "StringSelectMenu",
    "UserSelectMenu",
    "RoleSelectMenu",
    "MentionableSelectMenu",
    "ChannelSelectMenu",
    "AnyMessageInteractionComponent",
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
    "Separator",
    "Container",
    "Label",
    "Modal",
    "UnknownComponent",
    "_component_factory",
    "InteractionLabel",
    "InteractionComponent",
    "InteractionSelect",
    "InteractionStringSelect",
    "InteractionUserSelect",
    "InteractionButton",
    "InteractionRoleSelect",
    "InteractionMentionableSelect",
    "InteractionChannelSelect",
    "InteractionTextInput",
    "InteractionTextDisplay",
    "UnknownInteractionComponent",
    "_interaction_component_factory",
    "AnyComponent",
    "AnyTopLevelModalComponent",
    "AnyTopLevelMessageComponent",
    "AnyInteractionComponent",
    "AnyTopLevelModalInteractionComponent",
    "InteractionWalkableComponent",
)
