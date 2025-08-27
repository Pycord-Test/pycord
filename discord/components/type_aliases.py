from typing import TypeAlias
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

AnyComponent: TypeAlias = (
    ActionRow
    | Button
    | StringSelectMenu
    | InputText
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
    | UnknownComponent
)

__all__ = ("AnyComponent",)
