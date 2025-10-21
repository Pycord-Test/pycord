from typing import TypeAlias

from .action_row import ActionRow
from .button import Button
from .channel_select_menu import ChannelSelect
from .container import Container
from .file_component import FileComponent
from .label import Label
from .media_gallery import MediaGallery
from .mentionable_select_menu import MentionableSelect
from .partial_components import (
    PartialButton,
    PartialChannelSelect,
    PartialLabel,
    PartialMentionableSelect,
    PartialRoleSelect,
    PartialStringSelect,
    PartialTextDisplay,
    PartialTextInput,
    PartialUserSelect,
    UnknownPartialComponent,
)
from .role_select_menu import RoleSelect
from .section import Section
from .separator import Separator
from .string_select_menu import StringSelect
from .text_display import TextDisplay
from .text_input import TextInput
from .thumbnail import Thumbnail
from .unknown_component import UnknownComponent
from .user_select_menu import UserSelect

AnyComponent: TypeAlias = (
    ActionRow
    | Button
    | StringSelect
    | TextInput
    | UserSelect
    | RoleSelect
    | MentionableSelect
    | ChannelSelect
    | Section
    | TextDisplay
    | Thumbnail
    | MediaGallery
    | FileComponent
    | Separator
    | Container
    | Label
    | UnknownComponent
)

AnyTopLevelMessageComponent: TypeAlias = (
    ActionRow | Section | TextDisplay | MediaGallery | FileComponent | Separator | Container
)

AnyTopLevelModalComponent: TypeAlias = TextDisplay | Label

AnyPartialComponent: TypeAlias = (
    PartialLabel
    | PartialTextInput
    | PartialStringSelect
    | PartialTextDisplay
    | PartialUserSelect
    | PartialRoleSelect
    | PartialMentionableSelect
    | PartialChannelSelect
    | UnknownPartialComponent
    | PartialButton
)

AnyTopLevelModalPartialComponent: TypeAlias = PartialLabel | PartialTextDisplay | UnknownPartialComponent

AnyMessagePartialComponent: TypeAlias = (
    PartialStringSelect
    | PartialUserSelect
    | PartialRoleSelect
    | PartialMentionableSelect
    | PartialButton
    | PartialChannelSelect
    | UnknownPartialComponent
)

__all__ = (
    "AnyComponent",
    "AnyTopLevelMessageComponent",
    "AnyTopLevelModalComponent",
    "AnyPartialComponent",
    "AnyTopLevelModalPartialComponent",
    "AnyMessagePartialComponent",
)
