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

from this import s
from typing import Literal, TypeAlias, Union, Generic, TypeVar

from typing_extensions import NotRequired, TypedDict

from .channel import ChannelType
from .emoji import PartialEmoji
from .snowflake import Snowflake

ComponentType = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 17]
ButtonStyle = Literal[1, 2, 3, 4, 5, 6]
TextInputStyle = Literal[1, 2]
SeparatorSpacingSize = Literal[1, 2]


class BaseComponent(TypedDict):
    type: ComponentType
    id: NotRequired[int]


class ButtonComponent(BaseComponent):
    type: Literal[2]  # pyright: ignore[reportIncompatibleVariableOverride]
    style: ButtonStyle
    label: NotRequired[str]
    emoji: NotRequired[PartialEmoji]
    custom_id: NotRequired[str]
    url: NotRequired[str]
    disabled: NotRequired[bool]
    sku_id: NotRequired[Snowflake]


class TextInput(BaseComponent):
    type: Literal[4]  # pyright: ignore[reportIncompatibleVariableOverride]
    min_length: NotRequired[int]
    max_length: NotRequired[int]
    required: NotRequired[bool]
    placeholder: NotRequired[str]
    value: NotRequired[str]
    style: TextInputStyle
    custom_id: str
    label: str


class SelectOption(TypedDict):
    description: NotRequired[str]
    emoji: NotRequired[PartialEmoji]
    label: str
    value: str
    default: bool


T = TypeVar("T", bound=Literal["user", "role", "channel"])


class SelectDefaultValue(TypedDict, Generic[T]):
    id: int
    type: T


class StringSelect(BaseComponent):
    type: Literal[3]  # pyright: ignore[reportIncompatibleVariableOverride]
    custom_id: str
    options: list[SelectOption]
    placeholder: NotRequired[str]
    min_values: NotRequired[int]
    max_values: NotRequired[int]
    disabled: NotRequired[bool]
    required: NotRequired[bool]


class UserSelect(BaseComponent):
    type: Literal[5]  # pyright: ignore[reportIncompatibleVariableOverride]
    custom_id: str
    placeholder: NotRequired[str]
    default_values: NotRequired[list[SelectDefaultValue[Literal["user"]]]]
    min_values: NotRequired[int]
    max_values: NotRequired[int]
    disabled: NotRequired[bool]
    required: NotRequired[bool]


class RoleSelect(BaseComponent):
    type: Literal[6]  # pyright: ignore[reportIncompatibleVariableOverride]
    custom_id: str
    placeholder: NotRequired[str]
    default_values: NotRequired[list[SelectDefaultValue[Literal["role"]]]]
    min_values: NotRequired[int]
    max_values: NotRequired[int]
    disabled: NotRequired[bool]
    required: NotRequired[bool]


class MentionableSelect(BaseComponent):
    type: Literal[7]  # pyright: ignore[reportIncompatibleVariableOverride]
    custom_id: str
    placeholder: NotRequired[str]
    default_values: NotRequired[list[SelectDefaultValue[Literal["role", "user"]]]]
    min_values: NotRequired[int]
    max_values: NotRequired[int]
    disabled: NotRequired[bool]
    required: NotRequired[bool]


class ChannelSelect(BaseComponent):
    type: Literal[8]  # pyright: ignore[reportIncompatibleVariableOverride]
    custom_id: str
    channel_types: NotRequired[list[ChannelType]]
    placeholder: NotRequired[str]
    default_values: NotRequired[list[SelectDefaultValue[Literal["channel"]]]]
    min_values: NotRequired[int]
    max_values: NotRequired[int]
    disabled: NotRequired[bool]
    required: NotRequired[bool]


class SectionComponent(BaseComponent):
    type: Literal[9]  # pyright: ignore[reportIncompatibleVariableOverride]
    components: list[TextDisplayComponent]
    accessory: NotRequired[ThumbnailComponent | ButtonComponent]


class TextDisplayComponent(BaseComponent):
    type: Literal[10]  # pyright: ignore[reportIncompatibleVariableOverride]
    content: str


class UnfurledMediaItem(TypedDict):
    url: str
    proxy_url: str
    height: NotRequired[int | None]
    width: NotRequired[int | None]
    content_type: NotRequired[str]
    flags: NotRequired[int]
    attachment_id: NotRequired[Snowflake]


class ThumbnailComponent(BaseComponent):
    type: Literal[11]  # pyright: ignore[reportIncompatibleVariableOverride]
    media: UnfurledMediaItem
    description: NotRequired[str]
    spoiler: NotRequired[bool]


class MediaGalleryItem(TypedDict):
    media: UnfurledMediaItem
    description: NotRequired[str]
    spoiler: NotRequired[bool]


class MediaGalleryComponent(BaseComponent):
    type: Literal[12]  # pyright: ignore[reportIncompatibleVariableOverride]
    items: list[MediaGalleryItem]


class FileComponent(BaseComponent):
    type: Literal[13]  # pyright: ignore[reportIncompatibleVariableOverride]
    file: UnfurledMediaItem
    spoiler: NotRequired[bool]
    name: str
    size: int


class SeparatorComponent(BaseComponent):
    type: Literal[14]  # pyright: ignore[reportIncompatibleVariableOverride]
    divider: NotRequired[bool]
    spacing: NotRequired[SeparatorSpacingSize]


AllowedActionRowComponents = Union[
    ButtonComponent, TextInput, StringSelect, UserSelect, RoleSelect, MentionableSelect, ChannelSelect
]


class ActionRow(BaseComponent):
    type: Literal[1]  # pyright: ignore[reportIncompatibleVariableOverride]
    components: list[AllowedActionRowComponents]


AllowedContainerComponents = Union[
    ActionRow,
    TextDisplayComponent,
    MediaGalleryComponent,
    FileComponent,
    SeparatorComponent,
    SectionComponent,
]


class ContainerComponent(BaseComponent):
    type: Literal[17]  # pyright: ignore[reportIncompatibleVariableOverride]
    accent_color: NotRequired[int]
    spoiler: NotRequired[bool]
    components: list[AllowedContainerComponents]


AllowedLabelComponents: TypeAlias = TextDisplayComponent | StringSelect


class LabelComponent(BaseComponent):
    type: Literal[18]  # pyright: ignore[reportIncompatibleVariableOverride]
    component: AllowedLabelComponents
    label: str
    description: NotRequired[str]


Component = Union[
    ActionRow,
    ButtonComponent,
    StringSelect,
    UserSelect,
    RoleSelect,
    MentionableSelect,
    ChannelSelect,
    TextInput,
    TextDisplayComponent,
    SectionComponent,
    ThumbnailComponent,
    MediaGalleryComponent,
    FileComponent,
    SeparatorComponent,
    ContainerComponent,
    LabelComponent,
]

AllowedModalComponents = LabelComponent


class Modal(TypedDict):
    title: str
    custom_id: str
    components: list[AllowedModalComponents]
