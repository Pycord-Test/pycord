from typing import TypeAlias

from .action_row import ActionRow
from .button import Button
from .channel_select_menu import ChannelSelectMenu
from .container import Container
from .file_component import FileComponent
from .input_text import TextInput
from .interaction_components import (
    InteractionButton,
    InteractionChannelSelectMenu,
    InteractionLabel,
    InteractionMentionableSelectMenu,
    InteractionRoleSelectMenu,
    InteractionStringSelectMenu,
    InteractionTextDisplay,
    InteractionTextInput,
    InteractionUserSelectMenu,
    UnknownInteractionComponent,
)
from .label import Label
from .media_gallery import MediaGallery
from .mentionable_select_menu import MentionableSelectMenu
from .role_select_menu import RoleSelectMenu
from .section import Section
from .separator import Separator
from .string_select_menu import StringSelectMenu
from .text_display import TextDisplay
from .thumbnail import Thumbnail
from .unknown_component import UnknownComponent
from .user_select_menu import UserSelectMenu

AnyComponent: TypeAlias = (
    ActionRow
    | Button
    | StringSelectMenu
    | TextInput
    | UserSelectMenu
    | RoleSelectMenu
    | MentionableSelectMenu
    | ChannelSelectMenu
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

AnyInteractionComponent: TypeAlias = (
    InteractionLabel
    | InteractionTextInput
    | InteractionStringSelectMenu
    | InteractionTextDisplay
    | InteractionUserSelectMenu
    | InteractionRoleSelectMenu
    | InteractionMentionableSelectMenu
    | InteractionChannelSelectMenu
    | UnknownInteractionComponent
    | InteractionButton
)

AnyTopLevelModalInteractionComponent: TypeAlias = (
    InteractionLabel | InteractionTextDisplay | UnknownInteractionComponent
)

AnyMessageInteractionComponent: TypeAlias = (
    InteractionStringSelectMenu
    | InteractionUserSelectMenu
    | InteractionRoleSelectMenu
    | InteractionMentionableSelectMenu
    | InteractionButton
    | InteractionChannelSelectMenu
    | UnknownInteractionComponent
)

__all__ = ("AnyComponent",)
